# scripts/setup_ffmpeg.ps1
# Garante que ffmpeg.exe e ffprobe.exe estejam em .venv\Scripts\

$ErrorActionPreference = "SilentlyContinue"
$projectRoot = Split-Path -Parent $PSScriptRoot
$destDir = Join-Path $projectRoot ".venv\Scripts"

if (!(Test-Path $destDir)) {
    New-Item -ItemType Directory -Path $destDir -Force | Out-Null
}

$destFfmpeg = Join-Path $destDir "ffmpeg.exe"
$destFfprobe = Join-Path $destDir "ffprobe.exe"

if ((Test-Path $destFfmpeg) -and (Test-Path $destFfprobe)) {
    Write-Host "[OK] FFmpeg e FFprobe ja estao presentes em .venv\Scripts" -ForegroundColor Green
    exit 0
}

Write-Host "Verificando instalacao do FFmpeg..." -ForegroundColor Cyan

# 1. Procura em WinGet Links
$wingetLinks = "$env:LOCALAPPDATA\Microsoft\WinGet\Links"
if (Test-Path "$wingetLinks\ffmpeg.exe") {
    Copy-Item "$wingetLinks\ff*.exe" $destDir -Force
    if (Test-Path $destFfmpeg) {
        Write-Host "[OK] FFmpeg copiado de WinGet Links para .venv\Scripts" -ForegroundColor Green
        exit 0
    }
}

# 2. Procura em WinGet Packages
$pkgDir = "$env:LOCALAPPDATA\Microsoft\WinGet\Packages"
if (Test-Path $pkgDir) {
    $found = Get-ChildItem -Path $pkgDir -Filter "ffmpeg.exe" -Recurse | Select-Object -First 1
    if ($found) {
        $binDir = Split-Path -Parent $found.FullName
        Copy-Item "$binDir\ff*.exe" $destDir -Force
        if (Test-Path $destFfmpeg) {
            Write-Host "[OK] FFmpeg copiado de pacotes WinGet para .venv\Scripts" -ForegroundColor Green
            exit 0
        }
    }
}

# 3. Procura no PATH global
$pathFfmpeg = (Get-Command ffmpeg -ErrorAction SilentlyContinue).Source
if ($pathFfmpeg) {
    $pathDir = Split-Path -Parent $pathFfmpeg
    Copy-Item "$pathDir\ff*.exe" $destDir -Force
    if (Test-Path $destFfmpeg) {
        Write-Host "[OK] FFmpeg copiado do PATH para .venv\Scripts" -ForegroundColor Green
        exit 0
    }
}

# 4. Tenta instalar via winget
Write-Host "Instalando FFmpeg via WinGet..." -ForegroundColor Yellow
winget install --id Gyan.FFmpeg.Essentials -e --accept-source-agreements --accept-package-agreements --silent

$foundAfterWinget = Get-ChildItem -Path $pkgDir -Filter "ffmpeg.exe" -Recurse | Select-Object -First 1
if ($foundAfterWinget) {
    $binDir = Split-Path -Parent $foundAfterWinget.FullName
    Copy-Item "$binDir\ff*.exe" $destDir -Force
    if (Test-Path $destFfmpeg) {
        Write-Host "[OK] FFmpeg instalado com sucesso via WinGet!" -ForegroundColor Green
        exit 0
    }
}

# 5. Fallback: Download direto do zip portátil
Write-Host "Baixando FFmpeg portatil oficial..." -ForegroundColor Yellow
$zipUrl = "https://github.com/GyanD/codexffmpeg/releases/download/7.1/ffmpeg-7.1-essentials_build.zip"
$tempZip = Join-Path $env:TEMP "ffmpeg_essentials.zip"
$tempExtract = Join-Path $env:TEMP "ffmpeg_extract"

Invoke-WebRequest -Uri $zipUrl -OutFile $tempZip -UseBasicParsing
Expand-Archive -Path $tempZip -DestinationPath $tempExtract -Force

$foundInZip = Get-ChildItem -Path $tempExtract -Filter "ffmpeg.exe" -Recurse | Select-Object -First 1
if ($foundInZip) {
    $zipBin = Split-Path -Parent $foundInZip.FullName
    Copy-Item "$zipBin\ff*.exe" $destDir -Force
}

Remove-Item $tempZip -Force -ErrorAction SilentlyContinue
Remove-Item $tempExtract -Recurse -Force -ErrorAction SilentlyContinue

if (Test-Path $destFfmpeg) {
    Write-Host "[OK] FFmpeg instalado com sucesso em .venv\Scripts!" -ForegroundColor Green
    exit 0
} else {
    Write-Host "[AVISO] Nao foi possivel instalar o FFmpeg automaticamente." -ForegroundColor Red
    exit 1
}
