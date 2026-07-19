#!/usr/bin/env node
/**
 * Verify Cloudflare Pages readiness (scripts, configs, build, deploy).
 * Usage: node scripts/verify-cloudflare.mjs [--build]
 */
import { existsSync, readFileSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import { join } from 'node:path';

const root = process.cwd();
const runBuild = process.argv.includes('--build');
let errors = [];
let warnings = [];

function check(path, label) {
  if (!existsSync(join(root, path))) {
    errors.push(`Missing: ${path} (${label})`);
    return false;
  }
  return true;
}

const pkg = JSON.parse(readFileSync(join(root, 'package.json'), 'utf8'));
const requiredScripts = ['prebuild', 'build', 'deploy'];
for (const name of requiredScripts) {
  if (!pkg.scripts?.[name]) {
    errors.push(`package.json missing script: "${name}"`);
  }
}

const requiredFiles = [
  ['astro.config.mjs', 'Astro config'],
  ['wrangler.toml', 'Cloudflare config'],
  ['scripts/remove-template-junk.mjs', 'Template cleanup'],
  ['scripts/deploy.mjs', 'Deploy step'],
  ['src/layouts/BaseLayout.astro', 'Layout'],
  ['public/robots.txt', 'robots.txt'],
  ['public/styles/legacy.css', 'Bundled CSS'],
];

for (const [path, label] of requiredFiles) {
  check(path, label);
}

if (!existsSync(join(root, 'src/pages/index.astro'))) {
  errors.push('Missing: src/pages/index.astro');
}

const pageCount = spawnSync('node', ['-e', `
  const fs=require('fs');const path=require('path');
  function walk(d){let n=0;for(const e of fs.readdirSync(d,{withFileTypes:true})){
    if(e.isDirectory())n+=walk(path.join(d,e.name));
    else if(e.name==='index.astro')n++;
  }return n;}
  console.log(walk('src/pages'));
`], { cwd: root, encoding: 'utf8' });

const pages = parseInt(pageCount.stdout.trim(), 10);
if (pages < 300) {
  warnings.push(`Only ${pages} Astro pages (expected ~310)`);
}

function npm(args) {
  const r = spawnSync(process.platform === 'win32' ? 'npm.cmd' : 'npm', args, {
    cwd: root,
    encoding: 'utf8',
    shell: true,
  });
  return r;
}

console.log('=== Cloudflare readiness check ===\n');
console.log('Scripts in package.json:', Object.keys(pkg.scripts || {}).join(', '));

if (runBuild) {
  console.log('\nRunning: npm run build');
  const build = npm(['run', 'build']);
  if (build.status !== 0) {
    errors.push('npm run build failed');
    console.error(build.stdout || build.stderr);
  } else {
    console.log('Build: OK');
  }

  console.log('\nRunning: npm run deploy');
  const deploy = npm(['run', 'deploy']);
  if (deploy.status !== 0) {
    errors.push('npm run deploy failed');
    console.error(deploy.stdout || deploy.stderr);
  } else {
    console.log((deploy.stdout || '').trim() || 'Deploy: OK');
  }

  if (existsSync(join(root, 'dist/index.html'))) {
    console.log('dist/index.html: OK');
  } else {
    errors.push('dist/index.html not found after build');
  }
}

if (warnings.length) {
  console.log('\nWarnings:');
  warnings.forEach((w) => console.log('  -', w));
}

if (errors.length) {
  console.log('\nERRORS:');
  errors.forEach((e) => console.log('  -', e));
  process.exit(1);
}

console.log('\nAll checks passed.');
if (!runBuild) {
  console.log('Run with --build to test full pipeline.');
}
