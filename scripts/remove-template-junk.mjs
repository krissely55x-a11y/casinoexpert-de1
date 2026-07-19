#!/usr/bin/env node
/**
 * Remove Astro starter junk and force static-only Wrangler config.
 */
import { rmSync, existsSync, writeFileSync, readFileSync } from 'node:fs';
import { join } from 'node:path';

const root = process.cwd();

const removePaths = [
  'src/pages/rss.xml.js',
  'src/pages/rss.xml.ts',
  'src/pages/blog',
  'src/content',
  'src/content.config.ts',
  'src/content.config.mjs',
  'src/pages/about.astro',
  'src/layouts/BlogPost.astro',
  'src/components/HeaderLink.astro',
];

const WORKER_NAME = 'casinoexpert-de1';

const WRANGLER_TOML = `name = "${WORKER_NAME}"
compatibility_date = "2024-07-01"

[assets]
directory = "./dist"
not_found_handling = "404-page"
`;

const WRANGLER_JSONC = `{
  "$schema": "./node_modules/wrangler/config-schema.json",
  "name": "${WORKER_NAME}",
  "compatibility_date": "2024-07-01",
  "assets": {
    "directory": "./dist",
    "not_found_handling": "404-page"
  }
}
`;

function forceStaticWranglerConfig() {
  writeFileSync(join(root, 'wrangler.toml'), WRANGLER_TOML, 'utf8');
  writeFileSync(join(root, 'wrangler.jsonc'), WRANGLER_JSONC, 'utf8');

  const jsonPath = join(root, 'wrangler.json');
  if (existsSync(jsonPath)) {
    const text = readFileSync(jsonPath, 'utf8');
    if (text.includes('_worker.js') || text.includes('"main"')) {
      rmSync(jsonPath, { force: true });
      console.log('removed: wrangler.json (SSR template config)');
    }
  }

  console.log('wrote: wrangler.toml + wrangler.jsonc (static assets only)');
}

let removed = 0;
for (const rel of removePaths) {
  const abs = join(root, rel);
  if (!existsSync(abs)) continue;
  rmSync(abs, { recursive: true, force: true });
  console.log(`removed: ${rel}`);
  removed += 1;
}

forceStaticWranglerConfig();

if (removed === 0) {
  console.log('no template junk found');
}
