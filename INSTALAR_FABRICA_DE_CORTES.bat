@echo off
setlocal EnableExtensions
title Instalador Rapido - Fabrica dos Cortes
color 0E

set "URL=https://github.com/bazotepedro-oss/forjaviral/releases/latest/download/FabricaDosCortes.zip"
if not defined TARGET set "TARGET=%LOCALAPPDATA%\FabricaDosCortes"
set "ZIP=%TEMP%\FabricaDosCortes.zip"
set "EXTRACT=%TEMP%\FabricaDosCortes_extract"

echo ==============================================================
echo            FABRICA DOS CORTES - INSTALADOR RAPIDO
echo ==============================================================
echo.
echo  Este instalador baixa a versao mais recente do aplicativo e
echo  instala tudo automaticamente. Basta estar conectado a internet.
echo.
echo  Pasta de instalacao: %TARGET%
echo.

if exist "%TARGET%\INICIAR_FABRICA_DE_CORTES.bat" (
    echo  O aplicativo ja esta instalado nesta pasta.
    echo  Abrindo o instalador para reparar/atualizar as dependencias...
    echo.
    call "%TARGET%\INSTALADOR.bat"
    exit /b 0
)

echo [1/4] Verificando conexao com a internet...
powershell -NoProfile -ExecutionPolicy Bypass -Command "try { (Invoke-WebRequest -Uri 'https://github.com' -UseBasicParsing -TimeoutSec 12).StatusCode | Out-Null; exit 0 } catch { exit 1 }"
if errorlevel 1 (
    echo.
    echo [ERRO] Sem conexao com a internet. Verifique e tente novamente.
    pause
    exit /b 1
)
echo        OK

echo [2/4] Baixando o aplicativo (aprox. 5,7 MB)...
if exist "%ZIP%" del /f /q "%ZIP%" >nul 2>&1
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ProgressPreference='SilentlyContinue'; [Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri '%URL%' -OutFile '%ZIP%' -UseBasicParsing"
if not exist "%ZIP%" (
    echo.
    echo [ERRO] Falha ao baixar o aplicativo.
    echo Verifique a internet, o antivirus e tente novamente.
    pause
    exit /b 1
)
for %%A in ("%ZIP%") do if %%~zA LSS 1000000 (
    echo.
    echo [ERRO] O download veio incompleto. Tente novamente.
    pause
    exit /b 1
)
echo        OK

echo [3/4] Extraindo os arquivos...
if exist "%EXTRACT%" rmdir /s /q "%EXTRACT%" >nul 2>&1
mkdir "%EXTRACT%" >nul 2>&1
powershell -NoProfile -ExecutionPolicy Bypass -Command "Expand-Archive -LiteralPath '%ZIP%' -DestinationPath '%EXTRACT%' -Force"
if errorlevel 1 (
    echo.
    echo [ERRO] Falha ao extrair o pacote.
    pause
    exit /b 1
)

set "SRC="
for /d %%D in ("%EXTRACT%\FabricaDosCortes-*") do set "SRC=%%D"
if not defined SRC (
    echo.
    echo [ERRO] Pasta do aplicativo nao encontrada no pacote baixado.
    pause
    exit /b 1
)
echo        OK

echo [4/4] Copiando para a pasta definitiva...
if not exist "%TARGET%" mkdir "%TARGET%" >nul 2>&1
robocopy "%SRC%" "%TARGET%" /E /XD VIRALS models logs _update_backup .venv __pycache__ /XF api_config.json /R:1 /W:1 /NFL /NDL /NJH /NJS /NP >nul
if not exist "%TARGET%\INSTALADOR.bat" (
    echo.
    echo [ERRO] A copia dos arquivos falhou. Verifique o antivirus.
    pause
    exit /b 1
)
if not exist "%TARGET%\api_config.json" copy /y "%SRC%\api_config.json" "%TARGET%\api_config.json" >nul
echo        OK

if exist "%ZIP%" del /f /q "%ZIP%" >nul 2>&1
if exist "%EXTRACT%" rmdir /s /q "%EXTRACT%" >nul 2>&1

echo.
echo ==============================================================
echo  Download concluido. Abrindo o instalador oficial...
echo ==============================================================
echo.
if /i "%FDC_SKIP_LAUNCH%"=="1" (
    echo [teste] Instalador nao aberto porque FDC_SKIP_LAUNCH=1.
    exit /b 0
)
call "%TARGET%\INSTALADOR.bat"
exit /b 0
