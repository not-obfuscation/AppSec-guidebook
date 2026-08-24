// Тест-кейсы правила state-change-from-query.
// Разметка: строка // ruleid: <id> перед ожидаемой находкой,
// // ok: <id> — перед местом, где находки быть не должно.

const store = { email: '', role: 'user', items: [] };

// Значение из строки запроса записывается в состояние: действие достижимо
// одним переходом по ссылке.
function changeEmail(req) {
  const value = req.query.email;
  // ruleid: state-change-from-query
  store.email = value;
}

// Тот же дефект через WHATWG URL.
function changeRole(url) {
  const value = url.searchParams.get('role');
  // ruleid: state-change-from-query
  store.role = value;
}

// Запись по вычисляемому ключу — тот же сток.
function setField(req) {
  // ruleid: state-change-from-query
  store[req.query.field] = req.query.value;
}

// Значение из тела запроса: метод здесь не GET, и правило молчит.
function changeEmailFromBody(req) {
  const value = req.body.email;
  // ok: state-change-from-query
  store.email = value;
}

// Чтение строки запроса без записи в состояние: показ, а не действие.
function render(req) {
  const q = req.query.q;
  // ok: state-change-from-query
  const html = `<p>вы искали ${q}</p>`;
  return html;
}

// Маршрут на GET, обработчик меняет состояние.
// ruleid: state-change-on-get-route
app.get('/subscribe', (req, res) => {
  store.items.push(req.params.plan);
  res.end('ок');
});

// Тот же маршрут на POST: правило молчит.
// ok: state-change-on-get-route
app.post('/subscribe', (req, res) => {
  store.items.push(req.body.plan);
  res.end('ок');
});

// Маршрут на GET, который только читает.
// ok: state-change-on-get-route
app.get('/account', (req, res) => {
  res.end(JSON.stringify(store));
});
