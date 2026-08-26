/* 巴菲特投资智慧 · Windows 启动器（编译版，替代易被杀软误报的 VBS 脚本）
 * ======================================================================
 * 行为（与 Mac 版 main.swift 对齐）：
 *   1. 探测 127.0.0.1:8666 是否已有本应用服务（/llm-config.js 含 BUFFETT_LLM_CONFIG 标记）；
 *   2. 未运行则静默拉起内置 Python 本地服务（首选 8666，端口被占用自动回退 8667+）；
 *   3. 打开 Edge 应用模式窗口承载应用（找不到 Edge 则回退默认浏览器）。
 * 服务 PID 写入 %APPDATA%\巴菲特投资智慧\server.pid（ASCII），供停止/卸载使用。
 * 失败时：错误码 + 安装目录 + python 输出（管道捕获，写入 launch-debug.log）一并提示。
 *
 * 编译（macOS 交叉编译，由 package_windows.py 调用）：
 *   x86_64-w64-mingw32-gcc -O2 -municode -mwindows \
 *       -o 巴菲特投资智慧.exe launcher.c -lws2_32 -lshell32 -luser32 -ladvapi32
 */
#ifndef UNICODE
#define UNICODE
#endif
#ifndef _UNICODE
#define _UNICODE
#endif
#define WIN32_LEAN_AND_MEAN
#include <winsock2.h>
#include <ws2tcpip.h>
#include <windows.h>
#include <shellapi.h>
#include <stdio.h>
#include <wchar.h>

#define START_PORT 8666
#define MAX_PORT   8685
#define MARKER_ASC "BUFFETT_LLM_CONFIG"   /* 服务标记（ASCII，字节比较） */

static wchar_t g_appdir[MAX_PATH];     /* 本 exe 所在目录（安装目录） */
static wchar_t g_pidfile[MAX_PATH];    /* %APPDATA%\巴菲特投资智慧\server.pid */
static wchar_t g_debuglog[MAX_PATH];   /* %APPDATA%\巴菲特投资智慧\launch-debug.log */
static HANDLE  g_hOutR = NULL;         /* python 输出管道读端（诊断用） */
static HANDLE  g_hProc = NULL;         /* python 进程句柄 */

/* ---------- 通用 ---------- */
static void die_msg(const wchar_t *title, const wchar_t *fmt, ...)
{
    wchar_t buf[2048];
    va_list ap;
    va_start(ap, fmt);
    _vsnwprintf(buf, 2047, fmt, ap);
    va_end(ap);
    MessageBoxW(NULL, buf, title, MB_OK | MB_ICONERROR);
    ExitProcess(1);
}

static void init_paths(void)
{
    wchar_t appdata[MAX_PATH] = L"";
    wchar_t dir[MAX_PATH];
    DWORD n;

    GetModuleFileNameW(NULL, g_appdir, MAX_PATH);
    wchar_t *p = wcsrchr(g_appdir, L'\\');
    if (p) *p = 0;

    n = GetEnvironmentVariableW(L"APPDATA", appdata, MAX_PATH);
    if (n == 0 || n >= MAX_PATH) {
        GetEnvironmentVariableW(L"USERPROFILE", appdata, MAX_PATH);
        wcsncat(appdata, L"\\AppData\\Roaming", MAX_PATH - wcslen(appdata) - 1);
    }
    swprintf(dir, MAX_PATH, L"%ls\\巴菲特投资智慧", appdata);
    CreateDirectoryW(dir, NULL);            /* %APPDATA% 已存在，只建一层 */
    swprintf(g_pidfile, MAX_PATH, L"%ls\\server.pid", dir);
    swprintf(g_debuglog, MAX_PATH, L"%ls\\launch-debug.log", dir);
}

