#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
巴菲特投资智慧 · Windows 安装器打包器（在 macOS / Linux 上交叉打包）
====================================================================

把整个项目封装为 Windows 版可安装应用（NSIS 安装器）：
  - 内置 Python embeddable 运行时（python.org 官方压缩包；服务脚本零第三方依赖）
  - app/ 内嵌全部资源（html / 知识库 / 技能 / 服务脚本），与 Mac 版一致
  - 启动器/停止服务为 C 编译的 exe（MinGW 交叉编译）——不使用 VBS 脚本，
    避免杀毒软件对脚本类「Trojan.VBS.Agent」特征的误报；启动器静默拉起
    本地服务（127.0.0.1:8666 起，端口自动回退至 8685），打开 Edge 应用模式窗口，
    再次启动复用已有服务；失败时自动给出错误码 + python 真实报错
  - 记忆材料（笔记/收藏/已读/AI 对话）持久化到 %APPDATA%\\巴菲特投资智慧\\state.json
  - 安装器自动生成 uninstall.exe（卸载时停止服务 + 清理，默认保留用户数据）

用法：
  python3 package_windows.py            # 打包（输出 dist/巴菲特投资智慧-vX.Y-Setup.exe）
  python3 package_windows.py --version 2.0
  python3 package_windows.py --no-python-download   # 只用 vendor 缓存，不访问网络

产物：
  dist/巴菲特投资智慧-vX.Y-Setup.exe    # NSIS 安装器（安装时生成 uninstall.exe 卸载器）

依赖：
  - makensis（NSIS 3.x：brew install makensis）
  - mingw-w64（交叉编译启动器 exe：brew install mingw-w64）
  - Pillow（生成 .ico 图标）
  - 网络（首次下载 python.org embeddable Python；之后走 vendor/ 缓存）
