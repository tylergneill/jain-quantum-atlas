import json, sys, re, glob, collections
ep = sys.argv[1]
files = sorted(glob.glob(f'data/metadata_cache/jainelibrary/{ep}_p*.json'))
rs = []; total = None
for f in files:
    d = json.load(open(f)); total = d['count']; rs += d['results']
ids = {r['id'] for r in rs}
print(f'== {ep}: {len(rs)} records in {len(files)} pages, api count={total}, distinct ids={len(ids)}')
def parse(s):
    m = re.match(r'^\s*([\d.]+)\s*(B|K|KB|M|MB|G|GB)\s*$', s or '', re.I)
    if not m: return None
    return float(m.group(1)) * {'B':1,'K':1e3,'M':1e6,'G':1e9}[m.group(2).upper()[0]]
cls = collections.Counter(); cat = collections.Counter(); ft = collections.Counter(); ftbytes = collections.defaultdict(float); ftn = collections.Counter()
mf = collections.Counter(); lang = collections.Counter(); script = collections.Counter()
items_with = collections.Counter(); nodl = 0; unparsed = collections.Counter(); ncat = collections.Counter()
pages_sum = 0; pages_n = 0; active = collections.Counter(); copyright_ = collections.Counter(); has_text_doc = 0
for r in rs:
    cls[r.get('classification')] += 1
    cs = r.get('categories') or []
    ncat[len(cs)] += 1
    for c in cs: cat[c['slug']] += 1
    mf[r.get('master_folder')] += 1
    lang[r.get('language')] += 1
    script[r.get('script')] += 1
    active[r.get('is_active')] += 1
    copyright_[r.get('copyright')] += 1
    if r.get('pages'): pages_sum += r['pages']; pages_n += 1
    di = r.get('download_items') or []
    if not di: nodl += 1
    types = set()
    for it in di:
        t = it['file_type']; types.add(t); ft[t] += 1
        b = parse(it.get('file_size'))
        if b is None: unparsed[repr(it.get('file_size'))] += 1
        else: ftbytes[t] += b; ftn[t] += 1
    for t in types: items_with[t] += 1
    if any('docx' in t.lower() or 'doc' == t.lower() for t in types): has_text_doc += 1
print('items with no download_items:', nodl)
print('items with >=1 docx-type file:', has_text_doc)
print('items having each file_type:', items_with.most_common())
print('file entries by type (n, GB parsed, mean MB):')
for t, n in ft.most_common():
    print(f'   {t:20s} entries={n:6d} sized={ftn[t]:6d} total={ftbytes[t]/1e9:8.2f} GB mean={(ftbytes[t]/ftn[t]/1e6 if ftn[t] else 0):7.2f} MB')
print('total parsed GB:', sum(ftbytes.values())/1e9, 'unparsed size strings:', sum(unparsed.values()), unparsed.most_common(5))
print('pages: n', pages_n, 'sum', pages_sum)
print('n categories per item', dict(ncat))
print('classification top 40:', cls.most_common(40))
print('category slugs top 40:', cat.most_common(40))
print('distinct classification values:', len(cls), 'distinct category slugs:', len(cat))
print('master_folder', mf.most_common())
print('language top 20', lang.most_common(20))
print('script', script.most_common(12))
print('is_active', active, 'copyright', copyright_)
json.dump({'ep': ep, 'n': len(rs), 'count': total, 'classification': cls.most_common(), 'categories': cat.most_common(), 'file_types': ft.most_common(), 'items_with': items_with.most_common(), 'bytes_by_type': dict(ftbytes), 'master_folder': mf.most_common(), 'language': lang.most_common(), 'script': script.most_common(), 'pages_sum': pages_sum, 'pages_n': pages_n}, open(f'notes/recon/summary_{ep}.json','w'), ensure_ascii=False, indent=1)
