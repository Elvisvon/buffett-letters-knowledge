; 巴菲特投资智慧 · Windows 安装器（NSIS 3，Unicode）
; ---------------------------------------------------
; 本文件为模板：由 package_windows.py 替换 VERSION / STAGE / ICON / OUTFILE
; 占位符（形如 @VERSION@）后，以 UTF-8（带 BOM）写出并调用 makensis 编译。
; 特性：按用户安装（无需管理员）、开始菜单/桌面快捷方式、
;       「应用和功能」卸载注册（HKCU）、内置 uninstall.exe 卸载器
;       （卸载时自动停止服务；默认保留用户笔记数据，可勾选一并删除）。

Unicode true

!define APP_NAME "巴菲特投资智慧"
!define APP_VERSION "@VERSION@"
!define UNINST_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\巴菲特投资智慧"

Name "${APP_NAME}"
OutFile "@OUTFILE_ABS@"
RequestExecutionLevel user
SetCompressor /SOLID lzma

!include "MUI2.nsh"
!include "FileFunc.nsh"
!include "LogicLib.nsh"
!include "StrFunc.nsh"
${StrTrimNewLines}
${UnStrTrimNewLines}

; 安装开始前：确定安装目录（优先记忆上次位置，回退 LOCALAPPDATA/USERPROFILE，
; 个别精简版 Windows 的 %LOCALAPPDATA% 可能缺失或异常），
; 并自动停止旧版本正在运行的服务，避免安装时 python\ 文件被占用
; （报「无法打开要写入的文件」多为此类原因）
Function .onInit
  ReadRegStr $0 HKCU "${UNINST_KEY}" "InstallLocation"
  ${If} $0 != ""
    StrCpy $INSTDIR $0
  ${ElseIf} $LOCALAPPDATA != ""
    StrCpy $INSTDIR "$LOCALAPPDATA\巴菲特投资智慧"
  ${Else}
    StrCpy $INSTDIR "$USERPROFILE\AppData\Local\巴菲特投资智慧"
  ${EndIf}
  ClearErrors
  FileOpen $0 "$APPDATA\巴菲特投资智慧\server.pid" r
  IfErrors oninit_no_pid
  FileRead $0 $1
  FileClose $0
  ${StrTrimNewLines} $1 $1
  StrCmp $1 "" oninit_no_pid
  ExecWait 'taskkill /PID $1 /T /F'
  oninit_no_pid:
  nsExec::Exec "powershell -NoProfile -NonInteractive -Command $\"Get-CimInstance Win32_Process | Where-Object { $$_.CommandLine -like '*serve_buffett_app.py*' } | ForEach-Object { Stop-Process -Id $$_.ProcessId -Force }$\""
FunctionEnd

; 版本信息（资源管理器「属性 → 详细信息」）
VIProductVersion "@VERSION@.0.0"
VIAddVersionKey /LANG=2052 "ProductName" "巴菲特投资智慧"
VIAddVersionKey /LANG=2052 "FileDescription" "巴菲特投资智慧 安装程序"
VIAddVersionKey /LANG=2052 "FileVersion" "@VERSION@"
VIAddVersionKey /LANG=2052 "ProductVersion" "@VERSION@"
VIAddVersionKey /LANG=2052 "CompanyName" "本地个人应用（巴菲特致股东信知识库）"
VIAddVersionKey /LANG=2052 "LegalCopyright" "仅供个人学习研究使用"

; ---------- 安装界面 ----------
!define MUI_ABORTWARNING
!define MUI_ICON "@ICON_ABS@"
!define MUI_UNICON "@ICON_ABS@"
!define MUI_FINISHPAGE_RUN
!define MUI_FINISHPAGE_RUN_TEXT "立即启动 巴菲特投资智慧"
!define MUI_FINISHPAGE_RUN_FUNCTION "LaunchApp"

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_COMPONENTS
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_COMPONENTS
!insertmacro MUI_UNPAGE_INSTFILES

!insertmacro MUI_LANGUAGE "SimpChinese"

; 完成页「立即启动」：直接运行编译版启动器
Function LaunchApp
  Exec '"$INSTDIR\巴菲特投资智慧.exe"'
FunctionEnd

