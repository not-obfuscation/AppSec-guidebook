// Тесты функциональности кабинета: что обязано работать и после починки.
// Браузер здесь не нужен — обработчик вызывается напрямую.
//
//   node tests.mjs                          проверить code.mjs
//   LAB_TARGET=solution.mjs node tests.mjs   проверить solution.mjs

import { target } from './serve.mjs';

const mod = await target();
const results = [];

function check(name, ok, detail = '') {
  results.push(ok);
  console.log(`  ${ok ? 'ок  ' : 'НЕТ '} ${name}${detail ? ' — ' + detail : ''}`);
}

function call(state, method, path, { body = '', cookie = '' } = {}) {
  return mod.handle({ method, url: new URL(path, 'http://bank.example:8125'),
                      body, cookie }, state);
}

// Вход выдаёт сессионную cookie.
{
  const st = mod.freshState();
  const r = call(st, 'GET', '/login');
  check('вход выдаёт cookie сессии', /session=/.test(r.setCookie ?? ''), r.setCookie ?? '—');
}

// Кабинет показывает текущий адрес.
{
  const st = mod.freshState();
  const r = call(st, 'GET', '/account');
  check('кабинет показывает адрес', r.html.includes('wiener@bank.example'));
}

// Смена адреса своей формой проходит.
{
  const st = mod.freshState();
  const login = call(st, 'GET', '/login');
  const cookie = login.setCookie.split(';')[0];
  const form = call(st, 'GET', '/account', { cookie });
  const token = (/name="csrf" value="([^"]*)"/.exec(form.html) ?? [])[1] ?? '';
  const body = new URLSearchParams({ csrf: token, email: 'new@bank.example' }).toString();
  call(st, 'POST', '/email/change', { body, cookie });
  check('смена адреса своей формой', st.email === 'new@bank.example', st.email);
}

// Без сессии действие отклоняется.
{
  const st = mod.freshState();
  const body = new URLSearchParams({ email: 'mallory@evil.test' }).toString();
  const r = call(st, 'POST', '/email/change', { body });
  check('без сессии — отказ', r.status === 401 && st.email === 'wiener@bank.example',
        `код ${r.status}, адрес ${st.email}`);
}

// Пустое значение адреса не затирает сохранённый.
{
  const st = mod.freshState();
  const login = call(st, 'GET', '/login');
  const cookie = login.setCookie.split(';')[0];
  const form = call(st, 'GET', '/account', { cookie });
  const token = (/name="csrf" value="([^"]*)"/.exec(form.html) ?? [])[1] ?? '';
  const body = new URLSearchParams({ csrf: token, email: '' }).toString();
  call(st, 'POST', '/email/change', { body, cookie });
  check('пустое значение не затирает адрес', st.email === 'wiener@bank.example', st.email);
}

// Неизвестный путь отдаёт 404.
{
  const st = mod.freshState();
  const r = call(st, 'GET', '/нет-такой-страницы');
  check('неизвестный путь — 404', r.status === 404, `код ${r.status}`);
}

// Две сессии живут одновременно и не мешают друг другу.
{
  const st = mod.freshState();
  const a = call(st, 'GET', '/login').setCookie.split(';')[0];
  const b = call(st, 'GET', '/login').setCookie.split(';')[0];
  const okA = call(st, 'GET', '/account', { cookie: a }).status !== 401;
  const okB = call(st, 'GET', '/account', { cookie: b }).status !== 401;
  check('две сессии живут одновременно', okA && okB && a !== b, `${a} и ${b}`);
}

const bad = results.filter((ok) => !ok).length;
console.log(bad ? `\nТЕСТЫ ПРОВАЛЕНЫ: ${bad} из ${results.length}`
                : `\nТЕСТЫ ПРОЙДЕНЫ: ${results.length} из ${results.length}`);
process.exit(bad ? 1 : 0);
