# Download free CC0 Poly Haven assets on the PC:  fetch-assets.ps1 -Tex "id1,id2" -Hdri "id3"
param([string]$Tex = '', [string]$Hdri = '')
$ProgressPreference = 'SilentlyContinue'; [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$assets = 'D:\Ai Video Edit\assets'; New-Item -ItemType Directory -Force -Path $assets | Out-Null
foreach ($id in ($Tex -split ',' | Where-Object { $_ })) {
  $dst = Join-Path $assets $id
  if (Test-Path (Join-Path $dst 'done.txt')) { Write-Output "tex $id cached"; continue }
  try {
    $f = Invoke-RestMethod "https://api.polyhaven.com/files/$id"; New-Item -ItemType Directory -Force -Path $dst | Out-Null
    foreach ($m in @('Diffuse','nor_gl','Rough','Displacement','arm','AO')) {
      if ($f.$m -and $f.$m.'2k' -and $f.$m.'2k'.jpg) { $u = $f.$m.'2k'.jpg.url; Invoke-WebRequest $u -OutFile (Join-Path $dst ($m + [IO.Path]::GetExtension($u))) -UseBasicParsing }
    }
    Set-Content (Join-Path $dst 'done.txt') 'ok'; Write-Output "tex $id OK"
  } catch { Write-Output "tex $id FAILED: $_" }
}
foreach ($id in ($Hdri -split ',' | Where-Object { $_ })) {
  $dst = Join-Path $assets ($id + '.hdr')
  if (Test-Path $dst) { Write-Output "hdri $id cached"; continue }
  try { $f = Invoke-RestMethod "https://api.polyhaven.com/files/$id"; Invoke-WebRequest $f.hdri.'2k'.hdr.url -OutFile $dst -UseBasicParsing; Write-Output "hdri $id OK" } catch { Write-Output "hdri $id FAILED: $_" }
}
