// Карточка товара на петле. Одно значение, пять мест вставки.
//
//   node serve.mjs                        поднять и держать (Ctrl+C — стоп)
//   LAB_TARGET=solution.mjs node serve.mjs   отдавать решение вместо code.mjs

import { createServer } from 'node:http';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

export const DIR = dirname(fileURLToPath(import.meta.url));
export const PORT = 8124;
export const ORIGIN = `http://127.0.0.1:${PORT}`;

export async function start() {
  const file = process.env.LAB_TARGET ?? 'code.mjs';
  const { render } = await import(join(DIR, file));
  const server = createServer((req, res) => {
    const url = new URL(req.url, ORIGIN);
    if (url.pathname !== '/' && url.pathname !== '/card') {
      res.writeHead(404, { 'content-type': 'text/plain; charset=utf-8' }).end('404');
      return;
    }
    res.writeHead(200, { 'content-type': 'text/html; charset=utf-8' });
    res.end(render(url.searchParams.get('v') ?? ''));
  });
  await new Promise((r) => server.listen(PORT, '127.0.0.1', r));
  return server;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  await start();
  console.log(`карточка: ${ORIGIN}/card?v=скидка`);
}
