---
id: npm-dependencies
plan_id: t-7-3-02
title: 'Небезопасные зависимости npm'
summary: >
  Что фиксирует package-lock.json и зачем он коммитится, что считает
  npm audit и что означают его коды выхода, чем npm ci отличается от
  npm install в конвейере.
stage: code-review-languages
order: 120
status: published
depth: L3
mode: концепт
time_min: 15
teaches:
  - Назвать, что фиксирует lockfile и почему npm install его молча
    переписывает
  - Прочитать вывод npm audit и объяснить его код выхода
prerequisites: [supply-chain-threats, transitive-dependencies]
related: [supply-chain-threats, transitive-dependencies]
tags: [javascript, code-review, supply-chain]
cwe: [CWE-1357, CWE-1104]
asvs: []
wstg: []
owasp: ['A03:2025']
labs: []
sources: [npm-audit, npm-package-lock, node-security-best-practices]
reviewed: 2026-09-02
review_interval: 6
---

# Небезопасные зависимости npm

Уровень **L3** · время 15 мин

Что прочитать сначала: `supply-chain-threats`, `transitive-dependencies`.

Учебный проект с одной прямой зависимостью — lodash, заданной точным
номером 4.17.15 без диапазона. Оцените до вывода: сколько бюллетеней
даст одна такая зависимость? Прогон аудита:

```text
$ npm audit
lodash  <=4.17.23
Severity: high
Prototype Pollution in lodash — GHSA-p6mc-m468-83gw
Command Injection in lodash — GHSA-35jh-r3h4-6jhm
...
fix available via `npm audit fix --force`
Will install lodash@4.18.1, which is outside the stated dependency range
$ echo $?
1
```

Одна строка в package.json развернулась в список из шести бюллетеней.
Фикс предложен с `--force`: точный номер без диапазона делает любую
другую версию выходом за заявленное. Аудит
отработал за секунду, а код выхода 1 уже годится как сигнал конвейеру.
Заметим, чего аудит не сделал: он ничего не исправил без команды fix.
Прогон собирает дисциплину темы в один экран: аудит сигналит, но не
чинит. Решает человек или конвейер.

Это тема о минимальном наборе дисциплины зависимостей в экосистеме npm.
Угрозы цепочки поставки разобраны в теме `supply-chain-threats`,
транзитивная глубина — в `transitive-dependencies`. Здесь — как этот
класс выглядит в npm: lockfile, аудит и два режима установки.

## 0. Коротко

В package.json версии обычно записаны диапазонами, а реальное дерево
зависимостей фиксирует package-lock.json: версия каждого пакета, адрес
архива и его хеш integrity. Установка по lockfile — воспроизводимая;
npm ci ставит ровно его и падает при расхождении с package.json, а
npm install lockfile молча переписывает. Команда npm audit отправляет
дерево в реестр и возвращает бюллетени. Код выхода 1 при находках, порог
настраивается флагом `--audit-level`. Это CWE-1357 и CWE-1104 (каталог
Common Weakness Enumeration), категория `A03:2025` издания OWASP 2025
года. То же в терминах, которыми это обсуждают.

**Зачем это в работе AppSec-инженера.** Ревью зависимостей в npm-проекте
— это три вопроса: есть ли lockfile в репозитории, чем ставятся зависимости
в конвейере и что стоит на выходе аудита. Все три отвечаются чтением
файлов и одним прогоном.

## 3. Механика

**Откуда это взялось.** Диапазон версий в package.json — заявка, а не
факт: `^4.17.15` означает «что угодно совместимое», и две установки в
разные дни ставят разное. Lockfile появился как запись факта: дерево,
которое реально собралось, с хешем каждого архива. Наивная привычка
«не коммитить служебные файлы» здесь ломает воспроизводимость: без
lockfile сборка коллеги и сборка конвейера расходятся молча.

Формат lockfile читается глазами. У каждого пакета есть поля version,
resolved (адрес архива) и integrity (хеш для сверки при скачивании).
Прогон подтверждает: установка lodash 4.17.15 записала lockfileVersion 3
и sha512-хеш архива с реестра. Поэтому lockfile — это и карта для
аудита. Команда отправляет в реестр имена и версии всего дерева и
получает бюллетени по совпадениям диапазонов, включая мета-уязвимости.
Это пакеты, уязвимые через своих зависимых.

Коды выхода проверены прогоном. При находках уровня high аудит
завершается с кодом 1, а с `--audit-level=critical` тот же прогон
возвращает 0: порог меняет только сигнал, не отчёт. Отдельно
зафиксировано поведение npm ci. При расхождении package.json и lockfile
он падает с ошибкой EUSAGE вместо тихой переустановки. Это и делает его
формой для конвейера: сборка либо воспроизводима, либо не состоялась.
Ответьте без запуска: чем кончится npm ci в конвейере, где lockfile не
коммитили?

Границы: аудит видит только известные бюллетени по известным версиям;
свежескомпрометированный пакет он не отличит от честного. Дополнительные
меры из документации Node.js: флаг `--ignore-scripts` против установочных
скриптов и отложенная установка свежих версий через `--min-release-age`
в npm 11.10 и новее.

## 13. Источники

1. npm-audit, документация npm CLI v11; реестр `npm-audit`. Разделы:
   Synopsis и Description, Exit Code, `audit-level`, `audit fix` и его
   `--force`, Bulk Advisory Endpoint.
   <https://docs.npmjs.com/cli/v11/commands/npm-audit/>
2. package-lock.json, документация npm CLI v11; реестр
   `npm-package-lock`. Разделы: назначение lockfile и коммит в
   репозиторий, поля version/resolved/integrity, lockfileVersion,
   npm-shrinkwrap.json.
   <https://docs.npmjs.com/cli/v11/configuring-npm/package-lock-json>
3. Security Best Practices, документация Node.js; реестр
   `node-security-best-practices`. Разделы: Malicious Third-Party
   Modules и Supply chain attacks (lockfile, npm ci, ignore-scripts,
   min-release-age).
   <https://nodejs.org/learn/getting-started/security-best-practices>

Каркас этапа: у этапа 7 общих унаследованных источников нет; каждая тема
опирается на документацию своего языка и на материалы этапа 1 по
классам дефектов.

**Скоропортящийся слой.** Флаги и умолчания npm меняются между мажорными
версиями: `--min-release-age` появился в v11.10, формат lockfile —
на v7 и v9. Бюллетени по конкретным версиям устаревают сразу. При ревизии
перечитываются страницы CLI, а не механика.

**Маркеры уверенности.** **Проверено лично** 2026-09-02 на npm 12.0.2 и
Node.js 26.8.1: проект с lodash, заданной точным номером 4.17.15, даёт
отчёт из шести бюллетеней уровня high и код выхода 1; с
`--audit-level=critical` код 0; lockfile
содержит lockfileVersion 3, адрес архива и sha512-хеш; npm ci при
расхождении package.json и lockfile падает с EUSAGE и кодом 1. Расчёт
мета-уязвимостей и устройство endpoint'ов реестра — **по документации**
npm (обе страницы открыты лично 2026-09-02). Советы по `--ignore-scripts`
и `--min-release-age` — по документации Node.js, открытой в тот же день;
в прогонах не воспроизводились.