/* ---------- 端口探测：GET /llm-config.js 并检查标记 ---------- */
static int probe_port(int port)
{
    SOCKET s;
    struct sockaddr_in sa;
    u_long nb = 1;
    fd_set wf;
    struct timeval tv;
    const char *req = "GET /llm-config.js HTTP/1.0\r\nHost: 127.0.0.1\r\n\r\n";
    char buf[4096];
    int got = 0, r;
    DWORD to = 1500;

    s = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);
    if (s == INVALID_SOCKET) return 0;
    memset(&sa, 0, sizeof sa);
    sa.sin_family = AF_INET;
    sa.sin_port = htons((u_short)port);
    sa.sin_addr.s_addr = inet_addr("127.0.0.1");

    ioctlsocket(s, FIONBIO, &nb);
    if (connect(s, (struct sockaddr *)&sa, sizeof sa) != 0) {
        FD_ZERO(&wf); FD_SET(s, &wf);
        tv.tv_sec = 1; tv.tv_usec = 500000;
        if (select(0, NULL, &wf, NULL, &tv) <= 0) { closesocket(s); return 0; }
    }
    send(s, req, (int)strlen(req), 0);
    setsockopt(s, SOL_SOCKET, SO_RCVTIMEO, (const char *)&to, sizeof to);
    for (;;) {
        r = recv(s, buf + got, (int)sizeof buf - 1 - got, 0);
        if (r <= 0) break;
        got += r;
        if (got >= (int)sizeof buf - 1) break;
    }
    buf[got] = 0;
    closesocket(s);
    return strstr(buf, MARKER_ASC) != NULL;
}

static int wait_server(void)
{
    int t, p;
    for (t = 0; t < 20; t++) {                    /* 首选端口（正常启动路径） */
        if (probe_port(START_PORT)) return START_PORT;
        Sleep(500);
    }
    for (t = 0; t < 10; t++) {                    /* 回退端口扫描 */
        for (p = START_PORT + 1; p <= MAX_PORT; p++)
            if (probe_port(p)) return p;
        Sleep(800);
    }
    return 0;
}

/* ---------- 启动内置 Python（隐藏 + 输出管道捕获） ---------- */
static int start_python(void)
{
    wchar_t py[MAX_PATH], script[MAX_PATH], cmd[1200];
    STARTUPINFOW si;
    PROCESS_INFORMATION pi;
    SECURITY_ATTRIBUTES sa;
    HANDLE hOutW = NULL;
    wchar_t pidbuf[32];
    DWORD written;

    swprintf(py, MAX_PATH, L"%ls\\python\\python.exe", g_appdir);
    swprintf(script, MAX_PATH, L"%ls\\app\\serve_buffett_app.py", g_appdir);
    if (GetFileAttributesW(py) == INVALID_FILE_ATTRIBUTES)
        die_msg(L"巴菲特投资智慧", L"安装目录缺少文件：\n  %ls\n\n"
                L"可能原因：安全软件拦截了安装解压，或安装包下载不完整。\n"
                L"建议：重新下载安装包后重装（可暂时退出杀毒软件）。", py);
    if (GetFileAttributesW(script) == INVALID_FILE_ATTRIBUTES)
        die_msg(L"巴菲特投资智慧", L"安装目录缺少文件：\n  %ls", script);

    swprintf(cmd, 1200, L"\"%ls\" -u \"%ls\" --no-browser --port %d", py, script, START_PORT);

    memset(&si, 0, sizeof si);
    si.cb = sizeof si;
    memset(&sa, 0, sizeof sa);
    sa.nLength = sizeof sa;
    sa.bInheritHandle = TRUE;
    if (CreatePipe(&g_hOutR, &hOutW, &sa, 0)) {
        SetHandleInformation(g_hOutR, HANDLE_FLAG_INHERIT, 0);
        si.dwFlags = STARTF_USESTDHANDLES;
        si.hStdOutput = hOutW;
        si.hStdError = hOutW;
        si.hStdInput = GetStdHandle(STD_INPUT_HANDLE);
    }

    if (!CreateProcessW(NULL, cmd, NULL, NULL, TRUE, CREATE_NO_WINDOW,
                        NULL, g_appdir, &si, &pi)) {
        DWORD e = GetLastError();
        if (hOutW) CloseHandle(hOutW);
        die_msg(L"巴菲特投资智慧",
                L"本地服务启动失败（无法运行内置 Python）。\n\n"
                L"错误码：%lu\n安装目录：%ls\n\n"
                L"手动复现（命令提示符 cmd 中运行）：\n"
                L"  \"%ls\" -u \"%ls\" --no-browser --port 8666\n\n"
                L"常见原因：安全软件拦截 / 安装不完整 / 非 64 位系统。",
                e, g_appdir, py, script);
    }
    if (hOutW) CloseHandle(hOutW);
    g_hProc = pi.hProcess;
    CloseHandle(pi.hThread);

    /* 记录 PID（ASCII 文本，供停止服务/卸载器读取） */
    swprintf(pidbuf, 32, L"%lu", pi.dwProcessId);
    HANDLE h = CreateFileW(g_pidfile, GENERIC_WRITE, 0, NULL,
                           CREATE_ALWAYS, FILE_ATTRIBUTE_NORMAL, NULL);
    if (h != INVALID_HANDLE_VALUE) {
        char ascii[32];
        int len = WideCharToMultiByte(CP_ACP, 0, pidbuf, -1, ascii, 32, NULL, NULL);
        if (len > 0) WriteFile(h, ascii, (DWORD)(len - 1), &written, NULL);
        CloseHandle(h);
    }
    return 1;
}

