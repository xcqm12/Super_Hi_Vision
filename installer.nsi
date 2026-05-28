; Super Hi Vision NSIS Installation Script
; Version: 1.5.9

!include "MUI2.nsh"
!include "FileFunc.nsh"

; Application Info
!define APPNAME "Super Hi Vision"
!define COMPANYNAME "QLM Network Entertainment Technology Co., Ltd."
!define DESCRIPTION "Advanced HD Screen Recording Tool"
!define VERSIONMAJOR 1
!define VERSIONMINOR 5
!define VERSIONBUILD 9
!define HELPURL "https://team.qlm.org.cn"
!define UPDATEURL "https://team.qlm.org.cn"
!define ABOUTURL "https://team.qlm.org.cn"
!define INSTALLSIZE 50000

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

    ; Copy main files
    File "dist\SuperHiVision_v1.5.9.exe"
    File "CHANGELOG.md"
    File "LICENSE.txt"
    File "check_environment.py"

    ; Create Start Menu shortcuts
    CreateDirectory "$SMPROGRAMS\${APPNAME}"
    CreateShortCut "$SMPROGRAMS\${APPNAME}\${APPNAME}.lnk" "$INSTDIR\SuperHiVision_v1.5.9.exe" "" "$INSTDIR\SuperHiVision_v1.5.9.exe" 0
    CreateShortCut "$SMPROGRAMS\${APPNAME}\Changelog.lnk" "$INSTDIR\CHANGELOG.md" "" "$INSTDIR\CHANGELOG.md" 0
    CreateShortCut "$SMPROGRAMS\${APPNAME}\Environment Check.lnk" "$INSTDIR\check_environment.py" "" "$INSTDIR\check_environment.py" 0
    CreateShortCut "$SMPROGRAMS\${APPNAME}\Uninstall.lnk" "$INSTDIR\uninstall.exe" "" "$INSTDIR\uninstall.exe" 0

    ; Create Desktop shortcut
    CreateShortCut "$DESKTOP\${APPNAME}.lnk" "$INSTDIR\SuperHiVision_v1.5.9.exe" "" "$INSTDIR\SuperHiVision_v1.5.9.exe" 0

    ; Write uninstaller
    WriteUninstaller "$INSTDIR\uninstall.exe"

    ; Write registry info for uninstall
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "DisplayName" "${APPNAME}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "UninstallString" "$\"$INSTDIR\uninstall.exe$\""
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "QuietUninstallString" "$\"$INSTDIR\uninstall.exe$\" /S"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "InstallLocation" "$\"$INSTDIR$\""
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "DisplayIcon" "$\"$INSTDIR\SuperHiVision_v1.5.9.exe$\""
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
    Delete "$INSTDIR\SuperHiVision_v1.5.9.exe"
    Delete "$INSTDIR\CHANGELOG.md"
    Delete "$INSTDIR\LICENSE.txt"
    Delete "$INSTDIR\check_environment.py"
    Delete "$INSTDIR\uninstall.exe"

    ; Delete Start Menu shortcuts
    Delete "$SMPROGRAMS\${APPNAME}\${APPNAME}.lnk"
    Delete "$SMPROGRAMS\${APPNAME}\Changelog.lnk"
    Delete "$SMPROGRAMS\${APPNAME}\Environment Check.lnk"
    Delete "$SMPROGRAMS\${APPNAME}\Uninstall.lnk"
    RMDir "$SMPROGRAMS\${APPNAME}"

    ; Delete Desktop shortcut
    Delete "$DESKTOP\${APPNAME}.lnk"

    ; Delete directories
    RMDir "$INSTDIR\resources"
    RMDir "$INSTDIR"

    ; Delete registry info
    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}"
SectionEnd
