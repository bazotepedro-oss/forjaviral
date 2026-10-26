@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
title Instalador Oficial - Fábrica de Cortes

cd /d "%~dp0"
set "PATH=%USERPROFILE%\.local\bin;%LOCALAPPDATA%\uv;C:\Program Files\Git\cmd;%~dp0.venv\Scripts;%PATH%"
set "UV_LINK_MODE=copy"

:: 0. Sincronização / Download Automático do Código-Fonte do GitHub
if not exist "webui\app.py" (
    echo ====================================================================
    echo  [i] Código-fonte da Fábrica de Cortes não encontrado nesta pasta.
    echo  Baixando os arquivos mais recentes do GitHub automaticamente...
    echo ====================================================================
    where git >nul 2>&1
    if !ERRORLEVEL! EQU 0 (
        git clone https://github.com/bazotepedro-oss/forjaviral.git temp_src
        xcopy /s /e /y temp_src\* . >nul 2>&1
        rmdir /s /q temp_src >nul 2>&1
    ) else (
        echo  - Baixando pacote via download seguro...
        powershell -ExecutionPolicy Bypass -Command "$zip='temp_src.zip'; Invoke-WebRequest -Uri 'https://github.com/bazotepedro-oss/forjaviral/archive/refs/heads/main.zip' -OutFile $zip; Expand-Archive $zip -DestinationPath 'temp_src' -Force; Copy-Item 'temp_src\forjaviral-main\*' . -Recurse -Force; Remove-Item $zip -Force; Remove-Item 'temp_src' -Recurse -Force"
    )
    echo  [OK] Arquivos baixados do GitHub com sucesso!
    echo.
) else (
    if exist ".git" (
        where git >nul 2>&1
        if !ERRORLEVEL! EQU 0 (
            echo  [i] Sincronizando últimas atualizações do GitHub...
            git pull origin main >nul 2>&1
        )
    )
)

cls
echo ====================================================================
echo.
echo      ███████╗ █████╗ ██████╗ ██████╗ ██╗ ██████╗ █████╗ 
echo      ██╔════╝██╔══██╗██╔══██╗██╔══██╗██║██╔════╝██╔══██╗
echo      █████╗  ███████║██████╔╝██████╔╝██║██║     ███████║
echo      ██╔══╝  ██╔══██║██╔══██╗██╔══██╗██║██║     ██╔══██║
echo      ██║     ██║  ██║██████╔╝██║  ██║██║╚██████╗██║  ██║
echo      ╚═╝     ╚═╝  ╚═╝╚═════╝ ╚═╝  ╚═╝╚═╝ ╚═════╝╚═╝  ╚═╝
echo                         DE CORTES
echo.
echo           INSTALADOR AUTOMÁTICO - INTELIGÊNCIA ARTIFICIAL
echo                   https://fabricadecortes.com
echo ====================================================================
echo.

:: 1. Detecção automática de GPU NVIDIA
set "GPU_NAME="
for /f "tokens=*" %%a in ('nvidia-smi --query-gpu=name --format=csv^,noheader 2^>nul') do (
    set "GPU_NAME=%%a"
)

if defined GPU_NAME (
    echo  [✓] Placa de Vídeo Detectada: %GPU_NAME%
    echo      Recomendação: Escolha a Opção [1] para Aceleração Máxima com CUDA.
    set "DEFAULT_CHOICE=1"
) else (
    echo  [i] Nenhuma Placa de Vídeo NVIDIA detectada no sistema.
    echo      Recomendação: Escolha a Opção [2] para Modo Processador (CPU).
    set "DEFAULT_CHOICE=2"
)
echo.
echo --------------------------------------------------------------------
echo  Escolha como deseja instalar:
echo.
echo   [1] GPU  - Placa NVIDIA (Recomendado - 5x a 10x mais rápido)
echo   [2] CPU  - Modo Processador (Intel / AMD / Sem placa NVIDIA)
echo   [3] Sair
echo --------------------------------------------------------------------
set /p "USER_CHOICE=Digite sua escolha (1 ou 2) [Padrão: %DEFAULT_CHOICE%]: "

