# -*- coding: utf-8 -*-
"""爬虫与入库脚本的共享逻辑。"""

from __future__ import annotations

import json
import random
import sqlite3
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests
import tomli

try:
    from rdkit import Chem
    HAS_RDKIT = True
except ImportError:
    HAS_RDKIT = False

BACKEND_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = BACKEND_DIR / "config" / "config.toml"
DATA_DIR = BACKEND_DIR / "data" / "crawled"

PUBCHEM_BASE = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"
CROSSREF_BASE = "https://api.crossref.org/works"
OPENALEX_BASE = "https://api.openalex.org/works"
CROSSREF_MAILTO = "admin@ustc.edu.cn"

REQUEST_HEADERS = {
    "User-Agent": "PIChemData-Crawler/1.0 (local-dev; mailto:admin@ustc.edu.cn)",
    "Accept": "application/json",
}

MOLECULE_TYPES = {
    "芳香族化合物": ["芳香族", "有机"],
    "有机小分子": ["有机"],
    "无机小分子": ["无机"],
    "无机盐": ["无机", "盐"],
    "烯烃": ["烯烃", "有机"],
    "无机酸": ["无机酸", "无机"],
    "过渡金属配合物": ["过渡金属", "配合物"],
    "醇类": ["醇类", "有机", "溶剂"],
    "羧酸": ["羧酸", "有机酸"],
    "其他": ["其他"],
}

CRYSTAL_SYSTEMS = ["立方", "四方", "六方", "三方", "正交", "单斜", "面心立方", "体心立方", "菱方"]
SPACE_GROUPS = ["Fm-3m", "Pm-3m", "I41/amd", "P63mc", "R-3c", "Pnma", "P63/mmc", "Fd-3m", "Im-3m", "C2/m"]

LITERATURE_QUERIES = [
    "catalysis chemistry",
    "density functional theory",
    "organic synthesis",
    "electrochemistry",
    "materials science",
    "spectroscopy",
    "coordination chemistry",
    "polymer chemistry",
    "nanomaterials",
    "green chemistry",
]

MOLECULES_FILE = DATA_DIR / "molecules.json"
LITERATURE_FILE = DATA_DIR / "literature.json"
MATERIALS_FILE = DATA_DIR / "materials.json"
META_FILE = DATA_DIR / "meta.json"


def log(msg: str) -> None:
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


def get_db_path() -> str:
    with open(CONFIG_PATH, "rb") as f:
        config = tomli.load(f)
    rel = config.get("database", {}).get("path", "db_table/")
    return str(BACKEND_DIR / rel / "chemistry.db")


def ensure_data_dir() -> Path:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return DATA_DIR


def load_json_list(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data if isinstance(data, list) else []


def save_json_list(path: Path, records: List[Dict[str, Any]]) -> None:
    ensure_data_dir()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)


