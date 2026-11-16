# Instala o pacote de fontes da Fábrica dos Cortes para o usuário atual.
# Não exige administrador: usa a pasta de fontes por usuário e o registro HKCU.
$ErrorActionPreference = "SilentlyContinue"

$fontDir = Join-Path (Split-Path -Parent $PSScriptRoot) "webui\assets\fonts"
$manifestPath = Join-Path $fontDir "manifest.json"
$dest = Join-Path $env:LOCALAPPDATA "Microsoft\Windows\Fonts"
$regPath = "HKCU:\Software\Microsoft\Windows NT\CurrentVersion\Fonts"

if (-not (Test-Path $fontDir)) {
    Write-Host "Pasta de fontes nao encontrada."
    exit 0
}
New-Item -ItemType Directory -Path $dest -Force | Out-Null
if (-not (Test-Path $regPath)) {
    New-Item -Path $regPath -Force | Out-Null
}

$items = @()
if (Test-Path $manifestPath) {
    try {
        $items = Get-Content $manifestPath -Raw -Encoding UTF8 | ConvertFrom-Json
    } catch {
        $items = @()
    }
}
if (-not $items -or $items.Count -eq 0) {
    $items = Get-ChildItem $fontDir -Filter *.ttf | ForEach-Object {
        [pscustomobject]@{ family = $_.BaseName; style = ""; file = $_.Name }
    }
}

$installed = 0
foreach ($item in $items) {
    $file = [string]$item.file
    if ([string]::IsNullOrWhiteSpace($file)) { continue }
    $src = Join-Path $fontDir $file
    if (-not (Test-Path $src)) { continue }
    $target = Join-Path $dest $file
    $sourceSize = (Get-Item $src).Length
    $needsCopy = $true
    if (Test-Path $target) {
        $needsCopy = ((Get-Item $target).Length -ne $sourceSize)
    }
    if ($needsCopy) {
        Copy-Item -LiteralPath $src -Destination $target -Force
        $installed++
    }
    $family = [string]$item.family
    $style = [string]$item.style
    $regName = if ($style) { "$family $style (TrueType)" } else { "$family (TrueType)" }
    New-ItemProperty -Path $regPath -Name $regName -Value $target -PropertyType String -Force | Out-Null
}

Write-Host "Fontes da Fabrica dos Cortes prontas: $installed novas, $($items.Count) no pacote."
exit 0
