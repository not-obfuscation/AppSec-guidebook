// Проверка файла для телефона: открывается на узком экране, не ходит в сеть,
// все ссылки внутри файла живые, схемы видны.
//
// Проверять глазами тут нечего: файл собран из готового сайта, и сломаться в
// нём может ровно три вещи — адрес, который никуда не ведёт после склейки
// одиннадцати тем в одну страницу; картинка, не доехавшая в `data:`; и вылезшая
// за экран таблица. Всё три проверяются браузером на экране телефона.
//
//   node tools/check_phone.mjs [dist/appsec-stage-0.html]
//
// Ширина 390×844 — iPhone 14; на ней проверяется, что по горизонтали не
// прокручивается сама страница (широкое место обязано прокручиваться внутри
// своей рамки, а не тащить за собой текст).

import { existsSync, readdirSync } from 'node:fs';
import { resolve, dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const FILE = resolve(ROOT, process.argv[2] || 'dist/appsec-stage-0.html');
const PUP = join(ROOT, 'tools/node/node_modules/.pnpm');
const TOPICS = 11;
const VIEWPORT = { width: 390, height: 844, deviceScaleFactor: 3, isMobile: true };

function puppeteerPath() {
  const dirs = readdirSync(PUP).filter(d => d.startsWith('puppeteer@'));
  if (!dirs.length) throw new Error('нет puppeteer в tools/node — `make setup`');
  return join(PUP, dirs[0], 'node_modules/puppeteer/lib/puppeteer/puppeteer.js');
}

function chromePath() {
  const base = join(process.env.HOME, '.cache/puppeteer/chrome-headless-shell');
  if (!existsSync(base)) throw new Error('нет chrome-headless-shell — `make setup`');
  return join(base, readdirSync(base).sort().pop(),
              'chrome-headless-shell-linux64/chrome-headless-shell');
}

if (!existsSync(FILE)) {
  console.error(`нет файла ${FILE} — сначала \`make phone\``);
  process.exit(2);
}

const puppeteer = (await import(puppeteerPath())).default;
const browser = await puppeteer.launch({
  headless: true, executablePath: chromePath(),
  args: ['--no-sandbox', '--disable-gpu'],
});
const page = await browser.newPage();
await page.setViewport(VIEWPORT);
const external = new Set(), errors = new Set();
page.on('console', m => { if (m.type() === 'error') errors.add(m.text().slice(0, 160)); });
page.on('pageerror', e => errors.add(String(e).slice(0, 160)));
await page.setRequestInterception(true);
page.on('request', r => {
  if (/^https?:/.test(r.url())) { external.add(r.url().slice(0, 120)); r.abort(); }
  else r.continue();
});
await page.goto(`file://${FILE}`, { waitUntil: 'networkidle2', timeout: 60000 });

const seen = await page.evaluate(() => {
  const ids = new Set([...document.querySelectorAll('[id]')].map(e => e.id));
  const anchors = [...document.querySelectorAll('a[href]')].map(a => a.getAttribute('href'));
  const wide = [...document.querySelectorAll('body *')]
    .filter(e => e.getBoundingClientRect().right > window.innerWidth + 1)
    .map(e => `${e.tagName.toLowerCase()}${e.className ? '.' + String(e.className).split(' ')[0] : ''}`);
  return {
    topics: document.querySelectorAll('section.topic').length,
    tocItems: document.querySelectorAll('nav.toc > ol > li').length,
    h1: document.querySelectorAll('section.topic h1').length,
    dead: anchors.filter(h => h.startsWith('#') && !ids.has(decodeURIComponent(h.slice(1)))),
    toPages: anchors.filter(h => /\.html(#|$)/.test(h)),
    outside: anchors.filter(h => /^https?:/.test(h)).length,
    inside: anchors.filter(h => h.startsWith('#')).length,
    images: document.images.length,
    broken: [...document.images].filter(i => !i.complete || i.naturalWidth === 0).length,
    scrollW: document.documentElement.scrollWidth,
    innerW: window.innerWidth,
    wide: [...new Set(wide)].slice(0, 8),
    height: document.documentElement.scrollHeight,
  };
});
await browser.close();

const bad = [];
if (external.size) bad.push(`ходит в сеть: ${[...external].join(', ')}`);
if (errors.size) bad.push(`ошибки в консоли: ${[...errors].join(' | ')}`);
if (seen.topics !== TOPICS) bad.push(`тем в файле ${seen.topics}, а надо ${TOPICS}`);
if (seen.tocItems !== TOPICS) bad.push(`в оглавлении ${seen.tocItems} пунктов, а надо ${TOPICS}`);
if (seen.h1 !== TOPICS) bad.push(`заголовков тем ${seen.h1}, а надо ${TOPICS}`);
if (seen.dead.length) bad.push(`ссылки в никуда (${seen.dead.length}): ${seen.dead.slice(0, 6).join(', ')}`);
if (seen.toPages.length) bad.push(`остались ссылки на страницы сайта: ${seen.toPages.slice(0, 4).join(', ')}`);
if (seen.broken) bad.push(`картинок не отрисовалось: ${seen.broken}`);
if (seen.scrollW > seen.innerW + 1)
  bad.push(`страница прокручивается по горизонтали (${seen.scrollW} > ${seen.innerW}): ${seen.wide.join(', ')}`);

console.log(`файл для телефона: ${FILE.replace(ROOT + '/', '')}, экран ${VIEWPORT.width}×${VIEWPORT.height}`);
console.log(`  тем ${seen.topics}, оглавление ${seen.tocItems}, схем ${seen.images} ` +
            `(битых ${seen.broken}), ссылок внутрь ${seen.inside}, наружу ${seen.outside}`);
console.log(`  высота страницы ${(seen.height / VIEWPORT.height).toFixed(0)} экранов, ` +
            `ширина ${seen.scrollW} при экране ${seen.innerW}`);
for (const b of bad) console.log(`  НЕТ: ${b}`);
if (bad.length) { console.log('ИТОГ: не пройдено'); process.exit(1); }
console.log('ИТОГ: файл открывается на телефоне, ссылки живые, схемы видны, в сеть не ходит — пройдено');
