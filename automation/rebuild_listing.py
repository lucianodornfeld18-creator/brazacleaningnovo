#!/usr/bin/env python3
"""
rebuild_listing.py - Regenerate blog/index.html's card grid with ALL posts.

INDEXING-SAFE: only replaces the inner cards of <div class="blog-grid">. Does NOT
touch the page <head>/canonical, nav, CTA, footer, the individual posts, the
sitemap, or any canonical/robots directive. Pure additive internal linking.

Cards are sorted newest-first by datePublished. Reuses the tested extract_post /
build_card from update_site.py so card markup is identical to the automation path.

Usage: py automation/rebuild_listing.py [--dry]
"""
import os, re, sys, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import update_site as us

ROOT = us.ROOT
BLOG_INDEX = us.BLOG_INDEX

def main():
    dry = '--dry' in sys.argv
    slugs = []
    for path in glob.glob(os.path.join(ROOT, 'blog', '*', 'index.html')):
        slug = os.path.basename(os.path.dirname(path))
        if slug == 'category':
            continue
        slugs.append(slug)

    posts = [us.extract_post(s) for s in slugs]
    # newest first; posts without a date sink to the bottom deterministically
    posts.sort(key=lambda p: (p['date'] or '0000-00-00', p['slug']), reverse=True)

    cards = '\n  '.join(us.build_card(p) for p in posts)
    print(f"posts encontrados: {len(posts)}")
    missing_date = [p['slug'] for p in posts if not p['date']]
    if missing_date:
        print(f"  AVISO sem datePublished ({len(missing_date)}):", ", ".join(missing_date[:6]))

    s = us.read(BLOG_INDEX)
    # group(1)=grid open, group(2)=cards, group(3)=grid close + section close
    pat = re.compile(r'(<div class="blog-grid">)(.*?)(</div>\s*</div></section>)', re.S)
    m = pat.search(s)
    if not m:
        sys.exit("ERRO: nao achei o bloco .blog-grid em blog/index.html")

    new_block = m.group(1) + cards + '\n  ' + m.group(3)
    new_s = s[:m.start()] + new_block + s[m.end():]

    if dry:
        before = s.count('class="blog-card"')
        after = new_s.count('class="blog-card"')
        print(f"[dry] cards na listagem: {before} -> {after}")
        print("[dry] head/nav/footer/canonical/sitemap: intocados")
        return

    us.write(BLOG_INDEX, new_s)
    print(f"OK: listagem regenerada com {len(posts)} cards (era {s.count('class=\"blog-card\"')})")

if __name__ == '__main__':
    main()
