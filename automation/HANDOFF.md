# HANDOFF — Braza blog + automação (atualizado 2026-06-07)

Documento de retomada. Leia isto pra continuar de onde paramos.

## ✅ CRON ATIVO — setup concluído em 2026-06-07
O blog automático está NO AR e funcionando de ponta a ponta. Os 4 passos de setup foram feitos
(secrets `ANTHROPIC_API_KEY` + `RESEND_API_KEY`, permissão de escrita do Actions, Resend).
Teste manual via "Run workflow" passou VERDE e publicou o 1º post real do cron:
`/blog/move-in-cleaning-cost-in-windermere-fl/` (8 FAQs, 5 schemas, 2 tabelas, 5 interlinks, preços ≥ $120).
Cron rodando sozinho: seg/qua/sex 13:00 UTC + digest sexta 14:00 UTC.

### Correção aplicada nessa sessão (commit `1291780`)
`agent_run.py` agora REGENERA o post (até `MAX_TRIES=3`) quando o modelo viola o piso de $120,
em vez de falhar a execução inteira. O prompt de preço também foi reforçado. Antes disso, o 1º
teste real falhou exatamente por isso (modelo cotou $40/$100 em "deep cleaning cost").

### ⚠️ DIGEST DE E-MAIL PENDENTE (decisão do usuário: deixar pra depois)
O teste manual do "Weekly Blog Digest" montou os 2 posts certos mas o Resend retornou **HTTP 403**
— quase certo: domínio `brazacleaning.com` NÃO verificado no Resend (passo 4 do setup não concluído
ou DNS não propagado). `notify.py` foi melhorado (commit `4fce5b4`) pra imprimir o corpo da resposta
do Resend e uma dica no 403. Destino atual fixo: `brazacleaningservices@gmail.com` (confirmar se é esse
o inbox). CONSEQUÊNCIA: o cron do digest vai falhar VERMELHO toda sexta até resolver (só barulho; não
afeta a publicação dos posts). Opções quando voltar: (a) verificar domínio no Resend + DNS Cloudflare;
(b) caminho rápido `onboarding@resend.dev` (só envia pro e-mail dono da conta Resend); (c) desativar o
workflow do digest ou fazer `notify.py` sair 0 sem enviar pra parar o vermelho semanal.

## TL;DR do que foi feito
1. **Auditoria reconciliada** (prompt v2 dos Downloads × SEO-GEO-AUDIT-FINDINGS.md).
2. **Blog consertado e publicado** — grid quebrado (cards esticados) corrigido. No ar.
3. **Sistema de automação de blog completo** em `automation/` — testado peça por peça.
4. **Post-piloto real publicado**: `/blog/biweekly-house-cleaning-cost-minneola-fl/`.
5. **Cron GitHub Actions montado** (seg/qua/sex + digest sexta) — falta só o setup do usuário.
6. **Listagem regenerada (91 posts, era 50)** — resolveu os 41 órfãos. Indexação-safe (só cards
   internos; head/canonical/sitemap/posts intocados). Imagens com fallback anti-404. NO AR.
7. **`/automation/*` bloqueado no Cloudflare** (`_redirects` → 404) — scripts ficam no repo pro
   Actions mas não são baixáveis em brazacleaning.com. NO AR.

## Estado do git (tudo commitado E pushado pro origin/main — exceto este update)
```
71a6e5c Block /automation/* from public serving (Cloudflare 404)
30ae08b Blog listing: show all 91 posts (was 50), 404-safe hero fallback
d92a8d6 Add session handoff doc
ab54ed5 Add GitHub Actions cron: autonomous 3x/week blog + weekly digest
c2cd6ef Blog: Biweekly House Cleaning Cost in Minneola FL (2026)
0691001 Add blog automation pipeline (GEO/AEO, top-1 focus)
b1f3f9a Fix blog listing: restore broken grid (square/stretched cards)
```
Há um regenerador novo: `automation/rebuild_listing.py` (regenera a listagem inteira; safe).

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
1. ✅ ~~Setup do cron~~ — FEITO em 2026-06-07 (ver topo). Cron ativo e 1º post publicado.
2. **aggregateRating 5.0/68 fabricado** ainda em ~140 páginas ANTIGAS do site (achado nº1 da
   auditoria, risco de penalidade Google). Posts NOVOS já nascem sem ele. Falta limpar o legado.
3. **Outros docs internos JÁ expostos** no repo/deploy (pré-existentes, não criados por nós):
   `SEO-GEO-AUDIT-FINDINGS.md`, `SPRINT-2-ACTION-CHECKLIST.md`, `SOCIAL-AUTOMATION.md`,
   `PASSO-A-PASSO-PAINEIS.md`, `_audit/`, `blog-topics-bank.json`. Usuário foi avisado; ofereci
   bloquear todos via `_redirects` igual fiz com /automation/*. Aguarda OK dele.
4. Sobreposições parciais blog×página de serviço (7 casos) — dívida leve, gerenciar com interlink.

## ✅ RESOLVIDO desde o handoff anterior
- 41 posts órfãos → listagem regenerada com os 91 (commit 30ae08b). Feito.

## Como retomar
"Continuar a automação do blog da Braza — ler automation/HANDOFF.md". Provável próximo passo:
guiar o setup dos secrets, ou atacar os itens em aberto (aggregateRating / 41 órfãos).
