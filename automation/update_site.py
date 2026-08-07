#!/usr/bin/env python3
"""
update_site.py - Mechanical site updates after a blog post HTML is written.

Given a post that already exists at blog/<slug>/index.html, this:
  1. Inserts a card at the TOP of the .blog-grid in blog/index.html (newest first)
  2. Adds the post to the matching blog/category/<cat>/ listing if it exists
  3. Adds a <url> entry to sitemap.xml with today's lastmod
  4. Appends/updates the entry in _content_map.json (canibalization ledger)

It is DETERMINISTIC and idempotent: running twice does not duplicate anything.
It NEVER does git operations. Run from repo root:  py automation/update_site.py <slug> [--date YYYY-MM-DD]

This is the piece that fixes the root cause of the broken listing: cards are
inserted *inside* the grid via the real DOM anchor, never appended loose.
"""
import sys, os, re, json, argparse, html

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BLOG_INDEX = os.path.join(ROOT, 'blog', 'index.html')
SITEMAP = os.path.join(ROOT, 'sitemap.xml')
CMAP = os.path.join(ROOT, '_content_map.json')
BASE = 'https://brazacleaning.com'
DEFAULT_HERO = '/images/img-living-wintergarden.jpg'  # safe fallback (always exists)

def read(p):
    with open(p, encoding='utf-8') as f: return f.read()
def write(p, s):
    with open(p, 'w', encoding='utf-8', newline='\n') as f: f.write(s)
def grab(s, pat, flags=re.I | re.S):
    m = re.search(pat, s, flags); return m.group(1).strip() if m else ''

def extract_post(slug):
    """Pull listing/sitemap fields straight from the post's own HTML."""
    path = os.path.join(ROOT, 'blog', slug, 'index.html')
    if not os.path.isfile(path):
        sys.exit(f"ERRO: post nao existe: blog/{slug}/index.html")
    h = read(path)
    title = grab(h, r'<h1[^>]*class="blog-post-title"[^>]*>(.*?)</h1>') or grab(h, r'<title[^>]*>(.*?)</title>')
    title = re.sub(r'\s*\|\s*Braza.*$', '', re.sub(r'<[^>]+>', '', title)).strip()
    desc = grab(h, r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']*)')
    cat = grab(h, r'<span class="blog-cat">(.*?)</span>')
    cat_href = grab(h, r'<a href="(/blog/category/[^"]+)"')
    date = grab(h, r'"datePublished"\s*:\s*"([^"]+)"')
    read_m = grab(h, r'(\d+)\s*min read')
    # hero image (prefer in-body hero, fall back to og:image)
    img_block = grab(h, r'<div class="blog-post-img">(.*?)</div>')
    src = grab(img_block, r'src="([^"]+)"')
    alt = grab(img_block, r'alt="([^"]*)"')
    w = grab(img_block, r'width="(\d+)"') or '768'
    hh = grab(img_block, r'height="(\d+)"') or '1024'
    if not src:
        og = grab(h, r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)')
        src = re.sub(r'^https?://[^/]+', '', og)  # to site-relative path
    if not alt:
        alt = title
    # never reference a 404 image: try the .jpg sibling, then a safe default
    if src and not os.path.isfile(os.path.join(ROOT, src.lstrip('/'))):
        alt_jpg = re.sub(r'\.webp$', '.jpg', src)
        if os.path.isfile(os.path.join(ROOT, alt_jpg.lstrip('/'))):
            src = alt_jpg
        else:
            src = DEFAULT_HERO
    # excerpt: prefer the answer-first block, then first <p>, then meta description
    excerpt = grab(h, r'<div class="answer-first"[^>]*>(.*?)</div>') \
        or grab(h, r'<div class="blog-content">\s*<p[^>]*>(.*?)</p>')
    excerpt = re.sub(r'<[^>]+>', '', excerpt).strip()
    if not excerpt:
        excerpt = desc
    if len(excerpt) > 140:
        excerpt = excerpt[:137].rsplit(' ', 1)[0] + '...'
    # unescape text fields so build_card can re-escape exactly once (no &amp;amp;)
    title = html.unescape(title); cat = html.unescape(cat)
    excerpt = html.unescape(excerpt); alt = html.unescape(alt)
    return dict(slug=slug, title=title, desc=desc, cat=cat or 'Cleaning Tips',
                cat_href=cat_href, date=date, read=read_m or '6',
                src=src, alt=alt, w=w, hh=hh, excerpt=excerpt)

