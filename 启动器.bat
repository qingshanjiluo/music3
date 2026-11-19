@echo off
chcp 65001 >nul 2>&1
title music3
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1
python -X utf8 launcher.py
if errorlevel 1 (
  echo.
  echo Launcher exited with error. Press any key to close...
  pause >nul
)
