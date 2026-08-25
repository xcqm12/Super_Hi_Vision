' ================================================================
' Super Hi Vision - Application Mode Launcher
' Double-click to run. No console window is shown.
'
' Launch priority:
'   1. Packaged EXE  (SuperHiVision_v1.5.14.exe)
'   2. pythonw.exe running source  (Super_Hi_Vision_PyQt.py)
'   3. Super_Hi_Vision_App.pyw (pythonw launcher)
'   4. python.exe (fallback)
' ================================================================
Option Explicit

Dim fso, shell, appDir
Dim exePath, pywPath, pyPath, scriptPath, appPyw
Dim i, found

Set fso = CreateObject("Scripting.FileSystemObject")
Set shell = CreateObject("WScript.Shell")

' Folder that contains this launcher (handles paths with spaces / Chinese)
appDir = fso.GetParentFolderName(WScript.ScriptFullName)

' ---------- 1. Prefer the packaged EXE ----------
exePath = appDir & "\SuperHiVision_v1.5.14.exe"
If fso.FileExists(exePath) Then
    shell.Run """" & exePath & """", 1, False
    WScript.Quit
End If

' ---------- 2. Run source with pythonw.exe (no console) ----------
scriptPath = appDir & "\Super_Hi_Vision_PyQt.py"
If fso.FileExists(scriptPath) Then

    ' 2a. pythonw.exe next to the launcher
    pywPath = appDir & "\pythonw.exe"
    If fso.FileExists(pywPath) Then
        shell.Run """" & pywPath & """ """ & scriptPath & """", 1, False
        WScript.Quit
    End If

    ' 2b. pythonw.exe found on PATH
    pywPath = FindInPath("pythonw.exe")
    If pywPath <> "" Then
        shell.Run """" & pywPath & """ """ & scriptPath & """", 1, False
        WScript.Quit
    End If

    ' 2c. python.exe next to the launcher (fallback, may show a console)
    pyPath = appDir & "\python.exe"
    If fso.FileExists(pyPath) Then
        shell.Run """" & pyPath & """ """ & scriptPath & """", 1, False
        WScript.Quit
    End If

    ' 2d. python.exe found on PATH (fallback)
    pyPath = FindInPath("python.exe")
    If pyPath <> "" Then
        shell.Run """" & pyPath & """ """ & scriptPath & """", 1, False
        WScript.Quit
    End If

    ' 2e. Super_Hi_Vision_App.pyw (uses default pythonw file association)
    appPyw = appDir & "\Super_Hi_Vision_App.pyw"
    If fso.FileExists(appPyw) Then
        shell.Run """" & appPyw & """", 1, False
        WScript.Quit
    End If

    MsgBox "Python environment was not found." & vbCrLf & vbCrLf & _
           "Please install Python 3.8+ (check 'Add to PATH') and run:" & vbCrLf & _
           "  pip install PyQt5 opencv-python numpy pyaudio Pillow" & vbCrLf & vbCrLf & _
           "Or use the packaged EXE version instead.", _
           vbExclamation, "Super Hi Vision"

Else
    MsgBox "Main program file was not found: " & vbCrLf & _
           "  " & exePath & vbCrLf & _
           "  " & scriptPath & vbCrLf & vbCrLf & _
           "Cannot start Super Hi Vision.", _
           vbExclamation, "Super Hi Vision"
End If

' ================================================================
' Helper: search for an executable on the system PATH
' ================================================================
Function FindInPath(exeName)
    Dim pathEnv, paths, p
    pathEnv = shell.Environment("Process")("PATH")
    paths = Split(pathEnv, ";")
    For Each p In paths
        If p <> "" Then
            If fso.FileExists(p & "\" & exeName) Then
                FindInPath = p & "\" & exeName
                Exit Function
            End If
        End If
    Next
    FindInPath = ""
End Function
