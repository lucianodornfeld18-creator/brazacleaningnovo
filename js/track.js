/* Braza Cleaning conversion tracking (GA4 + Meta-ready)
   Tracks successful Web3Forms leads plus phone and WhatsApp contacts.
   Adds page and UTM attribution to Web3Forms submissions without changing
   the form markup duplicated across the static site. */
(function () {
  'use strict';

  function safeGtag() {
    if (typeof gtag === 'function') {
      try { gtag.apply(null, arguments); } catch (e) {}
    }
  }

  function metaTrack(eventName, params) {
    if (typeof fbq === 'function') {
      try { fbq('track', eventName, params || {}); } catch (e) {}
    }
  }

  var attributionStorageKey = 'braza_attribution_v1';

  function currentCampaignParams() {
    var params = {};
    try {
      var search = new URLSearchParams(window.location.search);
      ['utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content', 'gclid'].forEach(function (key) {
        var value = search.get(key);
        if (value) params[key] = value;
      });
    } catch (e) {}
    return params;
  }

  function campaignParams() {
    var current = currentCampaignParams();
    var stored = {};
    try {
      stored = JSON.parse(window.sessionStorage.getItem(attributionStorageKey) || '{}') || {};
    } catch (e) {}

    if (!stored.landing_page) stored.landing_page = window.location.pathname;
    Object.keys(current).forEach(function (key) { stored[key] = current[key]; });

    try {
      window.sessionStorage.setItem(attributionStorageKey, JSON.stringify(stored));
    } catch (e) {}
    return stored;
  }

  function eventParams(extra) {
    var params = {
      page_path: window.location.pathname,
      page_location: window.location.href,
      page_title: document.title
    };
    var campaign = campaignParams();
    Object.keys(campaign).forEach(function (key) { params[key] = campaign[key]; });
    if (extra) Object.keys(extra).forEach(function (key) { params[key] = extra[key]; });
    return params;
  }

  function trackContact(method, href) {
    var params = eventParams({ contact_method: method, link_url: href });
    safeGtag('event', 'contact_attempt', params);
    metaTrack('Contact', { method: method });
  }

  function isQuoteCta(href) {
    return href === '#contact' || href === '/#contact' ||
      href.indexOf('/contact/') === 0 || href.indexOf('brazacleaning.com/contact/') !== -1;
  }

  document.addEventListener('click', function (event) {
    var link = event.target.closest ? event.target.closest('a') : null;
    if (!link) return;

    var href = link.getAttribute('href') || '';
    if (href.indexOf('tel:') === 0) {
      trackContact('phone', href);
    } else if (href.indexOf('wa.me') !== -1 || href.indexOf('whatsapp') !== -1) {
      trackContact('whatsapp', href);
    } else if (href.indexOf('sms:') === 0) {
      trackContact('sms', href);
    } else if (href.indexOf('mailto:') === 0) {
      trackContact('email', href);
    } else if (isQuoteCta(href)) {
      safeGtag('event', 'quote_cta_click', eventParams({ link_url: href }));
    }
  }, true);

  document.addEventListener('focusin', function (event) {
    var form = event.target.closest ? event.target.closest('form#quoteForm') : null;
    if (!form || form.getAttribute('data-braza-form-started') === 'true') return;
    form.setAttribute('data-braza-form-started', 'true');
    safeGtag('event', 'form_start', eventParams({ form_id: 'quoteForm' }));
  }, true);

  document.addEventListener('submit', function (event) {
    var form = event.target && event.target.matches && event.target.matches('form#quoteForm') ? event.target : null;
    if (!form) return;
    safeGtag('event', 'form_submit_attempt', eventParams({ form_id: 'quoteForm' }));
  }, true);

  var originalFetch = window.fetch;
  if (!originalFetch) return;

  window.fetch = function (input, init) {
    var url = (typeof input === 'string') ? input : (input && input.url) || '';
    var isWeb3FormsLead = url.indexOf('api.web3forms.com/submit') !== -1;
    var requestInit = init;

    if (isWeb3FormsLead && init && typeof init.body === 'string') {
      try {
        var body = JSON.parse(init.body);
        if (body && typeof body === 'object') {
          var attribution = campaignParams();
          if (!body.page_url) body.page_url = window.location.href;
          if (!body.page_path) body.page_path = window.location.pathname;
          if (!body.landing_page) body.landing_page = attribution.landing_page;
          if (!body.source) body.source = attribution.landing_page;
          var botcheck = document.querySelector('form#quoteForm [name="botcheck"]');
          if (botcheck && !body.botcheck) body.botcheck = !!botcheck.checked;
          Object.keys(attribution).forEach(function (key) {
            if (key === 'landing_page') return;
            if (!body[key]) body[key] = attribution[key];
          });

          requestInit = Object.assign({}, init, { body: JSON.stringify(body) });
        }
      } catch (e) {}
    }

    var request = originalFetch.call(this, input, requestInit);

    if (isWeb3FormsLead) {
      request.then(function (response) {
        if (!response || !response.ok || !response.clone) return;
        return response.clone().json().then(function (payload) {
          if (!payload || payload.success !== true) return;
          safeGtag('event', 'generate_lead', eventParams({
            lead_type: 'quote_form',
            form_id: 'quoteForm',
            form_provider: 'web3forms'
          }));
          metaTrack('Lead', { content_name: 'quote_form' });
        }).catch(function () {});
      }).catch(function () {});
    }

    return request;
  };
})();
