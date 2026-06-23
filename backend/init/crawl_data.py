# -*- coding: utf-8 -*-
"""
化学数据爬取脚本（仅爬取，写入本地 JSON，不入库）

数据保存目录：backend/data/crawled/
  - molecules.json
  - literature.json
  - materials.json
  - meta.json          # 爬取元信息（上次 CID、记录数等）

用法：
  cd backend
  python init/crawl_data.py                           # 默认各 1000/1000/500
  python init/crawl_data.py --molecules 2000          # 仅爬分子
  python init/crawl_data.py --molecules 1000 --append # 追加到已有 JSON（去重）
  python init/crawl_data.py --cid-start 1500          # 从指定 CID 开始爬分子
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

# 允许从 backend 或 init 目录运行
sys.path.insert(0, str(Path(__file__).resolve().parent))

from data_common import (  # noqa: E402
    LITERATURE_FILE,
    MATERIALS_FILE,
    META_FILE,
    MOLECULES_FILE,
    crawl_literature_list,
    crawl_molecules_list,
    generate_materials_list,
    load_json_list,
    load_meta,
    log,
    merge_by_key,
    save_json_list,
    save_meta,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="爬取化学数据并保存为本地 JSON")
    parser.add_argument("--molecules", type=int, default=1000, help="爬取分子数量，0 表示跳过")
    parser.add_argument("--literature", type=int, default=1000, help="爬取文献数量，0 表示跳过")
    parser.add_argument("--materials", type=int, default=500, help="生成材料数量，0 表示跳过")
    parser.add_argument("--cid-start", type=int, default=None, help="PubChem 起始 CID（默认读 meta 或 1）")
    parser.add_argument("--append", action="store_true", help="追加到已有 JSON 文件（按 picId/doi/name 去重）")
    parser.add_argument("--overwrite", action="store_true", help="覆盖已有 JSON（默认追加模式下才合并）")
    parser.add_argument(
        "--literature-source",
        choices=["auto", "crossref", "openalex"],
        default="openalex",
        help="文献数据源（默认 openalex，国内网络推荐；Crossref 易出现 504）",
    )
    args = parser.parse_args()

    meta = load_meta()
    t0 = time.time()
    total_new = 0

    if args.molecules > 0:
        cid_start = args.cid_start
        if cid_start is None:
            cid_start = meta.get("molecules", {}).get("next_cid_start", 1)

        new_items, last_cid = crawl_molecules_list(args.molecules, cid_start)
        if args.append and not args.overwrite:
            existing = load_json_list(MOLECULES_FILE)
            merged, added = merge_by_key(existing, new_items, "picId")
            save_json_list(MOLECULES_FILE, merged)
            total_new += added
            log(f"分子 JSON 已更新：新增 {added} 条，合计 {len(merged)} 条 -> {MOLECULES_FILE}")
        else:
            save_json_list(MOLECULES_FILE, new_items)
            total_new += len(new_items)
            log(f"分子 JSON 已保存 {len(new_items)} 条 -> {MOLECULES_FILE}")

        meta.setdefault("molecules", {})
        meta["molecules"]["count"] = len(load_json_list(MOLECULES_FILE))
        meta["molecules"]["last_cid"] = last_cid
        meta["molecules"]["next_cid_start"] = last_cid + 1

    if args.literature > 0:
        new_items = crawl_literature_list(args.literature, source=args.literature_source)
        if args.append and not args.overwrite:
            existing = load_json_list(LITERATURE_FILE)
            merged, added = merge_by_key(existing, new_items, "doi")
            save_json_list(LITERATURE_FILE, merged)
            total_new += added
            log(f"文献 JSON 已更新：新增 {added} 条，合计 {len(merged)} 条 -> {LITERATURE_FILE}")
        else:
            save_json_list(LITERATURE_FILE, new_items)
            total_new += len(new_items)
            log(f"文献 JSON 已保存 {len(new_items)} 条 -> {LITERATURE_FILE}")

        meta.setdefault("literature", {})
        meta["literature"]["count"] = len(load_json_list(LITERATURE_FILE))

    if args.materials > 0:
        new_items = generate_materials_list(args.materials)
        if args.append and not args.overwrite:
            existing = load_json_list(MATERIALS_FILE)
            merged, added = merge_by_key(existing, new_items, "name")
            save_json_list(MATERIALS_FILE, merged)
            total_new += added
            log(f"材料 JSON 已更新：新增 {added} 条，合计 {len(merged)} 条 -> {MATERIALS_FILE}")
        else:
            save_json_list(MATERIALS_FILE, new_items)
            total_new += len(new_items)
            log(f"材料 JSON 已保存 {len(new_items)} 条 -> {MATERIALS_FILE}")

        meta.setdefault("materials", {})
        meta["materials"]["count"] = len(load_json_list(MATERIALS_FILE))

    save_meta(meta)
    elapsed = time.time() - t0
    log(f"爬取完成！本次新增 {total_new} 条，耗时 {elapsed:.1f} 秒")
    log(f"元信息 -> {META_FILE}")
    log("下一步：python init/insert_data.py")


if __name__ == "__main__":
    main()
