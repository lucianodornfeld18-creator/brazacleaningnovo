#!/usr/bin/env python3
"""
agent_run.py - The autonomous post generator for the GitHub Actions cron.

Runs the RUNBOOK pipeline once: picks a focus topic for the day, researches it
with web search, checks canibalization, writes the post JSON, then renders +
wires it into the site via build_post.py and update_site.py.

The Claude API writes CONTENT (a JSON object); the deterministic scripts do the
structure/schema/listing/sitemap so the model can't break the site. Prices < $120
are blocked by build_post.py's guard.

Env:  ANTHROPIC_API_KEY (required)
      TODAY=YYYY-MM-DD   (optional; defaults to system date — set by the workflow)
Usage: py automation/agent_run.py [--dry]   (--dry prints the plan, no API call)
"""
import os, re, sys, json, subprocess, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUNBOOK = os.path.join(ROOT, 'automation', 'RUNBOOK.md')
EXAMPLE = os.path.join(ROOT, 'automation', 'queue', '_example.json')
CMAP = os.path.join(ROOT, '_content_map.json')
MODEL = 'claude-sonnet-4-6'
MAX_TRIES = 3  # regenerate this many times if the $120 price floor is violated

# focus rotation by weekday (Mon=0)
ROTATION = {
    0: ("residential biweekly/recurring house cleaning",
        ["The Villages", "Leesburg", "Wildwood", "Minneola", "Clermont", "Winter Garden", "Windermere"]),
    2: ("Airbnb / vacation rental turnover cleaning",
        ["Kissimmee", "Davenport", "Celebration", "Orlando"]),
    4: ("opportunistic: deep / move-out / move-in / commercial",
        ["Clermont", "Winter Garden", "Windermere", "Minneola", "Kissimmee", "Davenport"]),
}

def today():
    return datetime.date.fromisoformat(os.environ.get('TODAY') or datetime.date.today().isoformat())

def existing_topics():
    rows = json.load(open(CMAP, encoding='utf-8'))
    return [r['url'] for r in rows if r.get('is_blog')]

def pick_focus(d):
    return ROTATION.get(d.weekday(), ROTATION[4])

def build_messages(d, correction=None):
    runbook = open(RUNBOOK, encoding='utf-8').read()
    example = open(EXAMPLE, encoding='utf-8').read()
    focus, cities = pick_focus(d)
    existing = existing_topics()
    system = (
        runbook
        + "\n\n## OUTPUT CONTRACT\n"
        "You are the autonomous generator. Produce ONE blog post as a single JSON object that "
        "matches the schema of automation/queue/_example.json EXACTLY (same keys). Rules:\n"
        "- Follow the RUNBOOK quality standard: ~1200-1500 words across the `sections`, >=6 question-style H2s, "
        ">=2 comparison tables (as HTML inside section `html`), 8 FAQs, a 40-60 word `answer_first`.\n"
        "- PRICE FLOOR: never write ANY dollar figure below $120 anywhere in the post — not even when "
        "citing market averages, hourly rates, competitor pricing, or low-end estimates. If real-world data "
        "is lower, omit the number or state Braza's $120 minimum instead. Ranges may go high; the floor is $120.\n"
        "- `interlinks` (3-6) MUST point to real existing URLs from the provided site list, reciprocal where possible.\n"
        "- `hero_img` MUST be an existing /images/ path (pick a plausible one already on the site).\n"
        "- title < 60 chars, meta_desc < 155 chars, both unique vs existing.\n"
        "- Output ONLY the JSON inside a single ```json fenced block. No prose before or after.\n\n"
        "## EXAMPLE SCHEMA (copy the shape, not the content)\n```json\n" + example + "\n```\n"
    )
    user = (
        f"Today is {d.isoformat()} ({d.strftime('%A')}). Focus of the day: {focus}.\n"
        f"Priority focus cities: {', '.join(cities)}.\n\n"
        "Existing blog post URLs (do NOT duplicate their intent — pick a genuine gap):\n"
        + "\n".join("- " + u for u in existing) +
        "\n\nResearch real 2026 pricing/questions for the chosen service+city with web search, "
        "pick the best gap that pushes a high-margin service, then output the post JSON."
    )
    if correction:
        user += ("\n\n## CORRECTION — your previous draft was REJECTED, fix it now\n" + correction)
    return system, user

