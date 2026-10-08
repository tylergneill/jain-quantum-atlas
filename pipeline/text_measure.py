"""Pure text handling: the cached booktext JSON -> pages -> clean text -> counts.

No network, no I/O. Everything that knows what Quantum's text looks like is
here, once, so that the two consumers cannot drift apart:

    pipeline/count_sizes.py                              measures (this repo, public)
    rivulet/extract/jainquantum/text_extractor.py        writes the text out (private)

rivulet imports from this module; this repo never imports rivulet. That is
the same publishing boundary E-bhāratīsampat draws with its `text_measure.py`.

## What a cached file holds

The data route's `pageProps.fullText`: one string, pages introduced by an
anchor and a dashed rule, and each page body opening with a BOM and a run of
underscores -- the OCR vendor's page marker:

    <a href="https://jainqq.org/explore/<srno>/<n>">Page #n</a>
    ------------------------------------------------------------
    ﻿________________\r\n
    <the page's OCR text>

## What is furniture

Measured over 40 random Sanskrit-only items, 12,443 pages (2026-10-07). The
page marker is on 93% of pages. The rest of the recurring lines are the
digitising libraries' stamps, OCR'd from the scans and therefore spelled
several ways each:

    Shri Mahavir Jain Aradhana Kendra        (also "Jan")
    www.kobatirth.org
    Acharya Shri Kailassagarsuri Gyanmandir  (also "Kailashsagarsuri", "Kalassagarsun")
    For Private and Personal Use Only        (also "And Personal", "Personel", "& Private")
    Jain Education International
    www.umaragyanbhandar.com
    Aho ! Shrutgyanam

and bare page numbers (a line of ASCII digits, 10,176 of them in the sample).
These are removed by **tolerant whole-line patterns**: a line is furniture
when it consists of nothing but one of these stamps, allowing for OCR
variation. Lines that merely contain a stamp alongside text are kept, because
cutting them would cut content. Verse numbers in Devanāgarī digits (`॥१२॥`)
are content and are kept; so is every line with any Indic character.

**Nothing here is a positive test for Devanāgarī.** Many of these books carry
Gujarati-script or Latin-script passages that are content, and the mixed
"Sanskrit, Hindi" books are the majority of the collection.
"""

import re

PAGE_SPLIT_RE = re.compile(
    r'<a href="[^"]*/explore/\d+/(\d+)">Page #\d+</a>\s*\n-{10,}\s*\n?')

# Whole-line furniture. Each pattern is anchored to the whole (stripped) line
# and written loosely enough to absorb the OCR misreadings seen in the sample.
FURNITURE_RES = tuple(re.compile(p, re.I) for p in (
    r"^[﻿_\s]*_{4,}[\s_]*$",                                   # the page marker
    r"^﻿?$",                                                   # a bare BOM
    r"^shri\s+mahavir\s+ja[i]?n\s+aradhana\s+kendra\W*$",
    r"^(www\.)?kobatirth\.org\W*$",
    r"^acharya\s+shri\s+ka[il]+a[s]+agar\s*sur[in]\s+gyanmandir\W*$",
    r"^for\s+(private\s+(and|&)\s+personal|personal\s+(and|&)\s+private)(\s+use\s+only)?\W*$",
    r"^for\s+private\s+(and|&)\s+persone?l\s+use\s+only\W*$",
    r"^jain\s+education\s+international\W*$",
    r"^(www\.)?umaragyanbhandar\.com\W*$",
    r"^aho\s*!?\s*shrutgyanam\W*$",
    r"^[\d\s.\-()\[\]|/]+$",                                        # a page number, bare or in brackets
    r"^[\W_]+$",                                                    # punctuation only: - . , \"
))

INDIC_RE = re.compile(r"[ऀ-ൿ]")  # Devanāgarī through Malayalam


def pages_from_fulltext(full_text: str) -> list[str]:
    """Split the route's `fullText` into page bodies, in page order.

    Text before the first anchor (normally empty) is discarded. A file with
    no anchors yields `[]`, which is how the twelve sized-but-empty items
    present.
    """
    parts = PAGE_SPLIT_RE.split(full_text or "")
    # split() interleaves the captured page numbers: [pre, n1, body1, n2, body2, ...]
    bodies = parts[2::2]
    return [b.replace("\r\n", "\n").replace("\r", "\n") for b in bodies]


def is_furniture(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return True
    if INDIC_RE.search(stripped):
        # Indic text is never furniture here; the stamps are all Latin. This
        # keeps Devanāgarī verse numbers and anything OCR'd alongside a stamp.
        return False
    return any(p.match(stripped) for p in FURNITURE_RES)


def clean_page(page: str) -> str:
    """A page body with the furniture lines removed and blank runs collapsed."""
    kept = [ln.rstrip() for ln in page.split("\n") if not is_furniture(ln)]
    text = "\n".join(kept)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def clean_pages(full_text: str) -> list[str]:
    return [clean_page(p) for p in pages_from_fulltext(full_text)]


def devanagari_chars(text: str) -> int:
    return sum(1 for ch in text if "ऀ" <= ch <= "ॿ")


def gujarati_chars(text: str) -> int:
    return sum(1 for ch in text if "઀" <= ch <= "૿")


def latin_letters(text: str) -> int:
    return sum(1 for ch in text if ("a" <= ch <= "z") or ("A" <= ch <= "Z"))


_transliterator = None


def to_iast(text: str) -> str:
    """Devanāgarī -> IAST via skrutable, for `transliterated_bytes`.

    Only the Devanāgarī is transliterated; Gujarati-script and Latin passages
    pass through unchanged. That makes the figure "bytes if the Devanāgarī
    were IAST", which is the comparable quantity across the Atlases, where
    the other collections are Devanāgarī or IAST throughout.
    """
    global _transliterator
    if not text.strip():
        return ""
    if _transliterator is None:
        from skrutable.transliteration import Transliterator
        _transliterator = Transliterator()
    return _transliterator.transliterate(text, from_scheme="DEV", to_scheme="IAST")


def measure(full_text: str, raw_bytes: int) -> dict:
    """The sibling trio plus this corpus's script breakdown, for one item."""
    pages = clean_pages(full_text)
    text = "\n\n".join(pages)
    content = text.encode("utf-8")
    return {
        "raw_bytes": raw_bytes,
        "content_bytes": len(content),
        "transliterated_bytes": len(to_iast(text).encode("utf-8")) if text else 0,
        "pages": len(pages),
        "chars": len(text),
        "devanagari_chars": devanagari_chars(text),
        "gujarati_chars": gujarati_chars(text),
        "latin_letters": latin_letters(text),
    }
