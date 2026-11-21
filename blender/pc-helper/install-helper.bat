@echo off
title Claude render helper install
set "SU=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
copy /y "D:\Ai Video Edit\_claude\start-watcher.vbs" "%SU%\claude-render-helper.vbs" > "D:\Ai Video Edit\_claude\install-log.txt" 2>&1
wscript "%SU%\claude-render-helper.vbs"
echo installed %DATE% %TIME% >> "D:\Ai Video Edit\_claude\install-log.txt"
