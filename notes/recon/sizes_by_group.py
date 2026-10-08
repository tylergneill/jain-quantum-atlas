import json, re, glob, collections
def parse(s):
    m = re.match(r'^\s*([\d.]+)\s*(B|K|KB|M|MB|G|GB)\s*$', s or '', re.I)
    return float(m.group(1)) * {'B':1,'K':1e3,'M':1e6,'G':1e9}[m.group(2).upper()[0]] if m else None
def toks(r): return {x.strip() for x in (r.get('language') or '').split(',') if x.strip()}
groups = {'all': lambda t: True, 'any Sanskrit': lambda t: 'Sanskrit' in t, 'Sanskrit-only': lambda t: t == {'Sanskrit'},
          'any Prakrit': lambda t: 'Prakrit' in t, 'Sanskrit or Prakrit': lambda t: bool(t & {'Sanskrit','Prakrit'})}
grand = {g: collections.defaultdict(lambda: [0,0,0.0]) for g in groups}  # type -> [items, entries, bytes]
for ep in ['books','manuscripts','magazines','articles','audio']:
    rs = {}; 
    for f in sorted(glob.glob(f'data/metadata_cache/jainelibrary/{ep}_p*.json')):
        for r in json.load(open(f))['results']: rs.setdefault(r['id'], r)
    rs = list(rs.values())
    print(f'\n== {ep} ({len(rs)} items)')
    for g, fn in groups.items():
        sub = [r for r in rs if fn(toks(r))]
        if not sub: continue
        by = collections.defaultdict(lambda: [0,0,0.0]); total = 0.0; unsized = 0
        for r in sub:
            seen = set()
            for it in r.get('download_items') or []:
                t = it['file_type']; b = parse(it.get('file_size'))
                by[t][1] += 1
                if t not in seen: by[t][0] += 1; seen.add(t)
                if b is None: unsized += 1
                else: by[t][2] += b; total += b
            for t in seen: grand[g][t][0] += 1
            for it in r.get('download_items') or []:
                b = parse(it.get('file_size')); grand[g][it['file_type']][1] += 1
                if b is not None: grand[g][it['file_type']][2] += b
        line = ', '.join(f"{t} {v[2]/1e9:.2f} GB ({v[0]} items)" for t, v in sorted(by.items(), key=lambda kv: -kv[1][2]) if v[2] > 0.005e9)
        print(f'  {g:20s} items={len(sub):6d}  ALL FILES {total/1e9:8.2f} GB  unsized={unsized:4d}  | {line}')
print('\n== ALL ENDPOINTS COMBINED')
for g in groups:
    total = sum(v[2] for v in grand[g].values())
    line = ', '.join(f"{t} {v[2]/1e9:.2f} GB ({v[0]} items)" for t, v in sorted(grand[g].items(), key=lambda kv: -kv[1][2]) if v[2] > 0.005e9)
    print(f'  {g:20s} ALL FILES {total/1e9:8.2f} GB | {line}')
