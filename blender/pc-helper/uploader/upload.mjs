// Free YouTube uploader: drives YouTube Studio in a real Chrome (owner's own signed-in profile), no API, no Zapier.
// Usage: node upload.mjs <meta.json>
// meta.json: { "video": "D:\\...\\final.mp4", "title": "...", "description": "...", "tags": ["a","b"],
//              "date": "24 Nov 2026", "time": "22:30",            // IST, as Studio shows it (15-minute steps)
//              "channel": "UCEbKzlOb63pBdElUTl9wRvg",
//              "telegram_file": "D:\\...\\share.mp4", "telegram_caption": "..." (optional) }
// Writes <meta dir>/upload-result.json and step screenshots in <meta dir>/upload-shots/.
import { chromium } from 'playwright-core';
import fs from 'node:fs';
import path from 'node:path';
import { execFileSync, spawn } from 'node:child_process';

const metaPath = process.argv[2];
const meta = JSON.parse(fs.readFileSync(metaPath, 'utf8').replace(/^\uFEFF/, ''));
const dir = path.dirname(metaPath);
const shots = path.join(dir, 'upload-shots'); fs.mkdirSync(shots, { recursive: true });
const resultPath = path.join(dir, 'upload-result.json');
const PROFILE = 'D:\\Ai Video Edit\\_claude\\yt-profile';
const CHROME = ['C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
  'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe',
  path.join(process.env.LOCALAPPDATA || '', 'Google\\Chrome\\Application\\chrome.exe')].find(p => fs.existsSync(p));
const CH = meta.channel || 'UCEbKzlOb63pBdElUTl9wRvg';
const log = [];
const say = (m) => { const l = new Date().toISOString() + ' ' + m; console.log(l); log.push(l); };
const done = (obj) => { fs.writeFileSync(resultPath, JSON.stringify({ ...obj, log }, null, 1)); };
const sleep = (ms) => new Promise(r => setTimeout(r, ms));
let n = 0;

