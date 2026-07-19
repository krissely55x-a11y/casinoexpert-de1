#!/usr/bin/env node
/**
 * Remove Astro starter/blog template files that break production builds.
 * Safe to run even when files are absent (e.g. clean local checkout).
 */
import { rmSync, existsSync } from 'node:fs';
import { join } from 'node:path';

const root = process.cwd();

const paths = [
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

let removed = 0;
for (const rel of paths) {
  const abs = join(root, rel);
  if (!existsSync(abs)) continue;
  rmSync(abs, { recursive: true, force: true });
  console.log(`removed: ${rel}`);
  removed += 1;
}

if (removed === 0) {
  console.log('no template junk found');
}
