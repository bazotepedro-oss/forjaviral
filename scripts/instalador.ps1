# scripts/instalador.ps1
# Instalador Oficial Automatizado da Fabrica de Cortes
$ErrorActionPreference = "Continue"
$Host.UI.RawUI.WindowTitle = "Instalador Oficial - Fabrica de Cortes"

$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot

$env:PATH = "$env:USERPROFILE\.local\bin;$env:LOCALAPPDATA\uv;C:\Program Files\Git\cmd;$projectRoot\.venv\Scripts;$env:PATH"
$env:UV_LINK_MODE = "copy"

Clear-Host
Write-Host "==================================================================" -ForegroundColor DarkYellow
Write-Host "                FABRICA DE CORTES - INSTALADOR OFICIAL           " -ForegroundColor Yellow
Write-Host "             Automacao Inteligente e Cortes Virais com IA        " -ForegroundColor White
Write-Host "                      https://fabricadecortes.com                " -ForegroundColor Cyan
Write-Host "==================================================================" -ForegroundColor DarkYellow
Write-Host ""

# 0. Sincronizacao / Download do Codigo Fonte do GitHub se necessario
$appPath = Join-Path $projectRoot "webui\app.py"
if (-not (Test-Path $appPath)) {
    Write-Host "[i] Codigo-fonte nao encontrado nesta pasta." -ForegroundColor Cyan
    Write-Host "Baixando versao oficial diretamente do GitHub..." -ForegroundColor Yellow
    
    $hasGit = Get-Command git -ErrorAction SilentlyContinue
    if ($hasGit) {
        & git clone https://github.com/bazotepedro-oss/forjaviral.git temp_git
        Copy-Item -Path "temp_git\*" -Destination $projectRoot -Recurse -Force
        Remove-Item "temp_git" -Recurse -Force -ErrorAction SilentlyContinue
    } else {
        $zipPath = Join-Path $env:TEMP "fabrica_src.zip"
        $extractPath = Join-Path $env:TEMP "fabrica_extract"
        Invoke-WebRequest -Uri "https://github.com/bazotepedro-oss/forjaviral/archive/refs/heads/main.zip" -OutFile $zipPath -UseBasicParsing
        Expand-Archive -Path $zipPath -DestinationPath $extractPath -Force
        Copy-Item -Path "$extractPath\forjaviral-main\*" -Destination $projectRoot -Recurse -Force
        Remove-Item $zipPath -Force -ErrorAction SilentlyContinue
        Remove-Item $extractPath -Recurse -Force -ErrorAction SilentlyContinue
    }
    Write-Host "[OK] Codigo-fonte baixado com sucesso!" -ForegroundColor Green
    Write-Host ""
} else {
    $gitDir = Join-Path $projectRoot ".git"
    if (Test-Path $gitDir) {
        $hasGit = Get-Command git -ErrorAction SilentlyContinue
        if ($hasGit) {
            Write-Host "[i] Sincronizando ultimas atualizacoes do GitHub..." -ForegroundColor Cyan
            & git pull origin main 2>$null | Out-Null
        }
    }
}

# 1. Deteccao automatica de Placa de Video (GPU NVIDIA)
$gpuName = $null
try {
    $smiOut = & nvidia-smi --query-gpu=name --format=csv,noheader 2>$null
    if ($LASTEXITCODE -eq 0 -and $smiOut) {
        $gpuName = $smiOut[0].Trim()
    }
} catch {
    $gpuName = $null
}

$defaultChoice = "2"
if ($gpuName) {
    Write-Host " [OK] Placa de Video Detectada: $gpuName" -ForegroundColor Green
    Write-Host "      Recomendacao: Opcao 1 (GPU com Aceleracao CUDA - Maxima Velocidade)" -ForegroundColor White
    $defaultChoice = "1"
} else {
    Write-Host " [i] Nenhuma Placa de Video NVIDIA detectada." -ForegroundColor Yellow
    Write-Host "     Recomendacao: Opcao 2 (Modo Processador / CPU)" -ForegroundColor White
    $defaultChoice = "2"
}

Write-Host ""
Write-Host "------------------------------------------------------------------" -ForegroundColor DarkGray
Write-Host " Escolha o modo de instalacao:" -ForegroundColor White
Write-Host "   (1) GPU  - Placa NVIDIA (Recomendado - 5x a 10x mais rapido)" -ForegroundColor Green
Write-Host "   (2) CPU  - Modo Processador (Intel / AMD / Sem placa NVIDIA)" -ForegroundColor Cyan
Write-Host "   (3) Sair" -ForegroundColor Gray
Write-Host "------------------------------------------------------------------" -ForegroundColor DarkGray

$promptMsg = "Digite sua escolha (1 ou 2) - Padrao e " + $defaultChoice + ": "
$choice = Read-Host -Prompt $promptMsg
if ([string]::IsNullOrWhiteSpace($choice)) {
    $choice = $defaultChoice
}

if ($choice -eq "3") {
    Write-Host "Instalacao cancelada pelo usuario." -ForegroundColor Yellow
    exit 0
}

Clear-Host
Write-Host "==================================================================" -ForegroundColor DarkYellow
Write-Host "                   INICIANDO CONFIGURACAO AUTOMATICA              " -ForegroundColor Yellow
Write-Host "==================================================================" -ForegroundColor DarkYellow
Write-Host ""

