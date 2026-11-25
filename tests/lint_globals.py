# -*- coding: utf-8 -*-
"""web.py global 完整性 lint: 扫全部 def, 写模块级 _PV_*/_pv_* 变量但漏 global 的报出。

防 R58/R59 同类炸(UnboundLocalError): 节流写盘函数 global 漏 *_LAST_FLUSH / 漏被写变量。
跑: python tests/lint_globals.py   (exit 0=全过, 1=有漏)
"""
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEB = os.path.join(ROOT, "src", "web.py")


def module_level_globals(src):
    """web.py 顶层(非 def 内)以 _ 开头的模块级变量名。"""
    g = set()
    for m in re.finditer(r"^(?!\s)(_\w+)\s*=", src, re.M):
        g.add(m.group(1))
    return g


def function_blocks(src):
    """切出所有顶层 def 块(到下一个同级 def 或 EOF), 返回 (name, body)。"""
    blocks = []
    starts = [m.start() for m in re.finditer(r"^def \w+\(", src, re.M)]
    starts.append(len(src))
    for i in range(len(starts) - 1):
        name_m = re.match(r"def (\w+)\(", src[starts[i]:])
        blocks.append((name_m.group(1), src[starts[i]:starts[i + 1]]))
    return blocks


def globals_declared(body):
    """该 def 块里 global 语句声明的变量名。"""
    d = set()
    for m in re.finditer(r"\bglobal\s+([^\n]+)", body):
        for v in m.group(1).replace("\n", " ").split(","):
            v = v.strip()
            if v:
                d.add(v)
    return d


def written_vars(body):
    """该 def 块里被赋值的 _ 前缀模块级变量(= / += / -= 等, 排除 import 名)。"""
    w = set()
    for m in re.finditer(r"(?m)(?<![.\w])(_\w+)(?=[\+\-]?=)", body):
        v = m.group(1)
        # 排除局部 import 的别名(_t/_j/_os 等, 它们 = 的是 import 目标不是模块变量)
        if re.search(r"import\s+" + v, body):
            continue
        w.add(v)
    return w


def main():
    src = io.open(WEB, encoding="utf-8").read()
    mods = module_level_globals(src)
    # 只对「被写 + 是模块级 + 在多个 def 共享」的变量查 global(模块级 _ 变量跨 def 共享才需 global)
    issues = []
    for name, body in function_blocks(src):
        declared = globals_declared(body)
        writes = written_vars(body)
        # 写的是模块级变量、且该变量在多个 def 出现(共享)、但该 def 没声明 global
        for v in writes:
            if v not in mods:
                continue
            # 跨 def 共享? 数含 v= 的 def 数
            shared = sum(1 for _, b in function_blocks(src) if re.search(r"(?<![.\w])" + v + r"(?=[\+\-]?=)", b))
            if shared > 1 and v not in declared:
                issues.append("%s: 写模块级共享变量 %s 但 global 漏声明(共 %d 个 def 写它)" % (name, v, shared))
    if issues:
        for x in issues:
            print("MISS", x)
        print("global 完整性 lint: %d 处漏" % len(issues))
        return 1
    print("global 完整性 lint: 全过 (扫 %d 个 def, %d 个模块级变量)" % (
        len(function_blocks(src)), len(mods)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
