// Проверка собранного сайта в настоящем браузере: сайт открывается из file://,
// в сеть не ходит ни за одним байтом, поиск находит.
//
// Зачем отдельная проверка. Свойство «офлайновый» сломалось молча: плагин
// `offline` у Material вставляет в каждую страницу шим WebWorker с unpkg, и
// собранный сайт без сети висел на «Инициализация поиска», хотя сборка была
// зелёной. Ни один линтер этого не видит — здесь нужен браузер.
//
//   node tools/check_site.mjs           проверить site/
//   node tools/check_site.mjs --keep    не гасить браузер (для отладки)
//
// Браузер — тот же chrome-headless-shell, которым рисуются схемы; ставится
// `tools/setup.sh`. Флаги — по умолчанию: с `--allow-file-access-from-files`
// воркер из file:// создаётся и без шима, то есть проверка стала бы ложно
// зелёной.

import { readdirSync, existsSync } from 'node:fs';
import { resolve, dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const SITE = join(ROOT, 'site');
const PUP = join(ROOT, 'tools/node/node_modules/.pnpm');
const QUERY = 'cookie';

function puppeteerPath() {
  const dirs = readdirSync(PUP).filter(d => d.startsWith('puppeteer@'));
  if (!dirs.length) throw new Error('нет puppeteer в tools/node — `make setup`');
  return join(PUP, dirs[0], 'node_modules/puppeteer/lib/puppeteer/puppeteer.js');
}

function chromePath() {
  const base = join(process.env.HOME, '.cache/puppeteer/chrome-headless-shell');
  if (!existsSync(base)) throw new Error('нет chrome-headless-shell — `make setup`');
  const v = readdirSync(base).sort().pop();
  return join(base, v, 'chrome-headless-shell-linux64/chrome-headless-shell');
}

// Проверяются две страницы: корневая и вложенная. Относительный путь к шиму и
// к индексу поиска у них разный, и ошибка в глубине пути видна только на
// вложенной.
const PAGES = [
  ['index.html', 'index.html'],
  ['вложенная страница', 'stage-0/cookies.html'],
];

async function check() {
  if (!existsSync(join(SITE, 'index.html')))
    throw new Error('нет site/index.html — сначала `make site`');

  const puppeteer = (await import(puppeteerPath())).default;
  const browser = await puppeteer.launch({
    headless: true,
    executablePath: chromePath(),
    args: ['--no-sandbox', '--disable-gpu'],
  });

  const problems = [];
  for (const [label, rel] of PAGES) {
    const page = await browser.newPage();
    const external = new Set(), errors = new Set();
    page.on('console', m => { if (m.type() === 'error') errors.add(m.text().slice(0, 160)); });
    page.on('pageerror', e => errors.add(String(e).slice(0, 160)));
    await page.setRequestInterception(true);
    page.on('request', r => {
      if (/^https?:/.test(r.url())) {           // сети нет: так же, как в самолёте
        external.add(r.url().slice(0, 120));
        r.abort();
      } else r.continue();
    });

    await page.goto(`file://${join(SITE, rel)}`, { waitUntil: 'networkidle2', timeout: 30000 });
    await page.evaluate(q => {
      const t = document.querySelector('#__search');
      if (t) { t.checked = true; t.dispatchEvent(new Event('change', { bubbles: true })); }
      const input = document.querySelector('[data-md-component=search-query]');
      input.focus(); input.value = q;
      input.dispatchEvent(new Event('input', { bubbles: true }));
    }, QUERY);

    let found = 0;
    for (let i = 0; i < 20 && !found; i++) {
      await new Promise(r => setTimeout(r, 500));
      found = await page.evaluate(() => document.querySelectorAll(
        '[data-md-component=search-result] .md-search-result__link').length);
    }

    const say = [];
    if (external.size) say.push(`ходит в сеть: ${[...external].join(', ')}`);
    if (!found) say.push(`поиск «${QUERY}» ничего не нашёл`);
    if (errors.size) say.push(`ошибки в консоли: ${[...errors].join(' | ')}`);
    console.log(`  ${say.length ? 'НЕТ ' : 'ок  '}${label}: ${found} ссылок в результатах, ` +
                `внешних запросов ${external.size}, ошибок ${errors.size}`);
    for (const s of say) { problems.push(`${label}: ${s}`); console.log(`        ${s}`); }
    await page.close();
  }

  if (!process.argv.includes('--keep')) await browser.close();
  return problems;
}

console.log(`сайт из file:// без сети, поиск «${QUERY}»`);
let problems;
try {
  problems = await check();
} catch (e) {
  console.error(`не удалось проверить: ${e.message}`);
  process.exit(2);
}
if (problems.length) {
  console.log(`\nИТОГ: ${problems.length} — не пройдено`);
  process.exit(1);
}
console.log('\nИТОГ: сайт открывается из file://, в сеть не ходит, поиск находит — пройдено');
