# 🔧 Correções de Rastreamento — brazacleaning.com

> **Para a sessão do Claude Code que vai executar:** este documento é uma ordem de serviço completa.
> Todos os fatos abaixo foram verificados em 02/06/2026 cruzando o código deste repositório com dados
> reais do Google Ads, Meta Ads, GA4 e Search Console (via Windsor.ai). Não é necessário redescobrir nada —
> mas valide os trechos de código citados antes de editar, pois o repo pode ter mudado.

---

## 📌 Contexto: por que essas correções importam

O site recebe tráfego pago e orgânico, gera leads por formulário/telefone/WhatsApp, **mas nenhuma
conversão é medida**. Consequências reais observadas nos dados de maio/2026:

| Dado observado | Causa raiz (neste código) |
|---|---|
| GA4 (`G-5YVG8BKPSD`) mostra **0 conversões** com ~355 sessões/mês | Formulário não dispara nenhum evento `gtag()` ao enviar |
| Campanha Google Ads "Airbnb Cleaning Service" gastou $141, teve 134 cliques e mostra **0 conversões** | Site não tem tag de conversão do Google Ads (AW-) — era impossível atribuir |
| Cliques em telefone/WhatsApp invisíveis nos relatórios | Links `tel:` e `wa.me` não têm rastreamento de clique |
| Campanhas do Meta não podem otimizar para conversão no site | Pixel do Meta não está instalado |

**Objetivo final:** todo lead (formulário, ligação, WhatsApp) registrado no GA4 → importado no Google Ads →
campanhas voltam a rodar com otimização automática por conversão.

---

## 📋 Fatos verificados do repositório (não precisa redescobrir)

| Item | Valor |
|---|---|
| **Caminho local** | `C:\Users\lucia\Documents\brazacleaningnovo` |
| **Git** | branch `main` → `https://github.com/lucianodornfeld18-creator/brazacleaningnovo.git` |
| **Deploy** | Cloudflare Pages — deploy automático no push para `main` |
| **Tecnologia** | HTML estático puro (sem framework, sem build step) |
| **GA4 já instalado** | `G-5YVG8BKPSD` via gtag.js em todas as páginas |
| **Formulário de lead** | POST JSON para `https://braza-email-proxy.lucianodornfeld18.workers.dev` |
| **Arquivos com o formulário** | **150 arquivos** (busque por `braza-email-proxy`) |
| **Links de telefone** | `tel:6892427469` — centenas de ocorrências em ~180+ arquivos |
| **Links de WhatsApp** | `wa.me/16892427469` — **544 ocorrências em 182 arquivos** |
| **CSP** | Configurado no arquivo `_headers` — **verificar antes de adicionar JS externo** |
| **Páginas PT** | `/pt/*` também têm formulário (4 páginas) — incluir nas correções |

### ⚠️ ATENÇÃO: estado do working tree

Há **mudanças não commitadas** no repo (em 02/06/2026):
- `.gitignore` (+6 linhas)
- `index.html` (36 linhas alteradas)

**Antes de começar qualquer tarefa:** rode `git status` e `git diff`, entenda o que são essas mudanças
e pergunte ao usuário se devem ser commitadas, descartadas ou preservadas. NÃO sobrescreva sem perguntar.

### Código atual do formulário (referência)

O handler está **inline e duplicado** nos 150 arquivos. Trecho relevante (em `index.html`, ~linha 946):

```javascript
form.addEventListener('submit',async function(e){
  e.preventDefault();
  // ... monta objeto d com os campos ...
  try{
    var res=await fetch('https://braza-email-proxy.lucianodornfeld18.workers.dev',{method:'POST',...});
    if(res.ok){document.getElementById('formWrap').style.display='none';document.getElementById('formSuccess').style.display='block';}
    else{...}
  }catch(err){...}
});
```

O ponto de sucesso é `if(res.ok){...}` — é ali que a conversão acontece e não é registrada.

---

## ✅ TAREFAS (em ordem de prioridade)

### TAREFA 0 — Resolver o working tree sujo
1. `git status` + `git diff` para entender as mudanças pendentes em `.gitignore` e `index.html`
2. Perguntar ao usuário o que fazer com elas (commitar / descartar)
3. Só prosseguir com o working tree limpo

