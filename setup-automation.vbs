' VBS Script para ejecutar PowerShell como administrador
Set objShell = CreateObject("Shell.Application")
strPath = WScript.ScriptFullName
Set objFSO = CreateObject("Scripting.FileSystemObject")
strFolder = objFSO.GetParentFolderName(strPath)
objShell.ShellExecute "powershell", "-NoProfile -ExecutionPolicy Bypass -File """ & strFolder & "\Setup-Automation.ps1""", "", "runas", 1
