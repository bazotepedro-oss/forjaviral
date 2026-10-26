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

echo ==============================================================
echo.
echo           INICIANDO FABRICA DE CORTES - EDICAO DE VIDEOS
echo.
echo  Aguarde... Seu navegador abrira automaticamente:
echo  --^> http://localhost:7860
echo.
echo  Para fechar o programa, feche esta janela do terminal.
echo ==============================================================
echo.

call ".venv\Scripts\activate.bat"
python "webui\app.py"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERRO] Ocorreu um problema ao executar a ferramenta.
    echo Se faltar alguma dependencia, execute novamente o INSTALADOR.bat
    pause
)