/* 启动失败时：把 python 已输出的内容写入调试日志（供弹窗展示） */
static void dump_debug_log(void)
{
    char buf[8192];
    DWORD avail = 0, read = 0;
    HANDLE h;

    if (!g_hOutR) return;
    if (!PeekNamedPipe(g_hOutR, NULL, 0, NULL, &avail, NULL) || avail == 0) return;
    if (avail > sizeof buf - 1) avail = sizeof buf - 1;
    if (!ReadFile(g_hOutR, buf, avail, &read, NULL) || read == 0) return;
    buf[read] = 0;
    h = CreateFileW(g_debuglog, GENERIC_WRITE, 0, NULL,
                    CREATE_ALWAYS, FILE_ATTRIBUTE_NORMAL, NULL);
    if (h != INVALID_HANDLE_VALUE) {
        DWORD w;
        WriteFile(h, buf, read, &w, NULL);
        CloseHandle(h);
    }
}

/* ---------- 定位 Edge ---------- */
static int find_edge(wchar_t *out, int cap)
{
    wchar_t base[MAX_PATH], p[MAX_PATH];
    const wchar_t *envs[] = { L"%ProgramFiles(x86)%", L"%ProgramFiles%" };
    int i;
    HKEY hk;
    DWORD sz;

    for (i = 0; i < 2; i++) {
        ExpandEnvironmentStringsW(envs[i], base, MAX_PATH);
        swprintf(p, MAX_PATH, L"%ls\\Microsoft\\Edge\\Application\\msedge.exe", base);
        if (GetFileAttributesW(p) != INVALID_FILE_ATTRIBUTES) {
            wcsncpy(out, p, cap - 1); out[cap - 1] = 0;
            return 1;
        }
    }
    /* 注册表 App Paths 兜底（Edge 自定义安装位置） */
    if (RegOpenKeyExW(HKEY_LOCAL_MACHINE,
                      L"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\App Paths\\msedge.exe",
                      0, KEY_READ, &hk) == ERROR_SUCCESS) {
        sz = sizeof p;
        if (RegQueryValueExW(hk, NULL, NULL, NULL, (BYTE *)p, &sz) == ERROR_SUCCESS &&
            GetFileAttributesW(p) != INVALID_FILE_ATTRIBUTES) {
            RegCloseKey(hk);
            wcsncpy(out, p, cap - 1); out[cap - 1] = 0;
            return 1;
        }
        RegCloseKey(hk);
    }
    if (RegOpenKeyExW(HKEY_CURRENT_USER,
                      L"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\App Paths\\msedge.exe",
                      0, KEY_READ, &hk) == ERROR_SUCCESS) {
        sz = sizeof p;
        if (RegQueryValueExW(hk, NULL, NULL, NULL, (BYTE *)p, &sz) == ERROR_SUCCESS &&
            GetFileAttributesW(p) != INVALID_FILE_ATTRIBUTES) {
            RegCloseKey(hk);
            wcsncpy(out, p, cap - 1); out[cap - 1] = 0;
            return 1;
        }
        RegCloseKey(hk);
    }
    return 0;
}

