// Тест-кейсы правила postmessage-no-origin-check.
// Разметка: строка // ruleid: <id> перед ожидаемой находкой,
// // ok: <id> — перед местом, где находки быть не должно.

const TRUSTED = 'https://widgets.example.com';

// ruleid: postmessage-no-origin-check
window.addEventListener('message', (event) => {
  applySettings(JSON.parse(event.data));
});

// ruleid: postmessage-no-origin-check
window.addEventListener('message', function (e) {
  document.getElementById('out').innerHTML = e.data;
});

// ruleid: postmessage-no-origin-check
addEventListener('message', (event) => {
  applySettings(JSON.parse(event.data));
});

// Проверка есть, но не та: сверяется форма данных, а не происхождение.
// ruleid: postmessage-no-origin-check
window.addEventListener('message', (event) => {
  if (typeof event.data !== 'string') return;
  applySettings(JSON.parse(event.data));
});

// Правдоподобная, но негодная проверка: источник сообщения сам по себе
// ничего не говорит о его origin.
// ruleid: postmessage-no-origin-check
window.addEventListener('message', (event) => {
  if (event.source !== frames[0]) return;
  applySettings(JSON.parse(event.data));
});

// ok: postmessage-no-origin-check
window.addEventListener('message', (event) => {
  if (event.origin !== TRUSTED) return;
  applySettings(JSON.parse(event.data));
});

// ok: postmessage-no-origin-check
window.addEventListener('message', function (e) {
  if (e.origin === TRUSTED && typeof e.data === 'string') {
    applySettings(JSON.parse(e.data));
  }
});

// ok: postmessage-no-origin-check
window.addEventListener('message', (event) => {
  if (!isTrusted(event.origin)) return;
  applySettings(JSON.parse(event.data));
});

// Слепое место правила: проверка есть и читается как проверка, но
// пропускает https://widgets.example.com.attacker.test.
// ok: postmessage-no-origin-check
window.addEventListener('message', (event) => {
  if (!event.origin.startsWith(TRUSTED)) return;
  applySettings(JSON.parse(event.data));
});

// Другое событие — правило не о нём.
// ok: postmessage-no-origin-check
window.addEventListener('click', (event) => {
  applySettings(JSON.parse(event.data));
});

// Обработчик передан по имени: тело в этом месте не видно.
// ruleid: postmessage-handler-by-name
window.addEventListener('message', onMessage);
