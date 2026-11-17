' Atalho oficial: inicia a Fabrica dos Cortes totalmente oculto.
' Roda o INICIAR_FABRICA_DE_CORTES.bat com a janela escondida (estilo 0).

Option Explicit

Dim fso, shell, root, bat, cmd
Set fso = CreateObject("Scripting.FileSystemObject")
Set shell = CreateObject("WScript.Shell")

' scripts\LAUNCH_HIDDEN.vbs -> raiz do aplicativo
root = fso.GetParentFolderName(fso.GetParentFolderName(WScript.ScriptFullName))
bat = root & "\INICIAR_FABRICA_DE_CORTES.bat"

If Not fso.FileExists(bat) Then
    WScript.Quit 1
End If

shell.CurrentDirectory = root
cmd = "cmd.exe /c """ & bat & """"
shell.Run cmd, 0, False

WScript.Quit 0
