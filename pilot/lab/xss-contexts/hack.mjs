// Пять опытов над карточкой: три эксплойта и два контроля.
// Зелёный (код 0), когда ни один эксплойт не сработал, а контроли живы.
//
//   node hack.mjs                        ожидается ЭКСПЛОЙТ СРАБОТАЛ, код 1
//   LAB_TARGET=solution.mjs node hack.mjs  ожидается ЭКСПЛОЙТ НЕ СРАБОТАЛ, код 0

import { start, ORIGIN } from './serve.mjs';
import { launch } from './labtarget.mjs';

const server = await start();
const browser = await launch();
const page = await browser.newPage();
const wait = (ms) => new Promise((r) => setTimeout(r, ms));

async function open(v) {
  await page.goto(`${ORIGIN}/card?v=${encodeURIComponent(v)}`,
                  { waitUntil: 'networkidle0' });
  await wait(200);
  return page.evaluate(() => ({
    ran: window.__ran ?? null,
    body: document.getElementById('body').textContent,
    quoted: document.getElementById('quoted').value,
    unquoted: document.getElementById('unquoted').getAttribute('data-mark'),
    href: document.getElementById('link').getAttribute('href'),
    mark: typeof window.mark === 'string' ? window.mark : null,
  }));
}

const results = [];
function say(n, what, ok, detail) {
  results.push(ok);
  console.log(`  опыт ${n} — ${what}: ${detail}`);
}

const r1 = await open('x autofocus onfocus=window.__ran=1');
say(1, 'значение атрибута без кавычек', r1.ran === null,
    r1.ran ? 'СКРИПТ ИСПОЛНЕН' : 'скрипт не исполнен');

const r2 = await open('javascript:window.__ran=2');
await page.click('#link').catch(() => {});
await wait(250);
const ran2 = await page.evaluate(() => window.__ran ?? null);
say(2, 'адрес javascript: в ссылке', ran2 === null,
    ran2 ? 'СКРИПТ ИСПОЛНЕН' : `скрипт не исполнен, href=${JSON.stringify(r2.href)}`);

const r3 = await open('</script><img src=/нет onerror="window.__ran=3">');
say(3, 'выход из элемента script', r3.ran === null,
    r3.ran ? 'СКРИПТ ИСПОЛНЕН' : 'скрипт не исполнен');

const r4 = await open('скидка 20 %');
const ok4 = r4.body === 'Метка: скидка 20 %' && r4.quoted === 'скидка 20 %'
         && r4.unquoted === 'скидка 20 %' && r4.mark === 'скидка 20 %';
say(4, 'контроль, обычное значение в пяти местах', ok4,
    ok4 ? 'везде показано целиком' : JSON.stringify(r4));

const r5 = await open('«тариф» & <эконом>');
const ok5 = r5.body === 'Метка: «тариф» & <эконом>' && r5.quoted === '«тариф» & <эконом>'
         && r5.mark === '«тариф» & <эконом>';
say(5, 'контроль, знаки разметки и кавычки', ok5,
    ok5 ? 'показаны буквально' : JSON.stringify(r5));

await browser.close();
server.close();

const bad = results.filter((ok) => !ok).length;
console.log(bad ? `\nЭКСПЛОЙТ СРАБОТАЛ: провалено опытов ${bad}` : '\nЭКСПЛОЙТ НЕ СРАБОТАЛ');
process.exit(bad ? 1 : 0);
