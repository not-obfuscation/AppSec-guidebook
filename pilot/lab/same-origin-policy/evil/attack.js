// Четыре опыта из чужого origin. Каждый пишет результат в window.__r,
// откуда его читает hack.mjs. Рабочего инструмента здесь нет: только
// проверка того, что политика запрещает, и того, что она пропускает.
const r = { read: null, fetch: null, embed: null, write: null, post: null };
window.__r = r;

const victim = document.getElementById('victim');
const probe = document.getElementById('probe');

probe.addEventListener('load', () => { r.embed = 'загрузилась'; });
probe.addEventListener('error', () => { r.embed = 'не загрузилась'; });

victim.addEventListener('load', async () => {
  // Опыт 1. Прочитать чужой документ через ссылку на его окно.
  try {
    r.read = 'прочитано: ' + victim.contentWindow.document.title;
  } catch (e) {
    r.read = e.name + ': ' + e.message;
  }
  // Опыт 2. Прочитать ответ сервера того же чужого origin.
  try {
    const response = await fetch('http://127.0.0.1:8081/balance.json');
    r.fetch = 'прочитано: ' + (await response.text());
  } catch (e) {
    r.fetch = e.name + ': ' + e.message;
  }
  // Опыт 3. Запись: отправка формы с побочным эффектом на чужой стороне.
  document.getElementById('write').submit();
  r.write = 'форма отправлена';
  // Опыт 4. Сообщение обработчику чужого документа.
  victim.contentWindow.postMessage(JSON.stringify({ theme: 'взломано' }), '*');
  r.post = 'сообщение отправлено';
  window.__done = true;
});
