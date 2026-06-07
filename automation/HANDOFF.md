# HANDOFF — Sessão de 2026-06-05 (blog + automação)

Documento de retomada. Leia isto pra continuar de onde paramos.

## TL;DR do que foi feito
1. **Auditoria reconciliada** (prompt v2 dos Downloads × SEO-GEO-AUDIT-FINDINGS.md).
2. **Blog consertado e publicado** — grid quebrado (cards esticados) corrigido. No ar.
3. **Sistema de automação de blog completo** em `automation/` — testado peça por peça.
4. **Post-piloto real publicado**: `/blog/biweekly-house-cleaning-cost-minneola-fl/`.
5. **Cron GitHub Actions montado** (seg/qua/sex + digest sexta) — falta só o setup do usuário.

## Estado do git (tudo commitado E pushado pro origin/main)
```
ab54ed5 Add GitHub Actions cron: autonomous 3x/week blog + weekly digest
c2cd6ef Blog: Biweekly House Cleaning Cost in Minneola FL (2026)
0691001 Add blog automation pipeline (GEO/AEO, top-1 focus)
b1f3f9a Fix blog listing: restore broken grid (square/stretched cards)
```
Working tree: este HANDOFF.md é a única coisa não commitada.

## ⏳ PRÓXIMA AÇÃO (é do usuário, ~5 min) — bloqueia o cron
Seguir `automation/SETUP-CRON.md`:
1. Secrets no GitHub (Settings → Secrets → Actions): `ANTHROPIC_API_KEY`, `RESEND_API_KEY`
2. Settings → Actions → General → "Read and write permissions"
3. Resend: verificar domínio `brazacleaning.com`
4. Testar via aba Actions → "Auto Blog Post" → "Run workflow"
> Até configurar, se o cron disparar seg/qua/sex ele FALHA (sem chave). Opção: desabilitar
> o workflow na aba Actions até o setup estar pronto.

## Como o sistema funciona (arquitetura escolhida pelo usuário)
- **Disparo:** GitHub Actions cron (não /schedule). Seg/qua/sex 13:00 UTC.
- **Publicação:** direto no main → deploy Cloudflare (sem aprovação prévia — escolha do usuário).
- **Email:** 1 digest semanal (sexta), canal Resend próprio — NUNCA toca o worker de leads.
- **Idioma:** EN por padrão. **Imagens:** reusar pool /images/ (usuário vai alimentar mais).

### Fluxo por post (RUNBOOK.md = pipeline operacional)
`agent_run.py` (Claude API claude-opus-4-8 + web_search) escolhe foco do dia por rotação
→ pesquisa → escreve JSON do post → `check_canib.py` (gate) → `build_post.py` (gera HTML,
**trava preço ≥ $120**) → `update_site.py` (card no grid + categoria + sitemap + content_map
+ log do digest) → workflow commita+pusha.

### Arquivos do toolkit
- `automation/agent_run.py` — orquestrador do cron (rotação seg=residencial biweekly / qua=Airbnb / sex=oportunista)
- `automation/build_post.py` — gerador GEO/AEO; trava `assert_min_price` ($120); SEM aggregateRating fabricado
- `automation/update_site.py` — insere card DENTRO do `.blog-grid` (conserta a raiz da quebra)
- `automation/check_canib.py` — PASS/ADJUST/REJECT vs `_content_map.json`
- `automation/notify.py` — `--weekly` (digest) e `--log <slug>` (interno)
- `automation/inventory.py` — regenera `_content_map.json`
- `automation/RUNBOOK.md` — regras + padrão top-1 (1200-1500 palavras, 8 FAQs, $120)
- `automation/queue/_example.json` — molde do JSON de conteúdo
- `_content_map.json` (raiz) — ledger de 185 URLs
- `.github/workflows/blog-auto.yml` + `blog-digest.yml`

### Regras de negócio travadas
- **Preço mínimo $120** em qualquer valor (trava automática no build_post.py — testada: $99 bloqueia).
- **Padrão sempre top-1**: ~1200-1500 palavras, ≥6 H2-pergunta, ≥2 tabelas, 8 FAQs, answer-first speakable.
- **Não estragar o formulário de lead** — automação não chama o worker de leads nem o track.js.

## Itens em ABERTO (não feitos ainda — decidir na volta)
1. **aggregateRating 5.0/68 fabricado** ainda em ~140 páginas ANTIGAS do site (achado nº1 da
   auditoria, risco de penalidade Google). Posts NOVOS já nascem sem ele. Falta limpar o legado.
2. **41 posts órfãos** — a listagem `blog/index.html` mostra ~50 de 91 posts. Usuário disse
   "espera" quando perguntei se regenerava a listagem completa. Decisão pendente.
3. Sobreposições parciais blog×página de serviço (7 casos) — dívida leve, gerenciar com interlink.

## Como retomar
"Continuar a automação do blog da Braza — ler automation/HANDOFF.md". Provável próximo passo:
guiar o setup dos secrets, ou atacar os itens em aberto (aggregateRating / 41 órfãos).
