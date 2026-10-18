@echo off
cd /d "%~dp0"
echo [*] Guncelleniyor...
git pull
if exist ".venv\.installed" del ".venv\.installed"
if exist "WF-AI.exe" del "WF-AI.exe"
call setup_and_run.bat