; ---------- 安装段 ----------
Section "应用文件（必需）" SecMain
  SectionIn RO
  SetOutPath "$INSTDIR"
  ; 先整目录重建 python/ 与 app/：只“新建”文件、绝不“覆盖”已有文件——
  ; 安全软件会把覆盖已有压缩包/文档文件判为勒索行为（误报），
  ; 新建文件是正常安装行为；同时规避旧文件被占用导致写入失败
  RMDir /r "$INSTDIR\python"
  RMDir /r "$INSTDIR\app"
  File /r "@STAGE_ABS@\巴菲特投资智慧\*.*"

  ; 开始菜单快捷方式（启动器/停止服务为编译 exe，非脚本）
  CreateDirectory "$SMPROGRAMS\巴菲特投资智慧"
  CreateShortcut "$SMPROGRAMS\巴菲特投资智慧\巴菲特投资智慧.lnk" "$INSTDIR\巴菲特投资智慧.exe" "" "$INSTDIR\icon.ico" 0
  CreateShortcut "$SMPROGRAMS\巴菲特投资智慧\停止服务.lnk" "$INSTDIR\停止服务.exe" "" "$INSTDIR\icon.ico" 0
  CreateShortcut "$SMPROGRAMS\巴菲特投资智慧\使用说明.lnk" "$INSTDIR\使用说明.txt" "" "$INSTDIR\icon.ico" 0
  CreateShortcut "$SMPROGRAMS\巴菲特投资智慧\卸载巴菲特投资智慧.lnk" "$INSTDIR\uninstall.exe" "" "$INSTDIR\icon.ico" 0
  ; 清理旧版残留的 VBS 脚本（已被编译版替代，避免杀毒软件继续误报）
  Delete "$INSTDIR\巴菲特投资智慧.vbs"
  Delete "$INSTDIR\停止服务.vbs"

  ; 卸载器 + 卸载注册（HKCU，随按用户安装）
  WriteUninstaller "$INSTDIR\uninstall.exe"
  WriteRegStr HKCU "${UNINST_KEY}" "DisplayName" "巴菲特投资智慧"
  WriteRegStr HKCU "${UNINST_KEY}" "DisplayVersion" "${APP_VERSION}"
  WriteRegStr HKCU "${UNINST_KEY}" "Publisher" "本地个人应用（巴菲特致股东信知识库）"
  WriteRegStr HKCU "${UNINST_KEY}" "InstallLocation" "$INSTDIR"
  WriteRegStr HKCU "${UNINST_KEY}" "DisplayIcon" "$INSTDIR\icon.ico"
  WriteRegStr HKCU "${UNINST_KEY}" "UninstallString" '"$INSTDIR\uninstall.exe"'
  WriteRegDWORD HKCU "${UNINST_KEY}" "NoModify" 1
  WriteRegDWORD HKCU "${UNINST_KEY}" "NoRepair" 1
  ${GetSize} "$INSTDIR" "/S=0K" $0 $1 $2
  WriteRegDWORD HKCU "${UNINST_KEY}" "EstimatedSize" "$0"
SectionEnd

Section "桌面快捷方式" SecDesktop
  ; 先删除可能存在的旧版残留（曾指向已移除的 vbs），再创建指向 exe 的新图标
  Delete "$DESKTOP\巴菲特投资智慧.lnk"
  CreateShortcut "$DESKTOP\巴菲特投资智慧.lnk" "$INSTDIR\巴菲特投资智慧.exe" "" "$INSTDIR\icon.ico" 0
SectionEnd

; ---------- 卸载段 ----------
Section "un.删除程序" SecUnMain
  SectionIn RO

  ; 1) 停止本地服务：优先按 PID 文件；缺失时按命令行匹配兜底
  ClearErrors
  FileOpen $0 "$APPDATA\巴菲特投资智慧\server.pid" r
  IfErrors pid_missing
  FileRead $0 $1
  FileClose $0
  ${UnStrTrimNewLines} $1 $1
  StrCmp $1 "" pid_missing
  ExecWait 'taskkill /PID $1 /T /F'
  pid_missing:
  nsExec::Exec "powershell -NoProfile -NonInteractive -Command $\"Get-CimInstance Win32_Process | Where-Object { $$_.CommandLine -like '*serve_buffett_app.py*' } | ForEach-Object { Stop-Process -Id $$_.ProcessId -Force }$\""

  ; 2) 删除安装目录（用户数据在 %APPDATA%，默认保留）
  RMDir /r "$INSTDIR"

  ; 3) 快捷方式
  Delete "$SMPROGRAMS\巴菲特投资智慧\巴菲特投资智慧.lnk"
  Delete "$SMPROGRAMS\巴菲特投资智慧\停止服务.lnk"
  Delete "$SMPROGRAMS\巴菲特投资智慧\使用说明.lnk"
  Delete "$SMPROGRAMS\巴菲特投资智慧\卸载巴菲特投资智慧.lnk"
  RMDir "$SMPROGRAMS\巴菲特投资智慧"
  Delete "$DESKTOP\巴菲特投资智慧.lnk"

  ; 4) 卸载注册
  DeleteRegKey HKCU "${UNINST_KEY}"
SectionEnd

Section /o "un.同时删除笔记 / 收藏 / AI 对话数据" SecUnData
  ; 默认不勾选：勾选后才删除 %APPDATA%\巴菲特投资智慧（含 state.json 与 server.pid/log）
  RMDir /r "$APPDATA\巴菲特投资智慧"
SectionEnd
