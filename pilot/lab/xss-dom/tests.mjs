// Функциональность кабинета. Зелёный до правки и обязан остаться зелёным после.
//
//   node tests.mjs                        ожидается: Упало проверок: 0
//   LAB_TARGET=solution.js node tests.mjs   то же самое

import { start, ORIGIN } from './serve.mjs';
import { launch } from './labtarget.mjs';

const server = await start();
const browser = await launch();
const page = await browser.newPage();
const wait = (ms) => new Promise((r) => setTimeout(r, ms));

async function open(path) {
  await page.goto(ORIGIN + path, { waitUntil: 'networkidle0' });
  await wait(120);
  return page.evaluate(() => ({
    section: document.getElementById('section').textContent,
    draft: document.getElementById('draft').textContent,
    href: document.getElementById('back').getAttribute('href'),
  }));
}

let failed = 0;
function check(name, ok, got) {
  if (!ok) { failed += 1; console.log(`  ПРОВАЛ  ${name}: ${JSON.stringify(got)}`); }
  else console.log(`  ок      ${name}`);
}

const def = await open('/');
check('без фрагмента открывается профиль', def.section === 'Раздел: profile', def);

const orders = await open('/#orders');
check('фрагмент orders открывает свой раздел', orders.section === 'Раздел: orders', orders);

const settings = await open('/#settings');
check('фрагмент settings открывает свой раздел', settings.section === 'Раздел: settings', settings);

await open('/#orders');
await page.evaluate(() => { location.hash = 'settings'; });
await wait(150);
const switched = await page.evaluate(() =>
  document.getElementById('section').textContent);
check('смена фрагмента меняет раздел без перезагрузки',
      switched === 'Раздел: settings', switched);

const back = await open('/?back=/orders');
check('параметр back попадает в ссылку', back.href === '/orders', back.href);

const noBack = await open('/#profile');
check('без параметра back ссылка ведёт в корень', noBack.href === '/', noBack.href);

const draft = await page.evaluate(() => document.getElementById('draft').textContent);
check('пустое имя окна не ломает страницу', typeof draft === 'string', draft);

await browser.close();
server.close();
console.log(`\nУпало проверок: ${failed}`);
process.exit(failed ? 1 : 0);
