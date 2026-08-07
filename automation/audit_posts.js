#!/usr/bin/env node
// One-shot audit of all blog posts. Read-only. Outputs JSON to stdout.
const fs = require('fs');
const path = require('path');

const BLOG = path.join(__dirname, '..', 'blog');
const dirs = fs.readdirSync(BLOG, { withFileTypes: true })
  .filter(d => d.isDirectory() && d.name !== 'category')
  .map(d => d.name);

function textOf(html) {
  // crude: strip tags/scripts/styles, collapse whitespace
  let s = html
    .replace(/<script[\s\S]*?<\/script>/gi, ' ')
    .replace(/<style[\s\S]*?<\/style>/gi, ' ')
    .replace(/<[^>]+>/g, ' ')
    .replace(/&[a-z]+;/gi, ' ')
    .replace(/\s+/g, ' ')
    .trim();
  return s;
}

function bodyOnly(html) {
  // restrict word count to the blog-content section if present
  const m = html.match(/class="[^"]*blog-content[^"]*"[\s\S]*?<\/section>/i);
  return m ? m[0] : html;
}

const rows = [];
for (const name of dirs) {
  const f = path.join(BLOG, name, 'index.html');
  if (!fs.existsSync(f)) continue;
  const html = fs.readFileSync(f, 'utf8');

  const body = bodyOnly(html);
  const words = textOf(body).split(' ').filter(Boolean).length;

  // body image: an actual <img> element INSIDE the blog-content section only
  const hasBodyImg = /<img\b/i.test(body);

  // FAQ in visible HTML (details/summary OR faq-item)
  const detailsCount = (html.match(/<details/gi) || []).length;
  const faqItemCount = (html.match(/class="[^"]*faq-question[^"]*"/gi) || []).length;
  const faqHtml = Math.max(detailsCount, faqItemCount);

  // FAQ schema questions
  let faqSchema = 0;
  const faqBlocks = html.match(/"@type":\s*"FAQPage"[\s\S]*?<\/script>/gi) || [];
  for (const b of faqBlocks) faqSchema += (b.match(/"@type":\s*"Question"/gi) || []).length;

  // fabricated aggregateRating / review claims
  const hasAggSchema = /"@type":\s*"AggregateRating"/i.test(html);
  const hasReviewClaim = /5\.0\s*(Google\s*)?Rating|verified reviews|60 verified|68 verified/i.test(html);

  const title = (html.match(/<title>([^<]*)<\/title>/i) || [])[1] || '';

  rows.push({
    slug: name,
    title: title.trim(),
    words,
    hasBodyImg,
    faqHtml,
    faqSchema,
    hasAggSchema,
    hasReviewClaim,
  });
}

rows.sort((a, b) => a.words - b.words);
console.log(JSON.stringify(rows, null, 0));
console.error(`\nAudited ${rows.length} posts.`);
console.error(`No body image:      ${rows.filter(r => !r.hasBodyImg).length}`);
console.error(`< 800 words:        ${rows.filter(r => r.words < 800).length}`);
console.error(`< 1000 words:       ${rows.filter(r => r.words < 1000).length}`);
console.error(`FAQ schema < 5:     ${rows.filter(r => r.faqSchema < 5).length}`);
console.error(`FAQ html < 5:       ${rows.filter(r => r.faqHtml < 5).length}`);
console.error(`Review claim in body: ${rows.filter(r => r.hasReviewClaim).length}`);
console.error(`AggregateRating schema: ${rows.filter(r => r.hasAggSchema).length}`);
