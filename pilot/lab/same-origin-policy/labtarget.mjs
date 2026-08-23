// Браузер для лабы: тот же chrome-headless-shell, которым гайдбук рисует
// схемы (ставится `tools/setup.sh`), и тот же puppeteer из `tools/node`.
// Разрешение имён обрублено на всё, кроме петли: правило 8.2 п. 7 свода
// требует, чтобы лаба проходилась без сети, и здесь это не обещание, а флаг.
//
// Переопределить браузер: CHROME_PATH=/путь/к/chrome node hack.mjs

import { readdirSync, existsSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const DIR = dirname(fileURLToPath(import.meta.url));
const PUP = join(DIR, '../../../tools/node/node_modules/.pnpm');

function puppeteerPath() {
  const dirs = readdirSync(PUP).filter((d) => d.startsWith('puppeteer@'));
  if (!dirs.length) throw new Error('нет puppeteer в tools/node — `make setup`');
  return join(PUP, dirs[0], 'node_modules/puppeteer/lib/puppeteer/puppeteer.js');
}

function chromePath() {
  if (process.env.CHROME_PATH) return process.env.CHROME_PATH;
  const base = join(process.env.HOME, '.cache/puppeteer/chrome-headless-shell');
  if (!existsSync(base)) throw new Error('нет chrome-headless-shell — `make setup`');
  return join(base, readdirSync(base).sort().pop(),
              'chrome-headless-shell-linux64/chrome-headless-shell');
}

export async function launch() {
  const puppeteer = (await import(puppeteerPath())).default;
  return puppeteer.launch({
    headless: true,
    executablePath: chromePath(),
    args: ['--no-sandbox', '--disable-gpu',
           '--host-resolver-rules=MAP * ~NOTFOUND, EXCLUDE 127.0.0.1'],
  });
}
