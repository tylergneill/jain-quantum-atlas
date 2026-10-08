import json, sys, re, collections
d = json.load(open(sys.argv[1]))
rs = d['results']
print('n', len(rs), 'total', d['count'])
cat = collections.Counter(); cls = collections.Counter(); mf = collections.Counter(); ft = collections.Counter(); lang = collections.Counter(); script=collections.Counter()
sizes = []; nodl = 0; ncat = collections.Counter()
for r in rs:
    for c in r.get('categories') or []: cat[c['slug']] += 1
    ncat[len(r.get('categories') or [])] += 1
    cls[r.get('classification')] += 1
    mf[r.get('master_folder')] += 1
    for l in r.get('languages') or []: lang[l['name']] += 1
    script[r.get('script')] += 1
    di = r.get('download_items') or []
    if not di: nodl += 1
    for it in di:
        ft[it['file_type']] += 1
        m = re.match(r'([\d.]+)\s*(KB|MB|GB)', it.get('file_size') or '')
        if m:
            v = float(m.group(1)) * {'KB':1e3,'MB':1e6,'GB':1e9}[m.group(2)]
            sizes.append((it['file_type'], v))
        else:
            sizes.append((it['file_type'], None))
print('categories', cat.most_common(30))
print('n categories per item', ncat)
print('classification', cls.most_common(20))
print('master_folder', mf.most_common())
print('file_type', ft.most_common())
print('languages', lang.most_common(15))
print('script', script.most_common(10))
print('items with no download_items', nodl)
unparsed = [s for s in sizes if s[1] is None]
print('size strings unparsed', len(unparsed), 'of', len(sizes))
print('sample raw size strings', [it.get('file_size') for r in rs[:5] for it in r.get('download_items') or []])
by = collections.defaultdict(list)
for t, v in sizes:
    if v: by[t].append(v)
for t, vs in by.items():
    print(f'{t:20s} n={len(vs):4d} sum={sum(vs)/1e9:8.2f} GB mean={sum(vs)/len(vs)/1e6:7.1f} MB')
pages = [r['pages'] for r in rs if r.get('pages')]
print('pages: n', len(pages), 'sum', sum(pages), 'mean', sum(pages)/len(pages))
print('other keys sample:', {k: rs[0][k] for k in ['pdf_url','file_urls','master_folder','sub_folder','web_date','copyright','is_active','downloads','views']})
