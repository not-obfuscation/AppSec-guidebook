// solution.mjs — образцовое решение.
//
// Фильтра на входе нет: он не знает, куда значение попадёт. Вместо него —
// экранирование на выводе, у самого места вставки. В теле документа хватает
// четырёх знаков разметки; в значении атрибута к ним добавляется кавычка,
// которой атрибут закрыт. Одна функция закрывает оба места, потому что
// кавычка в тексте безвредна, а в атрибуте обязательна.

const HTML = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#x27;' };

export function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (c) => HTML[c]);
}

export function handle(url, articles) {
  const q = url.searchParams.get('q') ?? '';
  const found = q ? articles.filter((a) => a.toLowerCase().includes(q.toLowerCase())) : [];
  return `<!doctype html>
<html lang="ru"><head><meta charset="utf-8"><title>База знаний</title></head>
<body>
<form action="/search">
  <input name="q" value="${escapeHtml(q)}">
  <button>Искать</button>
</form>
<p id="msg">По запросу «${escapeHtml(q)}» найдено статей: ${found.length}</p>
<ul id="hits">${found.map((t) => `<li>${escapeHtml(t)}</li>`).join('')}</ul>
</body></html>`;
}
