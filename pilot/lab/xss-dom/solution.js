// solution.js — образцовое решение.
//
// Три стока, две разные починки. Имя раздела и черновик — текст, и потому
// пишутся в сток, который текстом их и оставляет. Адрес возврата — адрес, и
// его проверяют по форме: экранирование здесь ни при чём, javascript:
// сущностями не закрывается.

const SECTIONS = ['profile', 'orders', 'settings'];

export function showSection() {
  const name = decodeURIComponent(location.hash.slice(1)) || 'profile';
  const known = SECTIONS.includes(name) ? name : 'profile';
  document.getElementById('section').textContent = 'Раздел: ' + known;  // (1)
}

export function showDraft() {
  document.getElementById('draft').textContent = window.name;           // (2)
}

export function showBackLink() {
  const back = new URLSearchParams(location.search).get('back') || '/';
  const safe = /^\/[A-Za-z0-9/_-]*$/.test(back) ? back : '/';           // (3)
  document.getElementById('back').setAttribute('href', safe);
}
