// 巴菲特投资智慧 · 原生 macOS 窗口壳
// ==================================
// - 双击 .app → 原生窗口承载 WKWebView，Dock 图标停留（常规激活策略）
// - 自动在后台启动 bundle 内 python3 本地服务（127.0.0.1:8666），窗口关闭即停止
// - 若 8666 已有可用服务（如开发者手动启动），直接复用、不重复拉起
// - 外部链接（非本机）交给系统默认浏览器，应用内保持本地页面
// 编译：xcrun swiftc -O -swift-version 5 -target arm64-apple-macos12.0 \
//        -o 巴菲特投资智慧 macapp/main.swift -framework Cocoa -framework WebKit

import Cocoa
import WebKit

final class AppDelegate: NSObject, NSApplicationDelegate, WKUIDelegate, WKNavigationDelegate {
    var window: NSWindow!
    var webView: WKWebView!
    var server: Process?
    var serverOwned = false

    func applicationDidFinishLaunching(_ notification: Notification) {
        NSApp.setActivationPolicy(.regular)          // 常规应用：Dock 图标 + 菜单栏
        buildMenu()
        buildWindow()
        let url = URL(string: "http://127.0.0.1:8666/")!
        ensureService(url: url) { [weak self] ok in
            guard let self = self else { return }
            if ok {
                self.webView.load(URLRequest(url: url))
            } else {
                self.showFatal("本地服务启动失败。\n\n请确认已安装 Command Line Tools：\n  xcode-select --install\n\n或检查 127.0.0.1:8666 是否被其他程序占用。")
            }
        }
        NSApp.activate(ignoringOtherApps: true)
    }

    func applicationShouldTerminateAfterLastWindowClosed(_ sender: NSApplication) -> Bool { true }

    func applicationWillTerminate(_ notification: Notification) {
        if serverOwned { server?.terminate() }       // 只停自己拉起的服务
    }

