// Два сервера на петле: кабинет подписки и страница чужого сайта.
//
//   node serve.mjs                          поднять и держать (Ctrl+C — стоп)
//   LAB_TARGET=solution.mjs node serve.mjs   отдавать решение вместо code.mjs
//
// В сеть не ходит: слушает только петлю. Имена `bank.example` и `evil.test`
// уводит на петлю сам браузер (`labtarget.mjs`); для браузера это разные
// сайты, для сети — один и тот же 127.0.0.1.

import { createServer } from 'node:http';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

export const DIR = dirname(fileURLToPath(import.meta.url));
export const APP_PORT = 8125;
export const EVIL_PORT = 8126;
export const APP = `http://bank.example:${APP_PORT}`;
export const EVIL = `http://evil.test:${EVIL_PORT}`;

export async function target() {
  const file = process.env.LAB_TARGET ?? 'code.mjs';
  return import(join(DIR, file));
}

function readBody(req) {
  return new Promise((res) => {
    let b = '';
    req.on('data', (c) => (b += c));
    req.on('end', () => res(b));
  });
}

// Страницы чужого сайта. Обе делают ровно то, что делает страница-приманка:
// отправляют запрос в кабинет и ничего о нём не знают.
function evilPage(url) {
  const t = url.searchParams.get('t') ?? `${APP}/email/change`;
  if (url.pathname === '/post') {
    return `<p>котики загружаются…</p>
<form id="f" action="${t}" method="POST">
  <input type="hidden" name="email" value="mallory@evil.test">
</form>
<script>document.getElementById('f').submit();</script>`;
  }
  if (url.pathname === '/get') {
    return `<p>котики загружаются…</p>
<script>location = ${JSON.stringify(t)};</script>`;
  }
  return '<p>котики</p>';
}

export async function start() {
  const mod = await target();
  const state = mod.freshState();

  const app = createServer(async (req, res) => {
    const url = new URL(req.url, APP);
    const body = req.method === 'POST' ? await readBody(req) : '';
    const out = mod.handle({
      method: req.method,
      url,
      body,
      cookie: req.headers.cookie ?? '',
    }, state);
    const head = { 'content-type': 'text/html; charset=utf-8' };
    if (out.setCookie) head['set-cookie'] = out.setCookie;
    res.writeHead(out.status ?? 200, head);
    res.end(out.html);
  });

  const evil = createServer((req, res) => {
    res.writeHead(200, { 'content-type': 'text/html; charset=utf-8' });
    res.end(evilPage(new URL(req.url, EVIL)));
  });

  await new Promise((r) => app.listen(APP_PORT, '127.0.0.1', r));
  await new Promise((r) => evil.listen(EVIL_PORT, '127.0.0.1', r));
  return { state, close: () => { app.close(); evil.close(); } };
}

if (import.meta.url === `file://${process.argv[1]}`) {
  await start();
  console.log(`кабинет:     ${APP}/`);
  console.log(`чужой сайт:  ${EVIL}/post`);
}
