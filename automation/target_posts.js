#!/usr/bin/env node
// One-shot: join audit.json with the set of slugs that DID get impressions in
// Google Search Console (last 3 months, via Windsor). Output = posts with ZERO
// impressions ("no ranking yet") + their audit flags, ranked worst-first.
const fs = require('fs');
const path = require('path');

// Slugs that appeared in GSC with >=1 impression (last_3m). Source: Windsor searchconsole.
const RANKED = new Set([
  'airbnb-cleaning-cost-orlando-fl','top-mistakes-airbnb-hosts-cleaning-kissimmee-fl',
  'airbnb-cleaning-cost-kissimmee-fl','house-cleaning-cost-the-villages-fl-guide',
  'airbnb-cleaning-cost-davenport-fl','airbnb-cleaning-cost-per-bedroom-kissimmee-fl',
  'house-cleaning-cost-leesburg-fl','house-cleaning-cost-davenport-fl',
  'house-cleaning-cost-kissimmee-fl','how-much-to-charge-airbnb-cleaning-fee-kissimmee',
  'airbnb-same-day-cleaning-kissimmee-davenport-fl','house-cleaning-cost-winter-garden-fl',
  'airbnb-turnover-checklist-orlando','airbnb-turnover-cleaning-disney-area-fl',
  'airbnb-turnover-cleaning-four-corners-fl','house-cleaning-cost-altamonte-springs-fl',
  'house-cleaning-cost-lady-lake-fl','house-cleaning-cost-maitland-fl',
  'house-cleaning-cost-ocoee-fl','house-cleaning-cost-orlando-fl',
  'house-cleaning-cost-summerfield-fl','professional-house-cleaning-the-villages-fl',
  'airbnb-cleaning-cost-celebration-fl','airbnb-cleaning-cost-per-square-foot-orlando-fl',
  'airbnb-cleaning-the-villages-fl','house-cleaning-cost-dr-phillips-fl',
  'house-cleaning-cost-winter-park-fl','trusted-cleaning-company-the-villages-fl',
  'vacation-rental-cleaning-cost-davenport-fl','vacation-rental-cleaning-the-villages-fl',
  'airbnb-cleaning-checklist-vacation-rental-kissimmee-fl','airbnb-cleaning-cost-four-corners-fl',
  'airbnb-cleaning-davenport-fl-turnover-checklist','airbnb-cleaning-orlando-reviews-bookings',
  'airbnb-linen-laundry-service-cost-kissimmee-fl','best-house-cleaning-services-clermont-fl',
  'cleanliness-affects-airbnb-reviews-kissimmee-fl','deep-cleaning-vs-regular-cleaning-orlando',
  'deep-cleaning-vs-standard-cleaning-davenport-fl','great-vacation-rental-cleaning-service-kissimmee-fl',
  'house-cleaning-cost-celebration-fl','house-cleaning-cost-winter-garden-fl-2026',
  'house-cleaning-frequency-the-villages-fl','house-cleaning-services-clermont-fl-guide',
  'how-often-house-cleaning-clermont-fl','janitorial-services-vs-commercial-cleaning-difference',
  'move-out-cleaning-checklist-minneola-fl','prepare-airbnb-for-cleaning-davenport-fl',
  'professional-cleaning-saves-time-money-orlando','professional-house-cleaning-worth-it-minneola-fl',
  'reliable-house-cleaning-clermont-fl','vacation-rental-cleaning-champions-gate-davenport-fl',
  'vacation-rental-cleaning-kissimmee-fl',
]);

const audit = JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'audit.json'), 'utf8'));
const targets = audit.filter(r => !RANKED.has(r.slug));

// rank worst-first: no image, then weakest FAQ schema, then fewest words
targets.sort((a, b) =>
  (a.hasBodyImg - b.hasBodyImg) ||
  (a.faqSchema - b.faqSchema) ||
  (a.words - b.words)
);

fs.writeFileSync(path.join(__dirname, '..', 'targets.json'), JSON.stringify(targets, null, 0));
console.error(`NO-RANKING posts (zero impressions): ${targets.length} of ${audit.length}`);
console.error(`  of those, no body image:  ${targets.filter(r => !r.hasBodyImg).length}`);
console.error(`  of those, FAQ schema <5:  ${targets.filter(r => r.faqSchema < 5).length}`);
console.error(`  of those, <1000 words:    ${targets.filter(r => r.words < 1000).length}\n`);
for (const r of targets) {
  console.error(
    `${r.hasBodyImg ? '  ' : 'NOIMG'} ${String(r.words).padStart(4)}w  faq:${r.faqHtml}/${r.faqSchema}  ${r.slug}`
  );
}
