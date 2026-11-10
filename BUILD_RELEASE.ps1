# BUILD_RELEASE.ps1
# Gera o ZIP oficial do aplicativo com APENAS os arquivos do cliente.
# Nunca inclui site, portal, servidor de licencas, banco, chaves ou configs locais.

[CmdletBinding()]
param(
    [string]$OutputDir = ""
)

$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot
if (-not $Root) { $Root = Split-Path -Parent $MyInvocation.MyCommand.Path }
if (-not $OutputDir) { $OutputDir = Join-Path $Root "release" }

$Version = "1.0.0"
try {
    $versionData = Get-Content (Join-Path $Root "version.json") -Raw | ConvertFrom-Json
    if ($versionData.version) { $Version = [string]$versionData.version }
} catch { }

$Name = "FabricaDosCortes-$Version"
$Stage = Join-Path $OutputDir $Name
$Zip = Join-Path $OutputDir "$Name.zip"

Write-Host "==============================================================" -ForegroundColor DarkYellow
Write-Host "  FABRICA DOS CORTES - BUILD DE RELEASE DO CLIENTE" -ForegroundColor Yellow
Write-Host "==============================================================" -ForegroundColor DarkYellow
Write-Host "Versao: $Version"
Write-Host "Destino: $Zip"
Write-Host ""

if (Test-Path $Stage) { Remove-Item $Stage -Recurse -Force }
New-Item -ItemType Directory -Path $Stage -Force | Out-Null

# Arquivos do aplicativo (lista branca)
$Files = @(
    "main_improved.py",
    "requirements.txt",
    "requirements_common.txt",
    "constraints.txt",
    "INSTALADOR.bat",
    "INICIAR_FABRICA_DE_CORTES.bat",
    "ATUALIZAR.bat",
    "install.bat",
    "install_cpu.bat",
    "install_gpu.bat",
    "install_dependencies.bat",
    "install_dependencies_advanced_LocalLLM.bat",
    "run.bat",
    "run_webui.bat",
    "COMO_INSTALAR.txt",
    "README_RELEASE.txt",
    "README_en.md",
    "LICENSE",
    "app.ico",
    "api_config.json",
    "temp_subtitle_config.json",
    "prompt.txt",
    "version.json",
    "ViralCutter.ipynb",
    "changelog.md"
)

# Pastas do aplicativo (lista branca)
$Dirs = @("webui", "scripts", "branding")

foreach ($file in $Files) {
    $src = Join-Path $Root $file
    if (-not (Test-Path $src)) { throw "Arquivo obrigatorio ausente: $file" }
    Copy-Item $src (Join-Path $Stage $file) -Force
    Write-Host "  + $file"
}

foreach ($dir in $Dirs) {
    $src = Join-Path $Root $dir
    if (-not (Test-Path $src)) { throw "Pasta obrigatoria ausente: $dir" }
    Copy-Item $src (Join-Path $Stage $dir) -Recurse -Force
    Write-Host "  + $dir/"
}

# i18n: apenas o runtime e os idiomas (sem ferramentas de desenvolvimento)
New-Item -ItemType Directory -Path (Join-Path $Stage "i18n") -Force | Out-Null
Copy-Item (Join-Path $Root "i18n\i18n.py") (Join-Path $Stage "i18n\i18n.py") -Force
Copy-Item (Join-Path $Root "i18n\locale") (Join-Path $Stage "i18n\locale") -Recurse -Force
Write-Host "  + i18n/ (runtime + idiomas)"

# models: apenas o marcador de pasta, sem modelos locais gigantes
New-Item -ItemType Directory -Path (Join-Path $Stage "models") -Force | Out-Null
if (Test-Path (Join-Path $Root "models\.local-model-here")) {
    Copy-Item (Join-Path $Root "models\.local-model-here") (Join-Path $Stage "models\.local-model-here") -Force
}
Write-Host "  + models/ (vazio)"

# Remove caches, arquivos acidentais e qualquer configuracao local
Get-ChildItem $Stage -Recurse -Force -Directory -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -eq "__pycache__" } |
    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

Get-ChildItem $Stage -Recurse -Force -File -ErrorAction SilentlyContinue |
    Where-Object {
        $_.Extension -in @(".pyc", ".pyo") -or
        $_.Name -eq "a" -or
        $_.Name -like ".env*" -or
        $_.Name -eq "config.local.php"
    } |
    Remove-Item -Force -ErrorAction SilentlyContinue

# Sanitiza a configuracao de IA: o cliente nunca recebe chave de API nossa.
$apiConfigPath = Join-Path $Stage "api_config.json"
if (Test-Path $apiConfigPath) {
    try {
        $apiConfig = Get-Content $apiConfigPath -Raw | ConvertFrom-Json
        if ($apiConfig.gemini) { $apiConfig.gemini.api_key = "" }
        $apiConfig | ConvertTo-Json -Depth 8 | Set-Content $apiConfigPath -Encoding UTF8
    } catch {
        throw "api_config.json invalido: $($_.Exception.Message)"
    }
}

# Arquivos de seguranca e leitura do pacote
$readme = @"
FABRICA DOS CORTES - PACOTE OFICIAL DO APLICATIVO
=================================================

Este pacote contem APENAS o aplicativo do cliente.

