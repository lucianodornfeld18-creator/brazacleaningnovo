# RUNBOOK — Blog Automático Braza Cleaning (Top-1 Google + GEO/AEO)

Pipeline operacional executado **3x/semana (seg/qua/sex)** pelo agente agendado.
Objetivo: não é "só postar" — é **pesquisar com foco na prioridade da empresa**,
**checar canibalização**, **criar post GEO/AEO citável pela IA e top-1 orgânico**, e
atualizar listagem/sitemap/schema/interlinks automaticamente.

> Adaptado ao stack REAL do repo (HTML hand-written + scripts Python).
> O build system Python idealizado do prompt original (`_data.py`/`_gen.py`/`_build_*.py`)
> **não existe** — esta automação usa os scripts em `automation/`.

---

## Stack desta automação

| Peça | Papel |
|---|---|
| `_content_map.json` | Ledger de TODO conteúdo (184+ URLs). Trava anti-canibalização. |
| `automation/check_canib.py` | Gate de canibalização (PASS/ADJUST/REJECT). |
| `automation/queue/<slug>.json` | Conteúdo estruturado do post (o agente preenche). |
| `automation/build_post.py` | Gera `blog/<slug>/index.html` completo (schema GEO/AEO, FAQ, etc). |
| `automation/update_site.py` | Insere card no grid + categoria + sitemap + content_map. |
| `automation/_inventory.py` | Regenera `_content_map.json` do zero (varre o site). |
| `automation/notify.py` | Email de resumo via Resend worker. |

## Regras fixas (valem sempre)

- **Idioma:** EN por padrão (público americano, prioridade do v2). PT só se o tópico for claramente para brasileiros.
- **NAP canônico:** Braza Cleaning Services · Ocoee, FL 34761 · (689) 242-7469. Nunca inventar — já embutido em `build_post.py`.
- **CTA primário:** telefone + formulário (`/#contact`). WhatsApp despriorizado.
- **Foco geográfico (priorize):**
  - Residencial: The Villages, Leesburg, Wildwood, Minneola, Clermont, Winter Garden, Windermere.
  - Airbnb/temporada: Kissimmee, Davenport, Celebration, Orlando.
  - **Maior margem = biweekly/recurring residential.** Priorizar tópicos que empurram esse serviço e o Airbnb turnover.
- **Nunca página órfã:** todo post linka para 1 página de serviço + 1 de localidade + 1 post relacionado (campo `interlinks`), e é linkado de volta pela listagem.
- **Imagens:** reusar pool `/images/` existente (escolher a mais relevante; nunca referenciar imagem inexistente).
- **Sem aggregateRating fabricado** (o `build_post.py` já omite — corrige o achado nº 1 da auditoria).
- **PREÇO MÍNIMO $120 — NUNCA exibir nenhum valor abaixo de $120.** Tetos/ranges máximos livres, mas o piso de qualquer preço é $120. O `build_post.py` tem trava automática (`assert_min_price`) que **bloqueia a geração** se houver `$<120` no conteúdo.

## Padrão de qualidade — meta: SEMPRE top-1 Google + top-1 citação de IA

Cada post deve ser a **fonte canônica** do tópico, não um texto raso. Padrão fixo:
- **Profundidade-alvo: ~1.200–1.500 palavras** de conteúdo útil (sem padding). Cobrir a intenção por completo: preço + o que afeta o preço + comparação (frequência/serviço) + o que está incluído + 1ª visita/expectativa + ângulo hiperlocal.
- **≥ 6 seções H2 em forma de pergunta**, **≥ 2 tabelas/listas comparativas extraíveis**, **8 FAQs**.
- **Dados específicos e verificáveis** (faixas de preço reais, comunidades locais reais, anos de operação) — IA cita fatos estruturados, não generalidades.
- **E-E-A-T:** autor real, experiência, prova local (cidades atendidas, bairros reais). Entidade Braza + serviço + cidade inequívocos.

---

## FASE 2 — Pesquisa (GEO/AEO first)

