@echo off
title Instalador Oficial - Fabrica de Cortes
cd /d "%~dp0"

if not exist "%~dp0scripts\instalador.ps1" (
    echo ==============================================================
    echo       FABRICA DE CORTES - INSTALADOR OFICIAL
    echo ==============================================================
    echo ERRO: pacote incompleto. O arquivo scripts\instalador.ps1 nao foi encontrado.
    echo Baixe novamente o ZIP oficial do aplicativo e extraia por completo.
    echo Nao baixe arquivos de fontes nao oficiais.
    echo.
    pause
    exit /b 1
)

if exist "%~dp0scripts\instalador.ps1" (
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\instalador.ps1"
) else (
    echo.
    echo [ERRO] Pacote incompleto. Baixe novamente o ZIP oficial do aplicativo.
    pause
    exit /b 1
)

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERRO] Ocorreu uma falha durante a instalacao.
    pause
)
