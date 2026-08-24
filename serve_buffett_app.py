#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
巴菲特投资智慧.html 本地启动器
==============================

作用：
  1. 以本地 HTTP 服务（仅 127.0.0.1）托管「巴菲特投资智慧.html」；
  2. 动态注入 /llm-config.js：API Key 从环境变量 DEEPSEEK_API_KEY 读取
     （未设置时回退项目根 .env），**密钥只存在于内存，绝不写入任何文件**；
  3. 自动打开浏览器。

用法：
  python3 serve_buffett_app.py [--port 8666]
  或双击同目录的「启动巴菲特知识库.command」

环境变量（可选）：
  DEEPSEEK_API_KEY    API Key（缺省读项目根 .env）
  DEEPSEEK_API_BASE   API Base（缺省 https://api.deepseek.com/v1）
  BUFFETT_LLM_MODEL   模型（缺省 deepseek-v4-flash）

直接双击 html（file:// 方式）也可以使用，此时密钥为空，
可在应用「设置」面板手动填写。
"""

import argparse
import http.server
import json
import os
import socketserver
import sys
import threading
import webbrowser

HERE = os.path.dirname(os.path.abspath(__file__))
INDEX = "巴菲特投资智慧.html"
DEFAULT_BASE = "https://api.deepseek.com/v1"
DEFAULT_MODEL = "deepseek-v4-flash"


def load_root_env():
    """向上查找项目根 .env（解析为 dict，找不到返回 {}）。"""
    d = HERE
    for _ in range(6):
        p = os.path.join(d, ".env")
        if os.path.isfile(p):
            env = {}
            try:
                for line in open(p, encoding="utf-8"):
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        env[k.strip()] = v.strip().strip('"').strip("'")
            except OSError:
                return {}
            return env
        d = os.path.dirname(d)
    return {}


def resolve_llm_config():
    env = load_root_env()
    key = (os.environ.get("DEEPSEEK_API_KEY") or env.get("DEEPSEEK_API_KEY") or "").strip()
    base = (os.environ.get("DEEPSEEK_API_BASE") or env.get("DEEPSEEK_API_BASE") or DEFAULT_BASE).strip()
    model = (os.environ.get("BUFFETT_LLM_MODEL") or DEFAULT_MODEL).strip()
    return {"base": base, "key": key, "model": model}


class Handler(http.server.SimpleHTTPRequestHandler):
    """静态文件 + 动态 /llm-config.js（密钥从环境变量注入，不落盘）。"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=HERE, **kwargs)

    def do_GET(self):
        path = self.path.split("?", 1)[0]
        if path == "/favicon.ico":
            self.send_response(204)
            self.end_headers()
            return
        if path == "/llm-config.js":
            cfg = resolve_llm_config()
            body = ("/* 动态生成：密钥由 serve_buffett_app.py 从环境变量注入，不落盘。 */\n"
                    "window.BUFFETT_LLM_CONFIG = " + json.dumps(cfg, ensure_ascii=False) + ";\n")
            data = body.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/javascript; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(data)
            return
        if path == "/":
            self.path = "/" + INDEX  # 首页直接指向应用
        return super().do_GET()

    def log_message(self, fmt, *args):
        sys.stderr.write("[server] %s\n" % (fmt % args))


def pick_port(preferred):
    for port in range(preferred, preferred + 20):
        try:
            srv = socketserver.ThreadingTCPServer(("127.0.0.1", port), Handler)
            return srv, port
        except OSError:
            continue
    raise SystemExit("[error] 端口 %d-%d 均被占用" % (preferred, preferred + 19))


def main():
    ap = argparse.ArgumentParser(description="巴菲特投资智慧 本地启动器")
    ap.add_argument("--port", type=int, default=int(os.environ.get("BUFFETT_PORT", "8666")))
    ap.add_argument("--no-browser", action="store_true", help="不自动打开浏览器")
    args = ap.parse_args()

    cfg = resolve_llm_config()
    if cfg["key"]:
        print("[ok] LLM 密钥已从环境变量注入（DEEPSEEK_API_KEY，%d 位）" % len(cfg["key"]))
    else:
        print("[warn] 未找到 DEEPSEEK_API_KEY（环境变量 / 项目根 .env），"
              "可在应用「设置」面板手动填写密钥")

    srv, port = pick_port(args.port)
    url = "http://127.0.0.1:%d/%s" % (port, INDEX)
    print("[ok] 服务已启动: %s" % url)
    print("     模型: %s | 按 Ctrl+C 停止" % cfg["model"])
    if not args.no_browser:
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\n[bye] 已停止")
    finally:
        srv.server_close()


if __name__ == "__main__":
    main()
