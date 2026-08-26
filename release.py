#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
巴菲特投资智慧 · 一键发布 GitHub Release（Mac DMG + Windows Setup.exe）
=====================================================================

把当前版本的两个安装包一起发布到 GitHub Releases，方便在任何机器上下载：
  - dist/巴菲特投资智慧-vX.Y.dmg          → BuffettWisdom-vX.Y.dmg
  - dist/巴菲特投资智慧-vX.Y-Setup.exe    → BuffettWisdom-vX.Y-Setup.exe
（附件名用 ASCII，避免 GitHub API 对非 ASCII 文件名截断的问题。）

用法：
  python3 release.py --version 2.1            # 两个安装包已存在时直接发布
  python3 release.py --version 2.1 --build    # 先打包（Mac + Windows）再发布
  python3 release.py --version 2.1 --dry-run  # 只打印将执行的操作，不实际发布
  python3 release.py --version 2.1 --repos pwu0125/buffett-letters-knowledge

行为：
  - 版本标签 vX.Y 与 Release 不存在 → 创建 Release（标签指向当前 HEAD）并上传两个附件
  - Release 已存在 → 更新说明文字，并用 --clobber 覆盖同名附件（可重复执行）
  - 依赖 gh CLI 且已登录（gh auth login）

发布后地址：
  https://github.com/<owner>/<repo>/releases/tag/vX.Y
"""

import argparse
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
DIST = os.path.join(HERE, "dist")
REPO = "pwu0125/buffett-letters-knowledge"

DMG_NAME = "巴菲特投资智慧-v%s.dmg"
SETUP_NAME = "巴菲特投资智慧-v%s-Setup.exe"
DMG_ASSET = "BuffettWisdom-v%s.dmg"
SETUP_ASSET = "BuffettWisdom-v%s-Setup.exe"

NOTES_TEMPLATE = """## 巴菲特投资智慧 v{version}（Mac + Windows 安装包）

### 🍎 Mac 版
- **{dmg_asset}**：DMG 安装镜像，把「巴菲特投资智慧.app」拖入 Applications 即可
- 首次打开如被 Gatekeeper 拦截：右键 → 打开，或 `xattr -dr com.apple.quarantine "/Applications/巴菲特投资智慧.app"`
- 原生窗口（Swift + WKWebView），关闭窗口即退出并停止本地服务

### 🪟 Windows 版（64 位 Windows 10/11）
- **{setup_asset}**：NSIS 安装器，按用户安装到 `%LOCALAPPDATA%\\巴菲特投资智慧`（无需管理员），
  安装时自动生成 `uninstall.exe` 卸载器并注册「应用和功能」
- 内置 Python 运行时与全部知识库，无需安装任何依赖，完全离线可用
- 启动自动拉起本地服务（127.0.0.1:8666）并打开 Edge 应用模式窗口；重复启动复用服务
- 卸载自动停止服务、清理文件/快捷方式/注册表；默认保留笔记数据（`%APPDATA%\\巴菲特投资智慧`）
- SmartScreen 未签名提示：更多信息 → 仍要运行

