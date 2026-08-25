; Super Hi Vision NSIS Installation Script
; Version: 1.5.15
; 应用模式：启动器通过 wscript 运行，无控制台窗口
; 安装包已合成全部运行时依赖（EXE + FFmpeg + 环境检测脚本）

!include "MUI2.nsh"
!include "FileFunc.nsh"

; Application Info
!define APPNAME "Super Hi Vision"
!define COMPANYNAME "QLM Network Entertainment Technology Co., Ltd."
!define DESCRIPTION "Advanced HD Screen Recording Tool"
!define VERSIONMAJOR 1
!define VERSIONMINOR 5
!define VERSIONBUILD 15
!define HELPURL "https://team.qlm.org.cn"
!define UPDATEURL "https://team.qlm.org.cn"
!define ABOUTURL "https://team.qlm.org.cn"
!define INSTALLSIZE 120000
!define EXEFILE "SuperHiVision_v1.5.15.exe"
!define LAUNCHERVBS "SuperHiVision_Launcher.vbs"

; Installer Settings
Name "${APPNAME}"
OutFile "SuperHiVision_Setup_v${VERSIONMAJOR}.${VERSIONMINOR}.${VERSIONBUILD}.exe"
InstallDir "$PROGRAMFILES64\${APPNAME}"

; Request Admin Rights
RequestExecutionLevel admin

; UI Settings
!define MUI_ABORTWARNING
!define MUI_ICON "${NSISDIR}\Contrib\Graphics\Icons\modern-install.ico"
!define MUI_UNICON "${NSISDIR}\Contrib\Graphics\Icons\modern-uninstall.ico"

; Pages
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "LICENSE.txt"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

; Uninstaller Pages
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

; Language
!insertmacro MUI_LANGUAGE "SimpChinese"

; Install Section
Section "install"
    SetOutPath $INSTDIR

    ; Create subdirectories
    CreateDirectory "$INSTDIR\resources"
    CreateDirectory "$INSTDIR\ffmpeg"

    ; ---- 主程序（EXE 已包含全部 Python 依赖）----
    File "${EXEFILE}"
    File "${LAUNCHERVBS}"
    File "Super_Hi_Vision_App.pyw"
    File "Create_Desktop_Shortcut.vbs"
    File "check_environment.py"
    File "CHANGELOG.md"
    File "LICENSE.txt"
    File "README.md"

    ; ---- FFmpeg 依赖（环境检测所需）----
    SetOutPath "$INSTDIR\ffmpeg"
    File "ffmpeg\ffmpeg.exe"
    File "ffmpeg\ffplay.exe"
    File "ffmpeg\ffprobe.exe"

    SetOutPath $INSTDIR

    ; ---- 快捷方式（全部指向 VBS 启动器，无控制台窗口）----
    CreateDirectory "$SMPROGRAMS\${APPNAME}"
    CreateShortCut "$SMPROGRAMS\${APPNAME}\${APPNAME}.lnk" "$WINDIR\System32\wscript.exe" '"$INSTDIR\${LAUNCHERVBS}"' "$INSTDIR\${EXEFILE}" 0
    CreateShortCut "$SMPROGRAMS\${APPNAME}\Changelog.lnk" "$INSTDIR\CHANGELOG.md" "" "$INSTDIR\CHANGELOG.md" 0
    CreateShortCut "$SMPROGRAMS\${APPNAME}\Create Desktop Shortcut.lnk" "$WINDIR\System32\wscript.exe" '"$INSTDIR\Create_Desktop_Shortcut.vbs"' "$INSTDIR\${EXEFILE}" 0
    CreateShortCut "$SMPROGRAMS\${APPNAME}\Environment Check.lnk" "$WINDIR\System32\wscript.exe" '"$INSTDIR\check_environment.py"' "$INSTDIR\${EXEFILE}" 0
    CreateShortCut "$SMPROGRAMS\${APPNAME}\Uninstall.lnk" "$INSTDIR\uninstall.exe" "" "$INSTDIR\uninstall.exe" 0

    ; Desktop shortcut -> launcher (no console)
    CreateShortCut "$DESKTOP\${APPNAME}.lnk" "$WINDIR\System32\wscript.exe" '"$INSTDIR\${LAUNCHERVBS}"' "$INSTDIR\${EXEFILE}" 0

    ; Write uninstaller
    WriteUninstaller "$INSTDIR\uninstall.exe"

    ; Write registry info for uninstall
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "DisplayName" "${APPNAME}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "UninstallString" "$\"$INSTDIR\uninstall.exe$\""
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "QuietUninstallString" "$\"$INSTDIR\uninstall.exe$\" /S"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "InstallLocation" "$\"$INSTDIR$\""
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "DisplayIcon" "$\"$INSTDIR\${EXEFILE}$\""
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "Publisher" "${COMPANYNAME}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "HelpLink" "${HELPURL}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "URLUpdateInfo" "${UPDATEURL}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "URLInfoAbout" "${ABOUTURL}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "DisplayVersion" "${VERSIONMAJOR}.${VERSIONMINOR}.${VERSIONBUILD}"
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "VersionMajor" ${VERSIONMAJOR}
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "VersionMinor" ${VERSIONMINOR}
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "NoModify" 1
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "NoRepair" 1
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "EstimatedSize" ${INSTALLSIZE}
SectionEnd

; Uninstall Section
Section "uninstall"
    ; Delete installed files
    Delete "$INSTDIR\${EXEFILE}"
    Delete "$INSTDIR\${LAUNCHERVBS}"
    Delete "$INSTDIR\Super_Hi_Vision_App.pyw"
    Delete "$INSTDIR\Create_Desktop_Shortcut.vbs"
    Delete "$INSTDIR\CHANGELOG.md"
    Delete "$INSTDIR\LICENSE.txt"
    Delete "$INSTDIR\README.md"
    Delete "$INSTDIR\check_environment.py"
    Delete "$INSTDIR\uninstall.exe"
    Delete "$INSTDIR\ffmpeg\ffmpeg.exe"
    Delete "$INSTDIR\ffmpeg\ffplay.exe"
    Delete "$INSTDIR\ffmpeg\ffprobe.exe"

    ; Delete Start Menu shortcuts
    Delete "$SMPROGRAMS\${APPNAME}\${APPNAME}.lnk"
    Delete "$SMPROGRAMS\${APPNAME}\Changelog.lnk"
    Delete "$SMPROGRAMS\${APPNAME}\Create Desktop Shortcut.lnk"
    Delete "$SMPROGRAMS\${APPNAME}\Environment Check.lnk"
    Delete "$SMPROGRAMS\${APPNAME}\Uninstall.lnk"
    RMDir "$SMPROGRAMS\${APPNAME}"

    ; Delete Desktop shortcut
    Delete "$DESKTOP\${APPNAME}.lnk"

    ; Delete directories
    RMDir "$INSTDIR\ffmpeg"
    RMDir "$INSTDIR\resources"
    RMDir "$INSTDIR"

    ; Delete registry info
    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}"
SectionEnd
