import json, glob, re
# srno -> (fullText chars, devanagari chars, pages in text) measured from Quantum booktext on 2026-10-07
Q = {'001014':(271996,192907,250),'001050':(365047,12780,302),'001069':(831410,628918,339),
     '002679':(523658,381629,266),'022358':(282183,201002,222),'001109':(1185195,953966,401),
     '090001':(464443,336801,270),'034181':(21173,15574,14),'016030':(1339639,937603,790),
     '022377':(445145,32590,240),'600381':(497346,355397,320),'600435':(619039,481321,328),
     '035040':(627022,447639,394),'006332':(1615203,1018198,764),'021005':(484413,311029,300),
     '521039':(150493,114042,96),'250107':(25094,923,6),'230273':(22838,1,10),'330064':(1693,0,2),
     '000008':(3299,0,2)}
def parse(s):
    m = re.match(r'^\s*([\d.]+)\s*(B|K|KB|M|MB|G|GB)\s*$', s or '', re.I)
    return float(m.group(1)) * {'B':1,'K':1e3,'M':1e6,'G':1e9}[m.group(2).upper()[0]] if m else None
recs = {}
for f in glob.glob('data/metadata_cache/jainelibrary/*_p*.json'):
    for r in json.load(open(f))['results']:
        if r['id'] in Q: recs[r['id']] = r
print(f"{'srno':7s} {'folder':11s} {'lang':22s} {'pages':>5s} {'textK':>7s} {'devK':>6s} {'ocrdocx':>8s} {'tocdocx':>8s} {'stdpdf':>7s} {'Qsize':>6s} | chars/docxB  dev/docxB")
rows = []
for s, (chars, dev, tp) in Q.items():
    r = recs.get(s)
    if not r: print(s, 'not in cache'); continue
    di = {it['file_type']: parse(it.get('file_size')) for it in r.get('download_items') or []}
    raw = {it['file_type']: it.get('file_size') for it in r.get('download_items') or []}
    ocr = di.get('OCR docx'); toc = di.get('TOC docx') or di.get('DOCX')
    ratio = chars/ocr if ocr else None; dratio = dev/ocr if ocr else None
    rows.append((s, ocr, chars, dev))
    print(f"{s:7s} {r.get('master_folder'):11s} {(r.get('language') or '')[:22]:22s} {r.get('pages') or 0:5.0f} {chars/1e3:7.0f} {dev/1e3:6.0f} {raw.get('OCR docx') or '-':>8s} {raw.get('TOC docx') or raw.get('DOCX') or '-':>8s} {raw.get('Standard PDF') or '-':>7s} {'':>6s} | {ratio if ratio else float('nan'):10.2f} {dratio if dratio else float('nan'):10.2f}")
have = [(c, o, d) for s, o, c, d in rows if o]
print('\nitems with OCR docx:', len(have), 'of', len(rows))
print('sum chars / sum docx bytes = %.2f' % (sum(c for c,o,d in have)/sum(o for c,o,d in have)))
print('sum devanagari / sum docx bytes = %.2f' % (sum(d for c,o,d in have)/sum(o for c,o,d in have)))
rs = sorted(c/o for c,o,d in have); print('per-item chars/byte: min %.2f median %.2f max %.2f' % (rs[0], rs[len(rs)//2], rs[-1]))