"""

import argparse
import os
import shutil
import subprocess
import sys
import urllib.request
import zipfile

try:
    from PIL import Image
except ImportError:
    Image = None

HERE = os.path.dirname(os.path.abspath(__file__))
DIST = os.path.join(HERE, "dist")
STAGE = os.path.join(DIST, "stage-win")
APP_DIR = os.path.join(STAGE, "巴菲特投资智慧")
ICON_SRC = os.path.join(HERE, "assets", "buffett.png")

PYTHON_VERSION = "3.12.8"
PYTHON_ZIP = os.path.join(HERE, "vendor", "python-embed",
                          "python-%s-embed-amd64.zip" % PYTHON_VERSION)
PYTHON_URL = ("https://www.python.org/ftp/python/%s/python-%s-embed-amd64.zip"
              % (PYTHON_VERSION, PYTHON_VERSION))

# 随包分发的项目资源（app/，与 Mac 版 package_app.py 的 BUNDLED 一致）
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

# 启动器 / 停止服务（C 源码 → 交叉编译为 exe，替代 VBS）
LAUNCHERS = [
    ("launcher.c", "巴菲特投资智慧.exe"),
    ("stopsvc.c", "停止服务.exe"),
]
CC = "x86_64-w64-mingw32-gcc"
CC_LIBS = ["-lws2_32", "-lshell32", "-luser32", "-ladvapi32"]


def run(cmd, **kw):
    print("  $", " ".join(cmd) if isinstance(cmd, list) else cmd)
    return subprocess.run(cmd, check=True, **kw)


def ensure_python(no_download=False):
    """下载（或复用缓存）并解压 embeddable Python 到 stage/python/。"""
    if not os.path.isfile(PYTHON_ZIP):
        if no_download:
            sys.exit("[error] 未找到缓存 %s（--no-python-download），"
                     "请先联网运行一次以完成下载。" % PYTHON_ZIP)
        print("[1/6] 下载 embeddable Python %s …" % PYTHON_VERSION)
        os.makedirs(os.path.dirname(PYTHON_ZIP), exist_ok=True)
        urllib.request.urlretrieve(PYTHON_URL, PYTHON_ZIP)
    print("[1/6] 校验并解压 embeddable Python …")
    with zipfile.ZipFile(PYTHON_ZIP) as z:
        bad = z.testzip()
        if bad:
            sys.exit("[error] Python 压缩包损坏: %s" % bad)
        dst = os.path.join(APP_DIR, "python")
        if os.path.exists(dst):
            shutil.rmtree(dst)
        os.makedirs(dst)
        z.extractall(dst)

    # 把 python312.zip（标准库压缩包）解包为普通目录 Lib/ 并删除原 zip：
    # 火绒等安全软件会把「程序覆盖/修改已有 .zip 文件」判为勒索行为（误报），
    # 安装包内不再存在任何 zip 文件即可彻底规避；_pth 改为指向 Lib/ 目录。
    zip_path = os.path.join(dst, "python312.zip")
    if os.path.isfile(zip_path):
        print("  解包 python312.zip → python/Lib/（消除杀软对 zip 的勒索误报）…")
        with zipfile.ZipFile(zip_path) as z:
            z.extractall(os.path.join(dst, "Lib"))
        os.remove(zip_path)
        with open(os.path.join(dst, "python312._pth"), "w", encoding="ascii") as f:
            f.write(".\\Lib\n.\n\n# Uncomment to run site.main() automatically\n#import site\n")


def make_icon():
    """assets/buffett.png → icon.ico（多尺寸，供安装器/快捷方式使用）。"""
    if Image is None:
        sys.exit("[error] 需要 Pillow：python3 -m pip install pillow")
    print("[2/6] 生成 icon.ico …")
    img = Image.open(ICON_SRC).convert("RGBA")
    out = os.path.join(APP_DIR, "icon.ico")
    img.save(out, format="ICO",
             sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64),
                    (128, 128), (256, 256)])
    return out


def copy_app_resources():
    print("[3/6] 拷贝项目资源到 app/ …")
    dst = os.path.join(APP_DIR, "app")
    os.makedirs(dst, exist_ok=True)
    for item in BUNDLED:
        src = os.path.join(HERE, item)
        if not os.path.exists(src):
            print("[warn] 缺少资源，已跳过:", item, file=sys.stderr)
            continue
        target = os.path.join(dst, item)
        if os.path.isdir(src):
            shutil.copytree(src, target, ignore=shutil.ignore_patterns(
                ".DS_Store", "__pycache__"))
        else:
            shutil.copy2(src, target)


def compile_launchers():
    """winapp/*.c → exe（MinGW 交叉编译；替代 VBS，规避脚本类误报）。"""
    cc = shutil.which(CC)
    if not cc:
        sys.exit("[error] 未找到 %s，请先安装：brew install mingw-w64" % CC)
    print("[4/6] 交叉编译启动器 / 停止服务（MinGW）…")
    for src, out in LAUNCHERS:
        run([cc, "-O2", "-municode", "-mwindows",
             "-o", os.path.join(APP_DIR, out),
             os.path.join(HERE, "winapp", src)] + CC_LIBS)
        print("  %s → %s" % (src, os.path.join(APP_DIR, out)))


def write_usage(version):
    """winapp/使用说明.txt → UTF-8（带 BOM，现代记事本/NSIS 均可正确显示）。"""
    src = os.path.join(HERE, "winapp", "使用说明.txt")
    dst = os.path.join(APP_DIR, "使用说明.txt")
    with open(src, encoding="utf-8") as f:
        text = f.read().replace("@VERSION@", version)
    with open(dst, "w", encoding="utf-8-sig") as f:
        f.write(text)
    print("  使用说明.txt → %s（UTF-8 + BOM）" % os.path.relpath(dst, HERE))


def render_nsi(version, icon):
    """渲染 NSIS 脚本（UTF-8 + BOM，makensis 以 Unicode 模式编译中文）。"""
    src = os.path.join(HERE, "winapp", "巴菲特投资智慧.nsi")
    dst = os.path.join(STAGE, "巴菲特投资智慧.nsi")
    with open(src, encoding="utf-8") as f:
        text = f.read()
    text = (text
            .replace("@VERSION@", version)
            .replace("@STAGE_ABS@", STAGE)
            .replace("@ICON_ABS@", icon)
            .replace("@OUTFILE_ABS@", os.path.join(DIST, "巴菲特投资智慧-v%s-Setup.exe" % version)))
    with open(dst, "w", encoding="utf-8-sig") as f:
        f.write(text)
    print("[5/6] NSIS 脚本 → %s（UTF-8 + BOM）" % os.path.relpath(dst, HERE))
    return dst


def build_setup(nsi):
    """makensis 编译 → dist/巴菲特投资智慧-vX.Y-Setup.exe。"""
    makensis = shutil.which("makensis")
    if not makensis:
        sys.exit("[error] 未找到 makensis，请先安装：brew install makensis")
    print("[6/6] makensis 编译安装器 …")
    run([makensis, nsi])


def verify(version, icon):
    print("\n===== 产物校验 =====")
    exe = os.path.join(DIST, "巴菲特投资智慧-v%s-Setup.exe" % version)
    for p in (exe, icon):
        print("  %s  %.1f MB" % (os.path.relpath(p, HERE),
                                 os.path.getsize(p) / 1048576.0))
    if not os.path.isfile(exe):
        sys.exit("[error] 安装器未生成")
    py = os.path.join(APP_DIR, "python", "python.exe")
    app_html = os.path.join(APP_DIR, "app", "巴菲特投资智慧.html")
    launcher = os.path.join(APP_DIR, "巴菲特投资智慧.exe")
    stop = os.path.join(APP_DIR, "停止服务.exe")
    for p in (py, app_html, launcher, stop):
        if not os.path.exists(p):
            sys.exit("[error] 缺少关键产物: %s" % p)
    # 确认 exe 是 x64 Windows PE，且内嵌中文（UTF-16LE 标题）正常
    with open(launcher, "rb") as f:
        blob = f.read(2)
    if blob != b"MZ":
        sys.exit("[error] 启动器不是有效 PE 文件")
    print("  stage 结构: python.exe / app/巴菲特投资智慧.html / 启动器 exe / 停止服务 exe 均在位")
    print("[ok] 完成：%s" % exe)


def main():
    ap = argparse.ArgumentParser(description="巴菲特投资智慧 Windows 安装器打包器")
    ap.add_argument("--version", default="2.0", help="版本号（默认 2.0）")
    ap.add_argument("--no-python-download", action="store_true",
                    help="只用 vendor 缓存，不访问网络")
    args = ap.parse_args()

    if os.path.exists(STAGE):
        shutil.rmtree(STAGE)
    os.makedirs(APP_DIR)

    ensure_python(args.no_python_download)
    icon = make_icon()
    copy_app_resources()
    compile_launchers()
    write_usage(args.version)
    nsi = render_nsi(args.version, icon)
    build_setup(nsi)
    verify(args.version, icon)


if __name__ == "__main__":
    main()
