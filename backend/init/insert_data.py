# -*- coding: utf-8 -*-
"""
从本地 JSON 批量入库（无需重新爬取）

读取目录：backend/data/crawled/
  - molecules.json
  - literature.json
  - materials.json

用法：
  cd backend
  python init/insert_data.py                    # 导入全部 JSON
  python init/insert_data.py --only molecules     # 仅导入分子
  python init/insert_data.py --only literature
  python init/insert_data.py --file data/crawled/molecules.json
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from data_common import (  # noqa: E402
    BACKEND_DIR,
    LITERATURE_FILE,
    MATERIALS_FILE,
    MOLECULES_FILE,
    get_db_path,
    insert_literature,
    insert_materials,
    insert_molecules,
    load_json_list,
    log,
    print_summary,
    refresh_tag_stats,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="从本地 JSON 导入数据到 SQLite")
    parser.add_argument(
        "--only",
        choices=["molecules", "literature", "materials", "all"],
        default="all",
        help="仅导入指定类型",
    )
    parser.add_argument("--file", type=str, default=None, help="指定单个 JSON 文件路径")
    parser.add_argument("--skip-tags", action="store_true", help="跳过标签统计更新")
    args = parser.parse_args()

    db_path = get_db_path()
    if not Path(db_path).exists():
        log(f"数据库不存在: {db_path}")
        log("请先运行: python init/initial_db.py")
        return

    log(f"目标数据库: {db_path}")
    t0 = time.time()
    total_inserted = 0

    if args.file:
        file_path = Path(args.file)
        if not file_path.is_absolute():
            file_path = BACKEND_DIR / file_path
        if not file_path.exists():
            log(f"文件不存在: {file_path}")
            return
        records = load_json_list(file_path)
        name = file_path.stem
        if name == "molecules":
            n = insert_molecules(db_path, records)
            log(f"分子入库 {n}/{len(records)} 条（跳过重复）")
            total_inserted += n
        elif name == "literature":
            n = insert_literature(db_path, records)
            log(f"文献入库 {n}/{len(records)} 条（跳过重复）")
            total_inserted += n
        elif name == "materials":
            n = insert_materials(db_path, records)
            log(f"材料入库 {n}/{len(records)} 条（跳过重复）")
            total_inserted += n
        else:
            log(f"无法识别文件类型: {file_path.name}，请使用 molecules/literature/materials")
            return
    else:
        do_all = args.only == "all"

        if do_all or args.only == "molecules":
            if MOLECULES_FILE.exists():
                records = load_json_list(MOLECULES_FILE)
                n = insert_molecules(db_path, records)
                log(f"分子入库 {n}/{len(records)} 条（跳过重复）")
                total_inserted += n
            else:
                log(f"跳过分子：文件不存在 {MOLECULES_FILE}")

        if do_all or args.only == "literature":
            if LITERATURE_FILE.exists():
                records = load_json_list(LITERATURE_FILE)
                n = insert_literature(db_path, records)
                log(f"文献入库 {n}/{len(records)} 条（跳过重复）")
                total_inserted += n
            else:
                log(f"跳过文献：文件不存在 {LITERATURE_FILE}")

        if do_all or args.only == "materials":
            if MATERIALS_FILE.exists():
                records = load_json_list(MATERIALS_FILE)
                n = insert_materials(db_path, records)
                log(f"材料入库 {n}/{len(records)} 条（跳过重复）")
                total_inserted += n
            else:
                log(f"跳过材料：文件不存在 {MATERIALS_FILE}")

    if not args.skip_tags:
        refresh_tag_stats(db_path)

    print_summary(db_path)
    elapsed = time.time() - t0
    log(f"入库完成！本次新增 {total_inserted} 条，耗时 {elapsed:.1f} 秒")


if __name__ == "__main__":
    main()
