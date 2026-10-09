; Super Hi Vision NSIS Installation Script
; Version: 1.5.26
; 应用模式：启动器通过 wscript 运行，无控制台窗口
; 安装包已合成全部运行时依赖（EXE + FFmpeg + 环境检测脚本）

!include "MUI2.nsh"
!include "FileFunc.nsh"

; Application Info
!define APPNAME "Super Hi Vision"
!define COMPANYNAME "QLM Network Entertainment Technology Co., Ltd."
!define PUBLISHER "SevenZeroMeowTeam"
!define DESCRIPTION "Advanced HD Screen Recording Tool"
!define VERSIONMAJOR 1
!define VERSIONMINOR 5
!define VERSIONBUILD 26
!define HELPURL "https://team.qlm.org.cn"
!define UPDATEURL "https://team.qlm.org.cn"
!define ABOUTURL "https://team.qlm.org.cn"
!define INSTALLSIZE 229000
!define EXEFILE "SuperHiVision_v1.5.26.exe"
!define LAUNCHERVBS "SuperHiVision_Launcher.vbs"

; Installer Settings
Name "${APPNAME}"
OutFile "SuperHiVision_Setup_v${VERSIONMAJOR}.${VERSIONMINOR}.${VERSIONBUILD}.exe"
InstallDir "$PROGRAMFILES64\${APPNAME}"

; ---- 文件版本信息资源：安装包属性里的公司/发行者名称 ----
; VIProductVersion 必须是四段版本号（x.x.x.x），否则 makensis 会报错。
VIProductVersion "${VERSIONMAJOR}.${VERSIONMINOR}.${VERSIONBUILD}.0"
VIAddVersionKey /LANG=2052 "ProductName"     "${APPNAME}"
VIAddVersionKey /LANG=2052 "CompanyName"     "${PUBLISHER}"
VIAddVersionKey /LANG=2052 "FileDescription" "${APPNAME} Setup"
VIAddVersionKey /LANG=2052 "FileVersion"     "${VERSIONMAJOR}.${VERSIONMINOR}.${VERSIONBUILD}"
VIAddVersionKey /LANG=2052 "ProductVersion"  "${VERSIONMAJOR}.${VERSIONMINOR}.${VERSIONBUILD}"
VIAddVersionKey /LANG=2052 "LegalCopyright"  "Copyright (C) 2019-2025 ${COMPANYNAME}"
VIAddVersionKey /LANG=2052 "OriginalFilename" "SuperHiVision_Setup_v${VERSIONMAJOR}.${VERSIONMINOR}.${VERSIONBUILD}.exe"

; Request Admin Rights
RequestExecutionLevel admin

; UI Settings
!define MUI_ABORTWARNING
!define MUI_ICON "icon.ico"
!define MUI_UNICON "icon.ico"

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

    ; ---- 主程序（EXE 已包含全部 Python 依赖 + 内置 FFmpeg）----
    File "${EXEFILE}"
    File "icon.ico"
    File "${LAUNCHERVBS}"
    File "Super_Hi_Vision_App.pyw"
    File "Create_Desktop_Shortcut.vbs"
    File "check_environment.py"
    File "CHANGELOG.md"
    File "LICENSE.txt"
    File "README.md"

    ; ---- 源码模式所需（EXE 缺失时 .pyw / 启动器会回退到源码运行）----
    File "Super_Hi_Vision_PyQt.py"
    File "Super_Hi_Vision.py"
    File "run.bat"
    File "requirements.txt"

    ; ---- FFmpeg：不再单独分发 ----
    ; 自 v1.5.23 起 ffmpeg.exe / ffprobe.exe 已内置在单文件主程序里（解包到 _MEIPASS），
    ; 这里再放一份会让安装包白白多出 ~200MB；用户仍可在 $INSTDIR\ffmpeg 下自备一份
    ; 来覆盖内置版本（程序优先使用外置的）。
    ; FFmpeg 为 GPLv3 静态构建，随附版本说明与许可全文（合规要求，必须保留）
    File "FFMPEG_NOTICE.txt"
    File "LICENSE_GPLv3.txt"

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
    Delete /REBOOTOK "$INSTDIR\${EXEFILE}"
    Delete "$INSTDIR\SuperHiVision_error.log"
    Delete "$INSTDIR\icon.ico"
    Delete "$INSTDIR\${LAUNCHERVBS}"
    Delete "$INSTDIR\Super_Hi_Vision_App.pyw"
    Delete "$INSTDIR\Create_Desktop_Shortcut.vbs"
    Delete "$INSTDIR\CHANGELOG.md"
    Delete "$INSTDIR\LICENSE.txt"
    Delete "$INSTDIR\README.md"
    Delete "$INSTDIR\check_environment.py"
    Delete "$INSTDIR\Super_Hi_Vision_PyQt.py"
    Delete "$INSTDIR\Super_Hi_Vision.py"
    Delete "$INSTDIR\run.bat"
    Delete "$INSTDIR\requirements.txt"
    Delete "$INSTDIR\uninstall.exe"
    ; 旧版本（≤1.5.22）曾在 $INSTDIR\ffmpeg 下放外置 FFmpeg，升级安装后这里可能还留着
    Delete "$INSTDIR\ffmpeg\ffmpeg.exe"
    Delete "$INSTDIR\ffmpeg\ffplay.exe"
    Delete "$INSTDIR\ffmpeg\ffprobe.exe"
    Delete "$INSTDIR\ffmpeg\FFMPEG_NOTICE.txt"
    Delete "$INSTDIR\ffmpeg\LICENSE_GPLv3.txt"
    ; v1.5.23 起 FFmpeg 版本说明与 GPLv3 全文放在安装根目录
    Delete "$INSTDIR\FFMPEG_NOTICE.txt"
    Delete "$INSTDIR\LICENSE_GPLv3.txt"

    ; Delete Start Menu shortcuts
    Delete "$SMPROGRAMS\${APPNAME}\${APPNAME}.lnk"
    Delete "$SMPROGRAMS\${APPNAME}\Changelog.lnk"
    Delete "$SMPROGRAMS\${APPNAME}\Create Desktop Shortcut.lnk"
    Delete "$SMPROGRAMS\${APPNAME}\Environment Check.lnk"
    Delete "$SMPROGRAMS\${APPNAME}\Uninstall.lnk"
    RMDir "$SMPROGRAMS\${APPNAME}"

    ; Delete Desktop shortcut
    Delete "$DESKTOP\${APPNAME}.lnk"

    ; Delete directories（resources 由程序运行时生成，可能非空；/r 保证删净）
    RMDir /r "$INSTDIR\ffmpeg"
    RMDir /r "$INSTDIR\resources"
    RMDir "$INSTDIR"

    ; Delete registry info
    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}"
SectionEnd
