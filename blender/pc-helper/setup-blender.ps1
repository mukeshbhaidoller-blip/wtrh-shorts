$ErrorActionPreference = 'Continue'
$ProgressPreference = 'SilentlyContinue'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$root = 'D:\Ai Video Edit'
$log = Join-Path $root 'setup-blender-log.txt'
function L($m) { Add-Content -Path $log -Value $m }
Set-Content -Path $log -Value "=== SETUP START $(Get-Date) ==="

# GPU info
try { L "--- GPU ---"; (Get-CimInstance Win32_VideoController | Select-Object Name, AdapterRAM, DriverVersion | Format-List | Out-String) | ForEach-Object { L $_ } } catch { L "gpu query failed $_" }
try { $smi = & nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv 2>&1; L ($smi | Out-String) } catch { L "no nvidia-smi" }
try { L "--- CPU/RAM ---"; L ((Get-CimInstance Win32_Processor).Name); L ("RAM GB " + [math]::Round((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory/1GB,1)) } catch {}

# Blender portable
$tools = Join-Path $root '_tools'
$bdir = Join-Path $tools 'blender'
$exe = Get-ChildItem -Path $bdir -Recurse -Filter blender.exe -ErrorAction SilentlyContinue | Select-Object -First 1
if (-not $exe) {
  try {
    $base = 'https://download.blender.org/release/Blender4.5/'
    $links = (Invoke-WebRequest $base -UseBasicParsing).Links.href | Where-Object { $_ -match '^blender-4\.5\.\d+-windows-x64\.zip$' }
    $pick = $links | Sort-Object { [int](($_ -replace '^blender-4\.5\.','') -replace '-windows-x64\.zip$','') } | Select-Object -Last 1
    L "Blender zip: $pick"
    $zip = Join-Path $tools $pick
    Invoke-WebRequest ($base + $pick) -OutFile $zip -UseBasicParsing
    L ("zip MB " + [math]::Round((Get-Item $zip).Length/1MB))
    New-Item -ItemType Directory -Force -Path $bdir | Out-Null
    Expand-Archive -Force $zip $bdir
    Remove-Item $zip -Force
  } catch { L "BLENDER DOWNLOAD FAILED: $_" }
  $exe = Get-ChildItem -Path $bdir -Recurse -Filter blender.exe -ErrorAction SilentlyContinue | Select-Object -First 1
}
L "BLENDER_EXE=$($exe.FullName)"

# Poly Haven CC0 assets
$assets = Join-Path $root 'assets'
New-Item -ItemType Directory -Force -Path $assets | Out-Null
function Get-Tex($id) {
  $dst = Join-Path $assets $id
  if (Test-Path (Join-Path $dst 'done.txt')) { L "tex $id cached"; return }
  try {
    $f = Invoke-RestMethod "https://api.polyhaven.com/files/$id"
    New-Item -ItemType Directory -Force -Path $dst | Out-Null
    foreach ($m in @('Diffuse','nor_gl','Rough','Displacement','arm','AO')) {
      if ($f.$m -and $f.$m.'2k' -and $f.$m.'2k'.jpg) {
        $u = $f.$m.'2k'.jpg.url
        $ext = [IO.Path]::GetExtension($u)
        Invoke-WebRequest $u -OutFile (Join-Path $dst ($m + $ext)) -UseBasicParsing
      } elseif ($f.$m -and $f.$m.'2k' -and $f.$m.'2k'.png) {
        Invoke-WebRequest $f.$m.'2k'.png.url -OutFile (Join-Path $dst ($m + '.png')) -UseBasicParsing
      }
    }
    Set-Content (Join-Path $dst 'done.txt') 'ok'
    L "tex $id OK: $((Get-ChildItem $dst).Name -join ',')"
  } catch { L "tex $id FAILED: $_" }
}
function Get-Hdri($id) {
  $dst = Join-Path $assets ($id + '.hdr')
  if (Test-Path $dst) { L "hdri $id cached"; return }
  try {
    $f = Invoke-RestMethod "https://api.polyhaven.com/files/$id"
    Invoke-WebRequest $f.hdri.'2k'.hdr.url -OutFile $dst -UseBasicParsing
    L "hdri $id OK"
  } catch { L "hdri $id FAILED: $_" }
}
# list matching ids so Claude can pick
try {
  $all = Invoke-RestMethod 'https://api.polyhaven.com/assets?t=textures'
  $names = $all.PSObject.Properties.Name
  L ("TEX asphalt/road: " + (($names | Where-Object { $_ -match 'asphalt|road|tarmac' }) -join ','))
  L ("TEX snow/grass/metal/concrete: " + (($names | Where-Object { $_ -match 'snow|grass|metal_plate|rusty|concrete_floor|painted_metal' }) -join ','))
  $h = Invoke-RestMethod 'https://api.polyhaven.com/assets?t=hdris'
  $hn = $h.PSObject.Properties.Name
  L ("HDRI sky/night: " + (($hn | Where-Object { $_ -match 'puresky|night|moon|road|highway|overcast|snow' }) -join ','))
} catch { L "list failed $_" }

foreach ($t in @('asphalt_02','asphalt_04','asphalt_track','rough_asphalt','aerial_grass_rock','snow_02','metal_plate','rubber_tiles','concrete_floor_worn_001')) { Get-Tex $t }
foreach ($h in @('kloofendal_48d_partly_cloudy_puresky','kloofendal_overcast_puresky','moonless_golf','dikhololo_night','snowy_field','qwantani_dusk_2_puresky','studio_small_09')) { Get-Hdri $h }

L "=== SETUP DONE $(Get-Date) ==="
