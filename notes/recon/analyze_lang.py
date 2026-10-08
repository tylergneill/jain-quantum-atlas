import json, sys, re, glob, collections
def parse(s):
    m = re.match(r'^\s*([\d.]+)\s*(B|K|KB|M|MB|G|GB)\s*$', s or '', re.I)
    return float(m.group(1)) * {'B':1,'K':1e3,'M':1e6,'G':1e9}[m.group(2).upper()[0]] if m else None
for ep in sys.argv[1:]:
    rs = []; seen = set()
    for f in sorted(glob.glob(f'data/metadata_cache/jainelibrary/{ep}_p*.json')):
        for r in json.load(open(f))['results']:
            if r['id'] in seen: continue
            seen.add(r['id']); rs.append(r)
    def langs(r): return {x.strip() for x in (r.get('language') or '').split(',') if x.strip()}
    def tokens(r):
        t = set()
        for l in langs(r):
            for x in l.split(','): t.add(x.strip())
        return t
    groups = {
      'all': lambda r: True,
      'any Sanskrit': lambda r: 'Sanskrit' in tokens(r),
      'Sanskrit only': lambda r: tokens(r) == {'Sanskrit'},
      'any Prakrit': lambda r: 'Prakrit' in tokens(r),
      'Sanskrit or Prakrit': lambda r: bool(tokens(r) & {'Sanskrit','Prakrit'}),
    }
    print(f'== {ep} ({len(rs)} distinct records)')
    print(f"{'group':20s} {'items':>6s} {'w/ OCR docx':>11s} {'OCR docx GB':>11s} {'w/ any docx':>11s} {'pages sum':>10s} {'std PDF GB':>10s}")
    for g, fn in groups.items():
        sub = [r for r in rs if fn(r)]
        ocr = [r for r in sub if any(it['file_type']=='OCR docx' for it in r.get('download_items') or [])]
        anyd = [r for r in sub if any('docx' in it['file_type'].lower() for it in r.get('download_items') or [])]
        ocr_gb = sum((parse(it.get('file_size')) or 0) for r in sub for it in r.get('download_items') or [] if it['file_type']=='OCR docx')/1e9
        std_gb = sum((parse(it.get('file_size')) or 0) for r in sub for it in r.get('download_items') or [] if it['file_type']=='Standard PDF')/1e9
        pg = sum(r.get('pages') or 0 for r in sub)
        print(f'{g:20s} {len(sub):6d} {len(ocr):11d} {ocr_gb:11.2f} {len(anyd):11d} {pg:10.0f} {std_gb:10.1f}')
    skt = [r for r in rs if 'Sanskrit' in tokens(r)]
    print('  Sanskrit items: language field values:', collections.Counter(r.get('language') for r in skt).most_common(8))
    print('  Sanskrit items: script:', collections.Counter(r.get('script') for r in skt).most_common(6))
    print('  Sanskrit items: classification:', collections.Counter(r.get('classification') for r in skt).most_common(10))
    print('  Sanskrit items: category slugs:', collections.Counter(c['slug'] for r in skt for c in r.get('categories') or []).most_common(25))
