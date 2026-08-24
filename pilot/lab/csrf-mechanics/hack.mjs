// Пять опытов над кабинетом: три эксплойта и два контроля.
// Зелёный (код 0), когда ни один эксплойт не сработал, а контроли живы.
//
//   node hack.mjs                          ожидается ЭКСПЛОЙТ СРАБОТАЛ, код 1
//   LAB_TARGET=solution.mjs node hack.mjs   ожидается ЭКСПЛОЙТ НЕ СРАБОТАЛ, код 0
//
// Вход выполняется заново перед каждым опытом. Причина не в удобстве: cookie
// без явного атрибута `SameSite` уходит с кросс-сайтовым POST только в первые
// две минуты после выставления, и без свежего входа опыт 1 стал бы зависеть
// от того, сколько времени прошло.

import { start, APP, EVIL } from './serve.mjs';
import { launch } from './labtarget.mjs';

const lab = await start();
const browser = await launch();
const results = [];

function say(n, what, ok, detail) {
  results.push(ok);
  console.log(`  опыт ${n} — ${what}: ${detail}`);
}

async function freshVictim() {
  const ctx = await browser.createBrowserContext();
  const page = await ctx.newPage();
  await page.goto(`${APP}/login`, { waitUntil: 'networkidle0' });
  lab.state.email = 'wiener@bank.example';
  return { ctx, page };
}

async function attack(path, target) {
  const { ctx, page } = await freshVictim();
  const url = `${EVIL}${path}?t=${encodeURIComponent(target)}`;
  try {
    await page.goto(url, { waitUntil: 'networkidle0', timeout: 8000 });
  } catch { /* переход уходит на другой сайт — это и есть атака */ }
  await new Promise((r) => setTimeout(r, 250));
  const got = lab.state.email;
  await ctx.close();
  return got;
}

// Опыт 1 — чужая страница отправляет POST-форму в кабинет.
const r1 = await attack('/post', `${APP}/email/change`);
say(1, 'POST-форма с чужого сайта', r1 === 'wiener@bank.example',
    r1 === 'wiener@bank.example' ? 'адрес не изменился' : `АДРЕС ПОДМЕНЁН на ${r1}`);

// Опыт 2 — то же действие методом GET, одним переходом.
const r2 = await attack('/get', `${APP}/email/change?email=mallory@evil.test`);
say(2, 'GET-переход с чужого сайта', r2 === 'wiener@bank.example',
    r2 === 'wiener@bank.example' ? 'адрес не изменился' : `АДРЕС ПОДМЕНЁН на ${r2}`);

// Опыт 3 — то же действие без входа: сессии нет, действия быть не должно.
{
  const ctx = await browser.createBrowserContext();
  const page = await ctx.newPage();
  lab.state.email = 'wiener@bank.example';
  try {
    await page.goto(`${EVIL}/post?t=${encodeURIComponent(`${APP}/email/change`)}`,
                    { waitUntil: 'networkidle0', timeout: 8000 });
  } catch { /* переход ожидаем */ }
  await new Promise((r) => setTimeout(r, 250));
  const r3 = lab.state.email;
  say(3, 'та же форма без входа', r3 === 'wiener@bank.example',
      r3 === 'wiener@bank.example' ? 'адрес не изменился' : `АДРЕС ПОДМЕНЁН на ${r3}`);
  await ctx.close();
}

// Опыт 4 — контроль: своя форма кабинета обязана работать и после починки.
{
  const { ctx, page } = await freshVictim();
  await page.goto(`${APP}/account`, { waitUntil: 'networkidle0' });
  await page.evaluate(() => {
    document.querySelector('input[name=email]').value = 'new@bank.example';
    document.querySelector('form').submit();
  });
  await new Promise((r) => setTimeout(r, 300));
  const ok = lab.state.email === 'new@bank.example';
  say(4, 'контроль, своя форма кабинета', ok,
      ok ? 'адрес сменился на new@bank.example' : `адрес остался ${lab.state.email}`);
  await ctx.close();
}

// Опыт 5 — контроль: кабинет открывается и показывает текущий адрес.
{
  const { ctx, page } = await freshVictim();
  await page.goto(`${APP}/account`, { waitUntil: 'networkidle0' });
  const shown = await page.$eval('#email', (e) => e.textContent);
  const ok = shown === 'wiener@bank.example';
  say(5, 'контроль, кабинет показывает адрес', ok,
      ok ? `на странице ${shown}` : `на странице ${JSON.stringify(shown)}`);
  await ctx.close();
}

await browser.close();
lab.close();

const bad = results.filter((ok) => !ok).length;
console.log(bad ? `\nЭКСПЛОЙТ СРАБОТАЛ: провалено опытов ${bad}` : '\nЭКСПЛОЙТ НЕ СРАБОТАЛ');
process.exit(bad ? 1 : 0);