static void open_window(int port)
{
    wchar_t url[64], edge[MAX_PATH], args[128];
    swprintf(url, 64, L"http://127.0.0.1:%d/", port);
    if (find_edge(edge, MAX_PATH)) {
        swprintf(args, 128, L"--app=%ls --window-size=1280,840", url);
        ShellExecuteW(NULL, L"open", edge, args, NULL, SW_SHOWNORMAL);
    } else {
        ShellExecuteW(NULL, L"open", url, NULL, NULL, SW_SHOWNORMAL);
    }
}

/* ---------- 入口 ---------- */
int wmain(void)
{
    WSADATA wsa;
    int port = 0;

    WSAStartup(MAKEWORD(2, 2), &wsa);
    init_paths();

    /* 1) 快速探测：服务已在运行则直接打开窗口 */
    if (probe_port(START_PORT)) {
        port = START_PORT;
    } else {
        Sleep(800);                        /* 消除「双开同时启动」竞态 */
        if (probe_port(START_PORT)) port = START_PORT;
    }

    /* 2) 未运行 → 拉起内置 Python */
    if (!port) {
        if (!start_python()) return 1;
        port = wait_server();
    }

    /* 3) 失败 → 展示诊断信息 */
    if (!port) {
        wchar_t msg[2500];
        wchar_t logw[1800] = L"";
        dump_debug_log();
        {
            HANDLE h = CreateFileW(g_debuglog, GENERIC_READ, FILE_SHARE_READ, NULL,
                                   OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, NULL);
            if (h != INVALID_HANDLE_VALUE) {
                char raw[1600];
                DWORD rd = 0;
                ReadFile(h, raw, sizeof raw - 1, &rd, NULL);
                CloseHandle(h);
                raw[rd] = 0;
                if (rd > 0)
                    MultiByteToWideChar(CP_ACP, 0, raw, -1, logw, 1799);
            }
        }
        swprintf(msg, sizeof msg / sizeof(wchar_t),
                 L"本地服务启动失败（20 秒内未就绪）。\n\n"
                 L"安装目录：%ls\n"
                 L"%ls%ls%ls"
                 L"\n请检查：\n"
                 L"  1. 安装目录是否完整（python\\ 文件夹存在）；\n"
                 L"  2. 8666-8685 端口是否被防火墙拦截；\n"
                 L"  3. 查看「使用说明.txt」的故障排查一节。",
                 g_appdir,
                 logw[0] ? L"调试日志（python 输出）：\n" : L"",
                 logw[0] ? logw : L"",
                 logw[0] ? L"\n" : L"");
        MessageBoxW(NULL, msg, L"巴菲特投资智慧", MB_OK | MB_ICONEXCLAMATION);
        if (g_hProc) { WaitForSingleObject(g_hProc, 3000); CloseHandle(g_hProc); }
        return 2;
    }

    /* 4) 打开应用窗口 */
    if (g_hOutR) CloseHandle(g_hOutR);
    if (g_hProc) CloseHandle(g_hProc);
    open_window(port);
    return 0;
}