def build_card(p):
    return (
        f'<a href="/blog/{p["slug"]}/" class="blog-card" style="display:block;text-decoration:none">\n'
        f'  <div class="blog-card-img"><img src="{p["src"]}" alt="{html.escape(p["alt"])}" loading="lazy" '
        f'style="width:100%;height:200px;object-fit:cover" onerror="this.style.opacity=\'0\'" '
        f'width="{p["w"]}" height="{p["hh"]}"></div>\n'
        f'  <div class="blog-card-body">\n'
        f'    <span class="blog-cat">{html.escape(p["cat"])}</span>\n'
        f'    <h3>{html.escape(p["title"])}</h3>\n'
        f'    <p>{html.escape(p["excerpt"])}</p>\n'
        f'    <div class="blog-meta"><span>{p["date"]}</span><span>&middot;</span><span>{p["read"]} min read</span></div>\n'
        f'  </div></a>'
    )

def insert_card(listing_path, p):
    """Insert card as FIRST child of .blog-grid. Idempotent on slug."""
    if not os.path.isfile(listing_path): return False, 'listing inexistente'
    s = read(listing_path)
    if f'/blog/{p["slug"]}/"' in s:
        return False, 'ja listado (skip)'
    m = re.search(r'(<div class="blog-grid">)', s)
    if not m:
        return False, 'sem .blog-grid'
    card = build_card(p)
    anchor = m.group(1)
    s = s.replace(anchor, anchor + card + '\n  ', 1)
    write(listing_path, s)
    return True, 'card inserido no topo do grid'

def add_sitemap(p):
    s = read(SITEMAP)
    loc = f'{BASE}/blog/{p["slug"]}/'
    if loc in s:
        # update lastmod
        s = re.sub(r'(<loc>' + re.escape(loc) + r'</loc>\s*<lastmod>)[^<]*(</lastmod>)',
                   r'\g<1>' + p['date'] + r'\2', s)
        write(SITEMAP, s); return 'lastmod atualizado'
    entry = (f'  <url>\n    <loc>{loc}</loc>\n    <lastmod>{p["date"]}</lastmod>\n'
             f'    <changefreq>monthly</changefreq>\n    <priority>0.7</priority>\n  </url>\n')
    s = s.replace('</urlset>', entry + '</urlset>', 1)
    write(SITEMAP, s); return 'entrada adicionada'

def update_cmap(p):
    rows = json.load(open(CMAP, encoding='utf-8')) if os.path.isfile(CMAP) else []
    url = f'/blog/{p["slug"]}/'
    rows = [r for r in rows if r.get('url') != url]
    rows.append(dict(url=url, section='blog', geo='', lang='en', title=p['title'],
                     h1=p['title'], canonical=f'{BASE}{url}', desc_len=len(p['desc']),
                     jsonld=4, date=p['date'], is_blog=True))
    rows.sort(key=lambda r: r['url'])
    json.dump(rows, open(CMAP, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    return f'{len(rows)} entradas'

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('slug')
    ap.add_argument('--date', default=None)
    a = ap.parse_args()
    p = extract_post(a.slug)
    if a.date: p['date'] = a.date
    if not p['date']: sys.exit('ERRO: post sem datePublished e --date nao informado')

    print(f"== update_site: {a.slug} ==")
    print(f"  title: {p['title']}")
    print(f"  cat:   {p['cat']}  | date: {p['date']} | img: {p['src']}")
    ok, msg = insert_card(BLOG_INDEX, p);            print(f"  [listagem]  {msg}")
    if p['cat_href']:
        cl = os.path.join(ROOT, p['cat_href'].strip('/'), 'index.html')
        _, cm = insert_card(cl, p);                  print(f"  [categoria] {p['cat_href']}: {cm}")
    print(f"  [sitemap]   {add_sitemap(p)}")
    print(f"  [contentmap]{update_cmap(p)}")
    # register in the weekly-digest log (separate channel from leads)
    try:
        import subprocess
        subprocess.run([sys.executable, os.path.join(ROOT, 'automation', 'notify.py'),
                        '--log', a.slug], check=False)
    except Exception as e:
        print("  [log] aviso:", e)
    print("OK")

if __name__ == '__main__':
    main()
