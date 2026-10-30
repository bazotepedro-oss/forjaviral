# scripts/setup_ffmpeg.ps1
# Garante que ffmpeg.exe, ffprobe.exe e aria2c.exe estejam em .venv\Scripts\

$ErrorActionPreference = "SilentlyContinue"
$projectRoot = Split-Path -Parent $PSScriptRoot
$destDir = Join-Path $projectRoot ".venv\Scripts"

if (!(Test-Path $destDir)) {
    New-Item -ItemType Directory -Path $destDir -Force | Out-Null
}

$destFfmpeg = Join-Path $destDir "ffmpeg.exe"
$destFfprobe = Join-Path $destDir "ffprobe.exe"
$destAria2 = Join-Path $destDir "aria2c.exe"

# ── 1. FFmpeg & FFprobe ─────────────────────────────────────────
if (-not ((Test-Path $destFfmpeg) -and (Test-Path $destFfprobe))) {
    Write-Host "Verificando instalacao do FFmpeg..." -ForegroundColor Cyan

    # 1. Procura em WinGet Links
    $wingetLinks = "$env:LOCALAPPDATA\Microsoft\WinGet\Links"
    if (Test-Path "$wingetLinks\ffmpeg.exe") {
        Copy-Item "$wingetLinks\ff*.exe" $destDir -Force
    }

    # 2. Procura em WinGet Packages
    if (-not (Test-Path $destFfmpeg)) {
        $pkgDir = "$env:LOCALAPPDATA\Microsoft\WinGet\Packages"
        if (Test-Path $pkgDir) {
            $found = Get-ChildItem -Path $pkgDir -Filter "ffmpeg.exe" -Recurse | Select-Object -First 1
            if ($found) {
                $binDir = Split-Path -Parent $found.FullName
                Copy-Item "$binDir\ff*.exe" $destDir -Force
            }
        }
    }

    # 3. Procura no PATH global
    if (-not (Test-Path $destFfmpeg)) {
        $pathFfmpeg = (Get-Command ffmpeg -ErrorAction SilentlyContinue).Source
        if ($pathFfmpeg) {
            $pathDir = Split-Path -Parent $pathFfmpeg
            Copy-Item "$pathDir\ff*.exe" $destDir -Force
        }
    }

    # 4. Tenta instalar via winget
    if (-not (Test-Path $destFfmpeg)) {
        Write-Host "Instalando FFmpeg via WinGet..." -ForegroundColor Yellow
        winget install --id Gyan.FFmpeg.Essentials -e --accept-source-agreements --accept-package-agreements --silent
        $pkgDir = "$env:LOCALAPPDATA\Microsoft\WinGet\Packages"
        $foundAfterWinget = Get-ChildItem -Path $pkgDir -Filter "ffmpeg.exe" -Recurse | Select-Object -First 1
        if ($foundAfterWinget) {
            $binDir = Split-Path -Parent $foundAfterWinget.FullName
            Copy-Item "$binDir\ff*.exe" $destDir -Force
        }
    }

    # 5. Fallback: Download direto do zip portátil
    if (-not (Test-Path $destFfmpeg)) {
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
    }
}

if ((Test-Path $destFfmpeg) -and (Test-Path $destFfprobe)) {
    Write-Host " [OK] FFmpeg e FFprobe prontos em .venv\Scripts!" -ForegroundColor Green
} else {
    Write-Host " [AVISO] Nao foi possivel configurar o FFmpeg automaticamente." -ForegroundColor Red
}

# ── 2. Aria2c (Acelerador de Download Turbo Multi-Thread) ─────────
if (-not (Test-Path $destAria2)) {
    Write-Host "Configurando acelerador de download turbo (aria2)..." -ForegroundColor Cyan
    $wingetAria = "$env:LOCALAPPDATA\Microsoft\WinGet\Links\aria2c.exe"
    if (Test-Path $wingetAria) {
        Copy-Item $wingetAria $destDir -Force
    } else {
        try {
            $ariaZip = Join-Path $env:TEMP "aria2.zip"
            $ariaExtract = Join-Path $env:TEMP "aria2_extract"
            Invoke-WebRequest -Uri "https://github.com/aria2/aria2/releases/download/release-1.37.0/aria2-1.37.0-win-64bit-build1.zip" -OutFile $ariaZip -UseBasicParsing
            Expand-Archive -Path $ariaZip -DestinationPath $ariaExtract -Force
            $foundAria = Get-ChildItem -Path $ariaExtract -Filter "aria2c.exe" -Recurse | Select-Object -First 1
            if ($foundAria) {
                Copy-Item $foundAria.FullName $destDir -Force
            }
            Remove-Item $ariaZip -Force -ErrorAction SilentlyContinue
            Remove-Item $ariaExtract -Recurse -Force -ErrorAction SilentlyContinue
        } catch {
            Write-Host " [i] Download do aria2c falhou. yt-dlp usara o modo turbo nativo de 10 threads." -ForegroundColor Gray
        }
    }
}

if (Test-Path $destAria2) {
    Write-Host " [OK] Acelerador Aria2 turbo configurado em .venv\Scripts!" -ForegroundColor Green
}
