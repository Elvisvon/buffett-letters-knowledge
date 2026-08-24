#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
巴菲特投资智慧 · 可安装 App 打包器（跨 Mac）
=============================================

把整个项目封装为自包含的 macOS App + DMG 安装镜像：
  - .app 内嵌全部资源（html / 知识库 / 技能 / 构建脚本），不依赖安装路径
  - 双击 .app → 原生窗口承载应用（Swift + WKWebView），**Dock 图标停留**，
    后台自动拉起本地服务（127.0.0.1:8666），关闭窗口即停止
  - 记忆材料（笔记/收藏/已读/AI 对话）默认持久化到
    ~/Library/Application Support/巴菲特投资智慧/state.json（不进 Git）
  - 密钥不落盘：启动时从环境变量 DEEPSEEK_API_KEY 注入，或应用内设置面板填写

用法：
  python3 package_app.py            # 打包（输出 dist/巴菲特投资智慧-vX.Y.dmg）
  python3 package_app.py --no-dmg   # 只生成 .app 不生成 DMG
  python3 package_app.py --version 2.0   # 指定版本号（默认 2.0）

产物：
  dist/巴菲特投资智慧.app            # 可直接运行的 App
  dist/巴菲特投资智慧-vX.Y.dmg      # 安装镜像（含 /Applications 拖放入口）

依赖：
  - Swift 工具链（Command Line Tools 自带 swiftc）
  - 运行目标 Mac 需 macOS 12+（Apple Silicon），且装有 python3（CLT 自带）
"""

import argparse
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
APP_NAME = "巴菲特投资智慧.app"
DIST = os.path.join(HERE, "dist")
STAGE = os.path.join(DIST, "stage")
ICON_SRC = os.path.join(HERE, "assets", "buffett.png")
MACAPP_SRC = os.path.join(HERE, "macapp", "main.swift")
SWIFT_TARGET = os.environ.get("BUFFETT_SWIFT_TARGET", "arm64-apple-macos12.0")

# 随包分发的项目资源（.app/Contents/Resources/project/）
BUNDLED = [
    "巴菲特投资智慧.html",
    "serve_buffett_app.py",
    "build_buffett_app.py",
    "llm-config.js",
    "README.md",
    "巴菲特致股东信分类索引(1956-2025) .xlsx",
    "巴菲特致股东信知识库",
    "skills",
]

SERVICE_COMMAND = r"""#!/bin/bash
# 巴菲特投资智慧 · 服务启动脚本（终端方式；.app 原生版已内置此逻辑，无需手动运行）
cd "$(dirname "$0")"
echo "🏛 巴菲特投资智慧 正在启动…"
echo "   服务地址将在下方显示；关闭本窗口或按 Ctrl+C 停止服务。"
exec python3 serve_buffett_app.py
"""

INFO_PLIST = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>CFBundleName</key><string>巴菲特投资智慧</string>
  <key>CFBundleDisplayName</key><string>巴菲特投资智慧</string>
  <key>CFBundleIdentifier</key><string>com.local.buffett-investment-wisdom</string>
  <key>CFBundleVersion</key><string>{version}</string>
  <key>CFBundleShortVersionString</key><string>{version}</string>
  <key>CFBundlePackageType</key><string>APPL</string>
  <key>CFBundleExecutable</key><string>巴菲特投资智慧</string>
  <key>CFBundleIconFile</key><string>icon</string>
  <key>LSMinimumSystemVersion</key><string>12.0</string>
  <key>NSHighResolutionCapable</key><true/>
  <key>LSApplicationCategoryType</key><string>public.app-category.finance</string>
  <key>LSMultipleInstancesProhibited</key><true/>
  <key>NSHumanReadableCopyright</key><string>本地个人应用：巴菲特致股东信知识库阅读研究</string>
  <key>NSAppTransportSecurity</key>
  <dict>
    <key>NSAllowsLocalNetworking</key><true/>
  </dict>
</dict>
</plist>
"""

README_TXT = """巴菲特投资智慧 · 安装说明
============================

一、安装
  1. 双击打开本 DMG；
  2. 把「巴菲特投资智慧.app」拖入 Applications 文件夹（或任意位置）。

二、首次打开（Gatekeeper）
  由于应用未做 Apple 开发者签名，首次打开可能被拦：
  - 右键点击 App → 「打开」→ 再次确认「打开」；
  或终端执行：xattr -dr com.apple.quarantine "/Applications/巴菲特投资智慧.app"

三、使用
  双击 App → 打开原生窗口（Dock 图标停留），后台自动启动本地服务
  （127.0.0.1:8666）。关闭窗口即退出应用并停止服务。
  - 原文链接等外部网页会用系统默认浏览器打开；
  - 若 8666 已被开发者手动启动的服务占用，App 会直接复用。

四、LLM 密钥（可选）
  - 应用内：打开页面右上角 ⚙ 设置 → 填写 API Key（仅存本机浏览器 localStorage）；
  - 或终端先导出环境变量再启动：export DEEPSEEK_API_KEY=sk-xxx
    然后 open "/Applications/巴菲特投资智慧.app"
  默认模型 deepseek-v4-flash；密钥不写入任何文件。

五、数据与记忆材料
  全部资料（188 篇文章 / 分类索引 / 巴菲特人格 Skill）已内嵌于 App 内，完全离线可用。
  你的笔记 / 高亮 / 收藏 / 已读标记 / AI 对话 会持久化保存到本地文件：
    ~/Library/Application Support/巴菲特投资智慧/state.json
  —— 属于本机用户数据，不会进入任何 Git 仓库 / 上传 GitHub。
  （如需改存到项目目录，可设环境变量 BUFFETT_DATA_DIR，并在项目 .gitignore 中忽略）

六、终端方式（可选，开发者）
  项目目录运行：python3 serve_buffett_app.py
  或双击「启动巴菲特知识库.command」；Ctrl+C 停止。

七、重新构建
  python3 build_buffett_app.py    # 重新生成单文件 HTML
  python3 package_app.py          # 重新打包 App + DMG
"""


