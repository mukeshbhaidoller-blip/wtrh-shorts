# Claude render helper: runs jobs Claude drops into D:\Ai Video Edit\jobs\<name>\ (job.bat + ready.txt)
$ErrorActionPreference = 'Continue'
$root = 'D:\Ai Video Edit'; $jobs = Join-Path $root 'jobs'
New-Item -ItemType Directory -Force -Path $jobs | Out-Null
$log = Join-Path $jobs 'watcher-log.txt'
$mutex = New-Object System.Threading.Mutex($false, 'Local\ClaudeRenderWatcher')
if (-not $mutex.WaitOne(0)) { exit }
Add-Content $log "$(Get-Date -Format o) watcher started (pid $PID)"
while ($true) {
  try {
    Set-Content (Join-Path $jobs 'heartbeat.txt') (Get-Date -Format o)
    Get-ChildItem $jobs -Directory | Sort-Object Name | ForEach-Object {
      $d = $_.FullName
      if ((Test-Path "$d\ready.txt") -and (Test-Path "$d\job.bat") -and -not (Test-Path "$d\running.txt") -and -not (Test-Path "$d\done.txt")) {
        Set-Content "$d\running.txt" (Get-Date -Format o)
        Add-Content $log "$(Get-Date -Format o) START $($_.Name)"
        $p = Start-Process -FilePath 'cmd.exe' -ArgumentList '/c', "`"$d\job.bat`"" -WorkingDirectory $d -WindowStyle Minimized -Wait -PassThru
        Set-Content "$d\done.txt" "exit=$($p.ExitCode) at $(Get-Date -Format o)"
        Add-Content $log "$(Get-Date -Format o) END $($_.Name) exit=$($p.ExitCode)"
      }
    }
  } catch { Add-Content $log "$(Get-Date -Format o) ERROR $_" }
  Start-Sleep -Seconds 20
}