def load_meta() -> Dict[str, Any]:
    if not META_FILE.exists():
        return {}
    with open(META_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_meta(meta: Dict[str, Any]) -> None:
    ensure_data_dir()
    meta["updated_at"] = datetime.now().isoformat(timespec="seconds")
    with open(META_FILE, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)


def merge_by_key(
    existing: List[Dict[str, Any]],
    new_items: List[Dict[str, Any]],
    key: str,
) -> Tuple[List[Dict[str, Any]], int]:
    seen = {item.get(key) for item in existing if item.get(key)}
    merged = list(existing)
    added = 0
    for item in new_items:
        k = item.get(key)
        if not k or k in seen:
            continue
        seen.add(k)
        merged.append(item)
        added += 1
    return merged, added


# ---------------------------------------------------------------------------
# 爬取 / 生成（仅返回数据，不写数据库）
# ---------------------------------------------------------------------------

def classify_molecule(smiles: str, formula: str) -> Tuple[str, List[str]]:
    s = (smiles or "").lower()
    f = formula or ""
    if "c1" in s or "c2" in s:
        return "芳香族化合物", MOLECULE_TYPES["芳香族化合物"]
    if "C=C" in smiles or "C#C" in smiles:
        return "烯烃", MOLECULE_TYPES["烯烃"]
    if any(x in f for x in ("OH", "ol")) or "CO" in smiles:
        if "C(=O)O" in smiles or "C(=O)[O-]" in smiles:
            return "羧酸", MOLECULE_TYPES["羧酸"]
        return "醇类", MOLECULE_TYPES["醇类"]
    if any(m in f for m in ("Fe", "Cu", "Ni", "Pd", "Pt", "Co", "Mn", "Cr", "Zn")):
        return "过渡金属配合物", MOLECULE_TYPES["过渡金属配合物"]
    if any(x in f for x in ("Cl", "Br", "I", "F")) and "C" not in f:
        return "无机小分子", MOLECULE_TYPES["无机小分子"]
    if "C" in f:
        return "有机小分子", MOLECULE_TYPES["有机小分子"]
    return "无机小分子", MOLECULE_TYPES["无机小分子"]


def smiles_to_atoms_bonds(smiles: str) -> Tuple[List[str], List[List[int]]]:
    if not HAS_RDKIT or not smiles:
        return [], []
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return [], []
    atoms = [a.GetSymbol() for a in mol.GetAtoms()]
    bonds = [
        [b.GetBeginAtomIdx(), b.GetEndAtomIdx(), int(b.GetBondTypeAsDouble())]
        for b in mol.GetBonds()
    ]
    return atoms, bonds


def estimate_volume(mass: float) -> float:
    if not mass:
        return round(random.uniform(20, 120), 2)
    return round(mass * random.uniform(0.6, 1.4), 2)


def fetch_pubchem_batch(cids: List[int]) -> List[Dict[str, Any]]:
    if not cids:
        return []
    cid_str = ",".join(str(c) for c in cids)
    url = (
        f"{PUBCHEM_BASE}/compound/cid/{cid_str}/property/"
        "MolecularFormula,ConnectivitySMILES,CanonicalSMILES,InChI,MolecularWeight,IUPACName,InChIKey/JSON"
    )
    try:
        resp = requests.get(url, headers=REQUEST_HEADERS, timeout=30)
        if resp.status_code != 200:
            return []
        data = resp.json()
        props = data.get("PropertyTable", {}).get("Properties", [])
        return props if isinstance(props, list) else [props]
    except requests.RequestException as exc:
        log(f"  PubChem 请求失败: {exc}")
        return []


def fetch_pubchem_sdf(cid: int) -> Optional[str]:
    """从 PubChem 获取 SDF 格式数据（包含 3D 坐标）"""
    url = f"{PUBCHEM_BASE}/compound/cid/{cid}/sdf"
    try:
        resp = requests.get(url, headers=REQUEST_HEADERS, timeout=30)
        if resp.status_code == 200:
            return resp.text
        return None
    except requests.RequestException:
        return None


def pubchem_to_molecule(rec: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    cid_val = rec.get("CID")
    smiles = rec.get("CanonicalSMILES") or rec.get("ConnectivitySMILES") or ""
    if not smiles or not cid_val:
        return None

    formula = rec.get("MolecularFormula") or ""
    inchi = rec.get("InChI") or ""
    mass = float(rec.get("MolecularWeight") or 0)
    mol_type, tags = classify_molecule(smiles, formula)
    atoms, bonds = smiles_to_atoms_bonds(smiles)
    iupac = rec.get("IUPACName") or formula

    # 获取 SDF 数据
    sdf_content = fetch_pubchem_sdf(cid_val)

    return {
        "picId": f"pubchem-{cid_val}",
        "cid": cid_val,
        "inchikey": rec.get("InChIKey"),
        "canonicalInchikey": rec.get("InChIKey"),
        "smiles": smiles,
        "canonicalSmiles": smiles,
        "inchi": inchi,
        "canonicalInchi": inchi,
        "iupac": iupac,
        "title": iupac,
        "displayFormula": formula,
        "formula": formula,
        "mass": mass,
        "weight": mass,
        "volume": estimate_volume(mass),
        "type": mol_type,
        "tags": tags,
        "charge": 0,
        "spin": 1,
        "atoms": atoms,
        "bonds": bonds,
        "molFile": sdf_content,  # SDF/MOL 格式数据
        "createTime": (datetime.now() - timedelta(days=random.randint(1, 365))).strftime("%Y-%m-%d"),
        "sourcePath": "pubchem",
        "categoryLabel": "Open database",
        "categoryObject": "molecule",
        "author": "pubchem-crawler",
    }


def crawl_molecules_list(target: int, cid_start: int = 1) -> Tuple[List[Dict[str, Any]], int]:
    log(f"爬取分子数据，目标 {target} 条（PubChem CID 从 {cid_start} 起）...")
    results: List[Dict[str, Any]] = []
    batch_size = 100
    cid = cid_start
    max_cid = cid_start + target * 3

    while len(results) < target and cid < max_cid:
        batch_cids = list(range(cid, min(cid + batch_size, max_cid)))
        cid += batch_size
        for rec in fetch_pubchem_batch(batch_cids):
            if len(results) >= target:
                break
            item = pubchem_to_molecule(rec)
            if item:
                results.append(item)
        time.sleep(0.25)
        if len(results) % 200 == 0 and results:
            log(f"  已爬取分子 {len(results)}/{target}")

    last_cid = max((r["cid"] for r in results), default=cid_start)
    log(f"分子爬取完成，共 {len(results)} 条，CID 范围至 {last_cid}")
    return results, last_cid


def parse_crossref_item(item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    title_list = item.get("title") or []
    title = title_list[0] if title_list else None
    if not title:
        return None

    doi = item.get("DOI")
    authors_list = item.get("author") or []
    author_names = []
    for a in authors_list[:6]:
        family = a.get("family", "")
        given = a.get("given", "")
        if family:
            author_names.append(f"{family}, {given[0]}." if given else family)
    authors = "; ".join(author_names)
    if len(authors_list) > 6:
        authors += "; et al."

    journal_list = item.get("container-title") or []
    journal = journal_list[0] if journal_list else ""
    issued = item.get("issued", {}).get("date-parts", [[None]])[0]
    year = issued[0] if issued else None

    abstract = item.get("abstract", "")
    if abstract:
        abstract = abstract.replace("<jats:p>", "").replace("</jats:p>", "").strip()

    subjects = item.get("subject") or []
    keywords = subjects[:5] if subjects else ["chemistry"]
    tags = random.sample(
        ["催化", "DFT计算", "有机合成", "电化学", "材料", "光谱", "纳米", "绿色化学"],
        k=3,
    )

    return {
        "doi": doi,
        "title": title[:500],
        "authors": authors[:300],
        "journal": journal[:200],
        "year": year,
        "volume": str(item.get("volume", "") or ""),
        "issue": str(item.get("issue", "") or ""),
        "pages": item.get("page", "") or "",
        "abstract": (abstract or f"Study on {title[:80]}...")[:1000],
        "keywords": keywords,
        "tags": tags,
    }


def _inverted_index_to_abstract(inv: Optional[Dict[str, List[int]]]) -> str:
    if not inv:
        return ""
    max_pos = max((max(positions) for positions in inv.values()), default=-1)
    if max_pos < 0:
        return ""
    words = [""] * (max_pos + 1)
    for word, positions in inv.items():
        for p in positions:
            words[p] = word
    return " ".join(words).strip()


def fetch_crossref_page(query: str, offset: int, rows: int = 25) -> List[Dict[str, Any]]:
    params = {
        "query": query,
        "rows": rows,
        "offset": offset,
        "mailto": CROSSREF_MAILTO,
        "filter": "type:journal-article",
        "select": "DOI,title,author,container-title,issued,volume,issue,page,abstract,subject",
    }
    for attempt in range(3):
        try:
            resp = requests.get(
                CROSSREF_BASE, params=params, headers=REQUEST_HEADERS, timeout=30
            )
            if resp.status_code in (502, 503, 504):
                log(f"  Crossref HTTP {resp.status_code}（网关超时，国内访问常见）")
                return []  # 不再重试，交给上层切换数据源
            if resp.status_code != 200:
                log(f"  Crossref HTTP {resp.status_code}")
                time.sleep(2)
                continue
            items = resp.json().get("message", {}).get("items", [])
            return [parse_crossref_item(i) for i in items if parse_crossref_item(i)]
        except requests.RequestException as exc:
            log(f"  Crossref 请求失败 (第{attempt + 1}次): {exc}")
            if attempt >= 1:
                return []
            time.sleep(2)
    return []


def parse_openalex_item(item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    doi = item.get("doi", "") or ""
    if doi.startswith("https://doi.org/"):
        doi = doi.replace("https://doi.org/", "")
    if not doi:
        return None

    title = item.get("title") or item.get("display_name")
    if not title:
        return None

    authorships = item.get("authorships") or []
    author_names = []
    for a in authorships[:6]:
        name = (a.get("author") or {}).get("display_name")
        if name:
            author_names.append(name)
    authors = "; ".join(author_names)
    if len(authorships) > 6:
        authors += "; et al."

    journal = ""
    loc = item.get("primary_location") or {}
    source = loc.get("source") or {}
    journal = source.get("display_name") or ""

    abstract = _inverted_index_to_abstract(item.get("abstract_inverted_index"))
    concepts = item.get("concepts") or []
    keywords = [c.get("display_name") for c in concepts[:5] if c.get("display_name")] or ["chemistry"]
    tags = random.sample(
        ["催化", "DFT计算", "有机合成", "电化学", "材料", "光谱", "纳米", "绿色化学"],
        k=3,
    )

    return {
        "doi": doi,
        "title": title[:500],
        "authors": authors[:300],
        "journal": journal[:200],
        "year": item.get("publication_year"),
        "volume": str(loc.get("volume") or ""),
        "issue": str(loc.get("issue") or ""),
        "pages": "",
        "abstract": (abstract or f"Study on {title[:80]}...")[:1000],
        "keywords": keywords,
        "tags": tags,
    }


def fetch_openalex_page(query: str, page: int, per_page: int = 50) -> List[Dict[str, Any]]:
    params = {
        "search": query,
        "filter": "type:article,has_doi:true",
        "per-page": per_page,
        "page": page,
        "mailto": CROSSREF_MAILTO,
        "select": "id,doi,title,authorships,primary_location,publication_year,abstract_inverted_index,concepts",
    }
    for attempt in range(4):
        try:
            resp = requests.get(
                OPENALEX_BASE, params=params, headers=REQUEST_HEADERS, timeout=60
            )
            if resp.status_code != 200:
                log(f"  OpenAlex HTTP {resp.status_code}")
                time.sleep(2 * (attempt + 1))
                continue
            items = resp.json().get("results", [])
            return [parse_openalex_item(i) for i in items if parse_openalex_item(i)]
        except requests.RequestException as exc:
            log(f"  OpenAlex 请求失败 (第{attempt + 1}次): {exc}")
            time.sleep(2 * (attempt + 1))
    return []


def crawl_literature_list(target: int, source: str = "auto") -> List[Dict[str, Any]]:
    """
    source: auto | crossref | openalex
    - auto: 先试 Crossref，失败则切 OpenAlex
    - openalex: 仅用 OpenAlex（国内推荐）
    """
    if source == "openalex":
        log(f"爬取文献数据，目标 {target} 条（OpenAlex）...")
        use_openalex = True
    elif source == "crossref":
        log(f"爬取文献数据，目标 {target} 条（Crossref）...")
        use_openalex = False
    else:
        log(f"爬取文献数据，目标 {target} 条（Crossref → OpenAlex 备用）...")
        use_openalex = False

    results: List[Dict[str, Any]] = []
    seen_dois: set = set()
    offset = 0
    query_idx = 0
    crossref_fail_streak = 0
    openalex_page = 1

    while len(results) < target:
        query = LITERATURE_QUERIES[query_idx % len(LITERATURE_QUERIES)]

        if not use_openalex:
            records = fetch_crossref_page(query, offset, rows=25)
            time.sleep(0.5)
            offset += 25
            if not records:
                crossref_fail_streak += 1
                if crossref_fail_streak >= 1 and source == "auto":
                    log("  Crossref 不可用，切换至 OpenAlex 数据源...")
                    use_openalex = True
                    openalex_page = 1
                    query_idx = 0
                    continue
                if source == "crossref":
                    query_idx += 1
                    if query_idx >= len(LITERATURE_QUERIES) * 3:
                        break
                    continue
                query_idx += 1
                if query_idx % len(LITERATURE_QUERIES) == 0:
                    offset = 0
                continue
            crossref_fail_streak = 0
        else:
            records = fetch_openalex_page(query, openalex_page, per_page=50)
            time.sleep(0.8)
            openalex_page += 1
            if not records:
                query_idx += 1
                openalex_page = 1
                if query_idx >= len(LITERATURE_QUERIES) * 3:
                    break
                continue

        for rec in records:
            if len(results) >= target:
                break
            doi = rec.get("doi")
            if doi and doi not in seen_dois:
                seen_dois.add(doi)
                results.append(rec)

        if len(results) % 100 == 0 and results:
            src = "OpenAlex" if use_openalex else "Crossref"
            log(f"  已爬取文献 {len(results)}/{target} ({src})")

    log(f"文献爬取完成，共 {len(results)} 条")
    return results


def generate_materials_pool() -> List[Dict[str, Any]]:
    pool: List[Dict[str, Any]] = []
    seen = set()

    def add(name, formula, mtype, tags, band_gap=None, lattice=None, crystal=None, sg=None):
        key = (name, formula)
        if key in seen:
            return
        seen.add(key)
        pool.append({
            "name": name,
            "formula": formula,
            "type": mtype,
            "tags": tags,
            "bandGap": band_gap,
            "latticeConstant": lattice,
            "crystalSystem": crystal,
            "spaceGroup": sg,
            "createTime": (datetime.now() - timedelta(days=random.randint(1, 500))).strftime("%Y-%m-%d"),
        })

    metals = ["Cu", "Ag", "Au", "Pt", "Pd", "Ni", "Fe", "Co", "Ti", "Zn", "Al", "Mg", "Mo", "W", "V", "Cr", "Mn"]
    facets = ["(111)", "(100)", "(110)", "(211)", "(311)"]
    for m in metals:
        for f in facets:
            add(f"{m}{f}表面", m, "金属表面", [m, "表面", "催化", "过渡金属"],
                None, round(random.uniform(3.5, 4.2), 3), "面心立方", "Fm-3m")

    oxides = [
        ("TiO2", "锐钛矿", 3.2, 3.785, "四方", "I41/amd"),
        ("ZnO", "纤锌矿", 3.37, 3.249, "六方", "P63mc"),
        ("Fe2O3", "赤铁矿", 2.2, 5.036, "六方", "R-3c"),
        ("Al2O3", "刚玉", 8.7, 4.759, "三方", "R-3c"),
        ("SiO2", "石英", 9.0, 4.913, "三方", "P3221"),
        ("CuO", "黑铜矿", 1.4, 4.68, "单斜", "C2/c"),
        ("NiO", "氧化镍", 3.6, 4.17, "立方", "Fm-3m"),
        ("Co3O4", "四氧化三钴", 1.6, 8.08, "立方", "Fd-3m"),
        ("MnO2", "二氧化锰", 0.3, 4.39, "四方", "I41/amd"),
        ("V2O5", "五氧化二钒", 2.3, 11.512, "正交", "Pmmn"),
        ("WO3", "三氧化钨", 2.8, 7.297, "单斜", "P21/n"),
        ("MoO3", "三氧化钼", 3.1, 3.962, "正交", "Pnma"),
        ("SnO2", "二氧化锡", 3.6, 4.738, "四方", "P42/mnm"),
        ("In2O3", "氧化铟", 3.0, 10.118, "立方", "Ia-3"),
        ("Bi2O3", "氧化铋", 2.8, 5.532, "单斜", "P-3m1"),
    ]
    for formula, name_suffix, bg, lat, crystal, sg in oxides:
        add(f"{formula} {name_suffix}", formula, "金属氧化物",
            [formula.split("O")[0], "氧化物", "半导体" if bg and bg < 4 else "陶瓷"],
            bg, lat, crystal, sg)

    tmd = ["MoS2", "WS2", "MoSe2", "WSe2", "NbSe2", "TaS2", "SnS2", "PtS2", "NiTe2", "Bi2Se3"]
    for t in tmd:
        add(f"{t} 单层", t, "二维材料", [t, "二维材料", "TMD", "层状"],
            round(random.uniform(1.0, 2.5), 2), round(random.uniform(3.0, 3.5), 3), "六方", "P63/mmc")

    a_site = ["Sr", "Ba", "Ca", "La", "Pr", "Nd", "Sm", "Gd", "Y", "K", "Rb", "Cs"]
    b_site = ["Ti", "Fe", "Co", "Ni", "Mn", "Cr", "V", "Nb", "Ta", "Zr", "Sn", "Pb"]
    for a in a_site:
        for b in b_site:
            if a == b:
                continue
            formula = f"{a}{b}O3"
            add(f"{formula} 钙钛矿", formula, "钙钛矿",
                [a, b, "钙钛矿", "氧化物"],
                round(random.uniform(1.5, 3.5), 2),
                round(random.uniform(3.8, 4.1), 3),
                random.choice(["立方", "四方", "正交"]),
                random.choice(["Pm-3m", "I4/mcm", "Pnma"]))

    alloys = [
        ("Fe-Cr-Ni", "不锈钢316"), ("Cu-Zn", "黄铜"), ("Cu-Sn", "青铜"),
        ("Al-Cu", "硬铝合金"), ("Ni-Cr", "镍铬合金"), ("Ti-Al-V", "TC4钛合金"),
        ("Fe-Ni", "因瓦合金"), ("Co-Cr", "钴铬合金"), ("Pd-Ag", "钯银合金"),
    ]
    for formula, name in alloys:
        add(name, formula, "合金", ["合金", "金属"], None,
            round(random.uniform(3.5, 4.0), 3), "面心立方", "Fm-3m")

    carbides_nitrides = [
        ("TiC", "碳化钛", 0, 4.328), ("SiC", "碳化硅", 2.4, 3.081),
        ("WC", "碳化钨", 0, 2.906), ("TiN", "氮化钛", 0, 4.24),
        ("AlN", "氮化铝", 6.2, 3.112), ("GaN", "氮化镓", 3.4, 3.189),
        ("BN", "氮化硼", 5.9, 2.504), ("ZrN", "氮化锆", 0, 4.578),
    ]
    for formula, name, bg, lat in carbides_nitrides:
        add(name, formula, "陶瓷", [formula, "陶瓷", "高硬度"],
            bg, lat, random.choice(CRYSTAL_SYSTEMS), random.choice(SPACE_GROUPS))

    base_oxides = ["TiO2", "ZnO", "Fe2O3", "Co3O4", "NiO", "CuO", "MnO2", "CeO2", "ZrO2", "SnO2"]
    dopants = ["Fe", "Co", "Ni", "Cu", "Mn", "V", "Nb", "Mo", "W", "La", "Ce", "Gd", "Y", "Al", "Mg"]
    for base in base_oxides:
        for d in dopants:
            pct = random.choice([1, 2, 3, 5, 10, 15, 20])
            name = f"{d}掺杂{base} ({pct}%)"
            formula = f"{base}:{d}{pct}%"
            add(name, formula, "金属氧化物",
                [base, f"{d}掺杂", "催化剂", "氧化物"],
                round(random.uniform(1.5, 4.0), 2),
                round(random.uniform(3.0, 5.5), 3),
                random.choice(CRYSTAL_SYSTEMS),
                random.choice(SPACE_GROUPS))

    return pool


def generate_materials_list(target: int) -> List[Dict[str, Any]]:
    log(f"生成材料数据，目标 {target} 条...")
    pool = generate_materials_pool()
    random.shuffle(pool)
    records = pool[:target]
    log(f"材料生成完成，共 {len(records)} 条")
    return records


# ---------------------------------------------------------------------------
# 入库（从 JSON 记录写入数据库）
# ---------------------------------------------------------------------------

def insert_molecules(db_path: str, records: List[Dict[str, Any]]) -> int:
    inserted = 0
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        for m in records:
            try:
                cursor.execute(
                    """
                    INSERT OR IGNORE INTO molecules
                    (picId, inchikey, canonicalInchikey, smiles, canonicalSmiles,
                     inchi, canonicalInchi, iupac, title, displayFormula, formula,
                     mass, weight, volume, type, tags, charge, spin, atoms, bonds, molFile, createTime,
                     cid, sourcePath, categoryLabel, categoryObject, author)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        m.get("picId"),
                        m.get("inchikey"),
                        m.get("canonicalInchikey"),
                        m.get("smiles"),
                        m.get("canonicalSmiles"),
                        m.get("inchi"),
                        m.get("canonicalInchi"),
                        m.get("iupac"),
                        m.get("title"),
                        m.get("displayFormula"),
                        m.get("formula"),
                        m.get("mass"),
                        m.get("weight"),
                        m.get("volume"),
                        m.get("type"),
                        json.dumps(m.get("tags", []), ensure_ascii=False),
                        m.get("charge", 0),
                        m.get("spin", 1),
                        json.dumps(m.get("atoms", []), ensure_ascii=False),
                        json.dumps(m.get("bonds", []), ensure_ascii=False),
                        m.get("molFile"),  # SDF/MOL 数据
                        m.get("createTime"),
                        m.get("cid"),
                        m.get("sourcePath"),
                        m.get("categoryLabel"),
                        m.get("categoryObject"),
                        m.get("author"),
                    ),
                )
                if cursor.rowcount > 0:
                    inserted += 1
            except sqlite3.Error as exc:
                log(f"  插入分子 {m.get('picId')} 失败: {exc}")
        conn.commit()
    return inserted


def insert_literature(db_path: str, records: List[Dict[str, Any]]) -> int:
    inserted = 0
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        for rec in records:
            if not rec.get("doi"):
                continue
            try:
                keywords = rec.get("keywords", [])
                tags = rec.get("tags", [])
                if isinstance(keywords, str):
                    keywords = json.loads(keywords)
                if isinstance(tags, str):
                    tags = json.loads(tags)
                cursor.execute(
                    """
                    INSERT OR IGNORE INTO literature
                    (doi, title, authors, journal, year, volume, issue, pages, abstract, keywords, tags)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        rec["doi"],
                        rec["title"],
                        rec.get("authors"),
                        rec.get("journal"),
                        rec.get("year"),
                        rec.get("volume"),
                        rec.get("issue"),
                        rec.get("pages"),
                        rec.get("abstract"),
                        json.dumps(keywords, ensure_ascii=False),
                        json.dumps(tags, ensure_ascii=False),
                    ),
                )
                if cursor.rowcount > 0:
                    inserted += 1
            except sqlite3.Error as exc:
                log(f"  插入文献失败: {exc}")
        conn.commit()
    return inserted


def insert_materials(db_path: str, records: List[Dict[str, Any]]) -> int:
    inserted = 0
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        for m in records:
            try:
                tags = m.get("tags", [])
                if isinstance(tags, str):
                    tags = json.loads(tags)
                cursor.execute(
                    """
                    INSERT OR IGNORE INTO materials
                    (name, formula, type, tags, bandGap, latticeConstant, crystalSystem, spaceGroup, createTime)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        m["name"],
                        m.get("formula"),
                        m.get("type"),
                        json.dumps(tags, ensure_ascii=False),
                        m.get("bandGap"),
                        m.get("latticeConstant"),
                        m.get("crystalSystem"),
                        m.get("spaceGroup"),
                        m.get("createTime"),
                    ),
                )
                if cursor.rowcount > 0:
                    inserted += 1
            except sqlite3.Error as exc:
                log(f"  插入材料 {m.get('name')} 失败: {exc}")
        conn.commit()
    return inserted


def refresh_tag_stats(db_path: str) -> None:
    log("更新标签统计...")
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT tags FROM molecules WHERE tags IS NOT NULL")
        tag_counts: Dict[str, int] = {}
        for (tags_json,) in cursor.fetchall():
            try:
                for t in json.loads(tags_json):
                    tag_counts[t] = tag_counts.get(t, 0) + 1
            except (json.JSONDecodeError, TypeError):
                pass

        cursor.execute("DELETE FROM molecule_tags WHERE category = '自动统计'")
        for name, count in sorted(tag_counts.items(), key=lambda x: -x[1])[:50]:
            cursor.execute(
                "INSERT INTO molecule_tags (name, count, category) VALUES (?, ?, ?)",
                (name, count, "自动统计"),
            )

        cursor.execute("SELECT tags FROM materials WHERE tags IS NOT NULL")
        mat_tag_counts: Dict[str, int] = {}
        for (tags_json,) in cursor.fetchall():
            try:
                for t in json.loads(tags_json):
                    mat_tag_counts[t] = mat_tag_counts.get(t, 0) + 1
            except (json.JSONDecodeError, TypeError):
                pass

        cursor.execute("DELETE FROM material_tags WHERE category = '自动统计'")
        for name, count in sorted(mat_tag_counts.items(), key=lambda x: -x[1])[:30]:
            cursor.execute(
                "INSERT INTO material_tags (name, count, category) VALUES (?, ?, ?)",
                (name, count, "自动统计"),
            )

        cursor.execute("SELECT type, COUNT(*) FROM molecules GROUP BY type")
        total_mol = sum(r[1] for r in cursor.fetchall())
        cursor.execute("DELETE FROM category_summary")
        cursor.execute("SELECT type, COUNT(*) FROM molecules GROUP BY type ORDER BY COUNT(*) DESC")
        for mtype, cnt in cursor.fetchall():
            pct = round(cnt / total_mol * 100, 1) if total_mol else 0
            cursor.execute(
                "INSERT INTO category_summary (category, count, percentage) VALUES (?, ?, ?)",
                (mtype or "其他", cnt, pct),
            )
        conn.commit()
    log("标签统计更新完成")


def print_summary(db_path: str) -> None:
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        log("=== 数据库当前记录数 ===")
        for t in ["molecules", "materials", "literature", "news", "users"]:
            try:
                n = cursor.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
                log(f"  {t}: {n}")
            except sqlite3.Error:
                pass

    log("=== 本地 JSON 文件记录数 ===")
    for label, path in [
        ("molecules", MOLECULES_FILE),
        ("literature", LITERATURE_FILE),
        ("materials", MATERIALS_FILE),
    ]:
        if path.exists():
            log(f"  {label}: {len(load_json_list(path))} ({path})")
