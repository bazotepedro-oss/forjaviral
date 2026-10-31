@echo off
title Atualizar Fabrica de Cortes
cd /d "%~dp0"
echo ==============================================================
echo        FABRICA DE CORTES - ATUALIZADOR OFICIAL
echo ==============================================================
echo.

if exist "%~dp0.venv\Scripts\python.exe" (
    "%~dp0.venv\Scripts\python.exe" "%~dp0scripts\auto_update.py" --force
    goto :done
)

where python >nul 2>nul
if errorlevel 1 (
    echo [ERRO] Python nao encontrado. Execute o INSTALADOR.bat primeiro.
    pause
    exit /b 1
)
python "%~dp0scripts\auto_update.py" --force

:done
echo.
pause
