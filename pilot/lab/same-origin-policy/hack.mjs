// Эксплойт лабы. Поднимает три origin, открывает страницу атакующего в
// настоящем браузере и смотрит, что политика одного источника пропустила.
//
//   node hack.mjs        код возврата 1 — эксплойт сработал, 0 — нет
//
// Браузер — тот же chrome-headless-shell, которым гайдбук рисует схемы
// (`tools/setup.sh`). Разрешение имён в нём обрублено на всё, кроме петли:
// лаба обязана проходиться без сети.
//
// Этапов два. Первый — пять опытов с чужого origin. Второй — доверенный
// виджет, который взломали: HTML Living Standard 9.3.2.1 называет этот
// случай прямо, потому что проверки origin для него мало.

import { start, ORIGIN } from './serve.mjs';
import { launch } from './labtarget.mjs';

const settle = () => new Promise((ok) => setTimeout(ok, 300));

export async function run() {
  const stop = await start();
  const browser = await launch();
  const page = await browser.newPage();
  const console_ = [];
  page.on('console', (m) => console_.push(m.text()));
  page.on('pageerror', (e) => console_.push('pageerror: ' + e.message));

  await page.goto(`${ORIGIN.evil}/attack.html`, { waitUntil: 'load' });
  await page.waitForFunction('window.__done === true', { timeout: 15000 });
  await settle();

  const r = await page.evaluate(() => window.__r);
  const victim = page.frames().find((f) => f.url().startsWith(ORIGIN.app));
  const theme = await victim.evaluate(
    () => document.getElementById('theme').textContent);
  const transfers = await (await fetch(`${ORIGIN.app}/transfers`)).json();

  // Этап 2. Виджет доверенный, и origin у его сообщения настоящий. Взломан
  // сам виджет: он посылает настройку не той формы, которую ждёт приложение.
  const app = await browser.newPage();
  app.on('pageerror', (e) => console_.push('pageerror: ' + e.message));
  await app.goto(`${ORIGIN.app}/`, { waitUntil: 'load' });
  const panel = app.frames().find((f) => f.url().startsWith(ORIGIN.widget));
  await panel.evaluate((target) => parent.postMessage(
    JSON.stringify({ theme: ['взломано'] }), target), ORIGIN.app);
  await settle();
  const shape = await app.evaluate(
    () => document.getElementById('theme').textContent);

  await browser.close();
  await stop();
  return { r, theme, shape, transfers, console: console_ };
}

if (import.meta.url === `file://${process.argv[1]}`) {
  const { r, theme, shape, transfers, console: log } = await run();
  console.log('опыт 1 — чтение чужого документа: ' + r.read);
  console.log('опыт 2 — чтение ответа сервера:   ' + r.fetch);
  console.log('опыт 3 — встраивание картинки:    ' + r.embed);
  console.log('опыт 4 — отправка формы:          ' + r.write
              + `, принято на стороне приложения: ${transfers.length}`
              + `, поле Origin запроса: ${transfers[0]?.origin ?? '(нет)'}`);
  console.log('опыт 5 — сообщение обработчику:   ' + r.post
              + `, тема после сообщения: ${theme}`);
  console.log('опыт 6 — взломанный виджет:       сообщение с настоящим origin'
              + ` и телом не той формы, тема: ${shape}`);
  if (log.length) {
    console.log('\nбраузер сказал:');
    for (const line of log) console.log('  ' + line);
  }
  const broken = theme === 'взломано' || shape === 'взломано';
  console.log('\n' + (broken ? 'ЭКСПЛОЙТ СРАБОТАЛ' : 'ЭКСПЛОЙТ НЕ СРАБОТАЛ'));
  process.exit(broken ? 1 : 0);
}
