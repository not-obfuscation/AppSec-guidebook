# Опорные источники

> **Статус: этот файл переезжает в `sources.yaml`.** Источник истины теперь —
> `sources.yaml` (реестр записей) и `topics.yaml` (карта «тема → источники»);
> человекочитаемые таблицы по этапам генерируются в `sources/` командой
> `python tools/gen_sources_md.py` и вручную не правятся. Покрытие проверяет
> `python tools/validate.py`.
>
> Таблицы ниже — исходный материал переноса. Источник считается перенесённым
> только после личной перепроверки: страница открыта заново, версия и дата
> сверены, проставлены `license` и `checked`. Перенос по старым датам не годится.
> Что уже перенесено — см. `STATUS.md`.
>
> Разделы «Критерий авторитетности» и «Протокол проверки источника» действуют
> без изменений и являются частью правил нового реестра.

Это костяк источников для гайдбука «как стать AppSec-инженером» — по одному набору на каждый этап плана обучения (кроме этапа 6, исключённого из гайдбука). Каждый источник в списке ниже лично открыт, проверен на дату/версию/статус и оценён на волатильность девятью независимыми заходами исследования, а затем сверен ещё раз сквозной проверкой.

Это **не** библиография и не список «прочитать всё от корки до корки». Это отправная точка: перед тем как писать конкретную тему этапа, вы открываете соответствующие строки этой таблицы, читаете их, и только потом добираете точечные источники под саму тему — они попадают в реестр `sources` контентной модели, а не в этот файл.

## Как этим пользоваться

- **Ядро этапа** — строка под каждой таблицей. Это 3–4 источника, на которые опирается большинство тем этапа; их открывают первыми, до начала работы над этапом. Остальные строки таблицы — справка, к которой обращаются под конкретную тему. Читать все десять подряд не нужно и не предполагается.
- Источник открывается **перед** тем как вы садитесь писать тему, а не подшивается постфактум для проформы.
- Каждое утверждение в гайде должно сводиться к источнику, который вы лично открыли и перечитали для этой темы — не к тому, что «где-то видели» или помнили с прошлого раза.
- Ссылки живут в реестре `sources` по `id`, в тексте темы вы ссылаетесь на `id`, а не вписываете голый URL в прозу.
- Если тема этапа шире, чем покрывают источники ниже (см. раздел «Провалы») — это ожидаемо: добираете самостоятельно и фиксируете новый источник по тому же протоколу проверки.
- Один и тот же источник, использованный в двух этапах, заводится в реестре один раз — смотрите раздел «Сквозные источники», прежде чем создавать дубль.
- Волатильность в таблицах — это не оценка качества, а сигнал «когда перепроверять»: быстро гниющие источники (живые каталоги, документация SaaS-инструментов) требуют повторной проверки при каждом использовании, стабильные — раз в полгода-год достаточно.

## Критерий авторитетности

Источники ранжируются по пяти уровням — при выборе между двумя вариантами всегда предпочитайте более высокий уровень:

1. **Первоисточник** — спецификация (RFC, W3C/WHATWG standard), официальная документация вендора/проекта, нормативный акт. Отвечает на вопрос «как это устроено на самом деле», а не «как кто-то это пересказал».
2. **Отраслевой консенсус** — OWASP (Top 10, ASVS, WSTG, Cheat Sheet Series, SAMM), NIST, MITRE/CWE, FIRST (CVSS/EPSS). Коллективно поддерживаемые документы признанных организаций.
3. **Учебный ресурс с репутацией** — PortSwigger Web Security Academy, Hacker101 и подобные: бесплатные, живые, с практикой, от организации с прослеживаемой историей и именем.
4. **Книга-эталон** — используется точечно и осознанно, когда первых трёх уровней недостаточно; должна быть явно указана с автором и годом издания, а не «где-то читал».
5. **Исследование** — оригинальная статья/публикация признанного автора или лаборатории (например GitHub Security Lab), когда она вводит термин или технику, которых нет больше нигде.

**Источником не считается**: агрегаторы без атрибуции авторства и даты (HackTricks, howtoharden.com и подобные вики), Medium-статьи, маркетинговые блоги вендоров безопасности (Wiz, Endor Labs и т.п.) без первичного исследования за ними, зеркала официальной документации на сторонних сайтах, страницы, которые не удалось открыть лично и проверить.

## Протокол проверки источника

При добавлении любого нового источника в реестр — короткий чеклист:

- [ ] источник открыт лично (не по памяти, не со слов поисковика);
- [ ] установлен автор/издатель и дата публикации или номер версии;
- [ ] определена волатильность (stable / medium / fast-rotting) — насколько быстро контент устаревает;
- [ ] записана лицензия (или явно отмечено «не указана» — это тоже факт, а не пропуск);
- [ ] для быстро гниющих источников — сохранена архивная копия (снимок страницы, дата снятия);
- [ ] проставлена дата проверки — когда именно источник открывали и сверяли.

## Источники по этапам

### Этап 0. База протокола и модели веб-приложения

