#!/usr/bin/env node
/** Fix relative wp-content URLs in built HTML (broken on nested routes). */
import { existsSync, readFileSync, writeFileSync } from 'node:fs';
import { readdirSync, statSync } from 'node:fs';
import { join } from 'node:path';

const root = join(process.cwd(), 'dist');
let files = 0;
let changes = 0;
const transparentPixel =
  'data:image/gif;base64,R0lGODlhAQABAAD/ACwAAAAAAQABAAACADs=';

function assetExists(url) {
  if (!url.startsWith('/') || url.startsWith('//')) return true;
  let pathname = url.split(/[?#]/, 1)[0];
  try {
    pathname = decodeURIComponent(pathname);
  } catch {
    return false;
  }
  const parts = pathname.split('/').filter(Boolean);
  return existsSync(join(root, ...parts));
}

function optimizeImage(attributes) {
  let optimized = attributes;
  let usableSources = [];
  let missingImage = false;

  optimized = optimized.replace(/\ssrcset=(['"])(.*?)\1/i, (_match, quote, value) => {
    usableSources = value
      .split(',')
      .map((candidate) => candidate.trim())
      .filter(Boolean)
      .filter((candidate) => assetExists(candidate.split(/\s+/, 1)[0]));
    return usableSources.length
      ? ` srcset=${quote}${usableSources.join(', ')}${quote}`
      : '';
  });

  optimized = optimized.replace(/\ssrc=(['"])(.*?)\1/i, (match, quote, value) => {
    if (assetExists(value)) return match;
    const fallback = usableSources[0]?.split(/\s+/, 1)[0];
    if (fallback) return ` src=${quote}${fallback}${quote}`;
    missingImage = true;
    return ` src=${quote}${transparentPixel}${quote}`;
  });

  if (missingImage) {
    if (/\bclass=(['"])/i.test(optimized)) {
      optimized = optimized.replace(/\bclass=(['"])(.*?)\1/i, (_classMatch, classQuote, classes) =>
        `class=${classQuote}${classes} missing-image${classQuote}`);
    } else {
      optimized += ' class="missing-image"';
    }
  }
  if (!/\bloading\s*=/i.test(optimized)) optimized += ' loading="lazy"';
  if (!/\bdecoding\s*=/i.test(optimized)) optimized += ' decoding="async"';
  return optimized;
}

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
  const css = before
    .replaceAll(badRoot, screenReader)
    .replace(/url\((['"]?)(?:\.\/)?wp-content\//g, 'url($1/wp-content/');
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
      .replace(/\ssrcset=(['"])(.*?)\1/gi, (_match, quote, value) => {
        const fixed = value
          .replace(/(^|,\s*)(?:\.\/)?\/{0,2}wp-content\//g, '$1/wp-content/');
        return ` srcset=${quote}${fixed}${quote}`;
      })
      .replace(/<img\b([^>]*)>/gi, (_match, attributes) =>
        `<img${optimizeImage(attributes)}>`
      );
    const mainStart = html.indexOf('<main');
    if (mainStart !== -1) {
      const firstMainImage = html.indexOf('<img', mainStart);
      if (firstMainImage !== -1) {
        const imageEnd = html.indexOf('>', firstMainImage);
        const image = html.slice(firstMainImage, imageEnd + 1)
          .replace('loading="lazy"', 'loading="eager" fetchpriority="high"');
        html = html.slice(0, firstMainImage) + image + html.slice(imageEnd + 1);
      }
    }
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
