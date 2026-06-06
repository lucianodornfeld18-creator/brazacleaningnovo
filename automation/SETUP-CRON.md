# Setup do blog automático (GitHub Actions)

O que o robô faz: **seg/qua/sex** gera 1 post GEO/AEO (Claude API + web search),
valida (anti-canibalização + preço ≥ $120), atualiza listagem/sitemap/interlinks e
**publica direto** (commit + push → deploy Cloudflare). **Sexta** manda 1 email-digest.

## O que VOCÊ precisa fazer (uma vez)

### 1. Adicionar 2 secrets no GitHub
No repositório → **Settings → Secrets and variables → Actions → New repository secret**:

| Secret | Valor | Onde pegar |
|---|---|---|
| `ANTHROPIC_API_KEY` | sua chave da Claude API (`sk-ant-...`) | console.anthropic.com → API Keys |
| `RESEND_API_KEY` | sua chave do Resend (`re_...`) | resend.com → API Keys (pro digest) |

### 2. Permitir que o Actions faça push
**Settings → Actions → General → Workflow permissions** → marcar **"Read and write permissions"** → Save.
(Os workflows já pedem `contents: write`, mas essa opção precisa estar ligada.)

### 3. (Resend) verificar o domínio de envio
O digest envia de `website@brazacleaning.com`. No Resend, **Domains → Add Domain → brazacleaning.com**
e adicionar os registros DNS no Cloudflare. Sem isso, o email pode cair em spam ou falhar.

## Como testar antes de confiar no cron
No GitHub → aba **Actions** → **Auto Blog Post** → botão **"Run workflow"** (dispara na hora).
Vê o log, confere o commit/post gerado. Mesma coisa pra **Weekly Blog Digest**.

## Horários (UTC)
- Posts: `0 13 * * 1,3,5` → seg/qua/sex 13:00 UTC (~9h da manhã na Flórida).
- Digest: `0 14 * * 5` → sexta 14:00 UTC (depois do post de sexta).
Pra mudar, edite o `cron:` nos arquivos `.github/workflows/blog-*.yml`.

## Rotação de foco (definida em automation/agent_run.py)
- **Seg** — residencial biweekly/recurring (maior margem): The Villages, Leesburg, Wildwood, Minneola, Clermont, Winter Garden, Windermere.
- **Qua** — Airbnb/temporada: Kissimmee, Davenport, Celebration, Orlando.
- **Sex** — oportunista: deep/move-out/move-in/comercial.

## Custo aproximado
GitHub Actions: grátis. Claude API: ~centavos por post. Resend: grátis até 3.000 emails/mês.

## Se algo falhar
- Workflow vermelho na aba Actions = o post foi rejeitado pelo gate de canibalização (nada publicado — normal de vez em quando) **ou** erro real (abrir o log).
- Para pausar: **Actions → Auto Blog Post → ⋯ → Disable workflow**.
