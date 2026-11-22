param([Parameter(Mandatory=$true)][string]$Text)
$cfgPath = 'D:\Ai Video Edit\_claude\telegram.json'
if (-not (Test-Path $cfgPath)) { Write-Output 'TELEGRAM NOT SET UP'; exit 2 }
$cfg = Get-Content $cfgPath -Raw | ConvertFrom-Json
try { Invoke-RestMethod "https://api.telegram.org/bot$($cfg.token)/sendMessage" -Method Post -Body @{ chat_id = $cfg.chat_id; text = $Text } | Out-Null; Write-Output 'TELEGRAM OK' } catch { Write-Output 'TELEGRAM FAILED'; exit 1 }
