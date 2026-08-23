// code.js — файл, который вы чините. Отдаётся приложению как /code.js.
// УЯЗВИМО — демонстрация, не для продакшена.
window.addEventListener('message', (event) => {
  const data = JSON.parse(event.data);
  applySettings(data);
});
