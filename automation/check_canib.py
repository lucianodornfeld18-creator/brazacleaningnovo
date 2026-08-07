#!/usr/bin/env python3
"""
check_canib.py - Canibalization gate against _content_map.json (Phase 3).

Given a candidate primary keyword (and optional title), report any existing URL
whose intent overlaps. Decision output: PASS (net-new), ADJUST (partial overlap,
pick pillar vs support + interlink), or REJECT (intent already owned).

Usage:  py automation/check_canib.py "biweekly house cleaning cost clermont fl" ["Optional title"]
Exit code: 0 PASS, 2 ADJUST, 3 REJECT  (so the runbook/cron can branch on it)
"""
import sys, os, re, json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CMAP = os.path.join(ROOT, '_content_map.json')
STOP = set('a an the in of for to and or vs is are do does how much what when '
           'why where which cost price guide 2026 fl florida braza cleaning '
           'service services near me'.split())

def toks(s):
    return [w for w in re.sub(r'[^a-z0-9 ]', ' ', s.lower()).split() if w not in STOP and len(w) > 2]

def main():
    if len(sys.argv) < 2:
        sys.exit("uso: py automation/check_canib.py \"keyword primaria\" [\"titulo\"]")
    kw = sys.argv[1]
    title = sys.argv[2] if len(sys.argv) > 2 else ''
    cand = set(toks(kw + ' ' + title))
    rows = json.load(open(CMAP, encoding='utf-8'))

    scored = []
    for r in rows:
        ex = set(toks(r['title'] + ' ' + r.get('h1', '')))
        if not ex:
            continue
        inter = cand & ex
        score = len(inter) / max(len(cand), 1)
        if score >= 0.5:
            scored.append((round(score, 2), r['url'], r['title'], r.get('is_blog')))
    scored.sort(reverse=True)

    print(f'CANDIDATO: "{kw}"  tokens={sorted(cand)}')
    if not scored:
        print('VEREDITO: PASS (net-new) — nenhuma URL com intencao sobreposta.')
        sys.exit(0)

    print(f'\n{len(scored)} URL(s) com sobreposicao de intencao:')
    for sc, url, t, isblog in scored[:8]:
        print(f'  [{sc:.2f}] {url}  ({"blog" if isblog else "page"}) — {t[:55]}')

    top = scored[0][0]
    blog_hit = any(s[3] for s in scored if s[0] >= 0.8)
    if top >= 0.8 and blog_hit:
        print('\nVEREDITO: REJECT — outro POST de blog ja cobre essa intencao. '
              'Escolha angulo long-tail distinto ou atualize o post existente.')
        sys.exit(3)
    print('\nVEREDITO: ADJUST — sobreposicao parcial (provavel pagina pilar). '
          'Siga, mas defina pilar vs suporte e crie interlink reciproco com a URL acima.')
    sys.exit(2)

if __name__ == '__main__':
    main()
