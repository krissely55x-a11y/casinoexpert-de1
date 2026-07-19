#!/usr/bin/env node
/** Fix relative wp-content URLs in built HTML (broken on nested routes). */
import { readFileSync, writeFileSync } from 'node:fs';
import { readdirSync, statSync } from 'node:fs';
import { join } from 'node:path';

const root = join(process.cwd(), 'dist');
let files = 0;
let changes = 0;

function fixGlobalCss() {
  const cssPath = join(root, 'styles', 'legacy.css');
  if (!statSync(cssPath, { throwIfNoEntry: false })?.isFile()) {
    throw new Error('fix_html_assets: dist/styles/legacy.css not found');
  }

  const badRoot =
    ':root{clip-path:inset(50%);height:1px;margin:-1px;overflow:hidden;' +
    'padding:0;position:absolute;width:1px;word-wrap:normal!important}';
  const screenReader =
    '.screen-reader-text{clip-path:inset(50%);height:1px;margin:-1px;' +
    'overflow:hidden;padding:0;position:absolute;width:1px;' +
    'word-wrap:normal!important}';

  const before = readFileSync(cssPath, 'utf8');
  const css = before.replaceAll(badRoot, screenReader);
  if (css.includes(badRoot)) {
    throw new Error('fix_html_assets: fatal document-collapsing :root rule remains');
  }
  if (css !== before) {
    writeFileSync(cssPath, css, 'utf8');
    console.log('fix_html_assets: repaired document-collapsing CSS rule');
  }
}

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

fixGlobalCss();
walk(root);
console.log(`fix_html_assets: checked ${files} html, updated ${changes}`);
