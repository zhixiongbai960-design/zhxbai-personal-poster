#!/usr/bin/env node
'use strict';
const fs = require('node:fs');
const path = require('node:path');
const { pathToFileURL } = require('node:url');

async function main() {
  const args = process.argv.slice(2);
  if (args.length !== 1 && !(args.length === 3 && args[1] === '--width')) {
    throw new Error('Usage: node render_poster.cjs OUTPUT_DIR [--width 1800]');
  }
  const width = args.length === 3 ? Number(args[2]) : 1800;
  if (!Number.isInteger(width) || width < 300 || width > 6000 || width % 3 !== 0) {
    throw new Error('Export width must be an integer multiple of 3, from 300 to 6000.');
  }
  let chromium;
  try {
    ({ chromium } = require('playwright'));
  } catch {
    throw new Error('Playwright is missing. Use the host dependency runtime or set NODE_PATH to its package directory.');
  }
  const root = path.resolve(args[0]);
  const source = path.join(root, 'poster.html');
  if (!fs.existsSync(source)) throw new Error('poster.html is missing. Build the poster first.');
  const options = { headless: true };
  if (process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE) options.executablePath = process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE;
  const browser = await chromium.launch(options);
  try {
    const failures = [];
    const page = await browser.newPage({ viewport: { width: 1080, height: 1440 }, deviceScaleFactor: width / 1080 });
    async function ready(target) {
      target.on('pageerror', error => failures.push(error.message));
      await target.goto(pathToFileURL(source).href, { waitUntil: 'load' });
      await target.evaluate(async () => {
        await document.fonts.ready;
        await Promise.all([...document.images].map(image => image.decode()));
        await new Promise(requestAnimationFrame);
        await new Promise(requestAnimationFrame);
      });
    }
    await ready(page);
    const checks = await page.evaluate(() => {
      const box = element => {
        const r = element.getBoundingClientRect();
        return { x: r.x, y: r.y, width: r.width, height: r.height, right: r.right, bottom: r.bottom };
      };
      const elements = [...document.querySelectorAll('.name,.identity,.roles,.statement,.stat p,.credential-main,.credential,.event')].filter(element => element.getClientRects().length);
      return {
        images: [...document.images].map(image => ({ src: image.getAttribute('src'), loaded: image.complete && image.naturalWidth > 0 })),
        overflow: elements.filter(element => element.scrollWidth > element.clientWidth + 1).map(element => element.textContent),
        outside: elements.filter(element => { const r = box(element); return r.x < 0 || r.y < 0 || r.right > 1081 || r.bottom > 1441; }).map(element => element.textContent),
        portrait: box(document.querySelector('.portrait')),
        text: document.querySelector('.poster').innerText,
      };
    });
    if (failures.length || checks.images.some(image => !image.loaded) || checks.overflow.length || checks.outside.length) {
      throw new Error('Poster layout check failed: ' + JSON.stringify({ failures, ...checks }));
    }
    await page.screenshot({ path: path.join(root, 'poster.png'), fullPage: false });
    const mobile = await browser.newPage({ viewport: { width: 390, height: 520 }, deviceScaleFactor: 1 });
    await ready(mobile);
    if (failures.length) throw new Error('Mobile render failed: ' + failures.join('; '));
    await mobile.screenshot({ path: path.join(root, 'preview_mobile.png'), fullPage: false });
    checks.export = { width, height: width * 4 / 3, mobileWidth: 390 };
    checks.visualReviewRequired = true;
    fs.writeFileSync(path.join(root, 'qa.json'), JSON.stringify(checks, null, 2) + '\n');
    console.log(JSON.stringify({ output: root, export: checks.export, visualReviewRequired: true }));
  } finally {
    await browser.close();
  }
}

main().catch(error => {
  console.error('Poster rendering failed:', error.message);
  process.exitCode = 1;
});
