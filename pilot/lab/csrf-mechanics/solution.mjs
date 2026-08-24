// Исправлено.
//
// Три правки. Изменяющее действие принимается только методом POST. К сессии
// привязан синхронизирующий токен, и он проверяется до действия. Сессионная
// cookie получила явное значение атрибута `SameSite`.

import { randomBytes, timingSafeEqual } from 'node:crypto';

export function freshState() {
  return { email: 'wiener@bank.example', sessions: new Map() };
}

const page = (body) => `<!doctype html><meta charset="utf-8"><title>кабинет</title>${body}`;

function form(email, token) {
  return page(`<p id="email">${email}</p>
<form action="/email/change" method="POST">
  <input type="hidden" name="csrf" value="${token ?? ''}">
  <input name="email" value="${email}">
  <button type="submit">сохранить</button>
</form>`);
}

function session(cookie) {
  const m = /(?:^|;\s*)session=([^;]+)/.exec(cookie);
  return m ? m[1] : null;
}

function sameToken(a, b) {
  const x = Buffer.from(String(a));
  const y = Buffer.from(String(b));
  return x.length === y.length && timingSafeEqual(x, y);       // (3)
}

export function handle(req, state) {
  const p = req.url.pathname;

  if (p === '/login') {
    const id = 'S' + (state.sessions.size + 1);
    state.sessions.set(id, randomBytes(32).toString('base64url'));  // (1)
    return {
      setCookie: `session=${id}; Path=/; HttpOnly; SameSite=Strict`,  // (4)
      html: page('<p id="ok">вошли</p>'),
    };
  }

  if (p === '/email/change') {
    if (req.method !== 'POST') {                               // (2)
      return { status: 405, html: page('<p id="err">только POST</p>') };
    }
    const sid = session(req.cookie);
    if (!sid || !state.sessions.has(sid)) {
      return { status: 401, html: page('<p id="err">нужен вход</p>') };
    }
    const body = new URLSearchParams(req.body);
    if (!sameToken(body.get('csrf'), state.sessions.get(sid))) {
      return { status: 403, html: page('<p id="err">токен не сошёлся</p>') };
    }
    const email = body.get('email');
    if (email) state.email = email;
    return { html: page(`<p id="ok">адрес теперь ${state.email}</p>`) };
  }

  if (p === '/' || p === '/account') {
    const sid = session(req.cookie);
    return { html: form(state.email, state.sessions.get(sid)) };
  }
  return { status: 404, html: page('<p>404</p>') };
}
