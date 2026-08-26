' 巴菲特投资智慧 · 停止本地服务
' ==============================
' 读取 server.pid 结束服务进程树；pid 文件缺失/陈旧时按命令行匹配兜底。
' 注意：本文件由打包器转为 UTF-16 LE（带 BOM）写入安装包，请勿改动编码。

Option Explicit

Dim fso, sh
Set fso = CreateObject("Scripting.FileSystemObject")
Set sh  = CreateObject("WScript.Shell")

Dim dataDir, pidFile
dataDir = sh.ExpandEnvironmentStrings("%APPDATA%") & "\巴菲特投资智慧"
pidFile = dataDir & "\server.pid"

' 1) 优先按 PID 停止（快速、精准）
If fso.FileExists(pidFile) Then
    Dim pid
    pid = Trim(fso.OpenTextFile(pidFile, 1).ReadAll)
    If Len(pid) > 0 And IsNumeric(pid) Then
        sh.Run "taskkill /PID " & pid & " /T /F", 0, True
    End If
    fso.DeleteFile pidFile, True
End If

' 2) 兜底：按命令行匹配（防止 PID 记录丢失或陈旧；只匹配本应用的服务脚本）
sh.Run "powershell -NoProfile -NonInteractive -Command ""Get-CimInstance Win32_Process | " & _
       "Where-Object { $_.CommandLine -like '*serve_buffett_app.py*' } | " & _
       "ForEach-Object { Stop-Process -Id $_.ProcessId -Force }""", 0, True

MsgBox "巴菲特投资智慧 本地服务已停止。" & vbCrLf & vbCrLf & _
       "（若此前未启动过服务，此提示可忽略。）", vbInformation, "巴菲特投资智慧"
