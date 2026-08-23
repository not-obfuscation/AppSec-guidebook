// Функциональность лабы: три проверки, которые обязаны быть зелёными и до
// починки, и после. Тест, который зеленеет только после правки, — это
// ретест, и он живёт в hack.mjs.
//
//   node tests.mjs       код возврата 0 — упавших нет
//
// Проверки написаны на наблюдаемом состоянии страницы, а не на внутренностях
// обработчика: иначе они сломались бы от любой законной переделки code.js.

import { start, ORIGIN } from './serve.mjs';
import { launch } from './labtarget.mjs';

const failures = [];

function check(name, got, want) {
  const ok = got === want;
  console.log(`  ${ok ? 'ок  ' : 'упал'}  ${name}`);
  if (!ok) {
    console.log(`        получено: ${got}`);
    console.log(`        ожидалось: ${want}`);
    failures.push(name);
  }
}

const theme = (page) => page.evaluate(
  () => document.getElementById('theme').textContent);

const post = (page, body, target) => page.evaluate(
  (b, t) => window.postMessage(b, t), body, target);

const settle = () => new Promise((ok) => setTimeout(ok, 200));

const stop = await start();
const browser = await launch();
console.log(`проверяется ${process.env.LAB_TARGET || 'code.js'}`);

// 1. Своё же сообщение. Обработчик слушает и внутриоригинные сообщения:
// приложение шлёт их между своими кадрами.
let page = await browser.newPage();
await page.goto(`${ORIGIN.app}/`, { waitUntil: 'load' });
await post(page, JSON.stringify({ theme: 'ночная' }), ORIGIN.app);
await settle();
check('настройка из своего документа применяется', await theme(page), 'ночная');

// 2. Доверенный виджет с третьего origin. Кнопку нажимает браузер.
await page.goto(`${ORIGIN.app}/`, { waitUntil: 'load' });
const panel = page.frames().find((f) => f.url().startsWith(ORIGIN.widget));
await panel.click('#apply');
await settle();
check('настройка доверенного виджета применяется', await theme(page), 'тёмная');

// 3. Неразбираемое тело. Страница остаётся живой, настройка не меняется.
await page.goto(`${ORIGIN.app}/`, { waitUntil: 'load' });
await post(page, 'не-json', ORIGIN.app);
await settle();
check('мусор в теле не меняет настройку', await theme(page), 'по умолчанию');
await post(page, JSON.stringify({ theme: 'ночная' }), ORIGIN.app);
await settle();
check('после мусора обработчик продолжает работать', await theme(page), 'ночная');

await browser.close();
await stop();
console.log(`Упало проверок: ${failures.length}`);
process.exit(failures.length ? 1 : 0);
