"""The cached Quantum catalog -> `data/catalogue.jsonl`, one row per item.

Offline: reads `data/metadata_cache/jainqq/catalog_pNNNN.json` (written by
`make fetch-catalog`) and nothing else. Public, and importable without rivulet,
because the text fetcher in rivulet reads the catalogue through this module:
the definitions of "has text" and of the language selectors live here, once,
so the fetcher's queue and the Atlas's counts cannot drift apart.

**Dedupe on `srno`.** Pages are not exactly 1000 rows and the site's ordering
is not promised stable, so the first occurrence of a serial wins and a count is
a count of distinct serials, never pages × 1000.

**`language` is the string.** `"Sanskrit, Hindi"` splits on commas into
tokens; the selectors test those. `Sanskrit-only` means the token set is
exactly {Sanskrit}. (On the API side the `languages[]` array is misleading --
it folds the script in -- but Quantum's catalog only has the string.)

**`has_text` is the blank-size rule.** A row with a non-blank `file_size` had
a booktext on every sampled item on 2026-10-07; a blank one had none. The
fetcher journals the character count of every fetch so the rule keeps being
tested.

    make parse-catalog            # write catalogue.jsonl and print the groups
"""

import argparse
import json
import re
from collections import Counter
from pathlib import Path

from pipeline.config import CATALOG_CACHE_DIR, CATALOGUE_PATH

# Fields kept per row. Everything in the page is kept in the cache; this is
# what downstream stages read.
FIELDS = ("srno", "title", "title_lang", "language", "script", "classification",
          "num_pages", "file_size", "filename", "master_folder", "sub_folder",
          "author", "sutra_author", "editor", "translator", "publisher",
          "pub_year", "download_count")

_SIZE_RE = re.compile(r"^\s*([\d.]+)\s*(B|K|KB|M|MB|G|GB)\s*$", re.I)
_UNIT = {"B": 1, "K": 1e3, "M": 1e6, "G": 1e9}


def language_tokens(row: dict) -> set[str]:
    return {t.strip() for t in (row.get("language") or "").split(",") if t.strip()}


def has_text(row: dict) -> bool:
    return bool((row.get("file_size") or "").strip())


def parse_size(text: str | None) -> float | None:
    """`"120 MB"` -> bytes, to the unit's precision; None if unparseable."""
    match = _SIZE_RE.match(text or "")
    if not match:
        return None
    return float(match.group(1)) * _UNIT[match.group(2).upper()[0]]


# The one vocabulary for "which rows". Used by `make fetch-text --languages`
# and by every count this Atlas publishes about a language slice.
SELECTORS = {
    "all": lambda r: True,
    "sanskrit-only": lambda r: language_tokens(r) == {"Sanskrit"},
    "any-sanskrit": lambda r: "Sanskrit" in language_tokens(r),
    "any-prakrit": lambda r: "Prakrit" in language_tokens(r),
    "sanskrit-or-prakrit": lambda r: bool(language_tokens(r) & {"Sanskrit", "Prakrit"}),
}


def load_pages(cache_dir: Path) -> list[dict]:
    pages = sorted(cache_dir.glob("catalog_p*.json"))
    if not pages:
        raise SystemExit(f"no catalog pages under {cache_dir}\n"
                         f"Run `make fetch-catalog` first.")
    return [json.loads(p.read_text(encoding="utf-8")) for p in pages]


def rows_from_pages(pages: list[dict]) -> list[dict]:
    """Distinct rows, first occurrence of each `srno` winning, in page order."""
    seen: set[str] = set()
    rows = []
    for page in pages:
        for entry in page.get("entries") or []:
            srno = entry.get("srno")
            if not srno or srno in seen:
                continue
            seen.add(srno)
            rows.append({k: entry.get(k) for k in FIELDS})
    return rows


def load_catalogue(path: Path) -> list[dict]:
    if not path.exists():
        raise SystemExit(f"no catalogue at {path}\n"
                         f"Run `make parse-catalog` first.")
    return [json.loads(line) for line in path.open(encoding="utf-8") if line.strip()]


def summarize(rows: list[dict]) -> str:
    lines = [f"{'selector':20s} {'rows':>6s} {'with text':>9s} {'pages':>10s} "
             f"{'file_size GB':>12s}"]
    for name, select in SELECTORS.items():
        sub = [r for r in rows if select(r)]
        texty = [r for r in sub if has_text(r)]
        pages = sum((r.get("num_pages") or 0) for r in texty)
        gb = sum((parse_size(r.get("file_size")) or 0) for r in texty) / 1e9
        lines.append(f"{name:20s} {len(sub):6d} {len(texty):9d} {pages:10.0f} "
                     f"{gb:12.1f}")
    folders = Counter(r.get("master_folder") for r in rows)
    lines.append("\nmaster_folder: " + ", ".join(
        f"{k} {v}" for k, v in folders.most_common()))
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--cache", type=Path, default=CATALOG_CACHE_DIR)
    parser.add_argument("--out", type=Path, default=CATALOGUE_PATH)
    args = parser.parse_args()

    pages = load_pages(args.cache)
    rows = rows_from_pages(pages)
    total_entries = sum(len(p.get("entries") or []) for p in pages)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"pages: {len(pages)}   entries: {total_entries}   "
          f"distinct srno: {len(rows)}")
    print(f"wrote: {args.out}\n")
    print(summarize(rows))


if __name__ == "__main__":
    main()