---

### TAREFA 1 — Rastreamento de conversões (a mais importante) ⭐

**Abordagem recomendada: arquivo JS central + interceptação** (NÃO editar os 150 handlers inline um a um).

Criar `/js/track.js` com:

```javascript
(function(){
  function safeGtag(){ if(typeof gtag==='function'){ gtag.apply(null,arguments); } }

  // 1. Cliques em telefone e WhatsApp (delegação de evento — cobre todos os links da página)
  document.addEventListener('click', function(e){
    var a = e.target.closest ? e.target.closest('a') : null;
    if(!a) return;
    var href = a.getAttribute('href') || '';
    if(href.indexOf('tel:') === 0){
      safeGtag('event', 'phone_call_click', { link_url: href, page_path: location.pathname });
    } else if(href.indexOf('wa.me') !== -1){
      safeGtag('event', 'whatsapp_click', { page_path: location.pathname });
    }
  }, true);

  // 2. Conversão de formulário (interceptação de fetch — não precisa tocar nos 150 handlers inline)
  var _fetch = window.fetch;
  window.fetch = function(url){
    var p = _fetch.apply(this, arguments);
    try{
      var u = (typeof url === 'string') ? url : (url && url.url) || '';
      if(u.indexOf('braza-email-proxy') !== -1){
        p.then(function(res){
          if(res && res.ok){
            safeGtag('event', 'generate_lead', { lead_type: 'web_form', page_path: location.pathname });
          }
        }).catch(function(){});
      }
    }catch(err){}
    return p;
  };
})();
```

Depois, inserir em **todas as páginas HTML** (busca e substituição em massa):

```html
<!-- inserir antes de </body> em todos os arquivos *.html -->
<script src="/js/track.js" defer></script>
```

**Passos:**
1. Verificar o CSP no arquivo `_headers` — confirmar que `script-src` permite `'self'` (JS do próprio domínio). Se não permitir, ajustar o CSP.
2. Criar `/js/track.js`
3. Escrever um script (PowerShell ou Node) que insira a tag `<script src="/js/track.js" defer></script>` antes de `</body>` em todos os `.html` do repo (exceto `/admin/` se preferir). **Idempotente**: não inserir duas vezes se já existir.
4. Testar localmente: abrir `index.html`, simular clique em tel/wa.me e envio de formulário, conferir no console que os eventos disparam (usar GA4 DebugView com `?debug_mode=1` ou extensão Tag Assistant).
5. Commit: `Tracking: adiciona track.js com eventos de conversao (form, telefone, WhatsApp)`

**Critério de aceite:** evento `generate_lead` aparece no GA4 DebugView ao enviar o formulário de teste;
eventos `phone_call_click` e `whatsapp_click` aparecem ao clicar nos links.

---

### TAREFA 2 — Cache do Cloudflare para o novo JS

O `_headers` configura cache de 1 ano para assets. Verificar se `/js/*` está coberto pela regra de cache
e se isso é desejável (se o track.js mudar no futuro, o cache de 1 ano atrasa a atualização).

**Recomendação:** adicionar regra específica no `_headers`:
```
/js/track.js
  Cache-Control: public, max-age=3600
```

Commit junto com a Tarefa 1 ou separado.

---

### TAREFA 3 — Preparar a integração com Google Ads (requer dado do usuário)

O site **não tem** tag de conversão do Google Ads. Há dois caminhos — **o caminho A é o recomendado**
e não precisa de código adicional:

**Caminho A (recomendado — sem código):** importar a conversão do GA4 no Google Ads
1. Isso é feito nos painéis (GA4 e Google Ads), não no código
2. Gerar para o usuário um passo-a-passo claro:
   - GA4 → Admin → Events → marcar `generate_lead` como Key Event
   - Google Ads → Tools → Conversions → New → Import → Google Analytics 4 → `generate_lead`
   - Google Ads → Tools → Linked accounts → confirmar vínculo com GA4 `G-5YVG8BKPSD`