def run(cmd, **kw):
    print("  $", " ".join(cmd) if isinstance(cmd, list) else cmd)
    return subprocess.run(cmd, check=True, capture_output=True, text=True, **kw)


def make_icon(app_resources):
    """assets/buffett.png → icon.icns"""
    iconset = os.path.join(DIST, "icon.iconset")
    if os.path.exists(iconset):
        shutil.rmtree(iconset)
    os.makedirs(iconset)
    for s in (16, 32, 128, 256, 512):
        run(["sips", "-z", str(s), str(s), ICON_SRC, "--out",
             os.path.join(iconset, "icon_%dx%d.png" % (s, s))])
        s2 = s * 2
        run(["sips", "-z", str(s2), str(s2), ICON_SRC, "--out",
             os.path.join(iconset, "icon_%dx%d@2x.png" % (s, s))])
    run(["iconutil", "-c", "icns", iconset, "-o", os.path.join(app_resources, "icon.icns")])
    shutil.rmtree(iconset)


def build_app(version):
    app = os.path.join(STAGE, APP_NAME)
    if os.path.exists(app):
        shutil.rmtree(app)
    contents = os.path.join(app, "Contents")
    macos = os.path.join(contents, "MacOS")
    os.makedirs(macos)
    os.makedirs(os.path.join(contents, "Resources", "project"))
    # Info.plist
    with open(os.path.join(contents, "Info.plist"), "w", encoding="utf-8") as f:
        f.write(INFO_PLIST.format(version=version))
    # 原生二进制（Swift + WKWebView）：Dock 图标停留 + 内嵌服务管理
    binary = os.path.join(macos, APP_NAME[:-4])
    run(["xcrun", "swiftc", "-O", "-swift-version", "5", "-target", SWIFT_TARGET,
         "-o", binary, MACAPP_SRC, "-framework", "Cocoa", "-framework", "WebKit"])
    # 图标
    make_icon(os.path.join(contents, "Resources"))
    # bundle 内服务脚本（终端方式备选）
    proj = os.path.join(contents, "Resources", "project")
    with open(os.path.join(proj, "启动服务.command"), "w", encoding="utf-8") as f:
        f.write(SERVICE_COMMAND)
    os.chmod(os.path.join(proj, "启动服务.command"), 0o755)
    # 项目资源
    for item in BUNDLED:
        src = os.path.join(HERE, item)
        if not os.path.exists(src):
            print("[warn] 缺少资源，已跳过:", item, file=sys.stderr)
            continue
        dst = os.path.join(proj, item)
        if os.path.isdir(src):
            shutil.copytree(src, dst, ignore=shutil.ignore_patterns(".DS_Store", "__pycache__"))
        else:
            shutil.copy2(src, dst)
    return app


def codesign(app):
    run(["codesign", "--force", "--deep", "--sign", "-", app])
    run(["codesign", "--verify", "--deep", "--strict", app])
    print("[ok] ad-hoc 签名完成（未签名，首次打开需右键确认）")


def make_dmg(version):
    dmg = os.path.join(DIST, "巴菲特投资智慧-v%s.dmg" % version)
    if os.path.exists(dmg):
        os.remove(dmg)
    # 安装说明 + /Applications 拖放入口
    with open(os.path.join(STAGE, "安装说明.txt"), "w", encoding="utf-8") as f:
        f.write(README_TXT)
    if not os.path.exists(os.path.join(STAGE, "Applications")):
        os.symlink("/Applications", os.path.join(STAGE, "Applications"))
    run(["hdiutil", "create", "-volname", "巴菲特投资智慧", "-srcfolder", STAGE,
         "-ov", "-format", "UDZO", dmg])
    return dmg


def main():
    ap = argparse.ArgumentParser(description="巴菲特投资智慧 App 打包器")
    ap.add_argument("--version", default="2.0", help="版本号（默认 2.0）")
    ap.add_argument("--no-dmg", action="store_true", help="只生成 .app，不生成 DMG")
    args = ap.parse_args()

    if os.path.exists(STAGE):
        shutil.rmtree(STAGE)
    os.makedirs(STAGE)

    print("[1/4] 生成 App bundle…")
    app = build_app(args.version)
    print("[2/4] 校验结构…")
    run(["plutil", "-lint", os.path.join(app, "Contents", "Info.plist")])
    run(["ls", os.path.join(app, "Contents", "Resources", "project")])
    print("[3/4] ad-hoc 签名…")
    codesign(app)
    if args.no_dmg:
        print("[ok] 完成：%s（未生成 DMG）" % app)
        return
    print("[4/4] 生成 DMG 安装镜像…")
    dmg = make_dmg(args.version)
    run(["hdiutil", "verify", dmg])
    print("[ok] 完成：%s" % dmg)


if __name__ == "__main__":
    main()
