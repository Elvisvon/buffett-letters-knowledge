' 巴菲特投资智慧 · Windows 启动器
' =================================
' 双击本文件（或开始菜单/桌面快捷方式）：
'   1. 探测 127.0.0.1:8666 是否已有本应用服务在运行（已运行则直接复用）；
'   2. 未运行则静默拉起内置 Python 本地服务（首选 8666，端口被占用自动回退 8667+）；
'   3. 打开 Edge 应用模式窗口承载应用（找不到 Edge 时回退默认浏览器）。
' 停止服务：双击同目录「停止服务.vbs」。
' 注意：本文件由打包器转为 UTF-16 LE（带 BOM）写入安装包，请勿改动编码。

Option Explicit

Const MARKER     = "BUFFETT_LLM_CONFIG"   ' 服务探测标记（/llm-config.js 端点内容）
Const START_PORT = 8666
Const MAX_PORT   = 8685                   ' 与服务端端口回退范围一致

Dim fso, sh
Set fso = CreateObject("Scripting.FileSystemObject")
Set sh  = CreateObject("WScript.Shell")

Dim appDir, dataDir, pidFile
appDir  = fso.GetParentFolderName(WScript.ScriptFullName)
dataDir = sh.ExpandEnvironmentStrings("%APPDATA%") & "\巴菲特投资智慧"
pidFile = dataDir & "\server.pid"

' ---------- 探测：某端口上是否已有本应用服务 ----------
Function IsBuffettServer(p)
    Dim req
    On Error Resume Next
    Set req = CreateObject("MSXML2.XMLHTTP")
    req.open "GET", "http://127.0.0.1:" & p & "/llm-config.js", False
    req.setRequestHeader "Cache-Control", "no-cache"
    req.timeout = 1500
    req.send ""
    If Err.Number = 0 And req.status = 200 Then
        If InStr(req.responseText, MARKER) > 0 Then
            IsBuffettServer = True
            Exit Function
        End If
    End If
    Err.Clear
    On Error GoTo 0
    IsBuffettServer = False
End Function

' ---------- 等待服务就绪（阶段一：首选端口；阶段二：回退端口扫描） ----------
Function WaitForServer()
    Dim t, p
    For t = 1 To 20
        If IsBuffettServer(START_PORT) Then
            WaitForServer = START_PORT
            Exit Function
        End If
        WScript.Sleep 500
    Next
    For t = 1 To 10
        For p = START_PORT + 1 To MAX_PORT
            If IsBuffettServer(p) Then
                WaitForServer = p
                Exit Function
            End If
        Next
        WScript.Sleep 800
    Next
    WaitForServer = 0
End Function

' ---------- 定位 Edge（应用模式窗口；找不到则回退默认浏览器） ----------
Function FindEdge()
    Dim p
    p = sh.ExpandEnvironmentStrings("%ProgramFiles(x86)%") & "\Microsoft\Edge\Application\msedge.exe"
    If fso.FileExists(p) Then
        FindEdge = p
        Exit Function
    End If
    p = sh.ExpandEnvironmentStrings("%ProgramFiles%") & "\Microsoft\Edge\Application\msedge.exe"
    If fso.FileExists(p) Then
        FindEdge = p
        Exit Function
    End If
    ' 注册表 App Paths 兜底（Edge 自定义安装位置）
    On Error Resume Next
    p = sh.RegRead("HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\msedge.exe\")
    If Err.Number = 0 And Len(p) > 0 And fso.FileExists(p) Then
        FindEdge = p
        Exit Function
    End If
    Err.Clear
    p = sh.RegRead("HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\msedge.exe\")
    If Err.Number = 0 And Len(p) > 0 And fso.FileExists(p) Then
        FindEdge = p
        Exit Function
    End If
    On Error GoTo 0
    FindEdge = ""
End Function

' ---------- 主流程 ----------
Dim port, url, pyExe, scriptPath, cmd, pid, tf

' 1) 快速探测：服务已在运行则直接打开窗口（不等 20 秒）
port = 0
If IsBuffettServer(START_PORT) Then
    port = START_PORT
Else
    WScript.Sleep 800                    ' 消除「双开同时启动」竞态窗口
    If IsBuffettServer(START_PORT) Then port = START_PORT
End If

' 2) 未运行 → 静默启动内置 Python 服务（隐藏窗口；无需系统安装 Python）
If port = 0 Then
    If Not fso.FolderExists(dataDir) Then fso.CreateFolder(dataDir)
    pyExe      = """" & appDir & "\python\python.exe"""
    scriptPath = """" & appDir & "\app\serve_buffett_app.py"""
    cmd = pyExe & " -u " & scriptPath & " --no-browser --port 8666"
    pid = sh.Run(cmd, 0, False)
    If pid = 0 Then
        MsgBox "本地服务启动失败：无法运行内置 Python。" & vbCrLf & _
               "请确认安装目录完整（python\ 与 app\ 文件夹存在），或重新安装。", _
               vbCritical, "巴菲特投资智慧"
        WScript.Quit 1
    End If
    ' 记录 PID（供「停止服务.vbs」与卸载器使用）
    Set tf = fso.CreateTextFile(pidFile, True, False)
    tf.Write pid
    tf.Close
    port = WaitForServer()
End If

If port = 0 Then
    MsgBox "本地服务启动失败（20 秒内未就绪）。" & vbCrLf & vbCrLf & _
           "请检查：" & vbCrLf & _
           "  1. 安装目录是否完整（python\ 文件夹存在）；" & vbCrLf & _
           "  2. 8666-8685 端口是否被防火墙拦截；" & vbCrLf & _
           "  3. 查看「使用说明.txt」的故障排查一节。", _
           vbExclamation, "巴菲特投资智慧"
    WScript.Quit 2
End If

' 3) 打开应用窗口
url = "http://127.0.0.1:" & port & "/"
Dim edge
edge = FindEdge()
If Len(edge) > 0 Then
    sh.Run """" & edge & """ --app=""" & url & """ --window-size=1280,840", 1, False
Else
    sh.Run """" & url & """", 1, False
End If
