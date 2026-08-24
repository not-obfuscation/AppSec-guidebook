// Тест-кейсы правила dom-untrusted-to-sink.
//
// Маркер стоит строкой выше ожидаемой находки: `ruleid:` — правило обязано
// сработать, `ok:` — обязано промолчать. Сверка:
//
//     .venv-tools/bin/python pilot/semgrep/check.py dom-sink

const SECTIONS = ['profile', 'orders'];
const PATH_RE = /^\/[A-Za-z0-9/_-]*$/;

// --- ловит -----------------------------------------------------------

function showFragment(el) {
  const name = location.hash.slice(1);
  // ruleid: dom-untrusted-to-sink
  el.innerHTML = 'Раздел: ' + name;
}

function showReferrer(el) {
  // ruleid: dom-untrusted-to-sink
  el.outerHTML = '<p>Вы пришли из ' + document.referrer + '</p>';
}

function restoreDraft(el) {
  const draft = window.name;
  // ruleid: dom-untrusted-to-sink
  el.insertAdjacentHTML('beforeend', draft);
}

function backLink(el) {
  const back = new URLSearchParams(location.search).get('back');
  // ruleid: dom-untrusted-to-sink
  el.setAttribute('href', back || location.href);
}

function runFromHash() {
  const code = location.hash.slice(1);
  // ruleid: dom-untrusted-to-sink
  eval(code);
}

function writeTitle() {
  // ruleid: dom-untrusted-to-sink
  document.write('<h1>' + document.baseURI + '</h1>');
}

// --- молчит ----------------------------------------------------------

function showFragmentSafe(el) {
  const name = location.hash.slice(1);
  // ok: dom-untrusted-to-sink
  el.textContent = 'Раздел: ' + name;
}

function showKnownSection(el) {
  const name = location.hash.slice(1);
  const known = SECTIONS.includes(name) ? name : 'profile';
  // ok: dom-untrusted-to-sink
  el.innerHTML = 'Раздел: ' + known;
}

function backLinkChecked(el) {
  const back = new URLSearchParams(location.search).get('back') || '/';
  const safe = PATH_RE.test(back) ? back : '/';
  // ok: dom-untrusted-to-sink
  el.setAttribute('href', safe);
}

function staticMarkup(el) {
  // ok: dom-untrusted-to-sink
  el.innerHTML = '<p>Раздел не выбран</p>';
}

function searchQueryInUrl(el) {
  const q = encodeURIComponent(location.search.slice(1));
  // ok: dom-untrusted-to-sink
  el.setAttribute('href', '/search?q=' + q);
}