1. Escolher um **serviço × cidade de foco** ainda não coberto (ver gaps no `_content_map.json`). Rodar foco em rotação: seg=residencial biweekly, qua=Airbnb turnover, sex=oportunista (deep/move-out/comercial ou cidade secundária).
2. Levantar **perguntas reais** que alguém faria ao Google **e a uma IA**: "how much", "is it worth it", "how often", "what's included", "biweekly vs weekly", "move-out checklist", etc. Usar web search se disponível; senão derivar dos gaps.
3. Ranquear 3–5 candidatos por: alinhamento com prioridade da empresa (peso maior) × gap real × potencial AEO (pergunta clara, resposta objetiva) × intenção local/comercial.

## FASE 3 — Gate de canibalização (OBRIGATÓRIO)

```
py automation/check_canib.py "<keyword primaria>" "<titulo candidato>"
```
- **PASS (exit 0):** seguir.
- **ADJUST (exit 2):** seguir, mas definir pilar (página de serviço) vs suporte (este post) e **incluir interlink recíproco** com a URL apontada.
- **REJECT (exit 3):** trocar de ângulo (long-tail distinto) ou atualizar o post existente. **Não criar URL duplicada.**

Confirmar também que `title` e `meta_desc` não duplicam nenhum existente.

## FASE 4 — Escrever o conteúdo → `automation/queue/<slug>.json`

Preencher o JSON (ver `automation/queue/_example.json` como molde). Exigências de conteúdo:
- `answer_first`: **40–60 palavras**, resposta direta à pergunta principal (vira citação de IA + snippet). É o bloco `.answer-first` (speakable).
- `sections`: H2 **em forma de pergunta** batendo com as queries; conteúdo **escaneável** (listas, **tabela comparativa** de preço/frequência, passos). Sem padding.
- `faq`: 5–8 perguntas com respostas curtas (espelha o FAQPage schema, gerado automático).
- `interlinks`: 3–6, **recíprocos**, âncora descritiva (1+ página de serviço, 1+ localidade, 1+ post relacionado).
- `hero_img`: caminho real de `/images/` + `hero_alt` descritivo com keyword natural.
- `title` < 60 chars · `meta_desc` < 155 chars · ambos únicos.
- `read_min`: estimativa honesta.

## FASE 5 — Gerar + validar

```
py automation/build_post.py <slug>
```
Gera `blog/<slug>/index.html` com: BlogPosting + FAQPage + BreadcrumbList + LocalBusiness + Speakable, answer-first, TOC, FAQ visível, CTA, og/twitter, geo.region, "Updated" visível.

**Validar antes de seguir:**
- Os 5 blocos JSON-LD são válidos (parse JSON).
- Todos os `interlinks` resolvem para URLs reais (existem no repo/`_content_map.json`).
- `title`/`meta_desc` únicos (re-cheque o content_map).

## FASE 6 — Publicar tudo

```
py automation/update_site.py <slug>          # card no grid (topo) + categoria + sitemap + content_map
```
Depois:
1. Inserir **interlinks reversos** nas páginas pilar (adicionar link para o novo post na página de serviço/localidade citada — manter recíproco).
2. `git add -A && git commit -m "Blog: <título>"`
3. `git push` → deploy Cloudflare. *(Em produção é automático; durante validação, só com OK.)*
4. `py automation/notify.py <slug>` → email de resumo.

## Relatório final (no commit + email)
Tópico · keyword primária · veredito anti-caniba · arquivos criados/alterados · interlinks (ambas direções) · schema incluído.

---

## CHECKLIST FINAL
- [ ] answer-first 40–60 palavras (speakable)
- [ ] H2 em forma de pergunta + FAQ visível espelhando FAQPage
- [ ] tabela/lista comparativa extraível
- [ ] 3–6 interlinks recíprocos, sem órfã
- [ ] imagem real do pool + alt + og:image
- [ ] title<60 / meta<155 únicos + canonical + OG/Twitter
- [ ] datePublished + dateModified + "Updated" visível
- [ ] BlogPosting + FAQPage + BreadcrumbList + LocalBusiness + Speakable
- [ ] NAP Ocoee 34761 consistente
- [ ] sitemap + listagem + categoria + content_map atualizados
- [ ] build/grid validados (grid não quebra), sem aggregateRating fabricado
