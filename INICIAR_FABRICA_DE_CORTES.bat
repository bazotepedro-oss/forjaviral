@echo off
chcp 65001 >nul
setlocal
title Fábrica de Cortes - IA de Vídeos
cd /d "%~dp0"

set "PATH=%~dp0.venv\Scripts;%USERPROFILE%\.local\bin;%PATH%"

if not exist ".venv\Scripts\python.exe" (
    echo ====================================================================
    echo  AVISO: A Fábrica de Cortes ainda não foi instalada no seu PC!
    echo  Iniciando o instalador automático agora mesmo...
    echo ====================================================================
    echo.
    call "%~dp0INSTALADOR.bat"
    exit /b 0
)

echo ====================================================================
echo.
echo           INICIANDO FÁBRICA DE CORTES - EDIÇÃO DE VÍDEOS
echo.
echo  Aguarde... Seu navegador abrirá automaticamente em alguns segundos:
echo  --^> http://localhost:7860
echo.
echo  Para fechar o programa, feche esta janela do terminal.
echo ====================================================================
echo.

call ".venv\Scripts\activate.bat"
python "webui\app.py"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERRO] Ocorreu um problema ao executar a ferramenta.
    echo Se faltar alguma dependência, execute novamente o INSTALADOR.bat
    pause
)