### 📁 数据位置
- Mac：`~/Library/Application Support/巴菲特投资智慧/state.json`
- Windows：`%APPDATA%\\巴菲特投资智慧\\state.json`
"""


def run(cmd, **kw):
    print("  $", " ".join(cmd) if isinstance(cmd, list) else cmd)
    return subprocess.run(cmd, check=True, capture_output=True, text=True, **kw)


def gh(args, check=True):
    """执行 gh 命令（args 为参数列表），返回 (returncode, stdout)。"""
    print("  $ gh " + " ".join(args))
    r = subprocess.run(["gh"] + args, capture_output=True, text=True)
    if check and r.returncode != 0:
        sys.exit("[error] gh %s 失败：%s" % (" ".join(args), r.stderr.strip()))
    return r


def upload_assets(tag, assets):
    """上传附件。assets: [(本地路径, ASCII 附件名), ...]

    GitHub API 会截断非 ASCII 附件名（中文名会变成 "-vX.Y.ext"），
    因此统一复制为 ASCII 临时文件名再上传；--clobber 保证重复发布时覆盖同名附件。
    """
    tmpdir = tempfile.mkdtemp(prefix="buffett-release-")
    try:
        for local, name in assets:
            tmp = os.path.join(tmpdir, name)
            shutil.copy2(local, tmp)
            gh(["release", "upload", tag, tmp, "--clobber"])
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def ensure_artifacts(version, build):
    dmg = os.path.join(DIST, DMG_NAME % version)
    setup = os.path.join(DIST, SETUP_NAME % version)
    if build:
        print("[1/4] 打包（--build）…")
        run([sys.executable, os.path.join(HERE, "package_app.py"), "--version", version])
        run([sys.executable, os.path.join(HERE, "package_windows.py"), "--version", version])
    missing = [p for p in (dmg, setup) if not os.path.isfile(p)]
    if missing:
        sys.exit("[error] 缺少安装包：\n  %s\n请先运行打包脚本，或加 --build 自动打包。"
                 % "\n  ".join(missing))
    return dmg, setup


def main():
    ap = argparse.ArgumentParser(description="巴菲特投资智慧 GitHub Release 发布器")
    ap.add_argument("--version", required=True, help="版本号，如 2.1（标签 v2.1）")
    ap.add_argument("--build", action="store_true", help="先打包 Mac + Windows 再发布")
    ap.add_argument("--dry-run", action="store_true", help="只打印操作，不实际发布")
    ap.add_argument("--repos", default=REPO, help="仓库 owner/name（默认 %s）" % REPO)
    args = ap.parse_args()

    tag = "v" + args.version
    dmg, setup = ensure_artifacts(args.version, args.build)
    dmg_asset, setup_asset = DMG_ASSET % args.version, SETUP_ASSET % args.version

    # gh 可用性
    if shutil.which("gh") is None:
        sys.exit("[error] 未找到 gh CLI，请先安装：brew install gh 并 gh auth login")

    print("[2/4] 检查 gh 登录状态…")
    r = gh(["auth", "status"], check=False)
    if r.returncode != 0:
        sys.exit("[error] gh 未登录，请先执行 gh auth login")

    print("[3/4] 检查 Release %s 是否存在…" % tag)
    r = gh(["release", "view", tag, "--json", "tagName"], check=False)
    exists = r.returncode == 0

    notes = NOTES_TEMPLATE.format(version=args.version,
                                  dmg_asset=dmg_asset, setup_asset=setup_asset)
    assets = [(dmg, dmg_asset), (setup, setup_asset)]
    if args.dry_run:
        print("\n[DRY-RUN] 将执行：")
        if exists:
            print("  gh release edit %s --notes <模板说明>" % tag)
            for _, name in assets:
                print("  gh release upload %s <%s> --clobber（ASCII 临时文件名上传）" % (tag, name))
        else:
            print("  gh release create %s --title ... --notes <模板说明>" % tag)
            for _, name in assets:
                print("  gh release upload %s <%s> --clobber（ASCII 临时文件名上传）" % (tag, name))
        print("\n[ok] dry-run 完成，未做任何修改。")
        return

    print("[4/4] 发布…")
    if exists:
        print("  Release 已存在 → 更新说明 + 覆盖附件")
        gh(["release", "edit", tag, "--notes", notes])
    else:
        print("  创建 Release %s（标签指向当前 HEAD）" % tag)
        title = "巴菲特投资智慧 v%s（Mac + Windows 安装包）" % args.version
        gh(["release", "create", tag, "--title", title, "--notes", notes])
    upload_assets(tag, assets)

    # 校验
    r = gh(["release", "view", tag, "--json", "assets",
            "--jq", ".assets[] | .name + \"|\" + (.size|tostring)"])
    ok = True
    for want, size in ((dmg_asset, os.path.getsize(dmg)),
                       (setup_asset, os.path.getsize(setup))):
        hit = [ln for ln in r.stdout.splitlines() if ln.startswith(want + "|")]
        if not hit or int(hit[0].split("|")[1]) != size:
            ok = False
            print("[warn] 附件校验未通过: %s" % want)
    if ok:
        print("[ok] 完成：https://github.com/%s/releases/tag/%s" % (args.repos, tag))
    else:
        print("[error] 发布完成但附件校验异常，请人工检查 Release 页面。")


if __name__ == "__main__":
    main()
