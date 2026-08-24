// УЯЗВИМО — демонстрация, не для продакшена.
//
// Кабинет подписки: вход, показ адреса почты, смена адреса. Кто прислал
// запрос, приложение решает по одной сессионной cookie.

export function freshState() {
  return { email: 'wiener@bank.example', sessions: new Set() };
}

const page = (body) => `<!doctype html><meta charset="utf-8"><title>кабинет</title>${body}`;

function form(email) {
  return page(`<p id="email">${email}</p>
<form action="/email/change" method="POST">
  <input name="email" value="${email}">
  <button type="submit">сохранить</button>
</form>`);
}

function session(cookie) {
  const m = /(?:^|;\s*)session=([^;]+)/.exec(cookie);
  return m ? m[1] : null;
}

export function handle(req, state) {
  const p = req.url.pathname;

  if (p === '/login') {
    const id = 'S' + (state.sessions.size + 1);
    state.sessions.add(id);
    return { setCookie: `session=${id}; Path=/`, html: page('<p id="ok">вошли</p>') };
  }

  if (p === '/email/change') {
    const sid = session(req.cookie);                         // (1)
    if (!sid || !state.sessions.has(sid)) {
      return { status: 401, html: page('<p id="err">нужен вход</p>') };
    }
    const src = req.method === 'POST'
      ? new URLSearchParams(req.body)
      : req.url.searchParams;                                // (2)
    const email = src.get('email');
    if (email) state.email = email;                          // (3)
    return { html: page(`<p id="ok">адрес теперь ${state.email}</p>`) };
  }

  if (p === '/' || p === '/account') return { html: form(state.email) };
  return { status: 404, html: page('<p>404</p>') };
}
