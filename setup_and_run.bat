@echo off
setlocal
cd /d "%~dp0"
title Warframe AI Asistani - Kurulum

set "PY="
where py >nul 2>nul && set "PY=py -3"
if not defined PY (
  where python >nul 2>nul && set "PY=python"
)
if not defined PY (
  echo [!] Python bulunamadi. winget ile Python 3.12 kuruluyor...
  winget install -e --id Python.Python.3.12 --accept-package-agreements --accept-source-agreements
  echo.
  echo Python kuruldu. Lutfen bu dosyayi TEKRAR calistir.
  pause
  exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
  echo [*] Sanal ortam olusturuluyor...
  %PY% -m venv .venv || goto :fail
)

if not exist ".venv\.installed" (
  echo [*] Kutuphaneler kuruluyor ^(ilk seferde 1-2 dk surebilir^)...
  ".venv\Scripts\python.exe" -m pip install --upgrade pip -q
  ".venv\Scripts\python.exe" -m pip install -r requirements.txt -q || goto :fail
  echo ok> ".venv\.installed"
)

if not exist "config.json" copy /y "config.example.json" "config.json" >nul

echo [*] Asistan baslatiliyor... (sistem tepsisinde simgesi var)
start "" ".venv\Scripts\pythonw.exe" "src\main.py"
exit /b 0

:fail
echo [X] Kurulum basarisiz oldu.
pause
exit /b 1
