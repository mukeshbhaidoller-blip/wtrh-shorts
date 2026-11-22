@echo off
title YouTube login for the uploader (one time)
echo.
echo  Ek Chrome window khulegi. Usme apne Google account se login karo
echo  (wahi account jisme "Wait, That Really Happened" channel hai).
echo  YouTube Studio khul jaye to Chrome band kar do. Bas.
echo.
start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --user-data-dir="D:\Ai Video Edit\_claude\yt-profile" --no-first-run "https://studio.youtube.com"
