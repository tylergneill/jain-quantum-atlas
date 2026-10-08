"""The two catalogues + the sizes -> docs/data/tree.json. Offline.

**The universe is the union of the two catalogues on `srno`**: every item the
jainelibrary.org API lists, plus the rows only Quantum has (the Āgama shelf,
audio, JAINA material). Provisional -- the todo's phase-0 item is still open
-- but it is the sibling pattern: E-bhāratīsampat counts its PDF-only works
and lets `text_count` fall below `count`, and this collection has the same
shape, with the post-2022 accessions standing where the scans stand there.

One work per item:

    id, serial        the six-digit sr_no (serial as int, for sort order)
    title             the API's English title, else Quantum's; `title_native`
                      the Devanāgarī/Gujarati one where either has it
    domain            the item type (Books, Manuscripts, Magazines, Articles,
                      Audio, Āgama shelf, JAINA Education, Other)
    sub_domain        the catalogue's `language` string
    author            API author, else sutra_author, else Quantum's
    text              "quantum" when Quantum has a booktext for it -- a sized
                      catalog row not journalled empty -- else null
    pdf               the API lists a Standard PDF, or Quantum's file is a .pdf
    sizes             from data/sizes.jsonl, where the text was fetched and measured
    has_text          the clean text is on this machine (data/text_extract/)
    added             web_date as YYYY-MM-DD
    ocr_docx          the API lists an OCR Word doc (login-gated, not fetched)
    sources           ["api", "quantum"] -- which catalogues know the item

`all_stats` is `shape.summarize` plus `quantum_text_count`, `api_count`,
`quantum_count` and `last_changed` (the newest web_date).

    make build
"""

import argparse
import glob
import json
import re
from pathlib import Path

from pipeline.config import (API_CACHE_DIR, CATALOGUE_PATH, DOCS_DIR, SIZES_PATH,
                             TEXT_EXTRACT_DIR, TEXT_LOG_PATH, TREE_PATH)
from pipeline.shape import build_axes, report, write

DOMAIN_OF_ENDPOINT = {"books": "Books", "articles": "Articles", "magazines": "Magazines",
                      "manuscripts": "Manuscripts", "audio": "Audio"}
DOMAIN_OF_FOLDER = {"book": "Books", "article": "Articles", "magazine": "Magazines",
                    "manuscript": "Manuscripts", "audio_file": "Audio", "agam": "Āgama shelf",
                    "jaina_edu": "JAINA Education"}

_SIZE_RE = re.compile(r"^\s*([\d.]+)\s*(B|K|KB|M|MB|G|GB)\s*$", re.I)


def load_api(cache: Path) -> dict[str, dict]:
    items: dict[str, dict] = {}
    for ep, domain in DOMAIN_OF_ENDPOINT.items():
        for f in sorted(glob.glob(str(cache / f"{ep}_p*.json"))):
            for r in json.load(open(f, encoding="utf-8"))["results"]:
                r["_domain"] = domain
                items.setdefault(str(r["id"]), r)
    return items


def load_quantum(path: Path) -> dict[str, dict]:
    if not path.exists():
        return {}
    return {r["srno"]: r for r in (json.loads(l) for l in path.open(encoding="utf-8") if l.strip())}


def load_sizes(path: Path) -> dict[str, dict]:
    if not path.exists():
        return {}
    out = {}
    for line in path.open(encoding="utf-8"):
        if line.strip():
            r = json.loads(line)
            out[r["srno"]] = r
    return out


def empty_from_journal(path: Path) -> set[str]:
    """Items whose booktext came back empty: a sized catalog row with no text."""
    empties = set()
    if not path.exists():
        return empties
    for line in path.open(encoding="utf-8"):
        if line.strip():
            r = json.loads(line)
            if "chars" in r:
                (empties.add if r["chars"] == 0 else empties.discard)(r["srno"])
    return empties


def web_date(v) -> str | None:
    s = str(int(v)) if isinstance(v, (int, float)) else str(v or "")
    return f"{s[:4]}-{s[4:6]}-{s[6:8]}" if re.fullmatch(r"(19|20)\d{6}", s) else None


