param([Parameter(Mandatory=$true)][string]$File, [string]$Caption = '', [string]$CaptionFile = '')
if ($CaptionFile -and (Test-Path $CaptionFile)) { $Caption = Get-Content $CaptionFile -Raw -Encoding UTF8 }
$cfgPath = 'D:\Ai Video Edit\_claude\telegram.json'
if (-not (Test-Path $cfgPath)) { Write-Output 'TELEGRAM NOT SET UP'; exit 2 }
$cfg = Get-Content $cfgPath -Raw | ConvertFrom-Json
Add-Type -AssemblyName System.Net.Http
$client = New-Object System.Net.Http.HttpClient
$client.Timeout = [TimeSpan]::FromMinutes(10)
$form = New-Object System.Net.Http.MultipartFormDataContent
$form.Add((New-Object System.Net.Http.StringContent([string]$cfg.chat_id)), 'chat_id')
$form.Add((New-Object System.Net.Http.StringContent($Caption)), 'caption')
$form.Add((New-Object System.Net.Http.StringContent('true')), 'supports_streaming')
$fs = [System.IO.File]::OpenRead($File)
$sc = New-Object System.Net.Http.StreamContent($fs)
$sc.Headers.ContentType = [System.Net.Http.Headers.MediaTypeHeaderValue]::Parse('video/mp4')
$form.Add($sc, 'video', [System.IO.Path]::GetFileName($File))
$r = $client.PostAsync("https://api.telegram.org/bot$($cfg.token)/sendVideo", $form).Result
$body = $r.Content.ReadAsStringAsync().Result
$fs.Close()
if ($r.IsSuccessStatusCode) { Write-Output 'TELEGRAM OK' } else { Write-Output ("TELEGRAM FAILED " + [int]$r.StatusCode + ' ' + ($body -replace $cfg.token, '***')) ; exit 1 }
