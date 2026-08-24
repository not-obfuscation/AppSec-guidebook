// Функциональность витрины. Зелёный до правки и обязан остаться зелёным после.
//
//   node tests.mjs                         ожидается: Упало проверок: 0
//   LAB_TARGET=solution.mjs node tests.mjs   то же самое

import { start, ORIGIN } from './serve.mjs';
import { launch } from './labtarget.mjs';

const server = await start();
const browser = await launch();
const page = await browser.newPage();

async function search(q) {
  await page.goto(`${ORIGIN}/search?q=${encodeURIComponent(q)}`,
                  { waitUntil: 'networkidle0' });
  return page.evaluate(() => ({
    msg: document.getElementById('msg').textContent,
    value: document.querySelector('input[name=q]').value,
    hits: [...document.querySelectorAll('#hits li')].map((li) => li.textContent),
  }));
}

let failed = 0;
function check(name, ok, got) {
  if (!ok) { failed += 1; console.log(`  ПРОВАЛ  ${name}: ${JSON.stringify(got)}`); }
  else console.log(`  ок      ${name}`);
}

const empty = await search('');
check('пустой запрос — ничего не найдено', empty.hits.length === 0 && empty.value === '', empty);

const pass = await search('пароль');
check('поиск «пароль» находит одну статью', pass.hits.length === 1, pass.hits);

const pay = await search('оплата');
check('поиск «оплата» находит одну статью', pay.hits.length === 1, pay.hits);

const none = await search('квартальный отчёт');
check('поиск без совпадений — ноль статей', none.hits.length === 0, none.hits);

const keep = await search('письмо');
check('поле ввода сохраняет запрос', keep.value === 'письмо', keep.value);

const upper = await search('ПАРОЛЬ');
check('регистр запроса не важен', upper.hits.length === 1, upper.hits);

const amp = await search('оплата & возврат');
check('амперсанд в запросе виден в сообщении',
      amp.msg.includes('оплата & возврат') && amp.value === 'оплата & возврат', amp);

const apos = await search("тариф O'Brien");
check('апостроф в запросе виден в поле ввода', apos.value === "тариф O'Brien", apos.value);

await browser.close();
server.close();
console.log(`\nУпало проверок: ${failed}`);
process.exit(failed ? 1 : 0);
