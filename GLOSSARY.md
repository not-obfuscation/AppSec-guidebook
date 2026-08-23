<!-- Собрано `tools/gen_glossary.py` из `glossary.yaml`. Не правьте этот файл:
     правки вносятся в `glossary.yaml`, затем `make glossary`. -->

# Глоссарий

Термины, которыми пользуются написанные темы. Одно написание на весь сайт (6.3);
синонимы живут здесь и только здесь. Проверки, следящие за этим, — `G-CANON`,
`G-FIRST`, `G-UNUSED` в `STYLE.md` § 5.

## Протокол и сообщения

### безопасный метод { #safe-method }

*англ. safe method*

Метод, о котором протокол утверждает, что он не меняет состояние на сервере. Свойство описывает намерение, а не гарантию: приложение вольно менять состояние по `GET`, и протокол этому не мешает.

*вводится в [http-basics](content/stage-0/http-basics.md); рядом: [метод](#method), [идемпотентность](#idempotency); источник: RFC 9110 § 9.2.1.*

### идемпотентность { #idempotency }

*англ. idempotency*

Свойство метода, при котором повторение одного и того же запроса даёт то же состояние, что и однократное исполнение. Опора серверных защит: повтор подделанного запроса не добавляет атакующему ничего нового.

*рядом: [безопасный метод](#safe-method), [метод](#method); источник: RFC 9110 § 9.2.2.*

### код ответа { #status-code }

*англ. status code · то же: «код состояния»*

Трёхзначное число в start-line ответа. Клиент обязан понимать класс кода и обращаться с незнакомым кодом как с `x00` своего класса: `471` обрабатывается как `400`.

*вводится в [http-basics](content/stage-0/http-basics.md); рядом: [start-line](#start-line); источник: RFC 9110 § 15.*

### метод { #method }

*англ. method*

Токен в start-line, объявляющий цель запроса; первичный источник семантики запроса. Регистрозависим, а стандартные методы записываются заглавными.

*вводится в [http-basics](content/stage-0/http-basics.md); рядом: [безопасный метод](#safe-method), [start-line](#start-line); источник: RFC 9110 § 9.1.*

### поле заголовка { #header-field }

*англ. header field*

Пара «имя — значение» в сообщении. Имя регистронезависимо; исторические реализации заменяют в имени дефис подчёркиванием, и на этом расхождении строится часть атак на посредников.

*вводится в [http-basics](content/stage-0/http-basics.md); рядом: [start-line](#start-line), [X-Forwarded-For](#x-forwarded-for); источник: RFC 9110 § 17.10.*

### HTTP { #http }

*англ. Hypertext Transfer Protocol*

Протокол обмена сообщениями «запрос — ответ», не помнящий предыдущего запроса. Из-за этого всякое состояние переносится самим сообщением, и отсюда растут cookie, сессии и токены.

*вводится в [http-basics](content/stage-0/http-basics.md); рядом: [start-line](#start-line), [поле заголовка](#header-field), [сессия](#session), [токен](#token); источник: RFC 9110 (STD 97).*

### start-line { #start-line }

Первая строка сообщения. У запроса состоит из метода, цели запроса и версии протокола, у ответа — из версии, кода состояния и поясняющей фразы. Дальше в обоих сообщениях идут поля, пустая строка и тело, если оно есть.

*вводится в [http-basics](content/stage-0/http-basics.md); рядом: [HTTP](#http), [метод](#method), [поле заголовка](#header-field); источник: RFC 9110.*

## Адреса и кодирование

### двойное кодирование { #double-encoding }

*англ. double encoding*

Процентное кодирование, применённое к уже закодированной строке: `%252e` разворачивается в `%2e`, а тот — в точку. Опасно там, где декодирование идёт больше одного раза, а проверка — один.

*вводится в [url-and-encoding](content/stage-0/url-and-encoding.md); рядом: [процентное кодирование](#percent-encoding), [нормализация](#normalization).*

### нормализация { #normalization }

*англ. normalization*

Приведение значения к канонической форме перед сравнением. Порядок обязателен: нормализация выполняется до проверки, и проверяется нормализованное значение, иначе проверка смотрит на одну строку, а система работает с другой.

*вводится в [url-and-encoding](content/stage-0/url-and-encoding.md); рядом: [процентное кодирование](#percent-encoding), [skeleton](#skeleton), [двойное кодирование](#double-encoding).*

### процентное кодирование { #percent-encoding }

*англ. percent-encoding*

Запись байта строкой из символа `%` и двух шестнадцатеричных ASCII-цифр. Ключевое свойство — набор символов, которые надо кодировать, зависит от компонента адреса, поэтому одно и то же значение в разных компонентах кодируется по-разному.

*вводится в [url-and-encoding](content/stage-0/url-and-encoding.md); рядом: [URL](#url), [нормализация](#normalization), [двойное кодирование](#double-encoding); источник: URL Standard § 1.3.*

### confusables { #confusables }

*то же: «омоглиф»*

Таблица Unicode, сводящая символы, которые выглядят похоже: `1/l/I`, `m/rn`, `0/O`, `а/a`. Отдельный класс — символы, невидимые вовсе, вроде U+202A LEFT-TO-RIGHT EMBEDDING.

*вводится в [url-and-encoding](content/stage-0/url-and-encoding.md); рядом: [skeleton](#skeleton); источник: UTS.*

### skeleton { #skeleton }

Механизм UTS #39 для сравнения строк, похожих на вид. Приводит строку к NFD, удаляет символы со свойством `Default_Ignorable_Code_Point`, заменяет каждый символ прототипом из таблицы confusables и снова применяет NFD; две строки визуально похожи, если их skeleton совпадают.

*вводится в [url-and-encoding](content/stage-0/url-and-encoding.md); рядом: [confusables](#confusables), [нормализация](#normalization); источник: UTS.*

### URI { #uri }

*англ. Uniform Resource Identifier*

Идентификатор ресурса в терминах RFC 3986. Разложение на пять компонентов — схема, authority, путь, запрос, фрагмент — принадлежит этой спецификации.

*вводится в [url-and-encoding](content/stage-0/url-and-encoding.md); рядом: [URL](#url); источник: RFC 3986 § 3.*

### URL { #url }

*англ. Uniform Resource Locator*

Адрес ресурса. Раскладывается на компоненты двумя способами: RFC 3986 описывает обобщённый синтаксис URI, URL Standard — структуру, которую строит браузер. Часть расхождений между парсерами берётся отсюда.

*вводится в [url-and-encoding](content/stage-0/url-and-encoding.md); рядом: [URI](#uri), [процентное кодирование](#percent-encoding), [нормализация](#normalization), [origin](#origin); источник: RFC 3986 (STD 66), URL Standard.*

## Источник и его политика

### кросс-доменный { #cross-origin }

*англ. cross-origin*

Признак запроса или ресурса, у которого origin не совпадает с origin документа. Слово говорит о разнице origin, а не о разнице доменов второго уровня: другой порт и другая схема тоже дают кросс-доменность.

*вводится в [cors](content/stage-0/cors.md), [same-origin-policy](content/stage-0/same-origin-policy.md); рядом: [origin](#origin), [политика одного источника](#same-origin-policy), [CORS](#cors).*

### политика одного источника { #same-origin-policy }

*англ. same-origin policy · то же: «SOP»*

Правило браузера, по которому документ читает данные только своего origin. Отправке запроса наружу политика не мешает и о правах отправителя не говорит ничего: доверенный origin, на котором есть XSS, шлёт сообщения от своего имени.

*вводится в [same-origin-policy](content/stage-0/same-origin-policy.md); рядом: [origin](#origin), [CORS](#cors), [CSRF-токен](#csrf-token), [SameSite](#samesite); источник: HTML Standard.*

### предварительный запрос { #preflight }

*англ. preflight request · то же: «preflight-запрос»*

Запрос методом `OPTIONS`, которым браузер спрашивает разрешение до отправки основного. Порождается не всяким кросс-доменным запросом: разрешённые сочетания метода и полей его не требуют.

*вводится в [cors](content/stage-0/cors.md); рядом: [CORS](#cors), [метод](#method), [политика одного источника](#same-origin-policy); источник: Fetch Standard.*

### CORS { #cors }

*англ. Cross-Origin Resource Sharing*

Механизм, которым сервер разрешает браузеру отдать скрипту ответ, полученный из другого origin. Разрешение выдаёт ответ сервера, а исполняет его браузер: без разрешения запрос уходит, а ответ скрипту не достаётся.

*вводится в [cors](content/stage-0/cors.md); рядом: [предварительный запрос](#preflight), [политика одного источника](#same-origin-policy), [origin](#origin), [Vary](#vary); источник: Fetch Standard.*

### opaque origin { #opaque-origin }

Внутреннее значение без восстановимой записи, сериализуется строкой `null`; единственная осмысленная операция над ним — сравнение на равенство. Приходит от документа в песочнице `iframe` и от страницы со схемой `data:`.

*вводится в [same-origin-policy](content/stage-0/same-origin-policy.md); рядом: [origin](#origin), [tuple origin](#tuple-origin), [CORS](#cors); источник: HTML Standard.*

### origin { #origin }

*то же: «источник», «происхождение»*

Единица, между которой браузер проводит границу доверия: акторы с общим origin считаются доверяющими друг другу и имеющими одинаковые полномочия, акторы с разными origin — потенциально враждебными. Спецификация различает два вида, opaque и tuple.

*вводится в [same-origin-policy](content/stage-0/same-origin-policy.md); рядом: [opaque origin](#opaque-origin), [tuple origin](#tuple-origin), [политика одного источника](#same-origin-policy), [CORS](#cors); источник: HTML Standard.*

### tuple origin { #tuple-origin }

Origin из четырёх полей: схема, хост, порт и домен, по умолчанию `null`. Сравнение идёт по полям, а не по строке адреса.

*вводится в [same-origin-policy](content/stage-0/same-origin-policy.md); рядом: [origin](#origin), [opaque origin](#opaque-origin); источник: HTML Standard.*

## Состояние — cookie, сессии, токены

### идентификатор сессии { #session-id }

*англ. session identifier*

Значение, по которому сервер находит запись сессии. Требования к нему три: имя не раскрывает стек, значение имеет достаточную энтропию, и приложение отвергает значение, которого само не выдавало.

*вводится в [sessions-vs-tokens](content/stage-0/sessions-vs-tokens.md); рядом: [сессия](#session), [энтропия](#entropy), [session fixation](#session-fixation), [CSPRNG](#csprng); источник: OWASP Session Management Cheat Sheet.*

### префикс имени cookie { #cookie-prefix }

*англ. cookie prefix · то же: «префикс имени», «__Secure-», «__Host-»*

Требование к атрибутам, закодированное в самом имени: `__Secure-` и `__Host-`. Придумано затем, чтобы сервер мог проверить набор атрибутов по тому, что ему приходит, — по имени, единственному, что возвращает браузер.

*вводится в [cookies](content/stage-0/cookies.md); рядом: [cookie](#cookie), [Set-Cookie](#set-cookie), [Secure](#secure-attribute); источник: draft-ietf-httpbis-rfc6265bis-22.*

### самодостаточный токен { #self-contained-token }

*англ. self-contained token*

Токен, несущий сами утверждения вместе с подписью; сервер о сессии не хранит ничего. Цена — отзыв: до истечения срока он требует списка завершённых токенов, отказа от токенов старше даты или ротации ключа подписи.

*вводится в [sessions-vs-tokens](content/stage-0/sessions-vs-tokens.md); рядом: [токен](#token), [ссылочный токен](#reference-token), [JWT](#jwt); источник: ASVS v5.0-7.4.1.*

### сессия { #session }

*англ. session*

Состояние, связывающее последовательность запросов одного пользователя. Смысл сессии лежит либо в хранилище сервера, либо в самом сообщении, и это различие определяет всё остальное: отзыв, срок и то, что видно атакующему.

*вводится в [sessions-vs-tokens](content/stage-0/sessions-vs-tokens.md); рядом: [идентификатор сессии](#session-id), [токен](#token), [ссылочный токен](#reference-token), [самодостаточный токен](#self-contained-token), [session fixation](#session-fixation).*

### ссылочный токен { #reference-token }

*англ. reference token*

Токен, несущий бессмысленный идентификатор; кто вы, что вам можно и когда сессия истекает — лежит в хранилище сервера. Гасится записью на бэкенде.

*вводится в [sessions-vs-tokens](content/stage-0/sessions-vs-tokens.md); рядом: [токен](#token), [самодостаточный токен](#self-contained-token), [идентификатор сессии](#session-id).*

### токен { #token }

*англ. token*

Значение, которым клиент предъявляет свою сессию. Различают ссылочный и самодостаточный: первый несёт бессмысленный идентификатор, второй — сами утверждения вместе с подписью.

*вводится в [sessions-vs-tokens](content/stage-0/sessions-vs-tokens.md); рядом: [ссылочный токен](#reference-token), [самодостаточный токен](#self-contained-token), [JWT](#jwt), [сессия](#session).*

### base64url { #base64url }

Кодирование двоичных данных печатными символами, пригодными для адреса. Не шифрование и не подпись: значение читается без ключа, и содержимое токена в этой кодировке считается открытым.

*вводится в [sessions-vs-tokens](content/stage-0/sessions-vs-tokens.md); рядом: [JWT](#jwt); источник: RFC 7519.*

### cookie { #cookie }

Пара «имя — значение», которую сервер устанавливает полем `Set-Cookie`, а браузер возвращает в последующих запросах. Область действия cookie задаёт своя модель, не совпадающая с origin: схема и порт в ней не участвуют.

*вводится в [cookies](content/stage-0/cookies.md); рядом: [Set-Cookie](#set-cookie), [префикс имени cookie](#cookie-prefix), [SameSite](#samesite), [HttpOnly](#httponly), [Secure](#secure-attribute), [сессия](#session); источник: draft-ietf-httpbis-rfc6265bis-22.*

### CSRF-токен { #csrf-token }

Значение, которое приложение выдаёт своей странице и требует обратно при изменяющем действии, чтобы отличить свой запрос от подделанного чужим сайтом. Дополняет `SameSite`, а не заменяется им.

*рядом: [SameSite](#samesite), [политика одного источника](#same-origin-policy), [идемпотентность](#idempotency).*

### HttpOnly { #httponly }

Атрибут cookie, закрывающий её от скриптов страницы. Кражу через XSS снижает, но не исключает: остаются каналы, по которым значение уходит без прямого чтения.

*вводится в [cookies](content/stage-0/cookies.md); рядом: [cookie](#cookie), [Secure](#secure-attribute), [политика одного источника](#same-origin-policy); источник: draft-ietf-httpbis-rfc6265bis-22.*

### JWT { #jwt }

*англ. JSON Web Token*

Формат самодостаточного токена: три части, разделённые точками, первые две декодируются из base64url в осмысленный JSON. Опознаётся по этому признаку без ключа и без проверки подписи.

*вводится в [sessions-vs-tokens](content/stage-0/sessions-vs-tokens.md); рядом: [самодостаточный токен](#self-contained-token), [base64url](#base64url), [токен](#token); источник: RFC 7519 § 3.*

### SameSite { #samesite }

Атрибут cookie, ограничивающий её отправку запросами того же сайта. Серверных защит не отменяет: same-site-запросы исполняются в связке с XSS или злоупотреблением редиректами.

*вводится в [cookies](content/stage-0/cookies.md); рядом: [cookie](#cookie), [CSRF-токен](#csrf-token), [политика одного источника](#same-origin-policy); источник: draft-ietf-httpbis-rfc6265bis-22.*

### Secure { #secure-attribute }

Атрибут cookie, запрещающий отправлять её по незащищённому каналу. Целостности не даёт: посредник в канале без TLS может cookie установить, даже если прочитать её не может.

*вводится в [cookies](content/stage-0/cookies.md); рядом: [cookie](#cookie), [HttpOnly](#httponly), [HSTS](#hsts); источник: draft-ietf-httpbis-rfc6265bis-22.*

### session fixation { #session-fixation }

*то же: «фиксация сессии»*

Атака, в которой значение сессии задаёт атакующий, а жертва входит уже под ним. Лечится сменой идентификатора при смене прав: старая запись гасится, новая создаётся.

*рядом: [идентификатор сессии](#session-id), [сессия](#session).*

### Set-Cookie { #set-cookie }

Поле ответа, которым сервер устанавливает cookie вместе с атрибутами. Обратно приходит только `имя=значение`: атрибуты браузер не возвращает, и сервер не может убедиться, с какими атрибутами cookie была установлена.

*вводится в [cookies](content/stage-0/cookies.md); рядом: [cookie](#cookie), [префикс имени cookie](#cookie-prefix); источник: draft-ietf-httpbis-rfc6265bis-22.*

## Поля ответа и политики

### директива { #directive }

*англ. directive*

Единица политики: имя и либо `'none'`, либо одно и более выражений источника через пробел. Одна директива комбинирует разные виды выражений — одноразовые значения и имена хостов вместе.

*вводится в [csp](content/stage-0/csp.md); рядом: [CSP](#csp), [одноразовое значение](#nonce), [отпечаток](#hash-source); источник: CSP Level 3 § 2.3.*

### одноразовое значение { #nonce }

*англ. nonce*

Выражение источника, разрешающее ровно те скрипты документа, у которых совпал атрибут. Одноразовость обязательна: значение, вычисленное один раз при запуске, разрешает и свой скрипт, и внедрённый, и статическую страницу с такой политикой отдавать нельзя.

*вводится в [csp](content/stage-0/csp.md); рядом: [CSP](#csp), [директива](#directive), [отпечаток](#hash-source), [CSPRNG](#csprng); источник: CSP Level 3 § 2.3.1.*

### отпечаток { #hash-source }

*англ. hash-source*

Выражение источника, разрешающее скрипт по хешу его содержимого: `sha256`, `sha384` или `sha512`. Привязано к содержимому, поэтому правка скрипта требует правки политики.

*вводится в [csp](content/stage-0/csp.md); рядом: [CSP](#csp), [одноразовое значение](#nonce), [хеш-функция](#hash-function); источник: CSP Level 3 § 2.3.1.*

### bootstrap MITM { #bootstrap-mitm }

Окно, которое HSTS не закрывает: первое обращение к незнакомому узлу по адресу со схемой `http` идёт по незащищённому каналу, и политики у браузера ещё нет.

*вводится в [security-headers](content/stage-0/security-headers.md); рядом: [HSTS](#hsts), [MITM](#mitm), [TLS](#tls); источник: RFC 6797 § 14.6.*

### CSP { #csp }

*англ. Content Security Policy*

Политика в поле ответа, перечисляющая, откуда странице разрешено брать ресурсы и что разрешено исполнять. Состоит из директив; ресурс разрешён, если подходит хотя бы под одно выражение источника своей директивы.

*вводится в [csp](content/stage-0/csp.md); рядом: [директива](#directive), [одноразовое значение](#nonce), [отпечаток](#hash-source), [frame-ancestors](#frame-ancestors), [security-заголовки](#security-headers); источник: CSP Level 3.*

### frame-ancestors { #frame-ancestors }

Директива CSP, задающая, кому разрешено встраивать страницу в кадр. Вытеснила отдельное поле `X-Frame-Options` и покрывает его случай целиком.

*вводится в [csp](content/stage-0/csp.md), [security-headers](content/stage-0/security-headers.md); рядом: [CSP](#csp), [директива](#directive), [security-заголовки](#security-headers); источник: CSP Level 3.*

### HSTS { #hsts }

*англ. HTTP Strict Transport Security*

Политика, которой сервер требует обращаться к себе только по защищённому каналу. Единственное поле группы, у которого есть своя спецификация и своя модель угроз.

*вводится в [security-headers](content/stage-0/security-headers.md); рядом: [security-заголовки](#security-headers), [bootstrap MITM](#bootstrap-mitm), [TLS](#tls), [Secure](#secure-attribute); источник: RFC 6797.*

### Referrer-Policy { #referrer-policy }

Поле ответа, управляющее тем, сколько сведений об адресе страницы уйдёт в поле `Referer` следующего запроса. Требуется политика, не пускающая путь и строку запроса третьим сторонам.

*вводится в [security-headers](content/stage-0/security-headers.md); рядом: [security-заголовки](#security-headers), [URL](#url); источник: ASVS v5.0-3.4.5.*

### security-заголовки { #security-headers }

*англ. security headers*

Группа полей ответа, каждое из которых включает одно небольшое ограничение. Читается с обратным ожиданием: группа сокращается — часть полей вытеснена директивами CSP, часть признана вредной, часть мертва.

*вводится в [security-headers](content/stage-0/security-headers.md); рядом: [CSP](#csp), [HSTS](#hsts), [frame-ancestors](#frame-ancestors), [Referrer-Policy](#referrer-policy); источник: OWASP Secure Headers Cheat Sheet.*

### Vary { #vary }

Поле ответа, называющее поля запроса, от которых ответ зависит. В связке с CORS обязательно: без него кеш отдаёт разрешение, выданное одному origin, другому.

*вводится в [cors](content/stage-0/cors.md); рядом: [CORS](#cors), [кеш](#cache); источник: RFC 9110.*

## Транспорт и посредники

### кеш { #cache }

*англ. cache*

Узел, отдающий сохранённый ответ вместо обращения к серверу. Опасен ровно там, где ответ зависит от того, чего кеш не учитывает, — отсюда обязательность `Vary`.

*вводится в [app-architecture](content/stage-0/app-architecture.md); рядом: [Vary](#vary), [сеть доставки](#cdn), [обратный прокси](#reverse-proxy); источник: RFC 9111 (STD 98).*

### обратный прокси { #reverse-proxy }

*англ. reverse proxy*

Посредник со стороны сервера: скрывает серверы и берёт на себя балансировку, кеширование и завершение TLS. Разбирает и пересобирает сообщение, поэтому список точек входа, собранный на нём, неполон.

*вводится в [app-architecture](content/stage-0/app-architecture.md); рядом: [прямой прокси](#forward-proxy), [сеть доставки](#cdn), [X-Forwarded-For](#x-forwarded-for), [эндпоинт](#endpoint); источник: MDN.*

### перехватывающий прокси { #intercepting-proxy }

*англ. intercepting proxy*

Инструмент, который встаёт между клиентом и сервером и предъявляет клиенту свой сертификат. Работает только там, где его корень добавлен в доверенные, и на этом же держится разница между инструментом и атакой.

*вводится в [tls-and-proxy](content/stage-0/tls-and-proxy.md); рядом: [MITM](#mitm), [TLS](#tls), [обратный прокси](#reverse-proxy).*

### прямой прокси { #forward-proxy }

*англ. forward proxy*

Посредник со стороны клиента: обслуживает клиента или группу клиентов и может скрывать их адреса.

*вводится в [app-architecture](content/stage-0/app-architecture.md); рядом: [обратный прокси](#reverse-proxy), [X-Forwarded-For](#x-forwarded-for); источник: MDN.*

### самоподписанный сертификат { #self-signed }

*англ. self-signed certificate*

Сертификат, подписанный своим же ключом. На стенде законен, но требует явно настроенного якоря; отключение проверки вместо этого остаётся в коде после отладки и снимает аутентификацию узла целиком.

*вводится в [tls-and-proxy](content/stage-0/tls-and-proxy.md); рядом: [якорь доверия](#trust-anchor), [цепочка сертификатов](#certificate-chain), [TLS](#tls); источник: ASVS v5.0-12.3.4.*

### сеть доставки { #cdn }

*англ. content delivery network · сокр. CDN*

Слой узлов, отдающих ответы близко к клиенту. Ещё одно место, где сообщение пересобирается, а поля ответа дописываются или переписываются.

*вводится в [app-architecture](content/stage-0/app-architecture.md); рядом: [обратный прокси](#reverse-proxy), [кеш](#cache), [security-заголовки](#security-headers).*

### цепочка сертификатов { #certificate-chain }

*англ. certificate chain*

Последовательность сертификатов от предъявленного до якоря доверия. Для каждого звена проверяется четыре вещи: подпись, срок, отзыв и соответствие имени.

*вводится в [tls-and-proxy](content/stage-0/tls-and-proxy.md); рядом: [якорь доверия](#trust-anchor), [TLS](#tls), [самоподписанный сертификат](#self-signed); источник: RFC 5280 § 6.1.3.*

### якорь доверия { #trust-anchor }

*англ. trust anchor*

Вход алгоритма проверки пути: сертификат, которому доверяют без проверки. Цель алгоритма — подтвердить связь между именем субъекта и его открытым ключом, опираясь на открытый ключ якоря.

*вводится в [tls-and-proxy](content/stage-0/tls-and-proxy.md); рядом: [цепочка сертификатов](#certificate-chain), [TLS](#tls), [самоподписанный сертификат](#self-signed); источник: RFC 5280 § 6.1.*

### MITM { #mitm }

*англ. man in the middle*

Посредник в канале, который читает и меняет сообщения. В работе это не только атака: перехватывающий прокси инструментального набора устроен так же и требует того же доверенного корня.

*вводится в [tls-and-proxy](content/stage-0/tls-and-proxy.md); рядом: [TLS](#tls), [перехватывающий прокси](#intercepting-proxy), [bootstrap MITM](#bootstrap-mitm).*

### SPA { #spa }

*англ. single-page application*

Приложение, у которого разметку собирает клиент. Для разбора важно не быстродействие, а то, что уезжает на клиент: логика вместе с адресами эндпоинтов, именами полей и признаками ролей.

*вводится в [app-architecture](content/stage-0/app-architecture.md); рядом: [эндпоинт](#endpoint), [REST](#rest), [GraphQL](#graphql).*

### TLS { #tls }

*англ. Transport Layer Security*

Протокол защиты канала: подтверждает, с кем установлено соединение, и закрывает содержимое от посредника. Аутентификацию узла даёт проверка сертификата, и без неё остальное не имеет силы.

*вводится в [tls-and-proxy](content/stage-0/tls-and-proxy.md); рядом: [цепочка сертификатов](#certificate-chain), [якорь доверия](#trust-anchor), [MITM](#mitm), [HSTS](#hsts); источник: RFC 9846.*

### X-Forwarded-For { #x-forwarded-for }

Поле, в которое посредники пишут адреса клиента и предыдущих посредников. Наличие поля нормально: его ставит свой прокси. Дефект — это решение о доступе, ограничение частоты или сборка ссылок по нему.

*вводится в [app-architecture](content/stage-0/app-architecture.md); рядом: [обратный прокси](#reverse-proxy), [прямой прокси](#forward-proxy), [поле заголовка](#header-field), [ограничение частоты](#rate-limiting); источник: RFC 7239.*

## API — REST и GraphQL

### авторизация { #authorization }

*англ. authorization*

Решение о том, что этому обратившемуся можно. Отделено от аутентификации, которая отвечает на другой вопрос — кто обратился; в GraphQL выполняется бизнес-логикой на уровне поля.

*вводится в [rest-and-graphql](content/stage-0/rest-and-graphql.md); рядом: [аутентификация](#authentication), [резолвер](#resolver), [GraphQL](#graphql).*

### аутентификация { #authentication }

*англ. authentication*

Установление того, кто обратился. GraphQL ставится после всего промежуточного слоя аутентификации, и после неё сервер не принимает решений об авторизации до начала исполнения.

*рядом: [авторизация](#authorization), [сессия](#session), [функция хеширования паролей](#password-hash).*

### интроспекция { #introspection }

*англ. introspection*

Возможность запросить у сервера GraphQL описание его собственной схемы. Включённая интроспекция сама по себе находкой не служит: её выключение — это security through obscurity, и одного его недостаточно.

*вводится в [rest-and-graphql](content/stage-0/rest-and-graphql.md); рядом: [GraphQL](#graphql), [резолвер](#resolver).*

### ограничение частоты { #rate-limiting }

*англ. rate limiting*

Ограничение числа запросов за интервал. Считать запросы достаточно не всегда: сервер заранее не знает, насколько дорого обойдётся конкретный набор полей, поэтому ограничения ставят в слое бизнес-логики.

*вводится в [rest-and-graphql](content/stage-0/rest-and-graphql.md), [app-architecture](content/stage-0/app-architecture.md); рядом: [псевдоним](#alias), [GraphQL](#graphql), [X-Forwarded-For](#x-forwarded-for).*

### псевдоним { #alias }

*англ. alias*

Имя, под которым результат поля возвращается в ответе GraphQL. Один запрос с сотней псевдонимов одного поля остаётся одним запросом `POST` и проходит любой ограничитель, считающий запросы.

*вводится в [rest-and-graphql](content/stage-0/rest-and-graphql.md); рядом: [GraphQL](#graphql), [ограничение частоты](#rate-limiting), [резолвер](#resolver).*

### резолвер { #resolver }

*англ. resolver*

Функция, исполняющая одно поле схемы GraphQL. Уровень, на котором стоит проверка доступа, определяет её ценность: проверка в резолвере корневого поля не защищает ни одно вложенное.

*вводится в [rest-and-graphql](content/stage-0/rest-and-graphql.md); рядом: [GraphQL](#graphql), [эндпоинт](#endpoint), [авторизация](#authorization).*

### эндпоинт { #endpoint }

*англ. endpoint*

Адрес, по которому приложение принимает запрос. В REST это пара «метод и путь», видимая в маршрутах и в описании OpenAPI; в GraphQL адрес один, а точками входа служат поля схемы.

*вводится в [rest-and-graphql](content/stage-0/rest-and-graphql.md); рядом: [REST](#rest), [GraphQL](#graphql), [резолвер](#resolver), [OpenAPI](#openapi).*

### GraphQL { #graphql }

Язык запросов к схеме, у которого адрес один, а точками входа служат поля схемы: их сотни, и каждое исполняется своим резолвером. Правило на прокси, разрешающее один этот адрес, разрешает всё, что можно выразить схемой.

*вводится в [rest-and-graphql](content/stage-0/rest-and-graphql.md); рядом: [REST](#rest), [резолвер](#resolver), [интроспекция](#introspection), [псевдоним](#alias), [эндпоинт](#endpoint).*

### OpenAPI { #openapi }

Формат описания REST API. Задаёт, среди прочего, где искать параметр операции: `path`, `query`, `querystring`, `header`, `cookie`.

*вводится в [rest-and-graphql](content/stage-0/rest-and-graphql.md); рядом: [REST](#rest), [эндпоинт](#endpoint); источник: OpenAPI v3.2.0.*

### REST { #rest }

Стиль устройства API, в котором точка входа — пара «метод и путь». Точки входа перечислимы: они видны в маршрутах и в описании OpenAPI.

*вводится в [rest-and-graphql](content/stage-0/rest-and-graphql.md); рядом: [GraphQL](#graphql), [эндпоинт](#endpoint), [OpenAPI](#openapi); источник: OWASP REST Security Cheat Sheet.*

## Хеши и хранение паролей

### радужная таблица { #rainbow-table }

*англ. rainbow table*

Заранее посчитанная таблица соответствий «хеш — пароль». Перестаёт подходить при уникальной соли, и только при уникальной: общая соль на всю базу оставляет одну таблицу кандидатов пригодной ко всем записям.

*вводится в [password-storage](content/stage-1/password-storage.md); рядом: [соль](#salt), [функция хеширования паролей](#password-hash).*

### соль { #salt }

*англ. salt*

Уникальное для каждой записи значение, добавляемое к паролю перед хешированием. Секретом не считается. Даёт три следствия: хеши вскрываются по одному, заранее посчитанные таблицы не подходят, и по дампу не видно, что два пользователя выбрали один пароль. Одну догадку не удорожает.

*вводится в [password-storage](content/stage-1/password-storage.md); рядом: [фактор стоимости](#cost-factor), [радужная таблица](#rainbow-table), [функция хеширования паролей](#password-hash); источник: OWASP Password Storage Cheat Sheet.*

### фактор стоимости { #cost-factor }

*англ. cost factor*

Настраиваемая цена одного вычисления хеша. Без него перебор идёт на полной скорости функции; вместе с уникальной солью он и определяет, во что атакующему обойдётся одна догадка.

*вводится в [password-storage](content/stage-1/password-storage.md); рядом: [соль](#salt), [функция хеширования паролей](#password-hash), [Argon2id](#argon2id), [scrypt](#scrypt); источник: NIST SP 800-63B-4 § 3.1.1.2.*

### функция хеширования паролей { #password-hash }

*англ. password hashing function · то же: «функция с настраиваемой ценой»*

Функция с настраиваемой ценой вычисления и уникальной солью на запись: argon2id, scrypt, bcrypt или PBKDF2. Отличать «хеширует» от «хеширует так, что перебор дорог» — навык ревьюера.

*вводится в [password-storage](content/stage-1/password-storage.md); рядом: [соль](#salt), [фактор стоимости](#cost-factor), [Argon2id](#argon2id), [scrypt](#scrypt), [bcrypt](#bcrypt), [PBKDF2](#pbkdf2), [хеш-функция](#hash-function); источник: OWASP Password Storage Cheat Sheet.*

### хеш-функция { #hash-function }

*англ. hash function*

Функция, сводящая вход произвольной длины к значению фиксированной. Для хранения паролей быстрая функция не годится: скорость — её достоинство и ровно то, что помогает атакующему.

*вводится в [password-storage](content/stage-1/password-storage.md); рядом: [функция хеширования паролей](#password-hash), [соль](#salt), [фактор стоимости](#cost-factor), [отпечаток](#hash-source).*

### энтропия { #entropy }

*англ. entropy*

Мера непредсказуемости значения. Различает два случая: идентификатор сессии порождает сервер, и от него энтропию требуют, а пароль выбирает человек, и энтропия у него низкая и внешне непроверяемая.

*вводится в [password-storage](content/stage-1/password-storage.md), [sessions-vs-tokens](content/stage-0/sessions-vs-tokens.md); рядом: [CSPRNG](#csprng), [идентификатор сессии](#session-id), [функция хеширования паролей](#password-hash); источник: ASVS v5.0-6.5.2.*

### Argon2id { #argon2id }

Функция хеширования паролей с настраиваемыми временем, памятью и параллелизмом. Первая рекомендация Cheat Sheet для новых систем.

*вводится в [password-storage](content/stage-1/password-storage.md); рядом: [функция хеширования паролей](#password-hash), [фактор стоимости](#cost-factor), [scrypt](#scrypt), [bcrypt](#bcrypt); источник: RFC 9106.*

### bcrypt { #bcrypt }

Функция хеширования паролей с фактором стоимости в самом значении. Отдельная особенность — ограничение длины входа, из-за которого длинный пароль усекается.

*вводится в [password-storage](content/stage-1/password-storage.md); рядом: [функция хеширования паролей](#password-hash), [фактор стоимости](#cost-factor).*

### CSPRNG { #csprng }

*англ. cryptographically secure pseudorandom number generator*

Генератор случайных значений, пригодный для секретов. Требуется там, где значение обязано быть непредсказуемым: идентификатор сессии, соль, одноразовое значение политики.

*вводится в [sessions-vs-tokens](content/stage-0/sessions-vs-tokens.md), [password-storage](content/stage-1/password-storage.md); рядом: [энтропия](#entropy), [идентификатор сессии](#session-id), [соль](#salt), [одноразовое значение](#nonce).*

### PBKDF2 { #pbkdf2 }

Функция вывода ключа из пароля, цена которой задаётся числом итераций. Годится там, где требуется алгоритм из утверждённого списка; по цене догадки уступает argon2id и scrypt.

*вводится в [password-storage](content/stage-1/password-storage.md); рядом: [функция хеширования паролей](#password-hash), [фактор стоимости](#cost-factor), [Argon2id](#argon2id); источник: NIST SP 800-63B-4.*

### scrypt { #scrypt }

Функция хеширования паролей, цена которой задаётся параметрами `N`, `r` и `p`. Вызов без явных параметров опасен умолчаниями: они бывают на порядки ниже нужного.

*вводится в [password-storage](content/stage-1/password-storage.md); рядом: [функция хеширования паролей](#password-hash), [фактор стоимости](#cost-factor), [Argon2id](#argon2id).*

## Ремесло ревью

### граница доверия { #trust-boundary }

*англ. trust boundary*

Линия, за которой данные перестают быть под контролем приложения. Сообщение приходит из-за границы доверия целиком: атакующий выбирает метод, цель запроса, каждое имя и значение поля, тело.

*вводится в [http-basics](content/stage-0/http-basics.md), [password-storage](content/stage-1/password-storage.md); рядом: [sink](#sink), [модель угроз](#threat-model).*

### дамп { #dump }

*англ. dump*

Выгрузка содержимого базы. Появляется не только при взломе базы: резервные копии, реплики для чтения, снимки для тестовых стендов и выгрузки для аналитики дают тот же результат.

*вводится в [password-storage](content/stage-1/password-storage.md); рядом: [модель угроз](#threat-model), [функция хеширования паролей](#password-hash).*

### модель угроз { #threat-model }

*англ. threat model*

Ответ на вопрос, от кого и от чего защищаемся, до разговора о средствах. У темы про хранение паролей она начинается там, где дамп уже у атакующего, и вопрос стоит один: во что ему обойдётся восстановление.

*вводится в [password-storage](content/stage-1/password-storage.md), [security-headers](content/stage-0/security-headers.md); рядом: [граница доверия](#trust-boundary), [sink](#sink).*

### стенд { #stand }

Своё приложение, поднятое для опытов. Все задачи гайда ставятся на стенде автора, а не на чужой системе: полезная работа с уязвимостью начинается там, где на неё есть право.

*рядом: [модель угроз](#threat-model).*

### тест на регресс { #regression-test }

*англ. regression test · то же: «регресс»*

Тест, который остаётся в репозитории после починки и ловит откат фикса. Важнее ретеста: ретест подтверждает починку один раз, тест на регресс переживает правку.

*вводится в [password-storage](content/stage-1/password-storage.md); рядом: [эксплойт](#exploit).*

### эксплойт { #exploit }

*англ. exploit*

Работающее воспроизведение дефекта. В проверке фикса служит ретестом: прогоняется тот же эксплойт, и признаком починки считается заранее названное изменение вывода.

*вводится в [password-storage](content/stage-1/password-storage.md); рядом: [тест на регресс](#regression-test), [стенд](#stand).*

### sink { #sink }

Место, где данные достигают действия с последствиями: запрос к базе, вывод в разметку, строка в таблице учётных записей. Второй конец пары «источник — sink», вокруг которой строится разбор дефекта.

*вводится в [password-storage](content/stage-1/password-storage.md); рядом: [граница доверия](#trust-boundary), [модель угроз](#threat-model).*
