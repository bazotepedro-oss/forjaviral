' Atalho oficial: inicia a Fabrica dos Cortes sem NENHUMA janela.
' Nao usa cmd.exe nem .bat: o Windows Terminal abre janela mesmo com estilo oculto
' quando o alvo e um arquivo em lote. Aqui rodamos pythonw + powershell ocultos.

Option Explicit

Dim fso, shell, root, pythonw, updater, ps1, cmd

Set fso = CreateObject("Scripting.FileSystemObject")
Set shell = CreateObject("WScript.Shell")

' scripts\LAUNCH_HIDDEN.vbs -> raiz do aplicativo
root = fso.GetParentFolderName(fso.GetParentFolderName(WScript.ScriptFullName))
pythonw = root & "\.venv\Scripts\pythonw.exe"

If Not fso.FileExists(pythonw) Then
    MsgBox "O aplicativo ainda nao foi instalado neste computador." & vbCrLf & vbCrLf & _
           "Execute o INSTALADOR.bat na pasta:" & vbCrLf & root, _
           vbExclamation, "Fabrica dos Cortes"
    WScript.Quit 1
End If

shell.CurrentDirectory = root

' 0) Checagem rapida: se as dependencias estiverem incompletas, avisa e abre o instalador.
Dim rc
On Error Resume Next
rc = shell.Run("""" & pythonw & """ -c ""import gradio""", 0, True)
On Error GoTo 0
If rc <> 0 Then
    MsgBox "As dependencias do aplicativo estao incompletas neste computador." & vbCrLf & vbCrLf & _
           "O instalador sera aberto para reparar. Isso pode levar alguns minutos.", _
           vbExclamation, "Fabrica dos Cortes"
    shell.Run """" & root & "\INSTALADOR.bat""", 1, False
    WScript.Quit 0
End If

' 1) Atualizacao silenciosa (pythonw = sem console). Espera terminar para nao
'    trocar arquivos enquanto o servidor inicia.
updater = root & "\scripts\auto_update.py"
If fso.FileExists(updater) Then
    On Error Resume Next
    shell.Run """" & pythonw & """ """ & updater & """", 0, True
    On Error GoTo 0
End If

' 2) Bandeja do Windows, tambem oculta.
ps1 = root & "\scripts\TRAY_FABRICA.ps1"
If Not fso.FileExists(ps1) Then
    MsgBox "Arquivo da bandeja nao encontrado:" & vbCrLf & ps1, vbExclamation, "Fabrica dos Cortes"
    WScript.Quit 1
End If

cmd = "powershell.exe -NoProfile -Sta -ExecutionPolicy Bypass -WindowStyle Hidden -File """ & ps1 & """"
shell.Run cmd, 0, False

WScript.Quit 0
