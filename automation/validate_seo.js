'use strict';

/*
 * Lightweight guard for the static marketing site. It deliberately uses only
 * Node's standard library so it can run locally and in GitHub Actions.
 */
const fs = require('fs');
const path = require('path');

const root = path.resolve(__dirname, '..');
const siteOrigin = 'https://brazacleaning.com';
const excludedCanonicalFiles = new Set(['404.html', 'admin/index.html']);
const errors = [];

function walk(directory) {
  const entries = fs.readdirSync(directory, { withFileTypes: true });
  return entries.flatMap((entry) => {
    const absolute = path.join(directory, entry.name);
    if (entry.isDirectory()) {
      return entry.name === '.git' ? [] : walk(absolute);
    }
    return entry.isFile() && entry.name.endsWith('.html') ? [absolute] : [];
  });
}

function relative(file) {
  return path.relative(root, file).split(path.sep).join('/');
}

function expectedCanonical(file) {
  const rel = relative(file);
  const pagePath = rel === 'index.html'
    ? '/'
    : `/${rel.replace(/\/index\.html$/, '/')}`;
  return `${siteOrigin}${pagePath}`;
}

function canonicalLinks(html) {
  return [...html.matchAll(/<link\b[^>]*>/gi)]
    .filter((match) => /\brel=(['"])canonical\1/i.test(match[0]))
    .map((match) => {
      const href = match[0].match(/\bhref=(['"])(.*?)\1/i);
      return href ? href[2] : '';
    });
}

for (const file of walk(root)) {
  const rel = relative(file);
  const html = fs.readFileSync(file, 'utf8');

  if (!excludedCanonicalFiles.has(rel)) {
    const canonicals = canonicalLinks(html);
    if (canonicals.length !== 1) {
      errors.push(`${rel}: expected exactly one canonical link; found ${canonicals.length}.`);
    } else if (canonicals[0] !== expectedCanonical(file)) {
      errors.push(`${rel}: canonical should be ${expectedCanonical(file)}, found ${canonicals[0] || '(empty)'}.`);
    }
  }

  if (/['"]@type['"]\s*:\s*['"]AggregateRating['"]/i.test(html) || /['"]reviewCount['"]\s*:/i.test(html)) {
    errors.push(`${rel}: contains self-serving AggregateRating/reviewCount markup.`);
  }

  if (/\b70\s+(?:verified\s+)?(?:google\s+)?reviews\b|\bacross\s+70\b/i.test(html)) {
    errors.push(`${rel}: contains a stale 70-review claim.`);
  }

  const jsonLdBlocks = [...html.matchAll(/<script\b[^>]*type=(['"])application\/ld\+json\1[^>]*>([\s\S]*?)<\/script>/gi)];
  jsonLdBlocks.forEach((match, index) => {
    try {
      JSON.parse(match[2].trim());
    } catch (error) {
      errors.push(`${rel}: invalid JSON-LD block ${index + 1}: ${error.message}`);
    }
  });
}

const sitemapFile = path.join(root, 'sitemap.xml');
const sitemap = fs.readFileSync(sitemapFile, 'utf8');
const locations = [...sitemap.matchAll(/<loc>(.*?)<\/loc>/gi)].map((match) => match[1].trim());
const uniqueLocations = new Set(locations);

if (uniqueLocations.size !== locations.length) {
  errors.push('sitemap.xml: duplicate <loc> values found.');
}

for (const location of locations) {
  let url;
  try {
    url = new URL(location);
  } catch (error) {
    errors.push(`sitemap.xml: invalid URL ${location}.`);
    continue;
  }

  if (url.origin !== siteOrigin || url.search || url.hash) {
    errors.push(`sitemap.xml: URL must be a clean brazacleaning.com canonical: ${location}.`);
    continue;
  }

  const local = url.pathname === '/'
    ? path.join(root, 'index.html')
    : path.join(root, url.pathname.replace(/^\//, ''), 'index.html');
  if (!fs.existsSync(local)) {
    errors.push(`sitemap.xml: URL has no matching file: ${location}.`);
  }
}

const redirectsFile = path.join(root, '_redirects');
const allowedRedirectStatuses = new Set(['200', '301', '302', '303', '307', '308']);
if (!fs.existsSync(redirectsFile)) {
  errors.push('_redirects: file is missing.');
} else {
  fs.readFileSync(redirectsFile, 'utf8').split(/\r?\n/).forEach((line, index) => {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith('#')) return;
    const fields = trimmed.split(/\s+/);
    if (fields.length !== 3) {
      errors.push(`_redirects:${index + 1}: expected source, destination and status.`);
      return;
    }
    const [source, destination, status] = fields;
    if (!source.startsWith('/') || !destination.startsWith('/')) {
      errors.push(`_redirects:${index + 1}: Pages redirects must use relative source and destination paths.`);
    }
    if (!allowedRedirectStatuses.has(status)) {
      errors.push(`_redirects:${index + 1}: unsupported status ${status}.`);
    }
  });
}

if (errors.length) {
  console.error(`SEO validation failed with ${errors.length} issue(s):`);
  errors.forEach((error) => console.error(`- ${error}`));
  process.exitCode = 1;
} else {
  console.log(`SEO validation passed: ${locations.length} sitemap URLs and static SEO checks are clean.`);
}
