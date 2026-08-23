// solution.js — образцовое решение. Отдаётся вместо code.js по LAB_TARGET.
const TRUSTED = ['http://127.0.0.1:8081', 'http://127.0.0.1:8083'];

window.addEventListener('message', (event) => {
  if (!TRUSTED.includes(event.origin)) return;
  const data = parseSettings(event.data);
  if (data) applySettings(data);
});

// Разбор отделён от применения: сначала значение приводится к ожидаемой
// форме, и только потом меняется состояние страницы.
function parseSettings(raw) {
  if (typeof raw !== 'string') return null;
  let value;
  try { value = JSON.parse(raw); } catch { return null; }
  if (!value || typeof value.theme !== 'string') return null;
  return { theme: value.theme };
}
