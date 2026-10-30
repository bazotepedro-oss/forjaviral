# scripts/create_shortcut.ps1
# Cria ou atualiza o atalho oficial da Fabrica de Cortes na Area de Trabalho com o icone oficial

$ErrorActionPreference = "SilentlyContinue"
$projectRoot = Split-Path -Parent $PSScriptRoot

$desktopPath = [Environment]::GetFolderPath("Desktop")
$shortcutPath = Join-Path $desktopPath "Fabrica dos Cortes.lnk"
$targetBat = Join-Path $projectRoot "INICIAR_FABRICA_DE_CORTES.bat"

$iconPath = Join-Path $projectRoot "app.ico"
if (-not (Test-Path $iconPath)) {
    $iconPath = Join-Path $projectRoot "branding\app.ico"
}

try {
    $WshShell = New-Object -ComObject WScript.Shell
    $Shortcut = $WshShell.CreateShortcut($shortcutPath)
    $Shortcut.TargetPath = $targetBat
    $Shortcut.WorkingDirectory = $projectRoot
    $Shortcut.Description = "Fabrica dos Cortes - IA para Cortes Virais Automaticos"
    if (Test-Path $iconPath) {
        $Shortcut.IconLocation = "$iconPath,0"
    }
    $Shortcut.Save()
    Write-Host " [OK] Atalho criado com sucesso na Area de Trabalho!" -ForegroundColor Green
    exit 0
} catch {
    Write-Host " [i] Erro ao criar atalho: $_" -ForegroundColor Yellow
    exit 1
}
