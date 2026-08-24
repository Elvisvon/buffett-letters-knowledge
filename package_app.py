#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
巴菲特投资智慧 · 可安装 App 打包器（跨 Mac）
=============================================

把整个项目封装为自包含的 macOS App + DMG 安装镜像：
  - .app 内嵌全部资源（html / 知识库 / 技能 / 构建脚本），不依赖安装路径
  - 双击 .app → 自动打开「终端」启动本地服务并打开浏览器
  - DMG 可拷贝到任意 Mac：拖入 /Applications 即可安装
  - 密钥不落盘：启动时从环境变量 DEEPSEEK_API_KEY 注入，或应用内设置面板填写

用法：
  python3 package_app.py            # 打包（输出 dist/巴菲特投资智慧-vX.Y.dmg）
  python3 package_app.py --no-dmg   # 只生成 .app 不生成 DMG
  python3 package_app.py --version 2.0   # 指定版本号（默认 1.0）

产物：
  dist/巴菲特投资智慧.app            # 可直接运行的 App
  dist/巴菲特投资智慧-vX.Y.dmg      # 安装镜像（含 /Applications 拖放入口）
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

LAUNCHER = r"""#!/bin/bash
# 巴菲特投资智慧 · 便携版启动器（随 .app 分发，不依赖安装位置）
APP_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PROJ="$APP_ROOT/Resources/project"
CMD="$PROJ/启动服务.command"

if [ ! -f "$CMD" ]; then
  osascript -e 'display dialog "应用资源不完整，请重新安装。" with icon stop buttons {"好"} default button 1'
  exit 1
fi
if ! command -v python3 >/dev/null 2>&1; then
  osascript -e 'display dialog "需要 Python 3 环境。\n\n请先安装 Command Line Tools：\n  xcode-select --install" with icon caution buttons {"知道了"} default button 1'
  exit 1
fi
# 交给「终端」运行 bundle 内的服务脚本（open 为系统命令，无引号/权限问题）
open -a Terminal "$CMD"
exit 0
"""

SERVICE_COMMAND = r"""#!/bin/bash
# 巴菲特投资智慧 · 服务启动脚本（由 .app 通过「终端」运行）
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
  <key>NSHumanReadableCopyright</key><string>本地个人应用：巴菲特致股东信知识库阅读研究</string>
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
  双击 App → 自动打开「终端」启动本地服务并弹出浏览器。
  关闭「终端」窗口（或 Ctrl+C）即停止服务。

四、LLM 密钥（可选）
  - 应用内：打开页面右上角 ⚙ 设置 → 填写 API Key（仅存本机浏览器）；
  - 或终端先导出环境变量再启动：export DEEPSEEK_API_KEY=sk-xxx
    然后 open "/Applications/巴菲特投资智慧.app"
  默认模型 deepseek-v4-flash；密钥不写入任何文件。

五、数据
  全部资料（188 篇文章 / 分类索引 / 巴菲特人格 Skill）已内嵌于 App 内，
  完全离线可用；知识库与构建脚本也随包携带，可用
  python3 build_buffett_app.py 自行重新构建。

六、停止
  关闭启动服务的「终端」窗口即可。
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
    os.makedirs(os.path.join(contents, "MacOS"))
    os.makedirs(os.path.join(contents, "Resources", "project"))
    # Info.plist
    with open(os.path.join(contents, "Info.plist"), "w", encoding="utf-8") as f:
        f.write(INFO_PLIST.format(version=version))
    # 启动器
    launcher = os.path.join(contents, "MacOS", APP_NAME[:-4])
    with open(launcher, "w", encoding="utf-8") as f:
        f.write(LAUNCHER)
    os.chmod(launcher, 0o755)
    # 图标
    make_icon(os.path.join(contents, "Resources"))
    # bundle 内服务脚本（供「终端」运行）
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
    ap.add_argument("--version", default="1.0", help="版本号（默认 1.0）")
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
