// Функциональность карточки. Зелёный до правки и обязан остаться зелёным после.
//
//   node tests.mjs                         ожидается: Упало проверок: 0
//   LAB_TARGET=solution.mjs node tests.mjs   то же самое
//
// Значения без пробела здесь не случайность: исходный code.mjs теряет хвост
// значения в атрибуте без кавычек, и тест на пробел был бы зелёным только
// после починки. Такую проверку делает опыт 4 в hack.mjs, а не этот файл.

import { start, ORIGIN } from './serve.mjs';
import { launch } from './labtarget.mjs';

const server = await start();
const browser = await launch();
const page = await browser.newPage();

async function open(v) {
  await page.goto(`${ORIGIN}/card?v=${encodeURIComponent(v)}`,
                  { waitUntil: 'networkidle0' });
  return page.evaluate(() => ({
    body: document.getElementById('body').textContent,
    quoted: document.getElementById('quoted').value,
    unquoted: document.getElementById('unquoted').getAttribute('data-mark'),
    href: document.getElementById('link').getAttribute('href'),
    mark: typeof window.mark === 'string' ? window.mark : null,
  }));
}

let failed = 0;
function check(name, ok, got) {
  if (!ok) { failed += 1; console.log(`  ПРОВАЛ  ${name}: ${JSON.stringify(got)}`); }
  else console.log(`  ок      ${name}`);
}

const plain = await open('скидка');
check('обычное значение в теле документа', plain.body === 'Метка: скидка', plain.body);
check('обычное значение в атрибуте в кавычках', plain.quoted === 'скидка', plain.quoted);
check('обычное значение в атрибуте без кавычек', plain.unquoted === 'скидка', plain.unquoted);
check('обычное значение в скрипте', plain.mark === 'скидка', plain.mark);

const empty = await open('');
check('пустое значение не ломает страницу', empty.body === 'Метка: ' && empty.mark === '', empty);

const amp = await open('цена&скидка');
check('амперсанд виден в теле и в атрибуте',
      amp.body === 'Метка: цена&скидка' && amp.quoted === 'цена&скидка', amp);

const quote = await open('тариф"эконом"');
check('двойная кавычка не рвёт атрибут', quote.quoted === 'тариф"эконом"', quote.quoted);

const apos = await open("O'Brien");
check('апостроф доезжает до скрипта целиком', apos.mark === "O'Brien", apos.mark);

const digits = await open('2026');
check('число выводится во всех местах',
      digits.body === 'Метка: 2026' && digits.unquoted === '2026' && digits.mark === '2026', digits);

const link = await open('/catalog');
check('путь от корня остаётся адресом ссылки', link.href === '/catalog', link.href);

await browser.close();
server.close();
console.log(`\nУпало проверок: ${failed}`);
process.exit(failed ? 1 : 0);
