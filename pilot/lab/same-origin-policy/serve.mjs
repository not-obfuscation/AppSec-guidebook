// Три статических сервера на 127.0.0.1 — три origin одной лабы.
//
//   8081  приложение (у него обработчик, который вы чините)
//   8082  сторона атакующего
//   8083  доверенный виджет
//
// Отличаются только портом: схема и хост совпадают. Этого достаточно —
// по правилу сравнения origin (HTML Standard § 7.1.1) порт входит в кортеж.
//
//   node serve.mjs            поднять и держать (Ctrl+C — остановить)
//   LAB_TARGET=solution.js node serve.mjs   отдавать решение вместо code.js
//
// В сеть не ходит: слушает только петлю, наружу не обращается.

import { createServer } from 'node:http';
import { readFile } from 'node:fs/promises';
import { dirname, join, normalize } from 'node:path';
import { fileURLToPath } from 'node:url';

export const DIR = dirname(fileURLToPath(import.meta.url));
export const PORTS = { app: 8081, evil: 8082, widget: 8083 };
export const ORIGIN = Object.fromEntries(
  Object.entries(PORTS).map(([k, p]) => [k, `http://127.0.0.1:${p}`]));

const TYPES = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8',
                '.json': 'application/json', '.png': 'image/png', '.txt': 'text/plain; charset=utf-8' };
// Однопиксельный PNG: встраивание картинки — та самая «запись/встраивание»,
// которую политика не закрывает.
const PIXEL = Buffer.from(
  'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==',
  'base64');

export const state = { transfers: [] };

function typeOf(path) {
  const dot = path.lastIndexOf('.');
  return TYPES[path.slice(dot)] ?? 'application/octet-stream';
}

async function serveFile(res, root, rel) {
  const path = join(root, normalize('/' + rel));
  if (!path.startsWith(root)) { res.writeHead(403).end('403'); return; }
  try {
    res.writeHead(200, { 'content-type': typeOf(path) });
    res.end(await readFile(path));
  } catch { res.writeHead(404, { 'content-type': 'text/plain' }).end('404'); }
}

function appServer() {
  const root = join(DIR, 'app');
  const target = process.env.LAB_TARGET || 'code.js';
  return createServer(async (req, res) => {
    const url = new URL(req.url, ORIGIN.app);
    if (url.pathname === '/code.js') {
      res.writeHead(200, { 'content-type': TYPES['.js'] });
      res.end(await readFile(join(DIR, target)));
    } else if (url.pathname === '/logo.png') {
      res.writeHead(200, { 'content-type': TYPES['.png'] });
      res.end(PIXEL);
    } else if (url.pathname === '/balance.json') {
      // Ответ без единого поля Access-Control-*: читать его чужому origin
      // браузер не даст, а запрос всё равно уйдёт.
      res.writeHead(200, { 'content-type': TYPES['.json'] });
      res.end(JSON.stringify({ owner: 'anna', balance: 12000 }));
    } else if (url.pathname === '/transfer' && req.method === 'POST') {
      let body = '';
      req.on('data', (c) => { body += c; });
      req.on('end', () => {
        state.transfers.push({ body, origin: req.headers.origin ?? '(нет)' });
        res.writeHead(200, { 'content-type': TYPES['.txt'] }).end('перевод принят');
      });
    } else if (url.pathname === '/transfers') {
      res.writeHead(200, { 'content-type': TYPES['.json'] });
      res.end(JSON.stringify(state.transfers));
    } else {
      await serveFile(res, root, url.pathname === '/' ? 'index.html' : url.pathname);
    }
  });
}

function staticServer(sub) {
  const root = join(DIR, sub);
  return createServer(async (req, res) => {
    const url = new URL(req.url, 'http://127.0.0.1');
    await serveFile(res, root, url.pathname === '/' ? 'index.html' : url.pathname);
  });
}

export async function start() {
  const servers = [[appServer(), PORTS.app], [staticServer('evil'), PORTS.evil],
                   [staticServer('widget'), PORTS.widget]];
  await Promise.all(servers.map(([s, port]) => new Promise((ok, bad) => {
    s.once('error', (e) => bad(new Error(
      e.code === 'EADDRINUSE' ? `порт ${port} занят — освободите его и повторите` : e.message)));
    s.listen(port, '127.0.0.1', ok);
  })));
  return async () => { await Promise.all(servers.map(([s]) => new Promise((ok) => s.close(ok)))); };
}

if (import.meta.url === `file://${process.argv[1]}`) {
  await start();
  console.log(`приложение   ${ORIGIN.app}/`);
  console.log(`атакующий    ${ORIGIN.evil}/attack.html`);
  console.log(`виджет       ${ORIGIN.widget}/panel.html`);
  console.log(`отдаётся     ${process.env.LAB_TARGET || 'code.js'}   Ctrl+C — остановить`);
}
