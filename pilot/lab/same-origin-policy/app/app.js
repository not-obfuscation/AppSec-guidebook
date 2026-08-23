// Инфраструктура страницы: применяет уже проверенную настройку. Проверять
// входящее — работа обработчика сообщения, а не этой функции. Чинить надо
// не здесь, а в code.js.
window.applySettings = function (data) {
  document.getElementById('theme').textContent = data.theme;
  window.__applied = (window.__applied || 0) + 1;
};
