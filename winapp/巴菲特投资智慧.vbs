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

' ---------- 工具：按 UTF-8 读取文件（兼容 PowerShell 重定向日志） ----------
Function ReadFileAny(path)
    Dim st, txt
    txt = ""
    On Error Resume Next
    Set st = CreateObject("ADODB.Stream")
    st.Type = 2                        ' adTypeText
    st.Charset = "utf-8"
    st.Open
    st.LoadFromFile path
    txt = st.ReadText
    st.Close
    If Err.Number <> 0 Then txt = ""
    On Error GoTo 0
    ReadFileAny = txt
End Function

Function LogTail(path, maxChars)
    Dim txt
    txt = ReadFileAny(path)
    If Len(txt) > maxChars Then txt = "…" & Right(txt, maxChars)
    LogTail = txt
End Function

' ---------- 主流程 ----------
Dim port, url, pyExe, scriptPath, cmd, pid, tf
Dim errNo, errDesc, i, debugLog, logTail

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
    pyExe      = appDir & "\python\python.exe"
    scriptPath = appDir & "\app\serve_buffett_app.py"
    debugLog   = dataDir & "\launch-debug.log"

    ' 预检：安装完整性（常见于安全软件拦截了解压）
    Dim missing
    missing = ""
    If Not fso.FileExists(pyExe) Then missing = missing & vbCrLf & "  " & pyExe
    If Not fso.FileExists(scriptPath) Then missing = missing & vbCrLf & "  " & scriptPath
    If Len(missing) > 0 Then
        MsgBox "安装目录缺少文件：" & missing & vbCrLf & vbCrLf & _
               "可能原因：安全软件拦截了安装解压，或安装包下载不完整。" & vbCrLf & _
               "建议：重新下载安装包后重装（安装时可暂时退出杀毒软件）。", _
               vbCritical, "巴菲特投资智慧"
        WScript.Quit 3
    End If

    ' 启动尝试一：直接隐藏运行（窗口样式 0），失败时捕获精确错误码
    cmd = """" & pyExe & """ -u """ & scriptPath & """ --no-browser --port 8666"
    pid = 0
    For i = 1 To 2
        On Error Resume Next
        pid = sh.Run(cmd, 0, False)
        errNo = Err.Number
        errDesc = Err.Description
        On Error GoTo 0
        If pid <> 0 And errNo = 0 Then Exit For
        WScript.Sleep 500                ' 重试一次（应对安全软件瞬时拦截）
    Next

    ' 启动尝试二：PowerShell 兜底（隐藏运行 + 输出重定向到调试日志）。
    ' Run 解析失败的个别环境 PS 可成功；即使失败，日志里也会有 python 的真实报错。
    If pid = 0 Or errNo <> 0 Then
        cmd = "powershell -NoProfile -ExecutionPolicy Bypass -Command " & _
              """& '" & pyExe & "' -u '" & scriptPath & _
              "' --no-browser --port 8666 2>&1 | Out-File -FilePath '" & debugLog & _
              "' -Encoding utf8"""
        On Error Resume Next
        pid = sh.Run(cmd, 0, False)
        If Err.Number <> 0 Then pid = 0
        errNo = Err.Number
        errDesc = Err.Description
        On Error GoTo 0
        WScript.Sleep 3000               ' 给 python 启动时间（同时让日志落盘）
    End If

    If pid = 0 Or errNo <> 0 Then
        ' 失败详情：错误码 + python 自检 + 调试日志 + 可手动复现的命令
        Dim diag, diagOut, diagErr, pyInfo
        diagOut = "" : diagErr = "" : pyInfo = ""
        On Error Resume Next
        Set diag = sh.Exec("""" & pyExe & """ -V")
        If Err.Number <> 0 Then
            pyInfo = "无法启动 python.exe（" & Err.Number & " " & Err.Description & "）"
        Else
            If Not diag Is Nothing Then
                If Not diag.StdOut.AtEndOfStream Then diagOut = diag.StdOut.ReadAll
                If Not diag.StdErr.AtEndOfStream Then diagErr = diag.StdErr.ReadAll
            End If
            If Len(Trim(diagOut & " " & diagErr)) = 0 Then
                pyInfo = "python.exe 无输出（可能被安全软件拦截）"
            Else
                pyInfo = Trim(diagOut & " " & diagErr)
            End If
        End If
        On Error GoTo 0
        logTail = LogTail(debugLog, 800)

        Dim msg
        msg = "本地服务启动失败。" & vbCrLf & vbCrLf & _
              "错误码：" & errNo & " " & errDesc & vbCrLf & _
              "python 自检：" & pyInfo & vbCrLf & _
              "安装目录：" & appDir & vbCrLf
        If logTail <> "" Then
            msg = msg & vbCrLf & "调试日志（python 真实报错）：" & vbCrLf & logTail & vbCrLf
        End If
        msg = msg & vbCrLf & "手动复现（命令提示符 cmd 中运行）：" & vbCrLf & _
              "  """ & pyExe & """ -u """ & scriptPath & """ --no-browser --port 8666" & vbCrLf & _
              "（PowerShell 中运行则开头加 & 再加空格）" & vbCrLf & vbCrLf & _
              "常见原因：" & vbCrLf & _
              "  · 安全软件拦截 python.exe（将安装目录加入信任区，或暂时退出后重试）；" & vbCrLf & _
              "  · 安装不完整（重新下载安装包并重装）；" & vbCrLf & _
              "  · 系统为 32 位或 ARM（本应用仅支持 64 位 Windows 10/11）。"
        MsgBox msg, vbCritical, "巴菲特投资智慧"
        WScript.Quit 4
    End If
    ' 记录 PID（供「停止服务.vbs」与卸载器使用；PS 兜底时记录的是 powershell 的 PID，
    ' taskkill /T 会连同其子进程 python 一起结束）
    Set tf = fso.CreateTextFile(pidFile, True, False)
    tf.Write pid
    tf.Close
    port = WaitForServer()
End If

If port = 0 Then
    logTail = LogTail(debugLog, 800)
    Dim msg2
    msg2 = "本地服务启动失败（20 秒内未就绪）。" & vbCrLf
    If logTail <> "" Then
        msg2 = msg2 & "调试日志：" & vbCrLf & logTail & vbCrLf
    End If
    msg2 = msg2 & vbCrLf & "请检查：" & vbCrLf & _
           "  1. 安装目录是否完整（python\ 文件夹存在）；" & vbCrLf & _
           "  2. 8666-8685 端口是否被防火墙拦截；" & vbCrLf & _
           "  3. 查看「使用说明.txt」的故障排查一节。"
    MsgBox msg2, vbExclamation, "巴菲特投资智慧"
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
