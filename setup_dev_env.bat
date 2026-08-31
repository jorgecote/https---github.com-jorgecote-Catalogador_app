@echo off
REM Wrapper para ejecutar setup_dev_env.ps1 con doble clic o desde cmd
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup_dev_env.ps1"
pause