async function main() {
  if (!fs.existsSync(meta.video)) throw new Error('video file missing: ' + meta.video);
  const ctx = await chromium.launchPersistentContext(PROFILE, {
    executablePath: CHROME, headless: false, viewport: { width: 1280, height: 900 },
    ignoreDefaultArgs: ['--enable-automation'], args: ['--disable-blink-features=AutomationControlled', '--no-first-run'],
  });
  const page = ctx.pages()[0] || await ctx.newPage();
  const snap = async (name) => { try { await page.screenshot({ path: path.join(shots, `${String(++n).padStart(2, '0')}-${name}.png`) }); } catch {} };
  try {
    say('open studio');
    await page.goto(`https://studio.youtube.com/channel/${CH}/videos/upload?d=ud`, { waitUntil: 'domcontentloaded', timeout: 90000 });
    await sleep(6000); await snap('open');
    if (/accounts\.google\.com/.test(page.url())) throw new Error('NOT_LOGGED_IN: run D:\\Ai Video Edit\\_claude\\uploader\\login.bat once');
    const chan = await page.evaluate(() => (window.ytcfg && ytcfg.get && ytcfg.get('CHANNEL_ID')) || '');
    say('channel ' + chan);
    if (chan !== CH) throw new Error('WRONG_CHANNEL ' + chan);

    // file
    let input = page.locator('ytcp-uploads-file-picker input[type=file]');
    if (!(await input.count())) {
      await page.getByRole('button', { name: /upload videos|select files/i }).first().click().catch(() => {});
      await sleep(2000); input = page.locator('ytcp-uploads-file-picker input[type=file]');
    }
    await input.setInputFiles(meta.video);
    say('file set'); await sleep(8000); await snap('file');

    // title + description (contenteditable boxes)
    const title = page.locator('#title-textarea #textbox, ytcp-social-suggestions-textbox#title-textarea [contenteditable="true"]').first();
    await title.waitFor({ timeout: 120000 });
    await title.click(); await page.keyboard.press('Control+A'); await page.keyboard.press('Delete');
    await page.keyboard.insertText(meta.title);
    const desc = page.locator('#description-textarea #textbox, ytcp-social-suggestions-textbox#description-textarea [contenteditable="true"]').first();
    await desc.click(); await page.keyboard.press('Control+A'); await page.keyboard.press('Delete');
    const lines = meta.description.split('\n');
    for (let i = 0; i < lines.length; i++) { if (lines[i]) await page.keyboard.insertText(lines[i]); if (i < lines.length - 1) await page.keyboard.press('Enter'); }
    say('title+description'); await snap('details');

    // made for kids: No
    const nk = page.locator('tp-yt-paper-radio-button[name="VIDEO_MADE_FOR_KIDS_NOT_MFK"]');
    if (await nk.count()) { await nk.scrollIntoViewIfNeeded(); await nk.click(); }
    else await page.getByRole('radio', { name: /not made for kids/i }).click();
    say('not made for kids');

    // tags
    if (meta.tags && meta.tags.length) {
      await page.locator('#toggle-button').first().click().catch(() => {});
      await sleep(1000);
      const tags = page.locator('#tags-container input, ytcp-free-text-chip-bar input').first();
      if (await tags.count()) { await tags.scrollIntoViewIfNeeded(); await tags.click(); await page.keyboard.insertText(meta.tags.join(',') + ','); say('tags'); }
      else say('tags box not found (skipped)');
    }
    await snap('tags');

    // next x3
    for (let i = 0; i < 3; i++) { await page.locator('#next-button').click(); await sleep(2500); }
    await snap('visibility');

    // schedule
    await page.locator('#second-container-expand-button').click().catch(async () => { await page.getByText('Schedule', { exact: true }).first().click(); });
    await sleep(1500);
    await page.locator('#datepicker-trigger').click(); await sleep(800);
    const dateIn = page.locator('ytcp-date-picker tp-yt-paper-input input, ytcp-date-picker input').first();
    await dateIn.fill(meta.date); await dateIn.press('Enter'); await sleep(1000);
    const timeIn = page.locator('#time-of-day-container input, ytcp-form-input-container#time-of-day-container input').first();
    await timeIn.click(); await timeIn.fill(meta.time); await timeIn.press('Enter'); await sleep(1000);
    const shown = await page.evaluate(() => {
      const d = document.querySelector('#datepicker-trigger'); const t = document.querySelector('#time-of-day-container input');
      return { date: d ? d.innerText.trim() : '', time: t ? t.value : '' };
    });
    say('schedule shown ' + JSON.stringify(shown)); await snap('schedule');
    if (!shown.date.includes(meta.date.split(' ')[0]) || shown.time !== meta.time) throw new Error('SCHEDULE_NOT_SET ' + JSON.stringify(shown));

    // wait for the upload itself to finish before scheduling/closing
    for (let i = 0; i < 120; i++) {
      const st = await page.evaluate(() => (document.querySelector('ytcp-video-upload-progress') || {}).innerText || '');
      if (!/upload(ing)?\s+\d+%|uploading/i.test(st)) { say('upload status: ' + st.replace(/\s+/g, ' ').slice(0, 80)); break; }
      await sleep(5000);
    }
    await page.locator('#done-button').click();
    say('clicked schedule'); await sleep(8000); await snap('done');

    const link = await page.evaluate(() => {
      const a = [...document.querySelectorAll('a')].map(x => x.href).find(h => /youtube\.com\/shorts\/|youtu\.be\//.test(h));
      return a || (document.body.innerText.match(/(https?:\/\/)?(youtube\.com\/shorts\/|youtu\.be\/)[\w-]+/) || [''])[0];
    });
    const id = (link.match(/(?:shorts\/|youtu\.be\/)([\w-]{6,})/) || [])[1] || '';
    const body = await page.evaluate(() => document.body.innerText);
    const ok = /Video scheduled|will be set to public on|scheduled/i.test(body) && !!id;
    say('result ' + ok + ' ' + link);
    if (!ok) throw new Error('NOT_CONFIRMED ' + link);

    let telegram = 'skipped';
    if (meta.telegram_file && fs.existsSync(meta.telegram_file)) {
      const cap = path.join(dir, 'telegram-caption.txt');
      fs.writeFileSync(cap, (meta.telegram_caption || meta.title) + `\nhttps://youtube.com/shorts/${id}`, 'utf8');
      try {
        telegram = execFileSync('powershell', ['-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', 'D:\\Ai Video Edit\\_claude\\send-telegram.ps1',
          '-File', meta.telegram_file, '-CaptionFile', cap], { encoding: 'utf8' }).trim();
      } catch (e) { telegram = 'TELEGRAM FAILED ' + String(e.stdout || e.message).slice(0, 200); }
    }
    done({ ok: true, id, url: `https://youtube.com/shorts/${id}`, telegram });
    // owner's wish: once it is scheduled on YouTube AND delivered on Telegram, free the disk space.
    // Keep a tiny record in jobs\_uploaded\<job>.json, then delete the whole job folder a minute later
    // (after the PC helper has finished writing done.txt).
    try {
      const rec = path.join(path.dirname(dir), '_uploaded'); fs.mkdirSync(rec, { recursive: true });
      fs.writeFileSync(path.join(rec, path.basename(dir) + '.json'), JSON.stringify({ ok: true, id, url: `https://youtube.com/shorts/${id}`,
        title: meta.title, date: meta.date, time: meta.time, telegram, at: new Date().toISOString() }, null, 1));
      if (/^TELEGRAM OK/.test(telegram) && /\\jobs\\[^\\]+$/i.test(dir)) {
        spawn('cmd.exe', ['/c', `timeout /t 90 /nobreak > nul & rd /s /q "${dir}"`], { detached: true, stdio: 'ignore', windowsHide: true }).unref();
        say('job folder will be deleted');
      }
    } catch (e) { say('cleanup skipped ' + e.message); }
  } catch (e) {
    say('ERROR ' + e.message); await snap('error');
    done({ ok: false, error: e.message });
    try {
      execFileSync('powershell', ['-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', 'D:\\Ai Video Edit\\_claude\\send-telegram-text.ps1',
        '-Text', `UPLOAD FAILED: ${meta.title}\n${e.message}\nVideo PC par hai: ${meta.video}`], { encoding: 'utf8' });
    } catch {}
    process.exitCode = 1;
  } finally {
    await ctx.close().catch(() => {});
  }
}
main();
