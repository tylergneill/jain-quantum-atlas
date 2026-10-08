"""web_date -> docs/data/changelog.json: the library's accession series, monthly.

Every API item records the day it went online, so growth here is **measured**
from the catalogue's own stamps rather than inferred -- the one thing this
collection does better than the sibling Atlases. Monthly periods, cumulative,
in E-bhāratīsampat's dict shape, which the aggregator already reads:

    {"granularity": "month", "periods": [
        {"date": "2007-03-01",
         "cumulative_count": ...,            every catalogued item
         "cumulative_text_count": ...,       items with a Quantum booktext
         "cumulative_sized_count": ...,      items whose text was fetched and measured
         "cumulative_iast_bytes_total": ...} IAST bytes over the sized items -- a FLOOR
     ], "undated_works": N}

**`cumulative_text_count` flattens after 2022** because Quantum did; that is
the finding, not an artefact, and the About page should say so. The byte
series covers only what has been fetched (the Sanskrit-only slice on the
seeding day) and is published as the floor it is.

Items only Quantum knows carry no date and are counted under `undated_works`.

    make changelog
"""

import argparse
import json
from collections import defaultdict
from pathlib import Path

from pipeline.config import CHANGELOG_PATH, TREE_PATH


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--tree", type=Path, default=TREE_PATH)
    parser.add_argument("--out", type=Path, default=CHANGELOG_PATH)
    args = parser.parse_args()

    tree = json.loads(args.tree.read_text(encoding="utf-8"))
    works = tree["works"]
    by_month: dict[str, list[dict]] = defaultdict(list)
    undated = 0
    for w in works:
        added = w.get("added")
        if not added:
            undated += 1
            continue
        by_month[added[:7]].append(w)

    periods = []
    c_all = c_text = c_sized = c_bytes = 0
    for month in sorted(by_month):
        ws = by_month[month]
        c_all += len(ws)
        c_text += sum(1 for w in ws if w.get("text"))
        sized = [w for w in ws if w.get("sizes")]
        c_sized += len(sized)
        c_bytes += sum(w["sizes"].get("transliterated_bytes", 0) for w in sized)
        periods.append({
            "date": f"{month}-01",
            "added": len(ws),
            "cumulative_count": c_all,
            "cumulative_text_count": c_text,
            "cumulative_sized_count": c_sized,
            "cumulative_iast_bytes_total": c_bytes,
        })

    out = {
        "granularity": "month",
        "source": "jainelibrary.org API web_date, the day each item went online",
        "periods": periods,
        "undated_works": undated,
        "note": ("cumulative_text_count counts items with a Jain Quantum booktext and "
                 "flattens after 2022, when Quantum's index stopped; "
                 "cumulative_iast_bytes_total covers only the items fetched and measured "
                 "so far and is a floor."),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    last = periods[-1] if periods else {}
    print(f"wrote {args.out}: {len(periods)} months, {periods[0]['date'] if periods else '-'} .. "
          f"{last.get('date')}; final count {last.get('cumulative_count')}, text "
          f"{last.get('cumulative_text_count')}, sized {last.get('cumulative_sized_count')}, "
          f"undated {undated}")


if __name__ == "__main__":
    main()
