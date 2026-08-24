// Приложение на петле. Сервер экранирует всё, что видит, — и это в лабе
// важно: фрагмент адреса он не видит вовсе.
//
//   node serve.mjs                        поднять и держать (Ctrl+C — стоп)
//   LAB_TARGET=solution.js node serve.mjs   отдавать решение вместо code.js
//
// В сеть не ходит: слушает только петлю, наружу не обращается.

import { createServer } from 'node:http';
import { readFile } from 'node:fs/promises';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

export const DIR = dirname(fileURLToPath(import.meta.url));
export const PORT = 8122;
export const EVIL_PORT = 8123;
export const ORIGIN = `http://127.0.0.1:${PORT}`;
export const EVIL = `http://127.0.0.1:${EVIL_PORT}`;

// Всё, что сервер увидел в запросах: лаба показывает, чего в этом списке нет.
export const seen = [];

export async function start() {
  const file = process.env.LAB_TARGET ?? 'code.js';
  const server = createServer(async (req, res) => {
    const url = new URL(req.url, ORIGIN);
    seen.push(url.pathname + url.search);
    if (url.pathname === '/code.js') {
      res.writeHead(200, { 'content-type': 'text/javascript; charset=utf-8' });
      res.end(await readFile(join(DIR, file)));
      return;
    }
    if (url.pathname === '/' || url.pathname === '/index.html') {
      res.writeHead(200, { 'content-type': 'text/html; charset=utf-8' });
      res.end(await readFile(join(DIR, 'app/index.html')));
      return;
    }
    res.writeHead(404, { 'content-type': 'text/plain; charset=utf-8' }).end('404');
  });
  await new Promise((r) => server.listen(PORT, '127.0.0.1', r));

  // Второй origin — чужая площадка: она задаёт имя окна и уводит браузер сюда.
  const evil = createServer(async (req, res) => {
    res.writeHead(200, { 'content-type': 'text/html; charset=utf-8' });
    res.end(await readFile(join(DIR, 'evil/index.html')));
  });
  await new Promise((r) => evil.listen(EVIL_PORT, '127.0.0.1', r));

  return { close: () => { server.close(); evil.close(); } };
}

if (import.meta.url === `file://${process.argv[1]}`) {
  await start();
  console.log(`кабинет: ${ORIGIN}/#profile`);
  console.log(`чужая площадка: ${EVIL}/?to=${ORIGIN}/`);
}