3. Salvar esse passo-a-passo em `PASSO-A-PASSO-PAINEIS.md` na raiz do repo

**Caminho B (alternativo — com código):** tag AW- direta
- Requer que o usuário crie uma conversão no Google Ads e forneça o ID `AW-XXXXXXXXX` e o label
- Se o usuário fornecer, adicionar `gtag('config', 'AW-XXXXXXXXX')` ao lado do config do GA4 existente
  e o evento de conversão no track.js

---

### TAREFA 4 — Pixel do Meta (requer dado do usuário)

O site não tem Pixel do Meta. Sem ele, campanhas de tráfego no Facebook/Instagram não otimizam
para conversões no site e não dá pra fazer retargeting de visitantes.

1. **Pedir ao usuário o Pixel ID** (Meta Business Manager → Events Manager → Data Sources)
2. Quando fornecido, adicionar o snippet base do pixel em todas as páginas (mesma técnica de inserção
   em massa da Tarefa 1), junto do GA4 existente:
```html
<!-- Meta Pixel -->
<script>
!function(f,b,e,v,n,t,s){if(f.fbq)return;n=f.fbq=function(){n.callMethod?
n.callMethod.apply(n,arguments):n.queue.push(arguments)};if(!f._fbq)f._fbq=n;
n.push=n;n.loaded=!0;n.version='2.0';n.queue=[];t=b.createElement(e);t.async=!0;
t.src=v;s=b.getElementsByTagName(e)[0];s.parentNode.insertBefore(t,s)}(window,
document,'script','https://connect.facebook.net/en_US/fbevents.js');
fbq('init', 'PIXEL_ID_AQUI');
fbq('track', 'PageView');
</script>
```
3. No `track.js`, adicionar `fbq('track', 'Lead')` junto do `generate_lead` (com guard `typeof fbq === 'function'`)
4. **Atualizar o CSP no `_headers`** para permitir `connect.facebook.net`
5. Commit separado: `Tracking: adiciona Meta Pixel`

⚠️ Se o usuário não tiver o Pixel ID em mãos, pular esta tarefa e deixar registrado no final.

---

### TAREFA 5 — Verificação final e deploy

1. Rodar uma verificação em todos os arquivos editados: HTML continua válido, nenhum `</body>` duplicado,
   scripts inseridos uma única vez
2. Conferir que `/pt/*` (páginas em português) também receberam o track.js
3. `git push` para `main` → Cloudflare Pages faz deploy automático
4. Após o deploy (~2 min), testar no site em produção:
   - Abrir `https://brazacleaning.com/?debug_mode=1`
   - Enviar um formulário de teste (avisar o usuário que vai chegar um e-mail de teste)
   - Confirmar no GA4 DebugView que `generate_lead`, `phone_call_click` e `whatsapp_click` disparam
5. Relatar ao usuário o que foi feito e o que falta fazer nos painéis (Tarefa 3, passos manuais)

---

## 🚫 O que NÃO fazer

- **Não** editar os 150 handlers de formulário inline um por um (use a interceptação de fetch)
- **Não** remover ou alterar o fluxo atual do formulário (ele funciona — só falta o evento)
- **Não** mexer no Cloudflare Worker `braza-email-proxy` (está fora deste repo e funcionando)
- **Não** alterar conteúdo/SEO das páginas (títulos, schema, textos) — escopo aqui é só rastreamento
- **Não** fazer push sem testar localmente primeiro
- **Não** commitar tudo num commit só — separar por tarefa

## ✋ O que depende do usuário (perguntar quando chegar na tarefa)

| Tarefa | O que pedir |
|---|---|
| Tarefa 0 | O que fazer com as mudanças não commitadas |
| Tarefa 3 | Acesso/confirmação de que GA4 e Google Ads estão vinculados (ou orientá-lo a fazer) |
| Tarefa 4 | Pixel ID do Meta (ou pular) |
| Tarefa 5 | Confirmar que pode receber e-mail de teste do formulário |

---

*Documento gerado em 02/06/2026 a partir do diagnóstico de marketing (Windsor.ai) + auditoria do código.
Dashboards de referência: `Desktop\dashboard-braza-cleaning.html`.*
