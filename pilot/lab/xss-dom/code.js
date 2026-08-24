// code.js — файл, который вы чините. Отдаётся приложению как /code.js.
// УЯЗВИМО — демонстрация, не для продакшена.
//
// Кабинет с разделами. Три значения приезжают из браузера, а не от сервера:
// имя раздела — из фрагмента адреса, черновик заметки — из имени окна,
// адрес возврата — из параметра back.

export function showSection() {
  const name = decodeURIComponent(location.hash.slice(1)) || 'profile';
  document.getElementById('section').innerHTML = 'Раздел: ' + name;   // (1)
}

export function showDraft() {
  document.getElementById('draft').innerHTML = window.name;           // (2)
}

export function showBackLink() {
  const back = new URLSearchParams(location.search).get('back') || '/';
  document.getElementById('back').setAttribute('href', back);         // (3)
}
