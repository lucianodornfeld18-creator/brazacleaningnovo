#!/usr/bin/env node
// One-shot: inject a hero image into the no-ranking posts that have no body image.
// Idempotent — skips any post that already has a .blog-post-img block.
// Image choice is hand-curated per slug (local relevance > generic).
const fs = require('fs');
const path = require('path');

const BLOG = path.join(__dirname, '..', 'blog');

// slug -> [image file in /images/, alt text]
const MAP = {
  'vacation-rental-cleaning-minneola-fl':            ['img-bathroom-minneola.jpg', 'Vacation rental cleaning in Minneola FL — spotless bathroom after turnover'],
  'house-cleaning-service-ocoee-fl':                 ['hero-dining.jpg', 'Professional house cleaning service in Ocoee FL — clean dining area'],
  'airbnb-cleaning-service-winter-garden-fl':        ['img-living-wintergarden.jpg', 'Airbnb cleaning service in Winter Garden FL — clean living room ready for guests'],
  'vacation-rental-cleaning-clermont-fl':            ['img-bathroom-clermont.jpg', 'Vacation rental cleaning in Clermont FL — sanitized bathroom turnover'],
  'best-maid-service-windermere-fl':                 ['hero-dining.jpg', 'Best maid service in Windermere FL — spotless luxury home interior'],
  'maid-service-vs-house-cleaning-the-villages-fl':  ['hero-dining.jpg', 'Maid service vs house cleaning in The Villages FL — clean home interior'],
  'maid-service-winter-garden-fl-recurring':         ['img-house-winter-garden.jpg', 'Recurring maid service in Winter Garden FL — tidy home'],
  'commercial-cleaning-the-villages-fl':             ['img-commercial.jpg', 'Commercial cleaning in The Villages FL — clean office space'],
  'move-out-cleaning-kissimmee-fl':                  ['img-moveout-villages.jpg', 'Move-out cleaning in Kissimmee FL — empty home cleaned for deposit return'],
  'post-construction-cleaning-orlando-fl':           ['img-office-deep.jpg', 'Post-construction cleaning in Orlando FL — dust-free finished space'],
  'deep-cleaning-service-kissimmee-fl':              ['airbnb-cleaning-kissimmee-fl-kitchen-open-floor-plan-spotless.jpg', 'Deep cleaning service in Kissimmee FL — spotless kitchen'],
  'recurring-maid-service-kissimmee-fl':             ['vacation_home_kissimmee.jpg', 'Recurring maid service in Kissimmee FL — consistently clean home'],
};

const ANCHOR = /(<div class="section-inner blog-content"[^>]*>)/i;

let done = 0, skipped = 0, missing = 0;
for (const [slug, [img, alt]] of Object.entries(MAP)) {
  const f = path.join(BLOG, slug, 'index.html');
  if (!fs.existsSync(f)) { console.error(`MISSING file: ${slug}`); missing++; continue; }
  let html = fs.readFileSync(f, 'utf8');

  if (/class="[^"]*blog-post-img[^"]*"/i.test(html)) { console.error(`skip (already has img): ${slug}`); skipped++; continue; }
  if (!ANCHOR.test(html)) { console.error(`NO ANCHOR: ${slug}`); missing++; continue; }
  // verify image file exists in pool
  if (!fs.existsSync(path.join(BLOG, '..', 'images', img))) { console.error(`IMG NOT IN POOL: ${slug} -> ${img}`); missing++; continue; }

  const block = `$1\n<div class="blog-post-img" style="margin-bottom:24px"><img src="/images/${img}" alt="${alt}" loading="eager" decoding="async" onerror="this.parentElement.style.display='none'" style="width:100%;height:360px;object-fit:cover;border-radius:16px" width="768" height="512"/></div>`;
  html = html.replace(ANCHOR, block);
  fs.writeFileSync(f, html);
  console.error(`OK: ${slug} -> ${img}`);
  done++;
}
console.error(`\nInjected: ${done}  Skipped: ${skipped}  Problems: ${missing}`);
