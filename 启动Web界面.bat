@echo off
chcp 65001 >nul 2>&1
title music3 web
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1
python -X utf8 run.py web
pause
