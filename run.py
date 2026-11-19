# -*- coding: utf-8 -*-
"""music3 统一入口（免 -m 前缀）。

  python run.py search "晴天 周杰伦"
  python run.py get "晴天 周杰伦"
  python run.py web
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def main():
    argv = sys.argv[1:]
    if not argv:
        print(__doc__)
        return 0
    if argv[0] in ("web", "serve", "ui"):
        from src import web

        return web.main()
    from src import cli

    return cli.main(argv)


if __name__ == "__main__":
    sys.exit(main() or 0)
