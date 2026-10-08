# todo

The spine of the backlog. Every open item lives here, grouped by phase; the
other files in `notes/` are the evidence behind these items, not separate lists.

**Terms** (shared with the other Atlases, stated in rivulet's `CLAUDE.md`):
single-threaded, one request per 2 s start-to-start, contact-bearing UA, stop
on 429/5xx, resumable cache. Nothing here logs in to jainelibrary.org.

## Phase 0 — decide the scope

- [ ] **Which items are the Atlas's "texts"?** The sibling Atlases count items
      with searchable text (`text_count`). Here the candidates are: items with
      a Quantum booktext (26,804 of 33,048 on the seeding day), items with an
      API "OCR docx" (25,663), or the intersection. Decide, and write the
      definition into `build_tree` before anything publishes a count.
- [ ] **Sanskrit scope.** `language` contains Sanskrit on 7,760 API items
      (books 6,285, manuscripts 889, magazines 583, articles 3) and 5,592
      Quantum rows; Sanskrit-only is 2,347 / 2,409. Most "Sanskrit, Hindi"
      books are a Sanskrit text with Hindi translation or commentary — the
      Sanskrit share of such a text is unknown until the OCR text is measured
      (the 22-item sample ran 55% Devanāgarī characters). Decide whether the
      Atlas is Sanskrit-only, Sanskrit-and-Prakrit, or the whole collection
      with language as a filter. The last matches how the siblings work.
- [ ] **Sanskrit inside Devanāgarī.** Most any-Sanskrit books are "Sanskrit,
      Hindi": root text plus Hindi translation or commentary in the same
      script. Script counting cannot separate them, so a real Sanskrit byte
      figure needs language identification within Devanāgarī text (per page
      or per line). None of the sibling Atlases faced this. The Sanskrit-only
      slice (2,347 API items / 2,409 Quantum rows) sidesteps it and is the
      clean first comparison.
- [x] **Which text source for the Sanskrit-only fetch.** Decided 2026-10-07:
      Quantum booktext (no account, Cloudflare clearance only). The API's OCR
      docx route needs a login and a download endpoint never located, and
      downloads there appear to be logged per user.
- [x] **Coverage mismatch between the sites.** Measured 2026-10-07 (see
      `site-structure.md`, "Growth"): 31,049 items in both; Quantum's 1,999
      extra are the Āgama shelf, audio and JAINA material; the API's 8,539
      extra are almost entirely 2023–2026 accessions. Quantum is a snapshot
      ending in 2022.
- [ ] **Decide the universe in light of that.** Options: (a) the Atlas is
      the Quantum snapshot, with text, and says the library has grown ~8.5k
      items since; (b) the Atlas is the API's live catalogue, with text for
      the pre-2023 part only, and `text_count` < `count` as in
      E-bhāratīsampat's PDF-only works. (b) matches the sibling pattern and
      keeps the growth chart honest. Either way `web_date` is the changelog
      axis and the API pull must be repeated periodically — the only
      recurring fetch this Atlas would have.
- [ ] **Language grouping must be era-proof.** The `language` string's
      convention shifted around 2023 (plain `Sanskrit` → `Sanskrit, Hindi`).
      Publish any-Sanskrit as the headline Sanskrit figure; keep
      Sanskrit-only as a filter with a note, not as a series.
- [ ] **The Āgama index.** `api/agam/` is 60,880 sutra rows pointing at
      mool/translation docx files by `sr_no`. Enumerating its distinct files
      (~120 requests) would give the canon's file list and the Prakrit
      mool texts; not yet pulled. Decide whether it is a branch of the tree or
      a separate axis.

## Phase 1 — acquisition (rivulet)

- [x] **Quantum catalog fetcher and booktext fetcher** —
      `rivulet/extract/jainquantum/`, on `http`/`pacing`/`cache`/`journal`,
      with Cloudflare clearance via `rivulet.clearance` (2026-10-07). The
      harvested `cf_clearance` cookie works on plain urllib requests with the
      same UA. Catalog fetched (34 pages, 33,048 distinct srno); Sanskrit-only
      text fetch (1,974 items) ran the same evening in 73 minutes: 1,974
      fetched, 0 errors, 12 empty (007833–007843 and 035329), 978 M
      characters over 569,653 pages (~1,720 a page), 2.4 GB of JSON in
      `data/fulltext_cache/`. Next slice: `--languages any-sanskrit` adds
      2,645 items, ~1h40m.
- [ ] **Promote the recon pull script** at
      `rivulet/notes/scratch/jain-elibrary-metadata-pull.py` into
      `rivulet/extract/jainelibrary/fetch_metadata.py`, behind the shared
      `http`/`pacing`/`cache`/`journal` machinery, with a `pipeline/fetch.py`
      shim here that exits 2 without rivulet. Dedupe on `id` (ordering is not
      stable across pages — see `site-structure.md`).
- [x] **`extract-text`** (2026-10-07): rules in `pipeline/text_measure.py`,
      writer in `rivulet/extract/jainquantum/text_extractor.py`, shim in
      `pipeline/fulltext.py`. 1,961 items written in 18 s, 13 empty. Pages
      separated by form feeds; the script as served (IAST on request). The
      furniture patterns are conservative — cover-page OCR noise stays, and
      only whole-line library stamps and bare page numbers go.
- [ ] **Furniture audit.** Sample 50 extracted texts and list the recurring
      non-content lines the patterns miss (running headers, the
      "Shri Mahavir Jain Aradhana Kendra" variants OCR'd with Devanāgarī
      noise, which the Indic-character guard currently keeps).
- [x] **Test the has-text rule.** Broken within the first 600 fetches: serials
      007833–007843 (one batch of 11) have a size and page count but empty
      text. Recorded in `site-structure.md`. Consequence for phase 2: an
      item "has text" when its journal row has `chars > 0`, never when the
      catalog has a size. Re-count exceptions when the run finishes.
- [ ] **Confirm whether the booktext route ignores the title segment.** If it
      does, URLs can be derived from `srno` alone and the index ships ids,
      not URLs.

## Phase 2 — the Atlas

- [ ] `parse_metadata` — API cache → one record per `sr_no`, joined with the
      Quantum row on `srno`; parse `file_size` strings (unit precision only —
      sums are approximate), `web_date`, `language` into a list.
- [ ] Category normalisation in the pipeline: fold classification typos,
      split comma-joined slugs, keep the per-Āgama slugs as the fine axis.
- [x] `count_sizes` over the cache (2026-10-07) — raw / content / IAST bytes
      plus Devanāgarī, Gujarati and Latin counts per item, in
      `data/sizes.jsonl`. Figures in `recon/figures-2026-10-07.md` once the
      first run completes.
- [ ] `build_tree` → `docs/data/tree.json` with `all_stats` — at least
      `count`, `text_count`, `pdf_count`, `sized`, `transliterated_bytes`,
      `last_changed` — in the shape `collect_atlas_counts.py` reads.
- [ ] `changelog` from `web_date` (monthly, cumulative) — growth of what is
      online, not of what was written; say so.
- [ ] Register the Atlas in `sagara-sangama` (`ATLASES` in
      `collect_atlas_counts.py`, the Makefile delegations, a fourth colour).

## Seeding-day loose ends

- [x] Pull the five item endpoints (done 2026-10-07; cache under `data/`).
- [ ] Dedupe check: 2 books ids were never seen across the 44 pages; refetch
      with a stable `ordering=` parameter if DRF exposes one (`?ordering=id`
      untested).
- [x] The Quantum catalog walk ran inside a browser tab and its rows were not
      saved. Replaced the same evening by `make fetch-catalog`; the figures
      in `recon/` match `make parse-catalog`'s table exactly.
