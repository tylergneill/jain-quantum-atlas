"""data/fulltext_cache/ -> data/sizes.jsonl: the three byte counts per item. No network.

Sizes are a pure function of the cached text, so they are derived here,
locally and repeatably, never as a side effect of fetching. The cleaning is
`text_measure.clean_pages`, the same function the extractor writes with, so
the figures describe the text a reader would get.

    raw_bytes             the cached JSON as served (escaped Unicode, so ~2.5x the text)
    content_bytes         UTF-8 of the cleaned text, furniture removed
    transliterated_bytes  the same with its Devanāgarī as IAST

plus `pages`, `chars`, and the script breakdown (`devanagari_chars`,
`gujarati_chars`, `latin_letters`) this corpus needs because it is mixed.

Transliteration is the cost: skrutable ran at ~1.3 M Devanāgarī characters a
second on the seeding machine, so the Sanskrit-only slice is ~15 minutes
single-threaded. A process pool spreads it; `--workers 1` for a quiet
machine. Items already in the output are skipped unless `--refresh`.

    make count-sizes
    make count-sizes WORKERS=4
"""

import argparse
import json
import os
import sys
from multiprocessing import Pool
from pathlib import Path

from pipeline.config import FULLTEXT_CACHE_DIR, SIZES_PATH
from pipeline.text_measure import measure


def _one(path: Path) -> dict:
    raw = path.read_bytes()
    try:
        full = json.loads(raw).get("pageProps", {}).get("fullText") or ""
    except json.JSONDecodeError:
        full = ""
    rec = measure(full, len(raw))
    rec["srno"] = path.stem
    return rec


def _load(path: Path) -> dict[str, dict]:
    rows: dict[str, dict] = {}
    if path.exists():
        for line in path.open(encoding="utf-8"):
            if line.strip():
                r = json.loads(line)
                rows[r["srno"]] = r
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--cache", type=Path, default=FULLTEXT_CACHE_DIR)
    parser.add_argument("--out", type=Path, default=SIZES_PATH)
    parser.add_argument("--workers", type=int,
                        default=max(1, (os.cpu_count() or 2) - 1))
    parser.add_argument("--refresh", action="store_true",
                        help="re-measure items already in the output")
    args = parser.parse_args()

    files = sorted(args.cache.glob("*.json"))
    if not files:
        sys.exit(f"no cache at {args.cache} -- run `make fetch-text` first.")
    if args.refresh and args.out.exists():
        args.out.unlink()
    done = _load(args.out)
    todo = [f for f in files if f.stem not in done]
    print(f"cache: {len(files)} items   measured already: {len(done)}   "
          f"to measure: {len(todo)}   workers: {args.workers}", flush=True)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with args.out.open("a", encoding="utf-8") as handle:
        if args.workers > 1 and todo:
            with Pool(args.workers) as pool:
                for rec in pool.imap_unordered(_one, todo, chunksize=4):
                    handle.write(json.dumps(rec, ensure_ascii=False) + "\n")
                    handle.flush()
                    n += 1
                    if n % 100 == 0 or n == len(todo):
                        print(f"  {n}/{len(todo)}", flush=True)
        else:
            for rec in map(_one, todo):
                handle.write(json.dumps(rec, ensure_ascii=False) + "\n")
                handle.flush()
                n += 1
                if n % 100 == 0 or n == len(todo):
                    print(f"  {n}/{len(todo)}", flush=True)

    rows = list(_load(args.out).values())
    texty = [r for r in rows if r["chars"]]

    def tot(key: str) -> int:
        return sum(r[key] for r in rows)

    chars = tot("chars") or 1
    print(f"\nitems: {len(rows)}   with text: {len(texty)}   "
          f"empty: {len(rows) - len(texty)}")
    print(f"pages: {tot('pages'):,}   chars: {tot('chars'):,}")
    print(f"raw_bytes: {tot('raw_bytes')/1e9:.2f} GB   "
          f"content_bytes: {tot('content_bytes')/1e9:.2f} GB   "
          f"transliterated_bytes: {tot('transliterated_bytes')/1e9:.2f} GB")
    d, g, l = tot("devanagari_chars"), tot("gujarati_chars"), tot("latin_letters")
    print(f"script: devanagari {d/1e6:.0f} M ({100*d/chars:.0f}%)   "
          f"gujarati {g/1e6:.1f} M   latin letters {l/1e6:.0f} M")
    print(f"wrote: {args.out}")


if __name__ == "__main__":
    main()
