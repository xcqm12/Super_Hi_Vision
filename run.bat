@echo off
rem ================================================================
rem  Super Hi Vision - Application Mode Launcher (no console)
rem  This batch file is only a thin wrapper. It delegates to the
rem  VBS launcher (wscript.exe) so NO console window stays open.
rem ================================================================
start "" wscript.exe "%~dp0SuperHiVision_Launcher.vbs"
exit /b 0
