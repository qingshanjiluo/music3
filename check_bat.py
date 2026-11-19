# -*- coding: utf-8 -*-
"""检查 .bat 文件是否含非 ASCII 字节。

为什么必须全 ASCII：cmd.exe 按系统 ANSI 码页（简体中文 Windows = GBK）
解析 .bat 文件本身。`chcp 65001` 只改控制台 I/O 的码页，管不到文件解析。
UTF-8 中文被按 GBK 拆开后，后半截字节会变成独立命令，典型症状：

    '音乐工具' is not recognized as an internal or external command
    'CODING' is not recognized as an internal or external command
    'tf8' is not recognized as an internal or external command

用法：
    python -X utf8 check_bat.py                 # 查当前目录
    python -X utf8 check_bat.py F:\\some\\dir    # 查指定目录
    python -X utf8 check_bat.py --fix            # 自动改成 ASCII（危险，需人工确认）

退出码：0 全部干净 / 1 发现问题
"""
from __future__ import annotations

import os
import sys


def scan(path):
    """返回 (ok, detail, bad_lines)。"""
    try:
        with open(path, "rb") as f:
            data = f.read()
    except Exception as e:
        return False, "读取失败: %r" % (e,), []

    if not data:
        return True, "空文件", []

    has_bom = data[:3] == b"\xef\xbb\xbf"
    non_ascii = [i for i, b in enumerate(data) if b > 127]

    bad_lines = []
    if non_ascii:
        # 按行定位，给出 GBK 视角的乱码预览
        gbk = data.decode("gbk", errors="replace")
        for no, line in enumerate(gbk.splitlines(), 1):
            if any(ord(ch) > 127 for ch in line):
                bad_lines.append((no, line.strip()[:70]))

    if has_bom:
        return False, "含 UTF-8 BOM（cmd 会把 BOM 当命令的一部分）", bad_lines
    if non_ascii:
        return False, "%d 个非 ASCII 字节（%d 行受影响）" % (len(non_ascii), len(bad_lines)), bad_lines
    return True, "纯 ASCII", []


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    root = args[0] if args else os.getcwd()
    fix = "--fix" in sys.argv

    if not os.path.isdir(root):
        print("目录不存在: %s" % root)
        return 2

    bats = [
        os.path.join(root, f)
        for f in os.listdir(root)
        if f.lower().endswith(".bat") or f.lower().endswith(".cmd")
    ]
    if not bats:
        print("没找到 .bat / .cmd 文件: %s" % root)
        return 0

    print("检查 %d 个批处理文件（%s）\n" % (len(bats), root))
    bad = 0
    for p in sorted(bats):
        okk, detail, bad_lines = scan(p)
        mark = "✓" if okk else "✗"
        print("  %s %-26s %s" % (mark, os.path.basename(p), detail))
        if not okk:
            bad += 1
            for no, line in bad_lines[:6]:
                print("      第 %d 行 GBK 视角: %s" % (no, line))
            if len(bad_lines) > 6:
                print("      … 另有 %d 行" % (len(bad_lines) - 6))
            print("      修法: 非 ASCII 全部改英文；中文标题用")
            print("            ctypes.windll.kernel32.SetConsoleTitleW(...)")
            print("            或 print 输出（Python 侧中文没问题）")

    print()
    if bad:
        print("%d 个文件有问题。批处理文件必须纯 ASCII。" % bad)
        return 1
    print("全部干净。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
