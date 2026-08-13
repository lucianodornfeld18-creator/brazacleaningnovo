'use strict';

/*
 * Guard the site's single service-area business entity. Local pages should
 * describe a Service and its areaServed, never fabricate a city office.
 */
const fs = require('fs');
const path = require('path');

const root = path.resolve(__dirname, '..');
const entityId = 'https://brazacleaning.com/#organization';
const errors = [];
let htmlFiles = 0;
let entityDefinitions = 0;
let serviceNodes = 0;

function walk(directory) {
  const entries = fs.readdirSync(directory, { withFileTypes: true });
  return entries.flatMap((entry) => {
    const absolute = path.join(directory, entry.name);
    if (entry.isDirectory()) return entry.name === '.git' ? [] : walk(absolute);
    return entry.isFile() && entry.name.endsWith('.html') ? [absolute] : [];
  });
}

function relative(file) {
  return path.relative(root, file).split(path.sep).join('/');
}

function typeList(node) {
  const type = node && node['@type'];
  return Array.isArray(type) ? type : type ? [type] : [];
}

function isBrandNode(node) {
  if (!node || typeof node !== 'object' || Array.isArray(node)) return false;
  return node['@id'] === entityId || /Braza Cleaning/i.test(`${node.name || ''} ${node.legalName || ''}`);
}

function isEntityDefinition(node) {
  return node &&
    node['@id'] === entityId &&
    node['@type'] === 'Organization' &&
    node.name === 'Braza Cleaning Services' &&
    node.url === 'https://brazacleaning.com/' &&
    node.telephone === '+16892427469' &&
    node.email === 'brazacleaningflorida@gmail.com' &&
    node.logo === 'https://brazacleaning.com/images/logo.webp';
}

function visit(node, state, rel) {
  if (Array.isArray(node)) {
    node.forEach((item) => visit(item, state, rel));
    return;
  }
  if (!node || typeof node !== 'object') return;

  const types = typeList(node);
  const isService = types.includes('Service');
  const isLocalBusiness = types.some((type) => [
    'LocalBusiness',
    'HomeAndConstructionBusiness',
    'CleaningService',
    'ProfessionalService',
  ].includes(type));

  if (node['@id'] === entityId) {
    state.references += 1;
    if (isEntityDefinition(node)) {
      state.definitions += 1;
      entityDefinitions += 1;
    }
  }

  if (isBrandNode(node)) {
    if (isLocalBusiness) {
      errors.push(`${rel}: Braza entity must not use a city-specific LocalBusiness type.`);
    }
    for (const forbidden of ['address', 'geo', 'areaServed', 'openingHoursSpecification', 'hoursAvailable']) {
      if (Object.prototype.hasOwnProperty.call(node, forbidden)) {
        errors.push(`${rel}: Braza entity must not contain ${forbidden}; use page-level Service areaServed instead.`);
      }
    }
  }

  if (isService) {
    serviceNodes += 1;
    if (node.provider?.['@id'] !== entityId) {
      errors.push(`${rel}: Service must reference the global Braza provider @id.`);
    }
    for (const required of ['@id', 'url', 'areaServed']) {
      if (!node[required]) errors.push(`${rel}: Service is missing ${required}.`);
    }
  }

  Object.values(node).forEach((value) => visit(value, state, rel));
}

for (const file of walk(root)) {
  htmlFiles += 1;
  const rel = relative(file);
  const html = fs.readFileSync(file, 'utf8');
  const state = { references: 0, definitions: 0 };
  const blocks = [...html.matchAll(/<script\b[^>]*type=(['"])application\/ld\+json\1[^>]*>([\s\S]*?)<\/script>/gi)];

  blocks.forEach((match, index) => {
    try {
      visit(JSON.parse(match[2].trim()), state, rel);
    } catch (error) {
      errors.push(`${rel}: invalid JSON-LD block ${index + 1}: ${error.message}`);
    }
  });

  if (state.references && state.definitions !== 1) {
    errors.push(`${rel}: must contain exactly one complete local definition of the global Braza entity.`);
  }
}

if (errors.length) {
  console.error(`Entity schema validation failed with ${errors.length} issue(s):`);
  errors.forEach((error) => console.error(`- ${error}`));
  process.exitCode = 1;
} else {
  console.log(`Entity schema validation passed: ${htmlFiles} HTML files, ${entityDefinitions} entity definitions, ${serviceNodes} Service nodes.`);
}
