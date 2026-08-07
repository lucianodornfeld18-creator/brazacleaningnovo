#!/usr/bin/env python3
"""
build_post.py - Generate a GEO/AEO-optimized blog post HTML from structured JSON.

The agent writes CONTENT as JSON (safe, can't break HTML); this script renders the
full, valid HTML using the real site shell (CSS/nav/footer extracted from a reference
post). Guarantees every post has: answer-first (speakable), TOC, question H2s,
visible FAQ + FAQPage schema, recriprocal interlinks, CTA, clean schema (NO fake
aggregateRating), correct BreadcrumbList, hreflang-ready, og/twitter, geo.region.

Usage:  py automation/build_post.py <slug>
Reads:  automation/queue/<slug>.json   Writes: blog/<slug>/index.html

JSON schema (see automation/queue/_example.json):
  slug, title(<60), meta_desc(<155), category, category_slug, h1,
  hero_img, hero_alt, hero_w, hero_h, date(YYYY-MM-DD), updated(opt), read_min,
  keyword_primary, answer_first(40-60w),
  sections:[{h2, anchor, html}], faq:[[q,a]...], interlinks:[[href,label]...]
"""
import sys, os, re, json, html as H

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REF = os.path.join(ROOT, 'blog', 'airbnb-cleaning-cost-kissimmee-fl', 'index.html')
BASE = 'https://brazacleaning.com'
AUTHOR = 'Luana'
PHONE_DISPLAY = '(689) 242-7469'
PHONE_TEL = '6892427469'
MIN_PRICE = 120  # business rule: never display any price below $120

def assert_min_price(text, where):
    """Abort if any dollar amount under MIN_PRICE appears (phone numbers excluded)."""
    bad = [int(n) for n in re.findall(r'\$\s?(\d{1,4})', text) if int(n) < MIN_PRICE]
    if bad:
        sys.exit(f"BLOQUEADO: preco abaixo de ${MIN_PRICE} em {where}: {sorted(set(bad))}. "
                 f"Regra de negocio: nenhum preco < ${MIN_PRICE}.")

def read(p):
    with open(p, encoding='utf-8') as f: return f.read()

def extract_shell():
    h = read(REF)
    css = re.search(r'<style>.*?</style>', h, re.S).group(0)
    nav = re.search(r'<nav class="nav".*?</nav>', h, re.S).group(0)
    mobile = re.search(r'<div class="mobile-nav".*?</div>\s*</div>(?=\s*<main)', h, re.S)
    mobile = mobile.group(0) if mobile else re.search(r'<div class="mobile-nav".*?</div>\n</div>', h, re.S).group(0)
    # footer through end-of-body scripts
    footer = re.search(r'<footer>.*?</body>', h, re.S).group(0)
    return css, nav, mobile, footer

def j(o):  # compact json-ld
    return json.dumps(o, ensure_ascii=False, separators=(',', ':'))

def localbusiness_schema():
    return {"@context": "https://schema.org", "@type": "LocalBusiness",
            "@id": BASE + "/#organization", "name": "Braza Cleaning Services",
            "description": "Professional house cleaning, Airbnb cleaning, vacation rental cleaning and commercial cleaning in Central Florida.",
            "telephone": "+1-689-242-7469", "url": BASE, "priceRange": "$$",
            "areaServed": "Central Florida",
            "address": {"@type": "PostalAddress", "addressLocality": "Ocoee",
                        "addressRegion": "FL", "postalCode": "34761", "addressCountry": "US"}}

def article_schema(d):
    return {"@context": "https://schema.org", "@type": "BlogPosting",
            "headline": d['title'],
            "author": {"@type": "Person", "name": AUTHOR, "url": BASE + "/about/"},
            "publisher": {"@type": "Organization", "name": "Braza Cleaning Services",
                          "logo": {"@type": "ImageObject", "url": BASE + "/images/logo.webp"}},
            "datePublished": d['date'], "dateModified": d.get('updated', d['date']),
            "image": BASE + d['hero_img'], "url": d['url'],
            "mainEntityOfPage": {"@type": "WebPage", "@id": d['url']}}

def breadcrumb_schema(d):
    return {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "Home", "item": BASE + "/"},
        {"@type": "ListItem", "position": 2, "name": "Blog", "item": BASE + "/blog/"},
        {"@type": "ListItem", "position": 3, "name": d['category'], "item": BASE + d['cat_url']},
        {"@type": "ListItem", "position": 4, "name": d['title'], "item": d['url']}]}

