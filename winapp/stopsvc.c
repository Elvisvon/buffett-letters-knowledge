/* 巴菲特投资智慧 · 停止本地服务（编译版，替代易被杀软误报的 VBS 脚本）
 * ======================================================================
 * 1) 读取 %APPDATA%\巴菲特投资智慧\server.pid → taskkill 结束进程树；
 * 2) pid 文件缺失/陈旧时按命令行匹配兜底（只匹配本应用服务脚本，不误伤其他 python）。
 *
 * 编译（macOS 交叉编译，由 package_windows.py 调用）：
 *   x86_64-w64-mingw32-gcc -O2 -municode -mwindows \
 *       -o 停止服务.exe stopsvc.c -lshell32 -luser32
 */
#ifndef UNICODE
#define UNICODE
#endif
#ifndef _UNICODE
#define _UNICODE
#endif
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <shellapi.h>
#include <stdio.h>
#include <wchar.h>

static void init_paths(wchar_t *pidfile, int cap)
{
    wchar_t appdata[MAX_PATH] = L"";
    DWORD n = GetEnvironmentVariableW(L"APPDATA", appdata, MAX_PATH);
    if (n == 0 || n >= MAX_PATH) {
        GetEnvironmentVariableW(L"USERPROFILE", appdata, MAX_PATH);
        wcsncat(appdata, L"\\AppData\\Roaming", MAX_PATH - wcslen(appdata) - 1);
    }
    swprintf(pidfile, cap, L"%ls\\巴菲特投资智慧\\server.pid", appdata);
    (void)cap;
}

static void run_hidden(const wchar_t *cmdline)
{
    STARTUPINFOW si;
    PROCESS_INFORMATION pi;
    wchar_t cmd[2000];

    wcsncpy(cmd, cmdline, 1999);        /* CreateProcessW 会改写缓冲区 */
    cmd[1999] = 0;
    memset(&si, 0, sizeof si);
    si.cb = sizeof si;
    if (CreateProcessW(NULL, cmd, NULL, NULL, FALSE, CREATE_NO_WINDOW,
                       NULL, NULL, &si, &pi)) {
        WaitForSingleObject(pi.hProcess, 15000);
        CloseHandle(pi.hProcess);
        CloseHandle(pi.hThread);
    }
}

int wmain(void)
{
    wchar_t pidfile[MAX_PATH];
    wchar_t cmd[300];
    char buf[64];
    DWORD rd = 0;
    HANDLE h;

    init_paths(pidfile, MAX_PATH);

    /* 1) 按 PID 停止（快速、精准；pid 文件为 ASCII 数字） */
    h = CreateFileW(pidfile, GENERIC_READ, FILE_SHARE_READ, NULL,
                    OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, NULL);
    if (h != INVALID_HANDLE_VALUE) {
        ReadFile(h, buf, sizeof buf - 1, &rd, NULL);
        CloseHandle(h);
        buf[rd] = 0;
        {
            int pid = atoi(buf);
            if (pid > 0) {
                swprintf(cmd, 300, L"taskkill /PID %d /T /F", pid);
                run_hidden(cmd);
            }
        }
        DeleteFileW(pidfile);
    }

    /* 2) 兜底：按命令行匹配（防止 PID 记录丢失/陈旧；只匹配本应用服务脚本） */
    run_hidden(L"powershell -NoProfile -NonInteractive -Command "
               L"\"Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*serve_buffett_app.py*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }\"");

    MessageBoxW(NULL,
                L"巴菲特投资智慧 本地服务已停止。\n\n（若此前未启动过服务，此提示可忽略。）",
                L"巴菲特投资智慧", MB_OK | MB_ICONINFORMATION);
    return 0;
}
