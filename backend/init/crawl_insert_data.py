# -*- coding: utf-8 -*-
"""
化学数据批量爬取 + 入库（兼容旧命令）

推荐拆分为两步：
  1. python init/crawl_data.py      # 爬取 -> backend/data/crawled/*.json
  2. python init/insert_data.py     # JSON -> SQLite

本脚本等价于依次执行上述两步。
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

INIT_DIR = Path(__file__).resolve().parent
PYTHON = sys.executable


def main() -> None:
    parser = argparse.ArgumentParser(description="爬取并入库（调用 crawl_data + insert_data）")
    parser.add_argument("--molecules", type=int, default=1000)
    parser.add_argument("--literature", type=int, default=1000)
    parser.add_argument("--materials", type=int, default=500)
    parser.add_argument("--cid-start", type=int, default=None)
    parser.add_argument("--append", action="store_true", help="追加到已有 JSON")
    parser.add_argument("--skip-tags", action="store_true")
    parser.add_argument("--skip-crawl", action="store_true", help="跳过爬取，仅入库已有 JSON")
    args = parser.parse_args()

    if not args.skip_crawl:
        cmd = [
            PYTHON, str(INIT_DIR / "crawl_data.py"),
            "--molecules", str(args.molecules),
            "--literature", str(args.literature),
            "--materials", str(args.materials),
        ]
        if args.cid_start is not None:
            cmd.extend(["--cid-start", str(args.cid_start)])
        if args.append:
            cmd.append("--append")
        subprocess.check_call(cmd)

    cmd = [PYTHON, str(INIT_DIR / "insert_data.py")]
    if args.skip_tags:
        cmd.append("--skip-tags")
    subprocess.check_call(cmd)


if __name__ == "__main__":
    main()