def call_api(system, user):
    import anthropic
    client = anthropic.Anthropic()
    msgs = [{"role": "user", "content": user}]
    tools = [{"type": "web_search_20260209", "name": "web_search"}]
    for _ in range(6):  # allow a few pause_turn continuations
        with client.messages.stream(
            model=MODEL, max_tokens=16000,
            thinking={"type": "adaptive"},
            output_config={"effort": "high"},
            system=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
            messages=msgs, tools=tools,
        ) as stream:
            msg = stream.get_final_message()
        if msg.stop_reason == "pause_turn":
            msgs.append({"role": "assistant", "content": msg.content})
            continue
        text = "".join(b.text for b in msg.content if b.type == "text")
        return text
    raise SystemExit("API: too many pause_turn continuations")

def extract_json(text):
    m = re.search(r'```json\s*(\{.*?\})\s*```', text, re.S) or re.search(r'(\{.*\})', text, re.S)
    if not m:
        raise SystemExit("Nao encontrei JSON na resposta do modelo")
    return json.loads(m.group(1))

def slugify(title):
    s = re.sub(r'\(2026[^)]*\)', '', title).lower()
    s = re.sub(r'[^a-z0-9]+', '-', s).strip('-')
    return s[:70]

def run(cmd):
    print("  $", " ".join(cmd[1:]))
    subprocess.run(cmd, check=True)

def main():
    d = today()
    focus, cities = pick_focus(d)
    if '--dry' in sys.argv:
        print(f"[dry] {d.isoformat()} {d.strftime('%A')} | focus: {focus} | cities: {cities}")
        print(f"[dry] {len(existing_topics())} existing posts in ledger; would call {MODEL} + web_search.")
        return

    print(f"== agent_run {d.isoformat()} ({d.strftime('%A')}) | focus: {focus} ==")
    correction = None
    last_price_err = None
    for attempt in range(1, MAX_TRIES + 1):
        if correction:
            print(f"== retry {attempt}/{MAX_TRIES}: regenerating with price correction ==")
        system, user = build_messages(d, correction)
        data = extract_json(call_api(system, user))
        data.setdefault('date', d.isoformat())
        slug = data.get('slug') or slugify(data['title'])
        data['slug'] = slug

        # canibalization gate (REJECT = hard stop, "nada publicado hoje" — not retryable)
        chk = subprocess.run([sys.executable, os.path.join(ROOT, 'automation', 'check_canib.py'),
                              data.get('keyword_primary', data['title']), data['title']])
        if chk.returncode == 3:
            raise SystemExit("BLOQUEADO pelo gate de canibalizacao (REJECT). Nada publicado hoje.")

        qf = os.path.join(ROOT, 'automation', 'queue', slug + '.json')
        json.dump(data, open(qf, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print(f"  wrote queue/{slug}.json")

        # build_post.py enforces the $120 price floor; capture output so a violation can be retried
        bp = subprocess.run([sys.executable, os.path.join(ROOT, 'automation', 'build_post.py'), slug],
                            capture_output=True, text=True)
        sys.stdout.write(bp.stdout)
        sys.stderr.write(bp.stderr)
        if bp.returncode == 0:
            run([sys.executable, os.path.join(ROOT, 'automation', 'update_site.py'), slug])
            try:
                run([sys.executable, os.path.join(ROOT, 'automation', 'indexnow_ping.py'),
                     f"https://brazacleaning.com/blog/{slug}/"])
            except Exception as e:
                print(f"  indexnow ping falhou (nao-fatal): {e}")
            print(f"PUBLISHED slug={slug}")
            # expose slug to the workflow
            gh_out = os.environ.get('GITHUB_OUTPUT')
            if gh_out:
                with open(gh_out, 'a', encoding='utf-8') as f:
                    f.write(f"slug={slug}\n")
            return

        combined = bp.stdout + bp.stderr
        if 'BLOQUEADO: preco' in combined:
            # price-floor violation is the model's mistake — feed it back and regenerate
            last_price_err = combined.strip().splitlines()[-1]
            print(f"  price floor violated, will retry: {last_price_err}")
            correction = ("Your previous draft contained a dollar amount below the $120 floor and was rejected. "
                          "Rewrite EVERY price so no figure anywhere is below $120 (including market averages, "
                          "hourly rates, competitor or low-end mentions). Omit sub-$120 numbers or use Braza's "
                          "$120 minimum instead. Rejection detail: " + last_price_err)
            try:
                os.remove(qf)  # discard the rejected draft before retrying
            except OSError:
                pass
            continue

        # any other build error is a real failure — surface it
        raise SystemExit(f"build_post.py falhou (nao foi preco):\n{combined.strip()[-800:]}")

    raise SystemExit(f"Esgotou {MAX_TRIES} tentativas no piso de preco. Ultimo erro: {last_price_err}. "
                     f"Nada publicado hoje.")

if __name__ == '__main__':
    main()
