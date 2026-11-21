$cfgPath = 'D:\Ai Video Edit\_claude\telegram.json'
Write-Host ''
Write-Host 'Telegram setup (aapka bot token sirf aapke PC par save hoga, Claude ko nahi dikhega)' -ForegroundColor Cyan
$token = Read-Host 'Apne Telegram bot ka TOKEN paste karo aur Enter dabao'
$token = $token.Trim()
try { $me = Invoke-RestMethod "https://api.telegram.org/bot$token/getMe" } catch { Write-Host 'Token galat hai. Window band karke dobara chalao.' -ForegroundColor Red; Read-Host 'Enter dabao'; exit 1 }
Write-Host ("Bot mila: @" + $me.result.username) -ForegroundColor Green
Write-Host ''
Write-Host ("Ab Telegram kholo, @" + $me.result.username + " ko koi bhi message bhejo (jaise: hi), phir yahan Enter dabao.") -ForegroundColor Yellow
Read-Host 'Message bhejne ke baad Enter'
$u = Invoke-RestMethod "https://api.telegram.org/bot$token/getUpdates"
$chat = ($u.result | Where-Object { $_.message } | Select-Object -Last 1).message.chat.id
if (-not $chat) { Write-Host 'Message nahi mila. Bot ko message bhejkar dobara chalao.' -ForegroundColor Red; Read-Host 'Enter dabao'; exit 1 }
@{ token = $token; chat_id = $chat } | ConvertTo-Json | Set-Content $cfgPath
Invoke-RestMethod "https://api.telegram.org/bot$token/sendMessage" -Method Post -Body @{ chat_id = $chat; text = 'Claude: Telegram connect ho gaya! Ab har scheduled Short yahan aayega.' } | Out-Null
Set-Content 'D:\Ai Video Edit\_claude\telegram-ok.txt' ("ok " + (Get-Date -Format o))
Write-Host 'Ho gaya! Telegram par test message check karo.' -ForegroundColor Green
Read-Host 'Enter dabao window band karne ke liye'
