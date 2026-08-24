// solution.mjs — образцовое решение.
//
// Пять мест вставки — четыре разных правила. Сущности HTML закрывают тело
// документа и значение атрибута, но только когда атрибут в кавычках. Адрес
// закрывается проверкой схемы, а не экранированием. Значение внутри скрипта
// уезжает не строкой шаблона, а через JSON с закрытыми знаками разметки.

const HTML = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#x27;' };

export function escHtml(value) {
  return String(value).replace(/[&<>"']/g, (c) => HTML[c]);
}

// Адрес: разрешены только http, https и путь от корня. Всё прочее — на корень.
export function safeUrl(value) {
  const v = String(value);
  if (/^\/[^/\\]/.test(v) || v === '/') return v;
  if (/^https?:\/\//i.test(v)) return v;
  return '/';
}

// Значение для скрипта: JSON плюс закрытые знаки, которыми разбор разметки
// вышел бы из элемента script.
export function forScript(value) {
  return JSON.stringify(String(value))
    .replace(/</g, '\\u003c')
    .replace(/>/g, '\\u003e')
    .replace(/&/g, '\\u0026')
    .replace(/\u2028/g, '\\u2028')
    .replace(/\u2029/g, '\\u2029');
}

export function render(v) {
  return `<!doctype html>
<html lang="ru"><head><meta charset="utf-8"><title>Карточка</title></head>
<body>
<p id="body">Метка: ${escHtml(v)}</p>
<input id="quoted" value="${escHtml(v)}">
<input id="unquoted" data-mark="${escHtml(v)}">
<a id="link" href="${escHtml(safeUrl(v))}">перейти</a>
<script>window.mark = ${forScript(v)};<\/script>
</body></html>`;
}