def make_work(srno: str, api: dict | None, q: dict | None, sizes: dict | None,
              empty: set[str], on_disk: set[str]) -> dict:
    title = (api or {}).get("title_en") or (q or {}).get("title") or srno
    native = (api or {}).get("title_native") or (q or {}).get("title_lang")
    language = (api or {}).get("language") or (q or {}).get("language") or ""
    domain = (api or {}).get("_domain") or DOMAIN_OF_FOLDER.get((q or {}).get("master_folder") or "", "Other")
    author = ((api or {}).get("author") or (api or {}).get("sutra_author")
              or (q or {}).get("author") or (q or {}).get("sutra_author") or None)
    q_sized = bool(q and (q.get("file_size") or "").strip())
    text = "quantum" if (q_sized and srno not in empty) else None
    api_files = [it["file_type"] for it in ((api or {}).get("download_items") or [])]
    pdf = ("Standard PDF" in api_files) or bool(q and (q.get("filename") or "").lower().endswith(".pdf"))
    work = {
        "id": srno, "serial": int(srno) if srno.isdigit() else 0,
        "title": title, "domain": domain,
        "sub_domain": language or None,
        "author": author or None,
        "language": language or None,
        "text": text, "pdf": pdf,
        "sources": [s for s, present in (("api", api), ("quantum", q)) if present],
    }
    if native and native != title:
        work["title_native"] = native
    if api:
        if api.get("publication_year"):
            work["publish_year"] = str(api["publication_year"])
        if api.get("pages"):
            work["pages"] = int(api["pages"])
        if api.get("classification"):
            work["classification"] = api["classification"]
        if web_date(api.get("web_date")):
            work["added"] = web_date(api.get("web_date"))
        if "OCR docx" in api_files:
            work["ocr_docx"] = True
        if api.get("publisher_name"):
            work["publisher"] = api["publisher_name"]
    elif q:
        if q.get("pub_year"):
            work["publish_year"] = str(q["pub_year"])
        if q.get("num_pages"):
            work["pages"] = int(q["num_pages"])
        if q.get("classification"):
            work["classification"] = q["classification"]
    if sizes and sizes.get("chars"):
        work["sizes"] = {k: sizes[k] for k in ("raw_bytes", "content_bytes", "transliterated_bytes")}
        work["sizes"]["pages"] = sizes.get("pages")
        work["sizes"]["devanagari_chars"] = sizes.get("devanagari_chars")
    if srno in on_disk:
        work["has_text"] = True
    return work


def stamp_version(works: list[dict]) -> str | None:
    """docs/VERSION: __content_version__ is the newest accession the data saw."""
    newest = max((w.get("added") or "" for w in works), default="")
    path = DOCS_DIR / "VERSION"
    lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
    kv = {l.split("=")[0].strip(): l for l in lines if "=" in l}
    from datetime import date
    kv.setdefault("__code_version__", '__code_version__ = "0.1.0"')
    kv["__data_version__"] = f'__data_version__ = "{date.today().isoformat()}"'
    if newest:
        kv["__content_version__"] = f'__content_version__ = "{newest}"'
    path.write_text("\n".join(kv[k] for k in ("__code_version__", "__data_version__", "__content_version__") if k in kv) + "\n",
                    encoding="utf-8")
    return newest or None


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--api-cache", type=Path, default=API_CACHE_DIR)
    parser.add_argument("--catalogue", type=Path, default=CATALOGUE_PATH)
    parser.add_argument("--sizes", type=Path, default=SIZES_PATH)
    parser.add_argument("--out", type=Path, default=TREE_PATH)
    args = parser.parse_args()

    api = load_api(args.api_cache)
    quantum = load_quantum(args.catalogue)
    sizes = load_sizes(args.sizes)
    empty = empty_from_journal(TEXT_LOG_PATH)
    on_disk = {p.stem for p in TEXT_EXTRACT_DIR.glob("*.txt")} if TEXT_EXTRACT_DIR.is_dir() else set()
    if not api and not quantum:
        raise SystemExit("neither the API cache nor data/catalogue.jsonl is present")
    print(f"api items {len(api)}   quantum rows {len(quantum)}   sized {len(sizes)}   "
          f"journalled empty {len(empty)}   text on disk {len(on_disk)}")

    srnos = sorted(set(api) | set(quantum))
    works = [make_work(s, api.get(s), quantum.get(s), sizes.get(s), empty, on_disk) for s in srnos]
    extra = {
        "api_count": len(api),
        "quantum_count": len(quantum),
        "quantum_text_count": sum(1 for w in works if w["text"]),
        "last_changed": max((w.get("added") or "" for w in works), default=None) or None,
    }
    tree = build_axes(works, "api+quantum", extra)
    write(tree, args.out)
    report(tree, args.out)
    if stamped := stamp_version(works):
        print(f"  content version: {stamped} (newest accession)")


if __name__ == "__main__":
    main()