| Источник | Тип | Что берём | Версия / дата | Гниёт |
|---|---|---|---|---|
| [RFC 9110 — HTTP Semantics](https://www.rfc-editor.org/rfc/rfc9110.html) | spec | методы, коды ответа, заголовки HTTP | Internet Standard, июнь 2022 | нет |
| [Cookies: HTTP State Management Mechanism (rfc6265bis)](https://datatracker.ietf.org/doc/draft-ietf-httpbis-rfc6265bis/) | spec | атрибуты cookie: Secure, HttpOnly, SameSite, Domain, Path | draft-22, декабрь 2025, в финальной проверке RFC Editor | нет |
| [Fetch Standard — CORS protocol](https://fetch.spec.whatwg.org/) | spec | CORS preflight, Access-Control-* | Living Standard, обновлён 2 июля 2026 | средне |
| [Content Security Policy Level 3](https://www.w3.org/TR/CSP3/) | spec | директивы CSP, nonce/hash-source | Working Draft, 13 августа 2026 | средне |
| [RFC 9846 — TLS 1.3](https://www.rfc-editor.org/rfc/rfc9846.html) | spec | рукопожатие TLS, цепочка сертификатов | опубликован июль 2026, обсолетит RFC 8446 | нет |
| [URL Standard](https://url.spec.whatwg.org/) | spec | структура URL, кодирование, double encoding | Living Standard, обновлён 6 июля 2026 | средне |
| [Burp Suite documentation — Tools](https://portswigger.net/burp/documentation/desktop/tools) | tool-docs | Proxy, Repeater, Decoder, Comparer, Intruder | актуальная desktop-документация | быстро |
| [HTTP Headers Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/HTTP_Headers_Cheat_Sheet.html) | owasp | HSTS, X-Frame-Options, X-Content-Type-Options, Referrer-Policy | живой документ | средне |
| [Same-origin policy (MDN)](https://developer.mozilla.org/en-US/docs/Web/Security/Same-origin_policy) | official-docs | определение origin, связь с cookies и CORS | обновлено 29 ноября 2025 | средне |
| [Learn GraphQL](https://graphql.org/learn/) | official-docs | схема, типы, запросы, мутации, сравнение с REST | живой сайт, 2026 | средне |

**Ядро этапа:** RFC 9110, rfc6265bis, Fetch Standard, MDN Same-origin policy. Остальное — справка по конкретной теме.

**Почему именно эти.** RFC 9110 — действующий Internet Standard, заменивший устаревшую серию RFC 7230–7235; rfc6265bis взят вместо формально ещё живого, но фактически устаревшего RFC 6265, который вообще не знает про SameSite. Fetch Standard выбран вместо W3C CORS, который сам W3C пометил obsolete ещё в 2017-м. CSP Level 3 хоть и черновик формально, но именно он соответствует тому, что реализуют браузеры сегодня — в отличие от финализированного, но урезанного CSP2. RFC 9846 — свежая (июль 2026) замена RFC 8446, ссылка на старый номер была бы устаревшей на момент написания гайда. URL Standard описывает боевой алгоритм парсинга/нормализации, от которого зависят double-encoding атаки, чего нет в абстрактном RFC 3986. MDN — единственное место, где Same-Origin Policy собрана в одну связную страницу, потому что формальной спецификации у неё нет.

Отвергнуто: диссертация Roy Fielding про REST (канонична, но избыточна по глубине для обзорного этапа — вынесена в провалы как опциональный deep-dive), spec.graphql.org (формальная грамматика, избыточна для уровня темы), OWASP Session Management Cheat Sheet (сильный источник, но его место — в этапе про аутентификацию, не здесь).

### Этап 1. Веб-уязвимости

| Источник | Тип | Что берём | Версия / дата | Гниёт |
|---|---|---|---|---|
| [OWASP Top 10:2025](https://owasp.org/Top10/2025/) | owasp | общая структура и приоритизация рисков | категории A01–A10 подтверждены лично 2026-08-16; статус релиза на странице не указан | средне |
| [OWASP ASVS 5.0.0](https://owasp.org/www-project-application-security-verification-standard/) | standard | чек-лист требований по всем темам этапа | v5.0.0, май 2025 | средне |
| [OWASP WSTG v4.2](https://owasp.org/www-project-web-security-testing-guide/) | owasp | методология тестирования по шагам | v4.2, 2020-12-03 (v5 в разработке, не стабильна) | нет |
| [OWASP Cheat Sheet Series](https://cheatsheetseries.owasp.org/) | owasp | защитные практики: XSS, SQLi, CSRF, JWT, OAuth2, SAML, SSRF, GraphQL | живой репозиторий | средне |
| [PortSwigger Web Security Academy](https://portswigger.net/web-security) | course | практика: smuggling, race conditions, JWT, GraphQL, WebSocket, LLM-атаки | живая платформа | средне |
| [RFC 9700 — OAuth 2.0 Security BCP](https://www.rfc-editor.org/rfc/rfc9700.html) | spec | атаки на redirect-flows, запрет Implicit/ROPC, обязательный PKCE | январь 2025, BCP 240 | нет |
| [RFC 8725 — JWT Best Current Practices](https://www.rfc-editor.org/rfc/rfc8725.html) | spec | alg:none, confusion, substitution-атаки на JWT | февраль 2020, BCP 225 | нет |
| [OWASP API Security Top 10 (2023)](https://owasp.org/API-Security/editions/2023/en/0x00-header/) | owasp | BOLA, BFLA как формально определённые классы | издание 2023 | средне |
| [NIST SP 800-63B-4](https://csrc.nist.gov/pubs/sp/800/63/b/4/final) | standard | хранение паролей, MFA, phishing-resistant auth | финал, 31 июля 2025 | средне |
| [2025 CWE Top 25](https://cwe.mitre.org/top25/archive/2025/2025_cwe_top25.html) | reference-db | приоритизация классов уязвимостей по данным CVE | обновлено 15 декабря 2025 | средне |
| [LLM01:2025 Prompt Injection](https://genai.owasp.org/llmrisk/llm01-prompt-injection/) | owasp | direct/indirect prompt injection, отличие от jailbreaking | издание 2025 | быстро |

**Ядро этапа:** PortSwigger Web Security Academy, OWASP Cheat Sheet Series, ASVS 5.0.0, WSTG v4.2. Первые два — рабочие инструменты на каждый день, вторые два — каркас требований и методологии.

**Почему именно эти.** Top 10:2025 — не draft, а финальный релиз, задающий каркас категорий почти дословно совпадающий с формулировками этапа. ASVS отвечает на «что должно быть реализовано», WSTG — на «как это протестировать», Cheat Sheet Series — на «как защититься»: три разных вопроса, ни один не дублирует другой. PortSwigger Academy — фактический живой преемник Web Application Hacker's Handbook той же команды, с интерактивной практикой, которой нет ни в одном справочнике. RFC 9700 и RFC 8725 — официальные BCP, а не пересказы: конкретно предписывают что запрещено (Implicit Grant, ROPC, alg:none) и что обязательно (PKCE). API Security Top 10 — источник самих терминов BOLA/BFLA, которых нет в основном Top 10.

Отвергнуто: The Web Application Hacker's Handbook (2011, не знает CSP/JWT/SSRF/GraphQL — заменена Academy той же командой), OWASP WSTG v5 (нестабильный GitHub-draft), исследовательский блог James Kettle (дублирует то, что уже разложено в Academy), OpenID Connect Core и OASIS SAML Core (избыточная глубина спецификаций для абзаца этапа), MITRE ATT&CK (про инфраструктурные атаки, не веб-уязвимости), HackTricks (вики без чёткой атрибуции и версионирования).

### Этап 2. Инструментарий AppSec

| Источник | Тип | Что берём | Версия / дата | Гниёт |
|---|---|---|---|---|
| [CWE (cwe.mitre.org)](https://cwe.mitre.org/) | reference-db | таксономия классов уязвимостей для маркировки находок SAST/DAST/SCA | v4.20, обновлено 10 июня 2026 | нет |
| [CVSS v3.1 Specification](https://www.first.org/cvss/v3.1/specification-document) | spec | формулы и векторы CVSS v3.1 | ревизия r1 | нет |
| [CVSS v4.0 Specification](https://www.first.org/cvss/v4-0/specification-document) | spec | метрики CVSS v4.0, отличия от v3.1 | версия документа 1.2, 18 июня 2024 | нет |
| [EPSS (first.org)](https://www.first.org/epss/) | spec | вероятностная оценка эксплуатации для приоритизации патчинга | модель v4, март 2025 | средне |
| [CISA Known Exploited Vulnerabilities Catalog](https://www.cisa.gov/known-exploited-vulnerabilities-catalog) | official-docs | приоритизация по факту реальной эксплуатации | пополняется, август 2026 | быстро |
| [CycloneDX Specification](https://cyclonedx.org/specification/overview/) | spec | формат SBOM | v1.7, опубликована 21 октября 2025 | средне |
| [Semgrep — Data-flow analysis and taint mode](https://docs.semgrep.dev/writing-rules/data-flow/taint-mode) | tool-docs | принцип SAST (источники/стоки), написание правил | живая документация | быстро |
| [OWASP ZAP — Authentication & OpenAPI Support](https://www.zaproxy.org/docs/desktop/addons/openapi-support/) | tool-docs | DAST, аутентифицированное сканирование, импорт OpenAPI | живая документация | быстро |
| [OWASP Dependency-Track Documentation](https://docs.dependencytrack.org/) | tool-docs | SBOM-driven SCA, сопоставление с CVE, триаж находок | v4.14 | быстро |
| [gitleaks](https://github.com/gitleaks/gitleaks) | tool-docs | поиск секретов в git-истории, pre-commit хук | v8.24.2, проект feature complete | средне |
| [Sigstore Documentation](https://docs.sigstore.dev/) | official-docs | подпись артефактов: cosign, keyless-подпись через OIDC, Fulcio, прозрачный лог Rekor, аттестации и provenance | живая документация, версия на странице не указана | быстро |

**Ядро этапа:** CWE, CVSS v3.1, Semgrep taint mode, Dependency-Track. Первые два — язык, на котором описываются находки; вторые два — как работает поиск и как ведётся триаж.

**Почему именно эти.** CWE — единственный официальный таксономический реестр, на который ссылаются и сканеры, и CVE-записи, и весь раздел триажа. CVSS v3.1 и v4.0 включены оба, потому что индустрия использует их параллельно, а не только последнюю версию. EPSS дополняет CVSS вероятностной оценкой, CISA KEV — приоритизацией по факту реальной эксплуатации: три источника вместе дают полную картину severity, ни один не заменяет другой. CycloneDX выбран как формат, который реально генерируют современные SCA-инструменты, и он стандартизирован как ECMA-424. Semgrep taint mode — редкий случай, когда документация одновременно объясняет концепцию SAST и учит писать правила. Dependency-Track закрывает разом SBOM, SCA и часть workflow триажа — то, что иначе потребовало бы трёх источников.

Отвергнуто: CVE Program (реестр идентификаторов без содержательной спецификации), SPDX (дублирует роль CycloneDX как SBOM-формата), CodeQL docs и Trivy docs (концептуально дублируют уже включённые Semgrep и Dependency-Track), trufflehog (прямой конкурент gitleaks по назначению), Solar appScreener / PT Application Inspector (маркетинговые страницы без проверяемой техдокументации).

### Этап 3. Встройка в CI/CD

| Источник | Тип | Что берём | Версия / дата | Гниёт |
|---|---|---|---|---|
| [Understanding GitHub Actions](https://docs.github.com/en/actions/get-started/understanding-github-actions) | official-docs | модель workflow → job → step → runner | living doc | средне |
| [Controlling permissions for GITHUB_TOKEN](https://docs.github.com/en/actions/writing-workflows/choosing-what-your-workflow-does/controlling-permissions-for-github_token) | official-docs | права токена, принцип наименьших привилегий | living doc | средне |
| [Security hardening for GitHub Actions](https://docs.github.com/en/actions/security-for-github-actions/security-guides/security-hardening-for-github-actions) | official-docs | инъекции в workflow, third-party actions, pull_request_target, OIDC | living doc | средне |
| [GitHub Security Lab — Preventing pwn requests](https://securitylab.github.com/resources/github-actions-preventing-pwn-requests/) | research | детальный разбор атаки через pull_request_target | опубликовано 3 августа 2021, актуально | нет |
| [Configuring OIDC in HashiCorp Vault](https://docs.github.com/en/actions/how-tos/secure-your-work/security-harden-deployments/oidc-in-hashicorp-vault) | official-docs | секреты в CI через OIDC вместо статичных токенов Vault | living doc | средне |
| [About protected branches](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches) | official-docs | защита веток, required status checks как blocking gate | living doc | средне |
| [About commit signature verification](https://docs.github.com/en/authentication/managing-commit-signature-verification/about-commit-signature-verification) | official-docs | подпись коммитов: GPG, SSH, S-MIME | living doc | средне |
| [GitLab CI/CD YAML syntax reference](https://docs.gitlab.com/ci/yaml/) | official-docs | устройство пайплайна: stages, needs, include, artifacts, cache | living doc, тиры Free/Premium/Ultimate | средне |
| [GitLab Pipeline security](https://docs.gitlab.com/ci/pipeline_security/) | official-docs | secrets management (упоминание Vault), pipeline integrity | living doc | средне |
| [OWASP Top 10 CI/CD Security Risks](https://owasp.org/www-project-top-10-ci-cd-security-risks/) | owasp | платформенно-независимая таксономия CICD-SEC-1..10 | v1.0, октябрь 2022 | нет |

**Ядро этапа:** Security hardening for GitHub Actions, GitLab CI/CD YAML reference, OWASP Top 10 CI/CD Security Risks, GHSL «Preventing pwn requests». Остальные страницы GitHub открываются точечно под конкретную тему.

**Почему именно эти.** Security hardening for GitHub Actions — центральный официальный чек-лист, одним заходом закрывающий script injection, доверие сторонним actions, права токена, pull_request_target и OIDC; GHSL pwn-requests добавляет глубину, которой в официальной доке всего два абзаца — это оригинальное исследование, введшее сам термин «pwn request». Protected branches закрывает разом две темы этапа: защиту веток и механизм required status checks как способ превратить проверку в блокирующую. GitLab YAML reference и Pipeline security — прямой аналог связки GitHub-документов со стороны второй платформы, без них набор был бы однобоко GitHub-центричным. OWASP Top 10 CI/CD даёт именованный, платформенно-независимый язык описания угроз пайплайна, построенный на разборе реальных инцидентов (SolarWinds, Codecov).

Отвергнуто: OWASP CI/CD Security Cheat Sheet (на 70–80% дублирует уже включённые официальные доки), SLSA (про целостность артефактов цепочки поставок, не про сам пайплайн — ближе к этапу 2), GitLab protected branches (прямой дубль уже включённого GitHub-аналога), вендорские блоги (Wiz) и Medium-статьи — не первоисточники по правилам отбора.

### Этап 4. Инфраструктура

| Источник | Тип | Что берём | Версия / дата | Гниёт |
|---|---|---|---|---|
| [capabilities(7)](https://man7.org/linux/man-pages/man7/capabilities.7.html) | official-docs | модель Linux capabilities, замена setuid-root | man-pages 6.18, 2026-02-08 | нет |
| [namespaces(7)](https://man7.org/linux/man-pages/man7/namespaces.7.html) | official-docs | все 8 типов namespaces — основа изоляции контейнеров | man-pages 6.18, 2026-02-08 | нет |
| [Docker Engine security](https://docs.docker.com/engine/security/) | official-docs | механизм изоляции, docker.sock, rootless-режим | living doc | средне |
| [Build secrets — Docker Build docs](https://docs.docker.com/build/building/secrets/) | official-docs | секреты, утекающие в build args/слои образа | living doc | средне |
| [Docker Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Docker_Security_Cheat_Sheet.html) | owasp | чек-лист: privileged, docker.sock, capabilities | живой документ | средне |
| [Hadolint](https://hadolint.github.io/hadolint/) | tool-docs | линтинг Dockerfile (AST + ShellCheck) | без явной версии на странице | средне |
| [Harbor Documentation](https://goharbor.io/docs/) | official-docs | self-hosted реестр, встроенная интеграция сканеров | v2.15.0 | средне |
| [Security — Kubernetes Documentation](https://kubernetes.io/docs/concepts/security/) | official-docs | RBAC, service accounts, Pod Security Standards, network policies, admission controllers | v1.36 | средне |
| [Kubernetes Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Kubernetes_Security_Cheat_Sheet.html) | owasp | практические рекомендации по RBAC/Pod Security/сетям | живой документ | средне |
| [Database secrets engine — Vault](https://developer.hashicorp.com/vault/docs/secrets/databases) | official-docs | static vs dynamic secrets, ротация, короткоживущие креды | living doc | средне |
| [The SELinux Notebook](https://github.com/SELinuxProject/selinux-notebook) | official-docs | SELinux: типы, контексты, устройство политики, компоненты ядра и userspace | живая книга проекта SELinux, 191 коммит; доступна в HTML/PDF/EPUB | средне |
| [AppArmor — Ubuntu Server documentation](https://ubuntu.com/server/docs/how-to/security/apparmor/) | official-docs | AppArmor: профили в `/etc/apparmor.d/`, режимы enforce/complain, `aa-status`, `aa-genprof`, `apparmor_parser` | Canonical; дата обновления на странице не указана | средне |

**Ядро этапа:** capabilities(7), namespaces(7), Docker Engine security, Security — Kubernetes Documentation. Первые две объясняют механизм, на который опираются все остальные документы этапа.

**Почему именно эти.** capabilities(7) и namespaces(7) — фундаментальные man-страницы, на понятия из которых опираются и Docker (--cap-drop/--cap-add), и Kubernetes securityContext; без них остальные документы этапа читаются как рецепт без объяснения механизма. Docker Engine security объясняет «почему это работает так», OWASP Docker Cheat Sheet — «что делать»: не дублируют, а дополняют друг друга. Build secrets отвечает на конкретную частую находку аудита — секреты в build args. kubernetes.io Security hub — единый хаб, из которого расходятся все нужные подстраницы (RBAC Good Practices, Pod Security Standards, Network Policies, Admission Controllers), что экономит бюджет источников без потери первоисточникового статуса. Vault database secrets engine на одной странице противопоставляет static roles и dynamic roles с leasing-механизмом.

Отвергнуто: NSA/CISA Kubernetes Hardening Guidance (недоступен для проверки, к тому же документу от августа 2022 больше трёх лет), CIS Docker/Kubernetes Benchmark (за регистрационным барьером), RHEL SELinux/Security Hardening guide (стабильно отдавал 403, не удалось верифицировать содержимое), man systemd.exec(5) (сильный источник по hardening юнитов, вырезан ради лимита в пользу более сквозных capabilities/namespaces).

### Этап 5. Процессы безопасной разработки

| Источник | Тип | Что берём | Версия / дата | Гниёт |
|---|---|---|---|---|
| [Threat Modeling Manifesto](https://www.threatmodelingmanifesto.org/) | reference-db | методологически-независимая рамка threat modeling («4 вопроса») | v1.0 | нет |
| [OWASP Threat Modeling Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Threat_Modeling_Cheat_Sheet.html) | owasp | DFD, границы доверия, STRIDE, упоминание PASTA/OCTAVE | живой документ | средне |
| [Threats — Microsoft Threat Modeling Tool docs](https://learn.microsoft.com/en-us/azure/security/develop/threat-modeling-tool-threats) | official-docs | эталонные определения всех шести категорий STRIDE | обновлено 2026-03-04 | нет |
| ASVS 5.0.0 *(сквозной, см. Этап 1)* | standard | ASVS как чек-лист требований, а не awareness-документ | v5.0.0, май 2025 | средне |
| [OWASP SAMM — The Model](https://owaspsamm.org/model/) | owasp | 5 бизнес-функций и 15 практик зрелости SSDLC | v2.0 | средне |
| OWASP Top 10:2025 *(сквозной, см. Этап 1)* | owasp | диаграмма маппинга категорий 2021→2025 | финал 2025 | средне |
| OWASP API Security Top 10 *(сквозной, см. Этап 1)* | owasp | отдельная модель угроз API, не пересекается с веб-Top10 | издание 2023 | средне |
| [NIST SP 800-218 — SSDF v1.1](https://csrc.nist.gov/pubs/sp/800/218/final) | standard | 4 группы практик secure SDLC верхнего уровня | v1.1, февраль 2022 | нет |
| [Logging Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html) | owasp | что логировать, что нельзя (пароли, session ID, PAN), алертинг | живой документ | средне |
| [NIST SP 800-61 Rev. 3](https://csrc.nist.gov/pubs/sp/800/61/r3/final) | standard | жизненный цикл реагирования на инциденты, привязан к CSF 2.0 | Rev.3, апрель 2025 | нет |

**Ядро этапа:** Threat Modeling Manifesto, OWASP Threat Modeling Cheat Sheet, ASVS 5.0.0, OWASP SAMM. Стандарты NIST открываются под конкретную тему, целиком не читаются.

**Почему именно эти.** Threat Modeling Manifesto задаёт рамку, без которой STRIDE и PASTA читались бы как несвязанные чек-листы. OWASP Threat Modeling Cheat Sheet закрывает сразу DFD, границы доверия, детальный STRIDE и краткое упоминание альтернативных методологий одним документом; Microsoft Threats page добавляет эталонные формулировки самих категорий STRIDE — методология родилась именно в Microsoft SDL. ASVS отличается от Top 10 тем, что это чек-лист требований, а не awareness-документ; SAMM — единственная зрелостная модель этапа. NIST SSDF даёт федеральную структуру secure SDLC (Executive Order 14028), Logging Cheat Sheet — конкретику по тому, что логировать нельзя, NIST 800-61 Rev.3 — актуальную (2025) замену устаревшего Rev.2, привязанную к CSF 2.0.

Отвергнуто: OWASP Top10:2021 (полностью перекрыт версией 2025, которая сама содержит маппинг), OpenSAMM (устаревшая v1.x, замещена owaspsamm.org), VerSprite-статьи про PASTA (вендорский маркетинг компании соавтора методологии), книга Шостака «Threat Modeling: Designing for Security» (эталонная, но платная и не проверяема по URL), эссе Брюса Шнайера про attack trees 1999 года (журнальная статья, не спецификация — вынесена в провалы).

### Этап 6. Российская нормативная база — исключён

**Снято 2026-08-20 решением автора: раздела в гайдбуке не будет.** Источники по
российской нормативной базе не собираются и в реестр `sources.yaml` не
переносятся; девять записей, стоявших здесь раньше (ГОСТ Р 56939-2024, приказы
ФСТЭК №240 и №76, БДУ ФСТЭК, Методика оценки угроз, 152-ФЗ, ГОСТ Р 57580.1-2017,
187-ФЗ, Реестр российского ПО), удалены вместе с разделом.

Ни одна из них не была верифицирована личным открытием страницы: домены семейства
`.gov.ru` не открывались при сборке из-за ошибки проверки TLS-сертификата, а
полные тексты ГОСТов платные. То есть выбрасывается не проверенная работа, а
неподтверждённый список — сожалеть не о чем.

Этап 6 остаётся в плане обучения (`plan.md.md`) как учебная тема — план правит
автор, и агент его не трогает. Исключение касается только гайдбука.

### Этап 7. Языки для code review

| Источник | Тип | Что берём | Версия / дата | Гниёт |
|---|---|---|---|---|
| [Deserialization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Deserialization_Cheat_Sheet.html) | owasp | Python: pickle/PyYAML; Java: gadget chains, ObjectInputStream | живой документ | средне |
| [subprocess — Security Considerations](https://docs.python.org/3/library/subprocess.html) | official-docs | shell=True, shlex.quote() | Python 3.14.7 | нет |
| [Security in Django](https://docs.djangoproject.com/en/stable/topics/security/) | official-docs | ORM/raw SQL, XSS auto-escape, CSRF middleware, файлы | Django 6.1 | средне |
| [Security Considerations — Flask](https://flask.palletsprojects.com/en/stable/web-security/) | official-docs | Jinja auto-escape, отсутствие встроенной CSRF-защиты, cookie-флаги | Flask 3.1.x | средне |
| [Node.js Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Nodejs_Security_Cheat_Sheet.html) | owasp | child_process как bash-интерпретатор, path traversal, npm audit | живой документ | средне |
| [Prototype Pollution Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Prototype_Pollution_Prevention_Cheat_Sheet.html) | owasp | prototype pollution в серверном JS/TS | живой документ | средне |
| [Data Race Detector (go.dev)](https://go.dev/doc/articles/race_detector) | official-docs | гонки в горутинах, флаг -race | стабильная официальная статья | нет |
| [OWASP Go Secure Coding Practices (Go-SCP)](https://github.com/OWASP/Go-SCP) | owasp | обработка ошибок, SQL, работа с путями, input validation в Go | Incubator Project | средне |
| [Endpoints — Spring Boot Actuator Reference](https://docs.spring.io/spring-boot/reference/actuator/endpoints.html) | official-docs | экспозиция и защита actuator-эндпоинтов | Spring Boot 4.1.0 | средне |
| [Security — Apache Log4j 2](https://logging.apache.org/log4j/2.x/security.html) | official-docs | JNDI-инъекции, Log4Shell (CVE-2021-44228) | обновляется, последняя запись CVE-2026-49844 | быстро |
| [Pydantic — Validators](https://pydantic.dev/docs/validation/latest/concepts/validators/) | official-docs | механика валидации: field/model-валидаторы, before/after/plain/wrap, порядок выполнения, `SkipValidation` | Pydantic v2, «latest» | средне |

**Ядро этапа:** Deserialization Cheat Sheet, Security in Django, Node.js Security Cheat Sheet, OWASP Go-SCP. Каждый закрывает свой язык, вместе — четыре языка плана.

**Почему именно эти.** Deserialization Cheat Sheet — редкий случай, когда один документ закрывает одну и ту же тему сразу для двух языков (Python pickle/PyYAML и Java gadget chains). subprocess docs — прямая цитата официальной команды CPython про риск shell=True, а не чей-то пересказ. Django security и Flask Security Considerations — официальные разделы самих фреймворков: что берёт на себя фреймворк и что остаётся на разработчике, применимо только к конкретному фреймворку и потому не заменяется общими источниками. Node.js Security Cheat Sheet закрывает три темы этапа (child_process, path traversal, npm audit) одним документом. OWASP Go-SCP переносит структуру OWASP Secure Coding Practices на Go построчно — папки error-handling-logging, database-security, file-management, input-validation закрывают разом три оставшиеся Go-темы. Apache Log4j security — первоисточник по Log4Shell, а не вендорский блог-пересказ, и страница живая — на ней есть записи вплоть до 2026 года.

Отвергнуто: SEI CERT Oracle Coding Standard for Java (сотни детальных правил — избыточно для обзорного уровня этапа), Spring Security Reference (общая тема аутентификации, не названная отдельно в плане), Node.js Security Best Practices на nodejs.org/learn (слишком общий чек-лист без конкретики по child_process/path/prototype pollution).

### Этап 8 (опционально). Фаззинг web2, мобильный AppSec, безопасность LLM, bug bounty, BSCP

| Источник | Тип | Что берём | Версия / дата | Гниёт |
|---|---|---|---|---|
| [OWASP MASVS](https://mas.owasp.org/MASVS/) | owasp | требования к безопасности мобильных приложений, карта домена | живой сайт, 2026 | средне |
| [OWASP MASTG](https://mas.owasp.org/MASTG/) | owasp | практические техники и инструменты тестирования Android/iOS | живой сайт, 2026 | быстро |
| [OWASP Top 10 for LLM Applications 2026](https://genai.owasp.org/resource/owasp-genai-llm-top-10-2026/) | owasp | актуальный список рисков LLM-приложений | опубликован 3–4 августа 2026 | быстро |
| [Burp Suite Certified Practitioner — how to prepare](https://portswigger.net/web-security/certification/how-to-prepare) | official-docs | формат экзамена BSCP, план подготовки | живая страница | средне |
| [Atheris (Google)](https://github.com/google/atheris) | tool-docs | coverage-guided фаззинг Python и нативных расширений | v3.1.0, 17 июня 2026 | быстро |
| [AFL++](https://aflplus.plus/) | tool-docs | общие принципы coverage-guided фаззинга, режимы для бинарей | v4.31c | быстро |
| [Hacker101](https://www.hacker101.com/) | course | обучение + CTF-практика для bug bounty | живой сайт | средне |

**Ядро этапа:** OWASP MASVS, OWASP Top 10 for LLM Applications 2026, BSCP «how to prepare». Этап обзорный, глубокое чтение здесь не требуется.

**Почему именно эти.** MASVS даёт карту домена мобильного AppSec («что проверять») прежде чем нырять в технику, MASTG — практическое дополнение («как проверять», инструменты вроде Frida/objection): вместе закрывают тему без дублирования. LLM Top 10 2026 — самая свежая версия проекта (опубликована буквально за пару недель до сверки), впервые построена не только на голосовании экспертов, но и на данных 6639 реальных инцидентов. BSCP how-to-prepare — единственный официальный источник по требованиям к сертификации, с конкретным четырёхшаговым планом подготовки, а не общий маркетинговый текст. Atheris выбран как мост к пониманию coverage-guided фаззинга через Python (доступный автору язык) без переключения на C/Go, AFL++ добавляет отраслевой эталон и общие принципы (power schedules, режимы для бинарей без исходников). Hacker101 — единственный бесплатный образовательный ресурс от крупной bug bounty платформы, сочетающий видео с реальной CTF-практикой.

Отвергнуто: Hypothesis (решает смежную задачу property-based тестирования, а не coverage-guided fuzzing), go-fuzz (устарел — заменён встроенным `go test -fuzz` с Go 1.18), The Bug Hunter's Methodology (стал платным курсом, больше не бесплатный первоисточник), Bugcrowd VRT и disclose.io (при проверке вернули 404 и 403 соответственно — не прошли верификацию).

## Сквозные источники

Эти источники используются больше чем на одном этапе — заводите их в реестре один раз по «домашнему» этапу, из остальных ссылайтесь на тот же `id`.

| Источник | Домашний этап | Где ещё применяется |
|---|---|---|
| OWASP Top 10:2025 | Этап 1 | Этап 5 (как маппинг рисков 2021→2025 и SDLC-контекст) |
| OWASP API Security Top 10 (2023) | Этап 1 | Этап 5 (терминология BOLA/BFLA) |
| OWASP ASVS 5.0.0 | Этап 1 | Этап 5 (как чек-лист требований, а не таксономия рисков) |

По ASVS в исходных материалах встретились два разных URL одного и того же стандарта — страница проекта OWASP и репозиторий на GitHub. Оба ведут на v5.0.0 и датированы маем 2025, но в реестре стоит закрепить один канонический адрес (рекомендуется страница проекта OWASP, `owasp.org/www-project-application-security-verification-standard/`) и не заводить второй как отдельную запись.

## Провалы

**Закрыто вручную 2026-08-16** (было критично, проверено личным открытием страниц):

- Этап 4 — SELinux и AppArmor. Добавлены The SELinux Notebook (книга проекта SELinux, донесена сообществу Ричардом Хейнсом) и раздел AppArmor в документации Ubuntu Server от Canonical. Первая закрывает типы, контексты и устройство политики; вторая — профили, режимы enforce/complain, `aa-status`, `aa-genprof`. RHEL-гайд по-прежнему отдаёт 403 и не нужен.
- Этап 2 — подпись артефактов. Добавлена документация Sigstore: cosign, keyless-подпись через OIDC, Fulcio, прозрачный лог Rekor, аттестации и provenance.

**Частично закрыто:**

- **Этап 7 — FastAPI и Pydantic. Подтверждено 2026-08-20 повторным открытием обеих страниц.** Документация Pydantic по валидаторам даёт механику (валидаторы поля и модели, режимы before/after/plain/wrap, порядок выполнения, `SkipValidation`), но безопасность не разбирает — ни строгий против нестрогого режима, ни работу с недоверенным вводом. Security-раздел FastAPI по-прежнему покрывает только OAuth2 и схемы аутентификации. Связка «валидация как граница доверия» в отрасли не описана: в теме её придётся выстроить самостоятельно из механики Pydantic и общих правил валидации ввода (`owasp-cs-input-validation` в реестре).

**Приемлемо — источника не существует в природе, зафиксировать это честно в тексте гайда, а не имитировать ссылку:**

- ~~Этап 1 — бизнес-логика~~ — **снято 2026-08-20.** Письменного стандарта по классу действительно нет, но набор из четырёх источников закрывает все темы 1.9: PortSwigger Business logic vulnerabilities и Race conditions (механика, включая TOCTOU, limit overrun и single-packet attack), CWE-682 и документация Python по плавающей точке (округление денег), CWE-190 (переполнения и отрицательные значения), черновик IETF Idempotency-Key (идемпотентность). Последний — черновик рабочей группы без назначенного статуса RFC; это отмечено в его записи.
- ~~Этап 5 — attack trees и abuse/misuse cases~~ — **снято 2026-08-20, оценка была ошибочной.** По abuse cases в серии есть OWASP Abuse Case Cheat Sheet — его просто не нашли (страница открыта лично, разбирает процесс от пользовательской истории к истории злоупотребления и критерии приёмки). По attack trees: эссе Шнайера отвергли как «журнальную публицистику», но по критерию авторитетности этого же файла уровень 5 — это «оригинальная публикация признанного автора, вводящая технику, которой нет больше нигде», и работа Шнайера (Dr. Dobb's Journal, декабрь 1999, полный текст на schneier.com) под него подходит буквально. Третьим взят разбор Carnegie Mellon SEI «Threat Modeling: 12 Available Methods» (Н. Шевченко, 3 декабря 2018) — он же закрывает и «PASTA обзорно», для которой других источников уровня лаборатории нет: сама PASTA описана в платной книге.
- ~~Этап 0 — целостная «модель современного приложения»~~ — **снято 2026-08-20.** Одной опорной ссылки действительно нет, но двух хватает: web.dev «Rendering on the Web» (SSR, статическая генерация, гидратация, клиентский рендеринг) и MDN «Proxy servers and tunneling» (прямой и обратный прокси, CONNECT, X-Forwarded-*).
- **Этап 3 — матрица «что на pre-commit / что на MR / что на релизе» и таксономия blocking vs advisory gates. Подтверждено 2026-08-20: готовой раскладки нет.** Проверены OWASP DevSecOps Guideline (даёт упорядоченный набор проверок: секреты → SAST → SCA → IAST → DAST → IaC → инфраструктура → соответствие, но не привязку к стадиям), GitLab Application security testing и документация GitHub. Ближайшее к таксономии гейтов — required status checks в «About protected branches»: механизм, которым проверка делается блокирующей, но не критерий, какую проверку такой делать. Матрицу в теме придётся построить самостоятельно, опираясь на эти два источника и на CICD-SEC-1 (Insufficient Flow Control Mechanisms).

**Прочее:**

- Этап 0 — сессии (server-side vs stateless tokens): OWASP Session Management Cheat Sheet сознательно не включён здесь — должен появиться в теме про аутентификацию.
- Этап 3 — для GitLab нет аналога исследованию GitHub Security Lab про pwn requests: GitLab Pipeline Security даёт общие принципы, но не разбирает конкретный эксплойт-сценарий так подробно.

## Что требует ручной проверки

Конкретные задачи для автора — не пометки «на будущее», а список действий:

1. ~~SELinux/AppArmor~~ — **закрыто 2026-08-16**, источники добавлены в этап 4.
2. ~~cosign/sigstore~~ — **закрыто 2026-08-16**, docs.sigstore.dev открыт и проверен, добавлен в этап 2.
3. ~~**fstec.ru/tekhnicheskaya-zashchita-informatsii/sertifikatsiya** — общий обзорный раздел ФСТЭК по всем схемам сертификации; сеть блокирует домен fstec.ru из песочницы, нужно зайти вручную и убедиться, что приказы №240 и №76 — это полный релевантный набор, а не только его часть.~~ — **снято 2026-08-20:** относилось к этапу 6, исключённому из гайдбука.
4. ~~**bdu.fstec.ru и reestr.digital.gov.ru** — прямой фетч невозможен из-за ошибки проверки TLS-сертификата на всех доменах семейства .gov.ru в этой среде; содержимое подтверждено только через WebSearch-сниппеты, а не через личное открытие страницы. Это структурный слепой участок именно для российских регуляторных источников — стоит перепроверить с обычной сети перед тем, как опираться на них в тексте.~~ — **снято 2026-08-20:** относилось к этапу 6, исключённому из гайдбука.
5. ~~**ГОСТ Р 56939-2024, полный текст** — docs.cntd.ru зацикливается на SSO-логин через auth.kodeks.ru; полный постатейный текст платный (Стандартинформ/КонсультантПлюс/Кодекс), в реестре сейчас только карточка с реквизитами.~~ — **снято 2026-08-20:** относилось к этапу 6, исключённому из гайдбука.
6. ~~**ГОСТ Р 57580.1-2017, полный текст** — аналогично платный, доступна только карточка со статусом на protect.gost.ru.~~ — **снято 2026-08-20:** относилось к этапу 6, исключённому из гайдбука.
7. ~~**CISA KEV**~~ — **закрыто 2026-08-20:** страница открыта лично curl'ом с браузерным User-Agent (HTTP 200), каталог живой — последние записи датированы 19 августа 2026. 403 отдаётся именно штатному фетчеру. Запись `cisa-kev` в `sources.yaml`.
8. ~~**graphql.org/learn**~~ — **закрыто 2026-08-20:** страница открыта лично curl'ом с браузерным User-Agent (HTTP 200), содержание и издатель (The GraphQL Foundation) сверены, запись `graphql-learn` заведена в `sources.yaml`. 403 отдаётся именно штатному фетчеру и не мешает.
9. ~~**EPSS, версия/дата**~~ — **закрыто 2026-08-20 с поправкой:** номер версии объявлен не на главной странице, а на `first.org/epss/data`, где перечислены все версии модели с датами начала публикации. Прежняя пометка «v4, март 2025» устарела: v4 (v2025.03.14) публиковалась с 17 марта 2025, текущая — **EPSS v5 (v2026.06.15), публикуется с 15 июня 2026**.
10. ~~**OWASP SAMM, точный номер версии**~~ — **закрыто 2026-08-20:** патч-версия **2.0.3** подтверждена независимо — она указана на странице проекта `owasp.org/www-project-samm/`. Сам `owaspsamm.org` действительно пишет только «Version 2.0», поэтому искать надо было на второй странице.
11. ~~**Дубль ASVS 5.0.0**~~ — **закрыто 2026-08-20:** канонический адрес зафиксирован как `owasp.org/www-project-application-security-verification-standard/`, запись `owasp-asvs-5` в `sources.yaml` одна. Страница открыта лично: v5.0.0 выпущена 30 мая 2025 на Global AppSec EU, лицензия CC BY-SA 4.0. Репозиторий на GitHub отдельной записью не заводится.
12. ~~**Статус релиза OWASP Top 10:2025**~~ — **закрыто 2026-08-20 по существу:** страница `owasp.org/Top10/2025/` озаглавлена «Welcome to the OWASP Top 10:2025 Release» и говорит «This is the 2025 version», нигде не помечая себя как release candidate. Даты релиза страница по-прежнему не даёт, поэтому в тексте гайда пишем «издание 2025», а не «финальная версия от такого-то числа». Категории A01–A10 сверены лично и совпадают с планом обучения.
13. ~~**Подзаконные акты для 152-ФЗ и 187-ФЗ** — Приказ ФСТЭК №21 от 18.02.2013, ПП РФ №1119 от 01.11.2012 (уровни защищённости ПДн) и ПП РФ №127 от 08.02.2018 (категорирование КИИ) не в реестре, но нужны для темы «влияние закона на архитектуру» — добавить отдельно при написании темы.~~ — **снято 2026-08-20:** относилось к этапу 6, исключённому из гайдбука.

## Реестр

Каждый источник из таблиц выше при первом реальном использовании в тексте получает свой `id` (см. колонку «Источник» — id совпадает с тем, что указан в скобках у соответствующей строки исследования) и заносится в коллекцию `sources` контентной модели с полями `url`, `license`, `checked` (дата последней личной проверки) и `archived_url` (архивный снимок — обязателен для источников с волатильностью «быстро», см. `PLAYBOOK.md`, часть 9). Тема ссылается на источник по `id`, а не по инлайновому URL — это позволяет обновить один источник и автоматически подтянуть исправление во все темы, которые на него ссылаются.