    // MARK: - 菜单（WKWebView 的复制粘贴需要编辑菜单提供 selector）
    private func buildMenu() {
        let main = NSMenu()
        let appItem = NSMenuItem(); main.addItem(appItem)
        let appMenu = NSMenu()
        appMenu.addItem(withTitle: "关于 巴菲特投资智慧", action: #selector(NSApplication.orderFrontStandardAboutPanel(_:)), keyEquivalent: "")
        appMenu.addItem(.separator())
        appMenu.addItem(withTitle: "隐藏", action: #selector(NSApplication.hide(_:)), keyEquivalent: "h")
        appMenu.addItem(.separator())
        appMenu.addItem(withTitle: "退出 巴菲特投资智慧", action: #selector(NSApplication.terminate(_:)), keyEquivalent: "q")
        appItem.submenu = appMenu

        let editItem = NSMenuItem(); main.addItem(editItem)
        let editMenu = NSMenu(title: "编辑")
        editMenu.addItem(withTitle: "撤销", action: Selector(("undo:")), keyEquivalent: "z")
        editMenu.addItem(withTitle: "重做", action: Selector(("redo:")), keyEquivalent: "Z")
        editMenu.addItem(.separator())
        editMenu.addItem(withTitle: "剪切", action: #selector(NSText.cut(_:)), keyEquivalent: "x")
        editMenu.addItem(withTitle: "拷贝", action: #selector(NSText.copy(_:)), keyEquivalent: "c")
        editMenu.addItem(withTitle: "粘贴", action: #selector(NSText.paste(_:)), keyEquivalent: "v")
        editMenu.addItem(withTitle: "全选", action: #selector(NSText.selectAll(_:)), keyEquivalent: "a")
        editItem.submenu = editMenu

        let winItem = NSMenuItem(); main.addItem(winItem)
        let winMenu = NSMenu(title: "窗口")
        winMenu.addItem(withTitle: "最小化", action: #selector(NSWindow.performMiniaturize(_:)), keyEquivalent: "m")
        winMenu.addItem(withTitle: "关闭窗口", action: #selector(NSWindow.performClose(_:)), keyEquivalent: "w")
        winItem.submenu = winMenu
        NSApp.mainMenu = main
    }

    private func buildWindow() {
        let rect = NSRect(x: 0, y: 0, width: 1280, height: 840)
        window = NSWindow(contentRect: rect,
                          styleMask: [.titled, .closable, .miniaturizable, .resizable],
                          backing: .buffered, defer: false)
        window.title = "巴菲特投资智慧"
        window.minSize = NSSize(width: 960, height: 640)
        window.setFrameAutosaveName("BuffettWisdomMain")
        let config = WKWebViewConfiguration()
        config.websiteDataStore = .default()
        webView = WKWebView(frame: rect, configuration: config)
        webView.uiDelegate = self
        webView.navigationDelegate = self
        window.contentView = webView
        window.center()
        window.makeKeyAndOrderFront(nil)
    }

    // MARK: - 服务管理
    private func findPython() -> URL? {
        let candidates = ["/usr/bin/python3", "/opt/homebrew/bin/python3", "/usr/local/bin/python3"]
        for c in candidates {
            let p = Process()
            p.executableURL = URL(fileURLWithPath: c)
            p.arguments = ["-c", "print(1)"]
            let pipe = Pipe()
            p.standardOutput = pipe; p.standardError = pipe
            do { try p.run(); p.waitUntilExit() } catch { continue }
            if p.terminationStatus == 0 { return URL(fileURLWithPath: c) }
        }
        return nil
    }

    private func probe(url: URL, completion: @escaping (Bool) -> Void) {
        var req = URLRequest(url: url)
        req.timeoutInterval = 2
        URLSession.shared.dataTask(with: req) { data, resp, _ in
            guard let resp = resp as? HTTPURLResponse, resp.statusCode == 200,
                  let data = data, let s = String(data: data, encoding: .utf8) else {
                completion(false); return
            }
            completion(s.contains("BUFFETT_DATA"))   // 确认是巴菲特应用的服务
        }.resume()
    }

    private func ensureService(url: URL, completion: @escaping (Bool) -> Void) {
        // 注意：所有 completion 必须在主线程回调（WKWebView 只能在主线程操作）
        probe(url: url) { [weak self] ok in
            guard let self = self else { return }
            if ok {                                       // 复用已有服务
                self.serverOwned = false
                DispatchQueue.main.async { completion(true) }
                return
            }
            guard let proj = Bundle.main.resourceURL?.appendingPathComponent("project"),
                  let py = self.findPython() else {
                DispatchQueue.main.async { completion(false) }
                return
            }
            let p = Process()
            p.executableURL = py
            p.arguments = ["serve_buffett_app.py", "--no-browser"]
            p.currentDirectoryURL = proj
            p.standardOutput = FileHandle.nullDevice
            p.standardError = FileHandle.nullDevice
            do { try p.run() } catch {
                DispatchQueue.main.async { completion(false) }
                return
            }
            self.server = p
            self.serverOwned = true
            var tries = 0
            func poll() {
                if tries > 40 {
                    DispatchQueue.main.async { completion(false) }
                    return
                }
                tries += 1
                self.probe(url: url) { ok in
                    if ok { DispatchQueue.main.async { completion(true) } }
                    else { DispatchQueue.main.asyncAfter(deadline: .now() + 0.3) { poll() } }
                }
            }
            poll()
        }
    }

    private func showFatal(_ msg: String) {
        DispatchQueue.main.async {
            let alert = NSAlert()
            alert.messageText = "巴菲特投资智慧"
            alert.informativeText = msg
            alert.alertStyle = .critical
            alert.addButton(withTitle: "退出")
            alert.runModal()
            NSApp.terminate(nil)
        }
    }

    // MARK: - WKUIDelegate（JS 弹窗）
    func webView(_ webView: WKWebView, runJavaScriptAlertPanelWithMessage message: String,
                 initiatedByFrame frame: WKFrameInfo, completionHandler: @escaping () -> Void) {
        let a = NSAlert(); a.messageText = message; a.addButton(withTitle: "好")
        a.beginSheetModal(for: self.window) { _ in completionHandler() }
    }
    func webView(_ webView: WKWebView, runJavaScriptConfirmPanelWithMessage message: String,
                 initiatedByFrame frame: WKFrameInfo, completionHandler: @escaping (Bool) -> Void) {
        let a = NSAlert(); a.messageText = message
        a.addButton(withTitle: "确定"); a.addButton(withTitle: "取消")
        a.beginSheetModal(for: self.window) { r in completionHandler(r == .alertFirstButtonReturn) }
    }
    func webView(_ webView: WKWebView, runJavaScriptTextInputPanelWithPrompt prompt: String,
                 defaultText: String?, initiatedByFrame frame: WKFrameInfo,
                 completionHandler: @escaping (String?) -> Void) {
        let a = NSAlert(); a.messageText = prompt
        let tf = NSTextField(frame: NSRect(x: 0, y: 0, width: 240, height: 24))
        tf.stringValue = defaultText ?? ""
        a.accessoryView = tf
        a.addButton(withTitle: "确定"); a.addButton(withTitle: "取消")
        a.beginSheetModal(for: self.window) { r in
            completionHandler(r == .alertFirstButtonReturn ? tf.stringValue : nil)
        }
    }

    // MARK: - WKNavigationDelegate（外部链接 → 系统浏览器，应用内保持本地页面）
    func webView(_ webView: WKWebView, decidePolicyFor navigationAction: WKNavigationAction,
                 decisionHandler: @escaping (WKNavigationActionPolicy) -> Void) {
        guard let u = navigationAction.request.url else { decisionHandler(.cancel); return }
        if u.host == nil || u.host == "127.0.0.1" || u.host == "localhost" || u.scheme == "about" {
            decisionHandler(.allow); return
        }
        NSWorkspace.shared.open(u)
        decisionHandler(.cancel)
    }
}

let app = NSApplication.shared
let delegate = AppDelegate()
app.delegate = delegate
app.run()
