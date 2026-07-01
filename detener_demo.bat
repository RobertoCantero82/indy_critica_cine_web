@echo off
rem detener_demo.bat — para el backend y el frontend arrancados por iniciar_demo.vbs

echo Deteniendo backend (uvicorn) y frontend (vite)...

rem filtro por nombre de proceso real (python.exe / node.exe), no por texto suelto en la linea de comandos,
rem para no tocar por error otras ventanas de terminal o procesos que solo mencionen estas palabras
powershell -NoProfile -Command "Get-CimInstance Win32_Process | Where-Object { ($_.Name -eq 'python.exe' -and $_.CommandLine -match 'uvicorn') -or ($_.Name -eq 'node.exe' -and $_.CommandLine -match 'vite') } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }"

echo Listo.
pause
