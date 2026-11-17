@echo off
title Fabrica de Cortes - IA de Videos
cd /d "%~dp0"

set "PATH=%~dp0.venv\Scripts;%USERPROFILE%\.local\bin;%PATH%"

if not exist ".venv\Scripts\python.exe" (
    echo ==============================================================
    echo  AVISO: O ambiente ainda nao foi instalado no seu PC!
    echo  Iniciando o instalador automatico agora mesmo...
    echo ==============================================================
    echo.
    call "%~dp0INSTALADOR.bat"
    exit /b 0
)

rem Auto-Update inteligente: sincroniza melhorias e arquivos do GitHub em 1-2 segundos
if exist "%~dp0scripts\auto_update.py" (
    "%~dp0.venv\Scripts\python.exe" "%~dp0scripts\auto_update.py"
)

rem Instala/atualiza o pacote de fontes para o usuario atual (sem admin).
if exist "%~dp0scripts\INSTALAR_FONTES.ps1" (
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\INSTALAR_FONTES.ps1" >nul 2>&1
)

rem Confere se as dependencias foram instaladas de verdade. O instalador antigo
rem podia falhar no meio e mesmo assim dizer que estava tudo pronto.
if exist "%~dp0.venv\Scripts\python.exe" (
    "%~dp0.venv\Scripts\python.exe" -c "import gradio" >nul 2>&1
    if errorlevel 1 (
        echo.
        echo [AVISO] As dependencias do aplicativo nao foram instaladas por completo.
        echo Abrindo o instalador para reparar agora...
        echo.
        call "%~dp0INSTALADOR.bat"
        exit /b 0
    )
)

echo ==============================================================
echo.
echo           INICIANDO FABRICA DE CORTES - EDICAO DE VIDEOS
echo.
echo  O programa vai iniciar em segundo plano e ficar na bandeja
echo  do Windows (na setinha perto do relogio).
echo.
echo  Para abrir: clique no icone da Fabrica dos Cortes.
echo  Para encerrar: botao direito no icone ^> Sair.
echo.
echo  Aguarde alguns segundos... o navegador abrira sozinho.
echo ==============================================================
echo.

if not exist "%~dp0logs" mkdir "%~dp0logs" >nul 2>&1

rem Se ja existe uma instancia, apenas abre o navegador.
netstat -aon 2>nul | findstr ":7860" | findstr "LISTENING" >nul
if %ERRORLEVEL% EQU 0 (
    start "" "http://localhost:7860"
    exit /b 0
)

rem Garante que o atalho oficial com ícone esteja na Área de Trabalho
if exist "%~dp0scripts\create_shortcut.ps1" (
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\create_shortcut.ps1" >nul 2>&1
)

echo Iniciando em segundo plano na bandeja do Windows...
start "" powershell.exe -NoProfile -Sta -WindowStyle Hidden -ExecutionPolicy Bypass -File "%~dp0scripts\TRAY_FABRICA.ps1"
exit /b 0