# Passo 1: uv (Gerenciador ultrarrapido)
Write-Host "[Passo 1/6] Verificando gerenciador Python uv..." -ForegroundColor Cyan
$hasUv = Get-Command uv -ErrorAction SilentlyContinue
if (-not $hasUv) {
    $uvLocal = Join-Path $env:USERPROFILE ".local\bin\uv.exe"
    if (-not (Test-Path $uvLocal)) {
        Write-Host " - Baixando uv oficial..." -ForegroundColor Yellow
        Invoke-Expression (Invoke-RestMethod "https://astral.sh/uv/install.ps1")
    }
    $env:PATH = "$env:USERPROFILE\.local\bin;$env:PATH"
}
Write-Host " [OK] Gerenciador uv pronto!" -ForegroundColor Green
Write-Host ""

# Passo 2: Python 3.10
Write-Host "[Passo 2/6] Garantindo Python 3.10 standalone oficial..." -ForegroundColor Cyan
& uv python install 3.10
Write-Host " [OK] Python 3.10 pronto!" -ForegroundColor Green
Write-Host ""

# Passo 3: Criar ambiente virtual isolado (.venv)
Write-Host "[Passo 3/6] Criando ambiente virtual isolado (.venv)..." -ForegroundColor Cyan
$venvPython = Join-Path $projectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    & uv venv .venv --python 3.10
} else {
    Write-Host " - Ambiente virtual ja existente, mantendo..." -ForegroundColor Gray
}
Write-Host " [OK] Ambiente virtual pronto!" -ForegroundColor Green
Write-Host ""

# Passo 4: FFmpeg
Write-Host "[Passo 4/6] Verificando e configurando o FFmpeg..." -ForegroundColor Cyan
$setupFfmpegScript = Join-Path $PSScriptRoot "setup_ffmpeg.ps1"
& powershell.exe -ExecutionPolicy Bypass -File $setupFfmpegScript
Write-Host " [OK] FFmpeg configurado em .venv\Scripts!" -ForegroundColor Green
Write-Host ""

# Passo 5: PyTorch
Write-Host "[Passo 5/6] Instalando PyTorch e aceleradores de IA..." -ForegroundColor Cyan
if ($choice -eq "1") {
    Write-Host " - Modo GPU: Instalando PyTorch com aceleracao CUDA 12.1..." -ForegroundColor Yellow
    & uv pip install --link-mode=copy torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
    & uv pip install --link-mode=copy onnxruntime-gpu
} else {
    Write-Host " - Modo CPU: Instalando PyTorch para processador..." -ForegroundColor Yellow
    & uv pip install --link-mode=copy torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
    & uv pip install --link-mode=copy onnxruntime
}
Write-Host " [OK] PyTorch instalado com sucesso!" -ForegroundColor Green
Write-Host ""

# Passo 6: Dependencias do App
Write-Host "[Passo 6/6] Instalando dependencias (WhisperX, MediaPipe, Gradio, etc)..." -ForegroundColor Cyan
$reqFile = Join-Path $projectRoot "requirements.txt"
if ($choice -eq "1") {
    & uv pip install --link-mode=copy -r $reqFile --extra-index-url https://download.pytorch.org/whl/cu121
} else {
    & uv pip install --link-mode=copy -r $reqFile --extra-index-url https://download.pytorch.org/whl/cpu
}
Write-Host " [OK] Todas as dependencias foram instaladas!" -ForegroundColor Green
Write-Host ""

# Passo 7: Atalho oficial na Area de Trabalho
Write-Host "Criando atalho oficial na Area de Trabalho..." -ForegroundColor Cyan
$setupShortcutScript = Join-Path $PSScriptRoot "create_shortcut.ps1"
if (Test-Path $setupShortcutScript) {
    & powershell.exe -ExecutionPolicy Bypass -File $setupShortcutScript
}

# Finalizacao
Write-Host "==================================================================" -ForegroundColor Green
Write-Host "              INSTALACAO CONCLUIDA COM SUCESSO!                  " -ForegroundColor Green
Write-Host "==================================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Tudo pronto! Para abrir o app a qualquer momento, voce pode usar:" -ForegroundColor White
Write-Host " -> O atalho oficial 'Fabrica dos Cortes' na sua Area de Trabalho" -ForegroundColor Yellow
Write-Host " -> Ou clicar no arquivo INICIAR_FABRICA_DE_CORTES.bat" -ForegroundColor Yellow
Write-Host ""

$launch = Read-Host -Prompt "Deseja abrir a Fabrica de Cortes agora? (S/N) - Padrao e S: "
if ([string]::IsNullOrWhiteSpace($launch) -or $launch.ToUpper() -eq "S") {
    Write-Host ""
    Write-Host "Iniciando a Fabrica de Cortes... O navegador abrira em http://localhost:7860" -ForegroundColor Cyan
    $runBat = Join-Path $projectRoot "INICIAR_FABRICA_DE_CORTES.bat"
    Start-Process -FilePath $runBat
} else {
    Write-Host "Tudo pronto. Voce pode iniciar quando quiser pelo atalho na Area de Trabalho!" -ForegroundColor White
}
