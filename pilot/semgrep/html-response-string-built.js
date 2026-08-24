// Тест-кейсы правила html-response-string-built.
//
// Маркер стоит строкой выше ожидаемой находки: `ruleid:` — правило обязано
// сработать, `ok:` — обязано промолчать. Сверка:
//
//     .venv-tools/bin/python pilot/semgrep/check.py html-response

const HTML = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#x27;' };
function escapeHtml(v) { return String(v).replace(/[&<>"']/g, (c) => HTML[c]); }

// --- ловит -----------------------------------------------------------

function statusPage(req, res) {
  const message = req.query.message;
  // ruleid: html-response-string-built
  res.send(`<p>Статус: ${message}</p>`);
}

function searchPage(url, res) {
  const q = url.searchParams.get('q');
  // ruleid: html-response-string-built
  res.end('<p>Вы искали: ' + q + '</p>');
}

function greeting(req, res) {
  const name = req.body.name;
  // ruleid: html-response-string-built
  res.write(`<div class="hi">Здравствуйте, ${name}</div>`);
}

function profileMarkup(req) {
  const bio = req.params.bio;
  // ruleid: html-response-string-built
  return `<section><p>${bio}</p></section>`;
}

function fromHeader(req, res) {
  const lang = req.headers['accept-language'];
  // ruleid: html-response-string-built
  res.send(`<html lang="${lang}"><body>ок</body></html>`);
}

// --- молчит ----------------------------------------------------------

function statusPageFixed(req, res) {
  const message = escapeHtml(req.query.message);
  // ok: html-response-string-built
  res.send(`<p>Статус: ${message}</p>`);
}

function searchLink(url, res) {
  const q = encodeURIComponent(url.searchParams.get('q'));
  // ok: html-response-string-built
  res.end(`<a href="/search?q=${q}">повторить</a>`);
}

function counter(req, res) {
  const page = Number(req.query.page);
  // ok: html-response-string-built
  res.send(`<p>Страница ${page}</p>`);
}

function staticPage(res) {
  // ok: html-response-string-built
  res.send('<p>Раздел временно недоступен</p>');
}

function jsonAnswer(req, res) {
  // Ответ не разметка: браузер его не разбирает как HTML.
  // ok: html-response-string-built
  res.send(JSON.stringify({ q: req.query.q }));
}
