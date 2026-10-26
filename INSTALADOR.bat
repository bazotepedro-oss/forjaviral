@echo off
title Instalador Oficial - Fabrica de Cortes
cd /d "%~dp0"

if not exist "%~dp0scripts\instalador.ps1" (
    echo ==============================================================
    echo       FABRICA DE CORTES - INSTALADOR OFICIAL
    echo ==============================================================
    echo Codigo-fonte nao encontrado nesta pasta.
    echo Baixando versao mais recente diretamente do GitHub oficial...
    echo.
    powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "$ProgressPreference='SilentlyContinue'; [Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12; $z='%~dp0repo.zip'; Invoke-WebRequest -Uri 'https://codeload.github.com/bazotepedro-oss/forjaviral/zip/refs/heads/main' -OutFile $z; Expand-Archive $z -DestinationPath '%~dp0temp_src' -Force; Copy-Item '%~dp0temp_src\forjaviral-main\*' '%~dp0' -Recurse -Force; Remove-Item $z -Force -ErrorAction SilentlyContinue; Remove-Item '%~dp0temp_src' -Recurse -Force -ErrorAction SilentlyContinue"
    echo [OK] Arquivos baixados com sucesso!
    echo.
)

if exist "%~dp0scripts\instalador.ps1" (
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\instalador.ps1"
) else (
    echo.
    echo [ERRO] Nao foi possivel baixar os arquivos necessarios do GitHub.
    echo Verifique sua conexao com a internet e tente novamente.
    pause
    exit /b 1
)

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERRO] Ocorreu uma falha durante a instalacao.
    pause
)
