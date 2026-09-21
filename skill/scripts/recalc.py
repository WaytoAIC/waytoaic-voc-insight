#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
跨环境 Excel 公式重算。

openpyxl 写出的公式没有缓存值——不重算的话，用 pandas 或轻量预览器打开会看到
一片空白，业务方会以为表坏了。Excel / WPS / Google Sheets 打开时会自己算，
但交付前最好先算好。

按可用性依次尝试：
  1. Anthropic 沙箱自带的 recalc（如果在那个环境里）
  2. 本机 LibreOffice headless
  3. 都没有 → 打印说明，不报错退出（公式本身是对的，打开即算）

用法: python recalc.py <xlsx路径>
"""
import os, shutil, subprocess, sys, tempfile

ANTHROPIC = "/mnt/skills/public/xlsx/scripts/recalc.py"


def try_anthropic(path):
    if not os.path.exists(ANTHROPIC):
        return False
    r = subprocess.run([sys.executable, ANTHROPIC, path], capture_output=True, text=True)
    if r.returncode == 0:
        print(r.stdout.strip() or "recalc via Anthropic helper: ok")
        return True
    return False


def try_soffice(path):
    exe = next((shutil.which(c) for c in ("soffice", "libreoffice") if shutil.which(c)), None)
    if not exe:
        return False
    with tempfile.TemporaryDirectory() as td:
        r = subprocess.run(
            [exe, "--headless", "--norestore", "--convert-to", "xlsx", "--outdir", td, path],
            capture_output=True, text=True, timeout=300)
        out = os.path.join(td, os.path.basename(path))
        if r.returncode == 0 and os.path.exists(out):
            shutil.copy(out, path)
            print(f"recalc via LibreOffice: ok ({path})")
            return True
    return False


def main():
    if len(sys.argv) < 2:
        sys.exit("用法: python recalc.py <xlsx路径>")
    path = sys.argv[1]
    if not os.path.exists(path):
        sys.exit(f"文件不存在: {path}")
    if try_anthropic(path) or try_soffice(path):
        return
    print("未找到可用的重算工具（LibreOffice / Anthropic recalc）。\n"
          "公式本身有效，Excel、WPS、Google Sheets 打开时会自动计算。\n"
          "但如果交付对象会用脚本或轻量预览器读这个文件，先提醒他们：\n"
          "统计页在打开前显示为空是正常的。")


if __name__ == "__main__":
    main()
