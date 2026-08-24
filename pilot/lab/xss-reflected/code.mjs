// code.mjs — файл, который вы чините.
// УЯЗВИМО — демонстрация, не для продакшена.
//
// Страница поиска по базе знаний. Присланная строка возвращается в том же
// ответе дважды: в тексте сообщения и в значении атрибута поля ввода.
// Перед этим она «чистится» на входе — вырезается слово <script>.

export function clean(value) {
  return value.replace(/<script/gi, '').replace(/<\/script>/gi, '');
}

export function handle(url, articles) {
  const q = clean(url.searchParams.get('q') ?? '');
  const found = q ? articles.filter((a) => a.toLowerCase().includes(q.toLowerCase())) : [];
  return `<!doctype html>
<html lang="ru"><head><meta charset="utf-8"><title>База знаний</title></head>
<body>
<form action="/search">
  <input name="q" value="${q}">
  <button>Искать</button>
</form>
<p id="msg">По запросу «${q}» найдено статей: ${found.length}</p>
<ul id="hits">${found.map((t) => `<li>${t}</li>`).join('')}</ul>
</body></html>`;
}
