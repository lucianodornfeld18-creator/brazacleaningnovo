/* Braza Cleaning conversion tracking (GA4 + Meta-ready)
   Tracks successful Web3Forms leads plus contact/quote intent.
   Adds page and UTM attribution to Web3Forms submissions without changing
   the form markup duplicated across the static site. */
(function () {
  'use strict';

  // Keep all tracker state on window so an accidental duplicate script include
  // cannot install a second set of listeners or send a second conversion.
  var trackerState = window.__brazaConversionTrackingState;
  if (!trackerState || typeof trackerState !== 'object') {
    trackerState = {};
    window.__brazaConversionTrackingState = trackerState;
  }
  if (trackerState.initialized) return;
  trackerState.initialized = true;

  function safeGtag() {
    var args = arguments;
    if (typeof window.gtag === 'function') {
      try {
        window.gtag.apply(window, args);
        return true;
      } catch (e) {}
    }

    // The inline Google tag normally creates this queue before this file loads.
    // Create/use it defensively so events are retained if gtag.js is still loading.
    try {
      var queue = window.dataLayer;
      if (!queue || typeof queue.push !== 'function') {
        queue = [];
        window.dataLayer = queue;
      }
      queue.push(args);
      return true;
    } catch (e) {
      return false;
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
      // Do not pass arbitrary query-string values to GA. Campaign values below
      // are intentionally allow-listed instead.
      page_location: (window.location.origin || '') + window.location.pathname,
      page_title: document.title
    };
    var campaign = campaignParams();
    Object.keys(campaign).forEach(function (key) { params[key] = campaign[key]; });
    if (extra) Object.keys(extra).forEach(function (key) { params[key] = extra[key]; });
    return params;
  }

  function trackContact(method) {
    // Do not send tel:, sms:, mailto: or WhatsApp URLs to analytics: each can
    // contain a phone number, e-mail address, prefilled message, or other PII.
    var params = eventParams({ contact_method: method });
    safeGtag('event', 'contact_attempt', params);
    metaTrack('Contact', { method: method });
  }

  function quoteCtaTarget(href) {
    href = (href || '').trim();
    if (href === '#contact' || href === '/#contact') return 'contact_anchor';

    try {
      var url = new URL(href, window.location.origin);
      var isInternal = url.origin === window.location.origin ||
        url.hostname === 'brazacleaning.com' || url.hostname === 'www.brazacleaning.com';
      var path = url.pathname.replace(/\/+$/, '') || '/';
      if (isInternal && path === '/contact') return 'contact_page';
    } catch (e) {}

    return '';
  }

  document.addEventListener('click', function (event) {
    var link = event.target.closest ? event.target.closest('a') : null;
    if (!link) return;

    var href = link.getAttribute('href') || '';
    if (href.indexOf('tel:') === 0) {
      trackContact('phone');
    } else if (href.indexOf('wa.me') !== -1 || href.indexOf('whatsapp') !== -1) {
      trackContact('whatsapp');
    } else if (href.indexOf('sms:') === 0) {
      trackContact('sms');
    } else if (href.indexOf('mailto:') === 0) {
      trackContact('email');
    } else {
      var ctaTarget = quoteCtaTarget(href);
      if (ctaTarget) {
        // A fixed target label preserves useful attribution without passing
        // query strings or any arbitrary destination into GA4.
        safeGtag('event', 'quote_cta_click', eventParams({ cta_target: ctaTarget }));
      }
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
    // This is the only form_submit_attempt listener. The initialization guard
    // above prevents a duplicated track.js include from adding another one.
    safeGtag('event', 'form_submit_attempt', eventParams({ form_id: 'quoteForm' }));
  }, true);

  function emitLeadOnce() {
    if (trackerState.generateLeadEmitted) return false;
    trackerState.generateLeadEmitted = true;

    // Deliberately exclude all submitted form fields: GA receives only fixed
    // conversion metadata plus the allow-listed attribution in eventParams().
    safeGtag('event', 'generate_lead', eventParams({
      lead_type: 'quote_form',
      form_id: 'quoteForm',
      form_provider: 'web3forms'
    }));
    metaTrack('Lead', { content_name: 'quote_form' });
    return true;
  }

  // Form handlers call this after their own Web3Forms success check. Exposing
  // the same once-only emitter keeps the inline fallback and fetch observer
  // from ever creating two GA4 conversions for one lead.
  window.__brazaTrackLeadSuccess = emitLeadOnce;

  function isVisibleInlineSuccess(element) {
    if (!element || element.hidden || element.getAttribute('aria-hidden') === 'true') return false;
    if (!window.getComputedStyle) return element.style.display !== 'none';

    var style = window.getComputedStyle(element);
    return style.display !== 'none' && style.visibility !== 'hidden';
  }

  function observeInlineSuccess() {
    function checkForSuccess() {
      var success = document.getElementById('formSuccess');
      if (isVisibleInlineSuccess(success)) emitLeadOnce();
    }

    checkForSuccess();
    if (typeof window.MutationObserver !== 'function' || !document.documentElement) return;

    var observer = new window.MutationObserver(function () {
      checkForSuccess();
      if (trackerState.generateLeadEmitted) observer.disconnect();
    });
    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ['aria-hidden', 'class', 'hidden', 'style'],
      childList: true,
      subtree: true
    });
  }

  // Some pages display #formSuccess after consuming the response themselves.
  // Observing it complements the fetch wrapper and uses the same once-per-page
  // emitter, so the two confirmation signals cannot double-count a lead.
  observeInlineSuccess();

  var originalFetch = window.fetch;
  if (!originalFetch) return;

  if (originalFetch.__brazaWeb3FormsTracking) return;

  var trackedFetch = function (input, init) {
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
          emitLeadOnce();
        }).catch(function () {});
      }).catch(function () {});
    }

    return request;
  };

  trackedFetch.__brazaWeb3FormsTracking = true;
  window.fetch = trackedFetch;
})();
