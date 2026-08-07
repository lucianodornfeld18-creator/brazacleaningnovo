import os, re, json, glob
from collections import Counter

def grab(html, pat, flags=re.I|re.S):
    m = re.search(pat, html, flags)
    return m.group(1).strip() if m else ""
def text(s):
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', s)).strip()

SKIP = ('admin/','social/','social-renderer/','social-uploader/','opus-portal/','_audit/','node_modules/')
rows = []
for path in glob.glob('**/index.html', recursive=True):
    p = path.replace(os.sep, '/')
    if any(p.startswith(s) for s in SKIP):
        continue
    try:
        html = open(path, encoding='utf-8', errors='ignore').read()
    except Exception:
        continue
    url = '/' + p[:-len('index.html')]
    title = text(grab(html, r'<title[^>]*>(.*?)</title>'))
    h1 = text(grab(html, r'<h1[^>]*>(.*?)</h1>'))
    canon = grab(html, r'<link[^>]+rel=["\']canonical["\'][^>]+href=["\']([^"\']+)')
    lang = grab(html, r'<html[^>]+lang=["\']([^"\']+)') or 'en'
    desc = grab(html, r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']*)')
    jsonld = len(re.findall(r'application/ld\+json', html))
    date = grab(html, r'"datePublished"\s*:\s*"([^"]+)"')
    seg = [x for x in url.strip('/').split('/') if x]
    section = seg[0] if seg else 'home'
    geo = seg[-1] if len(seg) >= 2 else ''
    rows.append(dict(url=url, section=section, geo=geo, lang=lang, title=title, h1=h1,
                     canonical=canon, desc_len=len(desc), jsonld=jsonld, date=date,
                     is_blog=(section == 'blog' and url.count('/') == 3)))
rows.sort(key=lambda r: r['url'])
json.dump(rows, open('_content_map.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

sec = Counter(r['section'] for r in rows)
print("TOTAL paginas mapeadas:", len(rows))
print("posts de blog (nivel /blog/x/):", sum(1 for r in rows if r['is_blog']))
print("\nPor secao (top 15):")
for k, v in sec.most_common(15):
    print("  %-26s %d" % (k, v))
print("\nQualidade de dados:")
print("  sem <title>:", sum(1 for r in rows if not r['title']))
print("  sem H1:", sum(1 for r in rows if not r['h1']))
print("  sem canonical:", sum(1 for r in rows if not r['canonical']))
print("  desc curta(<50)/ausente:", sum(1 for r in rows if r['desc_len'] < 50))
print("  lang pt:", sum(1 for r in rows if r['lang'].startswith('pt')))
print("\n_content_map.json:", os.path.getsize('_content_map.json'), "bytes")