def faq_schema(faq):
    return {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q,
         "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faq]}

def speakable_schema(d):
    return {"@context": "https://schema.org", "@type": "WebPage", "url": d['url'],
            "speakable": {"@type": "SpeakableSpecification",
                          "cssSelector": [".answer-first", ".faq-question"]}}

def render(d):
    css, nav, mobile, footer = extract_shell()
    d['url'] = f"{BASE}/blog/{d['slug']}/"
    d['cat_url'] = f"/blog/category/{d['category_slug']}/"
    upd = d.get('updated', d['date'])
    esc = H.escape

    # answer-first (speakable) box
    answer = (f'<div class="answer-first" style="background:var(--blue-light);border-left:4px solid var(--blue);'
              f'border-radius:0 10px 10px 0;padding:18px 22px;margin:0 0 28px;font-size:17px;line-height:1.6;color:var(--text)">'
              f'{esc(d["answer_first"])}</div>')

    # TOC from sections
    toc_items = ''.join(
        f'<li><a href="#{s["anchor"]}" style="color:var(--blue);text-decoration:none">{esc(s["h2"])}</a></li>'
        for s in d['sections'])
    toc = (f'<nav class="toc" aria-label="Table of contents" style="background:var(--gray-light);border:1px solid var(--gray-border);'
           f'border-radius:12px;padding:18px 22px;margin:0 0 28px">'
           f'<p style="font-weight:700;margin:0 0 8px;font-family:var(--font-head)">In this guide</p>'
           f'<ol style="margin:0;padding-left:20px;line-height:1.9">{toc_items}</ol></nav>')

    # body sections
    body = ''
    for s in d['sections']:
        body += f'\n<h2 id="{s["anchor"]}">{esc(s["h2"])}</h2>\n{s["html"]}\n'

    # reciprocal interlinks block (inline after first section is handled by content; here a related box at end)
    links = ''
    for href, label in d.get('interlinks', []):
        links += (f'<div style="background:var(--blue-light);border-left:3px solid var(--blue);border-radius:0 6px 6px 0;'
                  f'padding:.75rem 1rem;margin:1rem 0"><p style="margin:0;font-size:14px">👉 <strong>Related:</strong> '
                  f'<a href="{href}" style="color:var(--blue);font-weight:600">{esc(label)} →</a></p></div>')

    # visible FAQ (accordion classes already wired in footer JS)
    faq_html = '<h2 id="faq">Frequently Asked Questions</h2>\n<div class="faq-list" style="margin-top:8px">'
    for q, a in d['faq']:
        faq_html += (f'\n<div class="faq-item"><button class="faq-question" type="button">{esc(q)}</button>'
                     f'<div class="faq-answer"><div class="faq-answer-inner">{esc(a)}</div></div></div>')
    faq_html += '\n</div>'

    # CTA (phone + form link — WhatsApp deprioritized per v2)
    cta = (f'<div class="cta-section" style="margin-top:40px;border-radius:16px">'
           f'<h2>Ready for a Professional Clean?</h2>'
           f'<p>Serving Central Florida 7 days a week. Free quote in 2 hours.</p>'
           f'<div class="cta-btns"><a href="/#contact" class="btn-white">Get Free Quote</a>'
           f'<a href="tel:{PHONE_TEL}" class="btn-orange-outline">📞 {PHONE_DISPLAY}</a></div></div>')

    head = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(d['title'])}</title>
<meta name="description" content="{esc(d['meta_desc'])}">
<meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1">
<link rel="canonical" href="{d['url']}">
<meta property="og:type" content="article">
<meta property="og:site_name" content="Braza Cleaning Services">
<meta property="og:title" content="{esc(d['title'])}">
<meta property="og:description" content="{esc(d['meta_desc'])}">
<meta property="og:url" content="{d['url']}">
<meta property="og:image" content="{BASE}{d['hero_img']}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{esc(d['title'])}">
<meta name="twitter:description" content="{esc(d['meta_desc'])}">
<meta name="twitter:image" content="{BASE}{d['hero_img']}">
<meta name="geo.region" content="US-FL">
<meta name="geo.placename" content="Ocoee, Florida">
<link rel="icon" type="image/png" href="/images/logo.webp">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="preload" href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700;800&family=Lato:wght@400;700&display=swap" as="style" onload="this.onload=null;this.rel='stylesheet'">
<noscript><link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700;800&family=Lato:wght@400;700&display=swap" rel="stylesheet"></noscript>
<script type="application/ld+json">{j(localbusiness_schema())}</script>
<script type="application/ld+json">{j(article_schema(d))}</script>
<script type="application/ld+json">{j(breadcrumb_schema(d))}</script>
<script type="application/ld+json">{j(faq_schema(d['faq']))}</script>
<script type="application/ld+json">{j(speakable_schema(d))}</script>
{css}
</head>
<body>
{nav}
{mobile}
<main>
<div style="padding-top:110px;background:var(--gray-light)">
<div class="blog-post-inner">
<div class="blog-post-header">
<div class="breadcrumb" style="margin-bottom:16px"><a href="/">Home</a><span>›</span><a href="/blog/">Blog</a><span>›</span><a href="{d['cat_url']}">{esc(d['category'])}</a></div>
<span class="blog-cat">{esc(d['category'])}</span>
<h1 class="blog-post-title">{esc(d['h1'])}</h1>
<div class="blog-post-meta"><span>By <a href="/about/" rel="author" style="color:inherit;border-bottom:1px dotted currentColor">{AUTHOR}</a></span><span>·</span><span>Published {d['date']}</span><span>·</span><span>Updated {upd}</span><span>·</span><span>{d['read_min']} min read</span></div>
</div>
<div class="blog-post-img"><img alt="{esc(d['hero_alt'])}" loading="eager" onerror="this.style.opacity='0'" src="{d['hero_img']}" style="width:100%;height:400px;object-fit:cover" width="{d.get('hero_w',768)}" height="{d.get('hero_h',1024)}"/></div>
<div class="blog-content">
{answer}
{toc}
{body}
{links}
{faq_html}
{cta}
</div>
</div>
</div>
{footer}
'''
    return head

def main():
    if len(sys.argv) < 2:
        sys.exit("uso: py automation/build_post.py <slug>")
    slug = sys.argv[1]
    qf = os.path.join(ROOT, 'automation', 'queue', slug + '.json')
    if not os.path.isfile(qf):
        sys.exit(f"ERRO: faltando {qf}")
    d = json.load(open(qf, encoding='utf-8'))
    d['slug'] = slug
    assert_min_price(json.dumps(d), f"queue/{slug}.json")  # business rule guard
    out_dir = os.path.join(ROOT, 'blog', slug)
    os.makedirs(out_dir, exist_ok=True)
    htmlout = render(d)
    with open(os.path.join(out_dir, 'index.html'), 'w', encoding='utf-8', newline='\n') as f:
        f.write(htmlout)
    print(f"OK: blog/{slug}/index.html ({len(htmlout)} bytes)")

if __name__ == '__main__':
    main()