Nao contem:
- site de vendas;
- portal de membros (HostGator);
- servidor de licencas (Railway);
- banco de dados;
- chaves privadas, tokens administrativos ou senhas;
- ambiente virtual (.venv) ou arquivos de desenvolvimento.

Instalacao:
1. Extraia este ZIP em uma pasta limpa.
2. Execute INSTALADOR.bat.
3. Ao final, abra pelo atalho "Fabrica dos Cortes" na Area de Trabalho.

Atualizacoes:
- Use ATUALIZAR.bat ou abra o app normalmente.
- O atualizador sincroniza somente os arquivos do aplicativo.
"@
$readme | Set-Content (Join-Path $Stage "LEIA-ME-PRIMEIRO.txt") -Encoding UTF8

# Varredura de itens proibidos
$forbiddenNames = @(
    "membros_hostgator",
    "membros_hostgator.zip",
    "license_server_railway",
    "forja-license-main",
    "fabricadecortes-site",
    "site",
    ".venv",
    ".git",
    "config.local.php",
    "license_server_versionlock.py",
    "INICIAR_AREA_DE_MEMBROS.bat"
)

$bad = Get-ChildItem $Stage -Recurse -Force -ErrorAction SilentlyContinue |
    Where-Object { $forbiddenNames -contains $_.Name }

if ($bad) {
    $bad | ForEach-Object { Write-Host ("  [BLOQUEADO] " + $_.FullName) -ForegroundColor Red }
    throw "O pacote contem arquivos/pastas internas proibidas. Build cancelado."
}

# Varredura de segredos em arquivos de texto/codigo
$secretPatterns = @(
    "BEGIN [A-Z ]*PRIVATE KEY",
    "PRIVATE_KEY_B64\s*=\s*[A-Za-z0-9+/=]{20,}",
    "ADMIN_TOKEN\s*=\s*[A-Za-z0-9+/=]{20,}",
    "DB_PASS\s*=\s*[^\r\n]{6,}",
    "DB_PASSWORD\s*=\s*[^\r\n]{6,}",
    "MEMBERS_ADMIN_SECRET\s*=\s*[^\r\n]{20,}",
    "abc_live_[A-Za-z0-9]",
    "sk-[A-Za-z0-9]{20,}",
    "re_[A-Za-z0-9]{25,}"
)

$textExtensions = @(".py", ".json", ".txt", ".md", ".bat", ".ps1", ".env", ".example", ".php", ".yml", ".yaml")
$secretHits = @()

Get-ChildItem $Stage -Recurse -File -ErrorAction SilentlyContinue |
    Where-Object { $textExtensions -contains $_.Extension.ToLower() } |
    ForEach-Object {
        $content = Get-Content $_.FullName -Raw -ErrorAction SilentlyContinue
        if (-not $content) { return }
        foreach ($pattern in $secretPatterns) {
            if ($content -match $pattern) {
                $secretHits += ("{0}  ->  {1}" -f $_.FullName.Substring($Stage.Length + 1), $pattern)
            }
        }
    }

if ($secretHits.Count -gt 0) {
    $secretHits | ForEach-Object { Write-Host ("  [SEGREDO] " + $_) -ForegroundColor Red }
    throw "Possivel segredo encontrado no pacote. Build cancelado."
}

# Manifesto com hashes
$manifest = New-Object System.Collections.Generic.List[string]
$manifest.Add("Pacote: $Name")
$manifest.Add("Gerado em: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')")
$manifest.Add("Arquivos:")
$manifest.Add("")

Get-ChildItem $Stage -Recurse -File | Sort-Object FullName | ForEach-Object {
    $relative = $_.FullName.Substring($Stage.Length + 1)
    $hash = (Get-FileHash $_.FullName -Algorithm SHA256).Hash
    $manifest.Add("$hash  $relative")
}

$manifest | Set-Content (Join-Path $Stage "RELEASE-MANIFEST.txt") -Encoding UTF8

# Gera o ZIP
if (Test-Path $Zip) { Remove-Item $Zip -Force }
Compress-Archive -Path $Stage -DestinationPath $Zip -CompressionLevel Optimal

# Verifica o ZIP gerado
Add-Type -AssemblyName System.IO.Compression.FileSystem
$archive = [System.IO.Compression.ZipFile]::OpenRead($Zip)
$badEntries = @($archive.Entries | Where-Object {
    $_.FullName -match "membros_hostgator|license_server_railway|forja-license-main|fabricadecortes-site|\.venv/|config\.local\.php"
})
$entryCount = $archive.Entries.Count
$archive.Dispose()

if ($badEntries.Count -gt 0) {
    $badEntries | ForEach-Object { Write-Host ("  [ZIP BLOQUEADO] " + $_.FullName) -ForegroundColor Red }
    throw "O ZIP final contem itens internos. Build cancelado."
}

$sizeMb = [math]::Round((Get-Item $Zip).Length / 1MB, 2)
Write-Host ""
Write-Host "==============================================================" -ForegroundColor Green
Write-Host "  BUILD CONCLUIDO" -ForegroundColor Green
Write-Host "==============================================================" -ForegroundColor Green
Write-Host "ZIP: $Zip"
Write-Host "Tamanho: $sizeMb MB"
Write-Host "Entradas: $entryCount"
Write-Host "Segredos encontrados: 0"
Write-Host "Pastas internas encontradas: 0"
Write-Host ""
