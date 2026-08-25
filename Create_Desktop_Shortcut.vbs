' ================================================================
' Super Hi Vision - Create Desktop Shortcut
' Double-click this file to create a desktop shortcut that starts
' the application in "Application Mode" (no console window).
' ================================================================
Option Explicit

Dim fso, shell, desktopPath, appDir, lnkPath, lnk
Dim iconPath, targetPath

Set fso = CreateObject("Scripting.FileSystemObject")
Set shell = CreateObject("WScript.Shell")

' Folder that contains this script
appDir = fso.GetParentFolderName(WScript.ScriptFullName)

' Desktop folder
desktopPath = shell.SpecialFolders("Desktop")

' Shortcut target: the launcher (runs via wscript -> no console)
targetPath = appDir & "\SuperHiVision_Launcher.vbs"

' Icon: prefer the packaged EXE, fall back to the Python file
iconPath = appDir & "\SuperHiVision_v1.5.13.exe"
If Not fso.FileExists(iconPath) Then
    iconPath = appDir & "\Super_Hi_Vision_PyQt.py"
End If

lnkPath = desktopPath & "\Super Hi Vision.lnk"

Set lnk = shell.CreateShortcut(lnkPath)
lnk.TargetPath = targetPath
lnk.WorkingDirectory = appDir
lnk.IconLocation = iconPath & ", 0"
lnk.Description = "Super Hi Vision - Advanced HD Screen Recording Tool"
lnk.Save

MsgBox "Desktop shortcut created:" & vbCrLf & lnkPath, _
       vbInformation, "Super Hi Vision"
