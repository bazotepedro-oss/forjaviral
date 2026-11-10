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
echo  Carregando modelos de IA e CUDA na placa de video...
echo  (Na primeira inicializacao pode levar de 20 a 30 segundos)
echo.
echo  Aguarde... Seu navegador abrira automaticamente:
echo  --^> http://localhost:7860
echo.
echo  Para fechar o programa, feche esta janela do terminal.
echo ==============================================================
echo.

rem Não encerra processos desconhecidos que possam usar a porta 7860.
netstat -aon 2>nul | findstr ":7860" | findstr "LISTENING" >nul
if %ERRORLEVEL% EQU 0 (
    echo [AVISO] A porta 7860 já está em uso. Feche a instância anterior da Fábrica dos Cortes e tente novamente.
    pause
    exit /b 1
)

rem Garante que o atalho oficial com ícone esteja na Área de Trabalho
if exist "%~dp0scripts\create_shortcut.ps1" (
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\create_shortcut.ps1" >nul 2>&1
)

call ".venv\Scripts\activate.bat"
python "webui\app.py"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERRO] Ocorreu um problema ao executar a ferramenta.
    echo Se faltar alguma dependencia, execute novamente o INSTALADOR.bat
    pause
)
