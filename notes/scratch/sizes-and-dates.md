# Sizes and dates

Part of a pass across all seven repos, coordinated in
`sagara-sangama/notes/scratch/sizes-and-dates.md` -- read that first for what
was decided and why. This file lists only what is left **here**. Delete it
when the boxes are ticked. Written 2026-10-08.

Branch: `v0`.

## Done here

- Sizes are decimal everywhere (1 MB = 1,000,000 bytes).
- "Scan" is "PDF" throughout the About and tree pages.

## Left here

- [ ] **Publish `all_stats.sourced`** in `docs/data/tree.json`: the date this
      Atlas took its copy of the collection, YYYY-MM-DD. It must be the same
      value `__content_version__` gets in `docs/VERSION`, written in the same
      place, so the two cannot disagree. Do this as part of the
      fix below, in `stamp_version`.
- [ ] Rebuild the tree; commit `tree.json` and `docs/VERSION` together.
- [ ] **First: `__content_version__` is wrong here** (it is the newest
      accession, not the fetch date). Steps in
      [content-version.md](content-version.md); it needs the fetch journals,
      which are not on every machine.
