/* Braza Cleaning — conversion tracking (GA4 + Meta-ready)
   Eventos: phone_call_click, whatsapp_click, generate_lead
   generate_lead dispara SÓ quando o POST do formulário ao braza-email-proxy responde res.ok. */
(function () {
  function safeGtag() { if (typeof gtag === 'function') { try { gtag.apply(null, arguments); } catch (e) {} } }
  function metaTrack(ev, params) { if (typeof fbq === 'function') { try { fbq('track', ev, params || {}); } catch (e) {} } }

  // 1) Cliques em telefone e WhatsApp (delegação — cobre todos os links da página)
  document.addEventListener('click', function (e) {
    var a = e.target.closest ? e.target.closest('a') : null;
    if (!a) return;
    var href = a.getAttribute('href') || '';
    if (href.indexOf('tel:') === 0) {
      safeGtag('event', 'phone_call_click', { link_url: href, page_path: location.pathname });
      metaTrack('Contact', { method: 'phone' });
    } else if (href.indexOf('wa.me') !== -1 || href.indexOf('whatsapp') !== -1) {
      safeGtag('event', 'whatsapp_click', { page_path: location.pathname });
      metaTrack('Contact', { method: 'whatsapp' });
    }
  }, true);

  // 2) Conversão de formulário (interceptação de fetch — não toca nos handlers inline)
  var _fetch = window.fetch;
  if (_fetch) {
    window.fetch = function (url) {
      var p = _fetch.apply(this, arguments);
      try {
        var u = (typeof url === 'string') ? url : (url && url.url) || '';
        if (u.indexOf('braza-email-proxy') !== -1) {
          p.then(function (res) {
            if (res && res.ok) {
              safeGtag('event', 'generate_lead', { lead_type: 'web_form', page_path: location.pathname });
              metaTrack('Lead', { content_name: 'web_form' });
            }
          }).catch(function () {});
        }
      } catch (err) {}
      return p;
    };
  }
})();
