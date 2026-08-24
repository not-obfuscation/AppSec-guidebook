// Пять опытов над витриной: три эксплойта и два контроля.
// Зелёный (код 0), когда ни один эксплойт не сработал, а контроли живы.
//
//   node hack.mjs                        ожидается ЭКСПЛОЙТ СРАБОТАЛ, код 1
//   LAB_TARGET=solution.mjs node hack.mjs  ожидается ЭКСПЛОЙТ НЕ СРАБОТАЛ, код 0

import { start, ORIGIN } from './serve.mjs';
import { launch } from './labtarget.mjs';

const PAYLOAD_BODY = '<img src=/нет-такого onerror="window.__ran=1">';
const PAYLOAD_ATTR = '" autofocus onfocus="window.__ran=2" x="';
const PAYLOAD_SCRIPT = '<script>window.__ran=3<\/script><img src=/нет onerror="window.__ran=3">';

const server = await start();
const browser = await launch();
const page = await browser.newPage();

async function visit(q) {
  await page.goto(`${ORIGIN}/search?q=${encodeURIComponent(q)}`,
                  { waitUntil: 'networkidle0' });
  await new Promise((r) => setTimeout(r, 150));
  return page.evaluate(() => ({
    ran: window.__ran ?? null,
    msg: document.getElementById('msg').textContent,
    value: document.querySelector('input[name=q]').value,
    hits: document.querySelectorAll('#hits li').length,
  }));
}

const results = [];
function say(n, what, ok, detail) {
  results.push(ok);
  console.log(`  опыт ${n} — ${what}: ${detail}`);
}

const r1 = await visit(PAYLOAD_BODY);
say(1, 'разметка в тексте сообщения', r1.ran === null,
    r1.ran ? 'СКРИПТ ИСПОЛНЕН' : 'скрипт не исполнен');

const r2 = await visit(PAYLOAD_ATTR);
say(2, 'выход из значения атрибута', r2.ran === null,
    r2.ran ? 'СКРИПТ ИСПОЛНЕН' : 'скрипт не исполнен');

const r3 = await visit(PAYLOAD_SCRIPT);
say(3, 'обход чистки слова script', r3.ran === null,
    r3.ran ? 'СКРИПТ ИСПОЛНЕН' : 'скрипт не исполнен');

const r4 = await visit('пароль');
say(4, 'контроль, обычный поиск', r4.hits === 1 && r4.value === 'пароль',
    `найдено ${r4.hits}, в поле ввода ${JSON.stringify(r4.value)}`);

const r5 = await visit('счёт & <тариф>');
const shown = r5.msg.includes('счёт & <тариф>') && r5.value === 'счёт & <тариф>';
say(5, 'контроль, знаки разметки в запросе', shown,
    shown ? 'показаны буквально' : `сообщение ${JSON.stringify(r5.msg)}`);

await browser.close();
server.close();

const bad = results.filter((ok) => !ok).length;
console.log(bad ? `\nЭКСПЛОЙТ СРАБОТАЛ: провалено опытов ${bad}` : '\nЭКСПЛОЙТ НЕ СРАБОТАЛ');
process.exit(bad ? 1 : 0);
