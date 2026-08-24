#!/bin/bash
# 巴菲特投资智慧 · 一键启动（macOS 双击运行）
# 以本地服务启动，并从环境变量 / 项目根 .env 注入 LLM 密钥（密钥不落盘）。
cd "$(dirname "$0")" || exit 1
echo "正在启动 巴菲特投资智慧…（关闭本窗口或按 Ctrl+C 停止服务）"
exec python3 serve_buffett_app.py "$@"
