// Пять опытов над кабинетом: три эксплойта и два контроля.
// Зелёный (код 0), когда ни один эксплойт не сработал, а контроли живы.
//
//   node hack.mjs                       ожидается ЭКСПЛОЙТ СРАБОТАЛ, код 1
//   LAB_TARGET=solution.js node hack.mjs  ожидается ЭКСПЛОЙТ НЕ СРАБОТАЛ, код 0

import { start, ORIGIN, EVIL, seen } from './serve.mjs';
import { launch } from './labtarget.mjs';

const server = await start();
const browser = await launch();
const page = await browser.newPage();
const wait = (ms) => new Promise((r) => setTimeout(r, ms));

async function open(path) {
  await page.goto(ORIGIN + path, { waitUntil: 'networkidle0' });
  await wait(200);
  return read();
}

function read() {
  return page.evaluate(() => ({
    ran: window.__ran ?? null,
    section: document.getElementById('section').textContent,
    draft: document.getElementById('draft').textContent,
    href: document.getElementById('back').getAttribute('href'),
  }));
}

const results = [];
function say(n, what, ok, detail) {
  results.push(ok);
  console.log(`  опыт ${n} — ${what}: ${detail}`);
}

seen.length = 0;
const r1 = await open('/#' + encodeURIComponent('<img src=/нет onerror="window.__ran=1">'));
say(1, 'разметка из фрагмента адреса', r1.ran === null,
    r1.ran ? 'СКРИПТ ИСПОЛНЕН' : 'скрипт не исполнен');
console.log(`     сервер за этот опыт увидел: ${JSON.stringify(seen)}`);

await page.goto(`${EVIL}/?to=${encodeURIComponent(ORIGIN + '/')}`,
                { waitUntil: 'networkidle0' });
await wait(400);
const r2 = await read();
say(2, 'разметка из имени окна', r2.ran === null,
    r2.ran ? 'СКРИПТ ИСПОЛНЕН' : 'скрипт не исполнен');

const r3 = await open('/?back=' + encodeURIComponent('javascript:window.__ran=3'));
await page.click('#back').catch(() => {});
await wait(250);
const ran3 = await page.evaluate(() => window.__ran ?? null);
say(3, 'адрес javascript: в ссылке возврата', ran3 === null,
    ran3 ? 'СКРИПТ ИСПОЛНЕН' : `скрипт не исполнен, href=${JSON.stringify(r3.href)}`);

const r4 = await open('/#orders');
say(4, 'контроль, обычный раздел', r4.section === 'Раздел: orders',
    JSON.stringify(r4.section));

const r5 = await open('/?back=/orders#profile');
say(5, 'контроль, ссылка возврата', r5.href === '/orders',
    `href=${JSON.stringify(r5.href)}`);

await browser.close();
server.close();

const bad = results.filter((ok) => !ok).length;
console.log(bad ? `\nЭКСПЛОЙТ СРАБОТАЛ: провалено опытов ${bad}` : '\nЭКСПЛОЙТ НЕ СРАБОТАЛ');
process.exit(bad ? 1 : 0);
