@echo off
cd /d "%~dp0"
echo [*] Guncelleniyor...
git pull
if exist ".venv\.installed" del ".venv\.installed"
call setup_and_run.bat
