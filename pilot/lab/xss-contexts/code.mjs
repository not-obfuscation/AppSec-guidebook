// code.mjs — файл, который вы чините.
// УЯЗВИМО — демонстрация, не для продакшена.
//
// Карточка товара. Одно присланное значение выводится в пяти местах разметки.
// Автор знал про экранирование и применил его везде: сущностями HTML — в
// четырёх местах, обратным слэшем перед кавычкой — в строке скрипта.

const HTML = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#x27;' };

export function escHtml(value) {
  return String(value).replace(/[&<>"']/g, (c) => HTML[c]);
}

export function escQuote(value) {
  return String(value).replace(/'/g, "\\'");
}

export function render(v) {
  return `<!doctype html>
<html lang="ru"><head><meta charset="utf-8"><title>Карточка</title></head>
<body>
<p id="body">Метка: ${escHtml(v)}</p>
<input id="quoted" value="${escHtml(v)}">
<input id="unquoted" data-mark=${escHtml(v)}>
<a id="link" href="${escHtml(v)}">перейти</a>
<script>window.mark = '${escQuote(v)}';<\/script>
</body></html>`;
}
