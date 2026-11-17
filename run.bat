@echo off
setlocal
title Fabrica dos Cortes

cd /d "%~dp0"
call .venv\Scripts\activate.bat
python main_improved.py
echo.
pause