if "%USER_CHOICE%"=="" set "USER_CHOICE=%DEFAULT_CHOICE%"
if "%USER_CHOICE%"=="3" (
    echo Instalação cancelada pelo usuário.
    exit /b 0
)

cls
echo ====================================================================
echo               INICIANDO INSTALAÇÃO AUTOMÁTICA
echo ====================================================================
echo.

:: 2. Passo 1 - Gerenciador uv
echo [Passo 1/6] Verificando gerenciador Python ultra-rápido (uv)...
where uv >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    if not exist "%USERPROFILE%\.local\bin\uv.exe" (
        echo  - Baixando uv standalone oficial...
        powershell -ExecutionPolicy Bypass -Command "irm https://astral.sh/uv/install.ps1 | iex"
    )
    set "PATH=%USERPROFILE%\.local\bin;%PATH%"
)
echo  [OK] Gerenciador uv pronto!
echo.

:: 3. Passo 2 - Python 3.10 Standalone
echo [Passo 2/6] Instalando Python 3.10 isolado (Versão Oficial de IA)...
uv python install 3.10
echo  [OK] Python 3.10 configurado com sucesso!
echo.

:: 4. Passo 3 - Criar Ambiente Virtual (.venv)
echo [Passo 3/6] Criando ambiente virtual isolado (.venv)...
if not exist ".venv\Scripts\python.exe" (
    uv venv .venv --python 3.10
) else (
    echo  - Ambiente virtual já existente, atualizando...
)
echo  [OK] Ambiente virtual pronto!
echo.

:: 5. Passo 4 - Instalação do FFmpeg
echo [Passo 4/6] Verificando e configurando o FFmpeg para edição de vídeo...
powershell -ExecutionPolicy Bypass -File "%~dp0scripts\setup_ffmpeg.ps1"
echo  [OK] FFmpeg configurado em .venv\Scripts!
echo.

:: 6. Passo 5 - Instalar PyTorch (CPU ou GPU)
echo [Passo 5/6] Instalando PyTorch e bibliotecas de IA...
if "%USER_CHOICE%"=="1" (
    echo  - Modo selecionado: NVIDIA CUDA (GPU)
    echo  - Baixando PyTorch com aceleração CUDA 12.1...
    uv pip install torch==2.3.1+cu121 torchaudio==2.3.1+cu121 --index-url https://download.pytorch.org/whl/cu121
    uv pip install onnxruntime-gpu
) else (
    echo  - Modo selecionado: Processador (CPU)
    echo  - Baixando PyTorch para CPU...
    uv pip install torch==2.3.1+cpu torchaudio==2.3.1+cpu --index-url https://download.pytorch.org/whl/cpu
    uv pip install onnxruntime
)
echo  [OK] PyTorch instalado com sucesso!
echo.

:: 7. Passo 6 - Instalar requisitos do app
echo [Passo 6/6] Instalando ferramentas da Fábrica de Cortes (Whisper, MediaPipe, Gradio, etc)...
if "%USER_CHOICE%"=="1" (
    uv pip install -r "%~dp0requirements.txt" --extra-index-url https://download.pytorch.org/whl/cu121
) else (
    uv pip install -r "%~dp0requirements.txt" --extra-index-url https://download.pytorch.org/whl/cpu
)
echo  [OK] Todas as dependências foram instaladas com sucesso!
echo.

:: 8. Finalização
echo ====================================================================
echo                INSTALAÇÃO CONCLUÍDA COM SUCESSO! 🎉
echo ====================================================================
echo.
echo Tudo está pronto para você começar a criar seus cortes virais.
echo.
echo Para abrir a ferramenta a qualquer momento, basta dar dois cliques em:
echo   --^> INICIAR_FABRICA_DE_CORTES.bat
echo.
set /p "LAUNCH_NOW=Deseja abrir a Fábrica de Cortes agora? (S/N) [S]: "
if /i "%LAUNCH_NOW%"=="N" (
    echo.
    echo Você pode abrir quando quiser pelo arquivo INICIAR_FABRICA_DE_CORTES.bat!
    pause
    exit /b 0
)

echo.
echo Abrindo a Fábrica de Cortes no seu navegador...
call "%~dp0INICIAR_FABRICA_DE_CORTES.bat"
