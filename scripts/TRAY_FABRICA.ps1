# Bandeja do Windows para a Fabrica dos Cortes.
# Inicia o servidor sem console e mantem um icone na area de notificacao.
$ErrorActionPreference = "SilentlyContinue"
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

$root = Split-Path -Parent $PSScriptRoot
$logs = Join-Path $root "logs"
New-Item -ItemType Directory -Path $logs -Force | Out-Null
$trayLog = Join-Path $logs "tray.log"
$url = "http://localhost:7860"

function Write-TrayLog {
    param([string]$Message)
    try {
        $line = "[{0}] {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $Message
        Add-Content -LiteralPath $trayLog -Value $line -Encoding UTF8
    } catch {}
}

function Test-Port {
    param([int]$Port, [int]$TimeoutMs = 400)
    try {
        $client = New-Object System.Net.Sockets.TcpClient
        $iar = $client.BeginConnect("127.0.0.1", $Port, $null, $null)
        $ok = $iar.AsyncWaitHandle.WaitOne($TimeoutMs)
        if ($ok -and $client.Connected) {
            $client.Close()
            return $true
        }
        $client.Close()
    } catch {}
    return $false
}

# Impede duas bandejas ao clicar duas vezes no atalho durante a inicializacao.
$script:mutex = New-Object System.Threading.Mutex($false, "FabricaDosCortesTray")
if (-not $script:mutex.WaitOne(0)) {
    $deadline = (Get-Date).AddSeconds(90)
    while ((Get-Date) -lt $deadline -and -not (Test-Port 7860 250)) {
        Start-Sleep -Milliseconds 500
    }
    Start-Process $url
    exit
}

$pythonw = Join-Path $root ".venv\Scripts\pythonw.exe"
if (-not (Test-Path $pythonw)) {
    $pythonw = Join-Path $root ".venv\Scripts\python.exe"
}
$script:server = $null
$script:quitting = $false
$script:restarts = 0

function Start-Server {
    if (Test-Port 7860 300) {
        Write-TrayLog "Porta 7860 ja esta em uso; mantendo o servidor existente."
        return $true
    }
    Write-TrayLog "Iniciando servidor em segundo plano."
    $outLog = Join-Path $logs "app.stdout.log"
    $errLog = Join-Path $logs "app.stderr.log"
    try {
        $script:server = Start-Process -FilePath $pythonw `
            -ArgumentList @("webui\app.py") `
            -WorkingDirectory $root `
            -WindowStyle Hidden `
            -PassThru `
            -RedirectStandardOutput $outLog `
            -RedirectStandardError $errLog
    } catch {
        Write-TrayLog ("Falha ao iniciar o servidor: " + $_.Exception.Message)
        return $false
    }

    # Primeira execucao carrega Gradio, CUDA e modelos: pode passar de 2 minutos.
    $deadline = (Get-Date).AddSeconds(180)
    while ((Get-Date) -lt $deadline) {
        if (Test-Port 7860 250) {
            Write-TrayLog "Servidor pronto na porta 7860."
            return $true
        }
        if ($script:server -and $script:server.HasExited) {
            Write-TrayLog "O servidor encerrou durante a inicializacao."
            return $false
        }
        Start-Sleep -Milliseconds 500
    }
    if (Test-Port 7860 1500) {
        Write-TrayLog "Servidor pronto na porta 7860 (inicializacao lenta)."
        return $true
    }
    Write-TrayLog "Tempo esgotado aguardando a porta 7860."
    return $false
}

function Stop-Server {
    if ($script:server -and -not $script:server.HasExited) {
        Write-TrayLog ("Encerrando servidor PID " + $script:server.Id)
        & taskkill.exe /PID $script:server.Id /T /F | Out-Null
    }
    $script:server = $null
}

function Open-App {
    Start-Process $url
}

function Open-Logs {
    Start-Process explorer.exe $logs
}

function Exit-Tray {
    $script:quitting = $true
    Stop-Server
    if ($script:icon) {
        $script:icon.Visible = $false
        $script:icon.Dispose()
    }
    try { $script:mutex.ReleaseMutex() } catch {}
    [System.Windows.Forms.Application]::Exit()
}

$iconPath = Join-Path $root "app.ico"
if (-not (Test-Path $iconPath)) {
    $iconPath = Join-Path $root "branding\app.ico"
}

$script:icon = New-Object System.Windows.Forms.NotifyIcon
try {
    $script:icon.Icon = New-Object System.Drawing.Icon($iconPath)
} catch {
    $script:icon.Icon = [System.Drawing.SystemIcons]::Application
}
$script:icon.Text = "Fabrica dos Cortes"
$script:icon.Visible = $true

$menu = New-Object System.Windows.Forms.ContextMenuStrip
$openItem = $menu.Items.Add("Abrir Fabrica dos Cortes")
$openItem.Font = New-Object System.Drawing.Font($menu.Font, [System.Drawing.FontStyle]::Bold)
$openItem.Add_Click({ Open-App })

$logsItem = $menu.Items.Add("Abrir pasta de logs")
$logsItem.Add_Click({ Open-Logs })

$restartItem = $menu.Items.Add("Reiniciar servidor")
$restartItem.Add_Click({
    Stop-Server
    Start-Sleep -Milliseconds 600
    if (Start-Server) {
        Open-App
    } else {
        $script:icon.ShowBalloonTip(6000, "Fabrica dos Cortes", "Nao foi possivel reiniciar. Veja a pasta de logs.", [System.Windows.Forms.ToolTipIcon]::Error)
    }
})

$menu.Items.Add((New-Object System.Windows.Forms.ToolStripSeparator)) | Out-Null
$exitItem = $menu.Items.Add("Sair")
$exitItem.Add_Click({ Exit-Tray })

$script:icon.ContextMenuStrip = $menu
$script:icon.add_DoubleClick({ Open-App })

$timer = New-Object System.Windows.Forms.Timer
$timer.Interval = 3000
$timer.Add_Tick({
    if ($script:quitting) { return }
    if ($script:server -and $script:server.HasExited) {
        Write-TrayLog "O servidor encerrou inesperadamente."
        if ($script:restarts -lt 3) {
            $script:restarts++
            $script:icon.ShowBalloonTip(4000, "Fabrica dos Cortes", "O servidor encerrou. Reiniciando...", [System.Windows.Forms.ToolTipIcon]::Warning)
            Start-Sleep -Milliseconds 800
            if (Start-Server) {
                $script:restarts = 0
                $script:icon.ShowBalloonTip(4000, "Fabrica dos Cortes", "Servidor reiniciado. Clique para abrir.", [System.Windows.Forms.ToolTipIcon]::Info)
            }
        } else {
            $script:icon.ShowBalloonTip(8000, "Fabrica dos Cortes", "O servidor encerrou varias vezes. Abra os logs e use Reiniciar servidor.", [System.Windows.Forms.ToolTipIcon]::Error)
        }
    }
})
$timer.Start()

Write-TrayLog "Bandeja iniciada."
if (Start-Server) {
    $script:icon.ShowBalloonTip(4000, "Fabrica dos Cortes", "Rodando em segundo plano. Clique no icone para abrir.", [System.Windows.Forms.ToolTipIcon]::Info)
    Open-App
} else {
    $script:icon.ShowBalloonTip(8000, "Fabrica dos Cortes", "Nao foi possivel iniciar. Abra a pasta de logs.", [System.Windows.Forms.ToolTipIcon]::Error)
}

[System.Windows.Forms.Application]::Run()
