# `__content_version__` should be the fetch date

Written 2026-10-08 on a machine without `data/`, so nothing below was run.
Do it where the fetch journals are, and delete this file when it is done.

## What is wrong

`docs/VERSION` carries `__content_version__ = "2026-06-09"`. That is the
newest accession among the published items (`stamp_version` in
`pipeline/build_tree.py` takes `max(work["added"])`), which is already
published in the right place as `all_stats.last_changed`.

In every other Atlas `__content_version__` means **when our copy was taken**:
Sanskrit Documents and E-bhāratīsampat read it off their fetch journals,
GRETIL records the date of its scrape. Sāgarasaṅgama is about to print it on
the home card as "as of …", and the sibling About pages print it as "data last
sourced". For this Atlas the honest value is the day of the fetch
(2026-10-07 for the first build), not June.

## The fix

1. **`stamp_version`**: take the newest `fetched_at` from the fetch journals
   instead of the newest `added`. Port E-bhāratīsampat's `stamp_version`
   (`pipeline/build_tree.py` there), which already does exactly this and
   handles a missing journal by leaving the old value alone.
2. **Which journals.** There are three sources and only two keep a journal:
   - `data/text_fetch_log.jsonl` (`TEXT_LOG_PATH`), one row per booktext fetch;
   - `data/catalog_fetch_log.jsonl` (`CATALOG_LOG_PATH`), one row per Quantum
     catalog page;
   - the jainelibrary.org API pull, which was a one-off script with **no
     journal**. Its pages are under `data/metadata_cache/jainelibrary/`; if a
     date is wanted from it, the cache files' own dates are all there is, until
     the pull is promoted into rivulet (already in `todo.md`, Phase 1).

   Use the newest `fetched_at` across the two journals. Counts come from the
   catalogues and sizes from the texts, so either being re-fetched makes the
   published figures newer.
3. **`about.html`**: the inline version loader labels this line
   `newest Sanskrit book online: …`, with a comment saying why it is not "last
   sourced". Once the value is a fetch date, change the label back to the
   siblings' `data last sourced: …` and drop the comment.
4. Rebuild (`make build`), check `docs/VERSION`, commit it with the tree.

## The journal's shape, as rivulet writes it

Read from `rivulet/extract/jainquantum/` rather than from a real file, so
**check one line of each journal before trusting this**:

    text_fetch_log.jsonl     {"srno": "001014", "url": "…", "fetched_at": "2026-10-07T21:14:05+00:00",
                              "bytes": …, "chars": …, "pages": …, "catalog_pages": …, "file_size": …}
                             or, on failure: {"srno", "url", "fetched_at", "error"}
    catalog_fetch_log.jsonl  {"page": 1, "rows": 1000, "build_id": "…", "source": "html" | "data",
                              "bytes": …, "fetched_at": "…"}

`fetched_at` is UTC, ISO 8601 to the second, with a `+00:00` offset. Error rows
carry it too, and should count: a failed request still says the fetcher was
running that day. `empty_from_journal` in `build_tree.py` already reads the text
journal line by line and is the pattern to follow.

## Not part of this

The "Where the Text Stops" figures on the About page are computed from the
items' own `added` dates and do not use `__content_version__`; they are
unaffected.
