' Abre a bandeja da Fabrica dos Cortes sem NENHUMA janela visivel.
' Usa WScript.Shell.Run com estilo 0 (oculto): nao aparece janela nem botao na barra.

Option Explicit

Dim fso, shell, root, ps1, cmd
Set fso = CreateObject("Scripting.FileSystemObject")
Set shell = CreateObject("WScript.Shell")

' scripts\LAUNCH_TRAY.vbs -> raiz do aplicativo
root = fso.GetParentFolderName(fso.GetParentFolderName(WScript.ScriptFullName))
ps1 = root & "\scripts\TRAY_FABRICA.ps1"

If Not fso.FileExists(ps1) Then
    WScript.Quit 1
End If

shell.CurrentDirectory = root
cmd = "powershell.exe -NoProfile -Sta -ExecutionPolicy Bypass -WindowStyle Hidden -File """ & ps1 & """"
shell.Run cmd, 0, False

WScript.Quit 0
