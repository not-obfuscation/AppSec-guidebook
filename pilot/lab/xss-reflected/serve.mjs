// Один сервер на петле: витрина поиска по базе знаний.
//
//   node serve.mjs                       поднять и держать (Ctrl+C — стоп)
//   LAB_TARGET=solution.mjs node serve.mjs   отдавать решение вместо code.mjs
//
// В сеть не ходит: слушает только петлю, наружу не обращается.

import { createServer } from 'node:http';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

export const DIR = dirname(fileURLToPath(import.meta.url));
export const PORT = 8121;
export const ORIGIN = `http://127.0.0.1:${PORT}`;

const ARTICLES = [
  'Как сбросить пароль',
  'Почему не приходит письмо',
  'Оплата картой',
];

export async function target() {
  const file = process.env.LAB_TARGET ?? 'code.mjs';
  return import(join(DIR, file));
}

export async function start() {
  const { handle } = await target();
  const server = createServer((req, res) => {
    const url = new URL(req.url, ORIGIN);
    if (url.pathname !== '/search' && url.pathname !== '/') {
      res.writeHead(404, { 'content-type': 'text/plain; charset=utf-8' }).end('404');
      return;
    }
    res.writeHead(200, { 'content-type': 'text/html; charset=utf-8' });
    res.end(handle(url, ARTICLES));
  });
  await new Promise((r) => server.listen(PORT, '127.0.0.1', r));
  return server;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  await start();
  console.log(`витрина: ${ORIGIN}/search?q=пароль`);
}
