// Тест-кейсы правил html-attr-unquoted-interpolation и
// html-value-in-script-string.
//
// Маркер стоит строкой выше ожидаемой находки: `ruleid:` — правило обязано
// сработать, `ok:` — обязано промолчать. Сверка:
//
//     .venv-tools/bin/python pilot/semgrep/check.py html-context

function escHtml(v) { return String(v); }
function forScript(v) { return JSON.stringify(String(v)); }

// --- ловит -----------------------------------------------------------

function markUnquoted(v) {
  // ruleid: html-attr-unquoted-interpolation
  return `<input id="m" data-mark=${escHtml(v)}>`;
}

function classUnquoted(v) {
  // ruleid: html-attr-unquoted-interpolation
  return `<div class=${escHtml(v)}>карточка</div>`;
}

function widthUnquoted(v) {
  // ruleid: html-attr-unquoted-interpolation
  return `<img src="/p.png" width=${v} alt="товар">`;
}

function markInScriptSingle(v) {
  // ruleid: html-value-in-script-string
  return `<script>window.mark = '${escHtml(v)}';</script>`;
}

function markInScriptDouble(v) {
  // ruleid: html-value-in-script-string
  return `<script>var t = "${escHtml(v)}";</script>`;
}

// --- молчит ----------------------------------------------------------

function markQuoted(v) {
  // ok: html-attr-unquoted-interpolation
  return `<input id="m" data-mark="${escHtml(v)}">`;
}

function bodyText(v) {
  // ok: html-attr-unquoted-interpolation
  return `<p>Метка: ${escHtml(v)}</p>`;
}

function markInScriptJson(v) {
  // ok: html-value-in-script-string
  return `<script>window.mark = ${forScript(v)};</script>`;
}

function markViaDataAttribute(v) {
  // ok: html-value-in-script-string
  return `<span id="m" data-mark="${escHtml(v)}"></span>`;
}

function staticMarkup() {
  // ok: html-attr-unquoted-interpolation
  return `<input id="m" data-mark="нет">`;
}
