#!/usr/bin/env node
/** Fix relative wp-content URLs in built HTML (broken on nested routes). */
import { readFileSync, writeFileSync } from 'node:fs';
import { readdirSync, statSync } from 'node:fs';
import { join } from 'node:path';

const root = join(process.cwd(), 'dist');
let files = 0;
let changes = 0;

function walk(dir) {
  for (const name of readdirSync(dir)) {
    const path = join(dir, name);
    if (statSync(path).isDirectory()) {
      walk(path);
      continue;
    }
    if (!name.endsWith('.html')) continue;
    files += 1;
    let html = readFileSync(path, 'utf8');
    const before = html;
    html = html
      .replace(/url\((['"]?)wp-content\//g, 'url($1/wp-content/')
      .replace(/url\((['"]?)\.\/wp-content\//g, 'url($1/wp-content/')
      .replace(/(\s(?:src|href|poster|data-src)=)(['"])wp-content\//g, '$1$2/wp-content/')
      .replace(/(\s(?:srcset)=)(['"][^'"]*?)wp-content\//g, '$1$2/wp-content/');
    if (html !== before) {
      writeFileSync(path, html, 'utf8');
      changes += 1;
    }
  }
}

if (!statSync(root, { throwIfNoEntry: false })?.isDirectory()) {
  console.log('fix_html_assets: dist/ not found, skipping');
  process.exit(0);
}

walk(root);
console.log(`fix_html_assets: checked ${files} html, updated ${changes}`);
