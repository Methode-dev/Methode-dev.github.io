/* Mesure d'audience et de conversions, chargée sur toutes les pages.
 *
 * Règle : rien n'est déposé ni envoyé avant le choix du visiteur dans le bandeau Axeptio.
 * Google (Analytics, Ads) et LinkedIn ne sont chargés qu'après consentement au service
 * correspondant (mode « basique » du Consent Mode v2, recommandé pour la CNIL).
 *
 * À remplir avant la mise en ligne (un champ vide = l'outil n'est pas chargé) :
 *   ga4            ID de flux Google Analytics 4        ex. 'G-XXXXXXXXXX'
 *   googleAds      ID du compte Google Ads              ex. 'AW-XXXXXXXXXX'
 *   googleAdsLead  libellé de la conversion « contact » ex. 'AbCdEfGhIjK'
 *   linkedin       ID partenaire de l'Insight Tag       ex. '1234567'
 *   linkedinLead   ID de la conversion « contact »      ex. '12345678'
 * Les noms de services (vendors) doivent correspondre à ceux du projet Axeptio.
 */
(function () {
  'use strict';

  var CONFIG = {
    axeptioClientId: '6ac395fd46081e00d620b4b1',
    axeptioCookiesVersion: '7ee846a8-0530-41d2-904a-be6936e37d6a',
    ga4: '',
    googleAds: '',
    googleAdsLead: '',
    linkedin: '',
    linkedinLead: '',
    vendors: {
      google: ['google_analytics', 'Google_Analytics', 'google_ads', 'Google_Ads'],
      linkedin: ['linkedin', 'LinkedIn', 'linkedin_insight_tag']
    }
  };

  var w = window, d = document;

  function charger(src) {
    var s = d.createElement('script');
    s.async = true;
    s.src = src;
    d.head.appendChild(s);
  }

  function accepte(choix, noms) {
    for (var i = 0; i < noms.length; i++) if (choix[noms[i]]) return true;
    return false;
  }

  /* ---------- Google : consentement refusé par défaut ---------- */
  w.dataLayer = w.dataLayer || [];
  w.gtag = w.gtag || function () { w.dataLayer.push(arguments); };
  w.gtag('consent', 'default', {
    analytics_storage: 'denied',
    ad_storage: 'denied',
    ad_user_data: 'denied',
    ad_personalization: 'denied',
    wait_for_update: 500
  });

  var googleCharge = false;
  function chargerGoogle() {
    var id = CONFIG.ga4 || CONFIG.googleAds;
    if (googleCharge || !id) return;
    googleCharge = true;
    charger('https://www.googletagmanager.com/gtag/js?id=' + encodeURIComponent(id));
    w.gtag('js', new Date());
    if (CONFIG.ga4) w.gtag('config', CONFIG.ga4);
    if (CONFIG.googleAds) w.gtag('config', CONFIG.googleAds);
  }

  /* ---------- LinkedIn Insight Tag ---------- */
  var linkedinCharge = false;
  function chargerLinkedin() {
    if (linkedinCharge || !CONFIG.linkedin) return;
    linkedinCharge = true;
    w._linkedin_partner_id = CONFIG.linkedin;
    w._linkedin_data_partner_ids = w._linkedin_data_partner_ids || [];
    w._linkedin_data_partner_ids.push(CONFIG.linkedin);
    if (!w.lintrk) {
      w.lintrk = function (a, b) { w.lintrk.q.push([a, b]); };
      w.lintrk.q = [];
    }
    charger('https://snap.licdn.com/li.lms-analytics/insight.min.js');
  }

  /* ---------- Bandeau Axeptio ---------- */
  w.axeptioSettings = {
    clientId: CONFIG.axeptioClientId,
    cookiesVersion: CONFIG.axeptioCookiesVersion,
    googleConsentMode: {
      default: {
        analytics_storage: 'denied',
        ad_storage: 'denied',
        ad_user_data: 'denied',
        ad_personalization: 'denied',
        wait_for_update: 500
      }
    }
  };
  w._axcb = w._axcb || [];
  w._axcb.push(function (sdk) {
    sdk.on('cookies:complete', function (choix) {
      if (accepte(choix, CONFIG.vendors.google)) chargerGoogle();
      if (accepte(choix, CONFIG.vendors.linkedin)) chargerLinkedin();
    });
  });
  charger('https://static.axept.io/sdk.js');

  /* ---------- Événements ---------- */
  function evenement(nom, params) {
    if (googleCharge) w.gtag('event', nom, params || {});
  }

  function contact(origine) {
    evenement('generate_lead', { origine: origine, page: location.pathname });
    if (googleCharge && CONFIG.googleAds && CONFIG.googleAdsLead) {
      w.gtag('event', 'conversion', { send_to: CONFIG.googleAds + '/' + CONFIG.googleAdsLead });
    }
    if (linkedinCharge && CONFIG.linkedinLead) {
      w.lintrk('track', { conversion_id: Number(CONFIG.linkedinLead) });
    }
  }

  /* Formulaire de l'accueil : envoyé par son propre script après validation. */
  d.addEventListener('methode:contact', function () { contact('formulaire-accueil'); });

  /* Autres formulaires (pages réalisations, estimation, blog) envoyés au même worker.
     Écouté sur window : le script Webstudio de ces pages arrête l'événement au niveau du document. */
  w.addEventListener('submit', function (e) {
    var f = e.target;
    if (!f || f.id === 'form' || !f.action || f.action.indexOf('workers.dev') === -1) return;
    contact('formulaire');
  }, true);

  /* Clics sur le téléphone et l'adresse e-mail. */
  d.addEventListener('click', function (e) {
    var a = e.target.closest ? e.target.closest('a[href]') : null;
    if (!a) return;
    var h = a.getAttribute('href') || '';
    if (h.indexOf('tel:') === 0) { evenement('clic_telephone', { page: location.pathname }); contact('telephone'); }
    else if (h.indexOf('mailto:') === 0) { evenement('clic_email', { page: location.pathname }); contact('email'); }
  }, true);
})();
