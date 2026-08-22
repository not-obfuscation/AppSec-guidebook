# Объяснение через контраст и через историю проблемы: мета-обзор первоисточников

> **Статус:** подысследование к области «Ремесло технической документации» (02). Веб-поиск в сессии был исчерпан, часть источников добыта через прямые WebFetch и API (OpenAlex, Crossref, PubMed, archive.org). Три источника не верифицированы — см. раздел в конце.

**Методологическая оговорка.** Все источники ниже открывались напрямую (PDF/HTML/API OpenAlex, Crossref, PubMed, archive.org), не по пересказам на Medium. Там, где полный текст был недоступен (paywall Taylor & Francis, Springer, APA), я брал верифицируемый абстракт из издательской записи или PMID и явно это помечаю. Три источника достать не удалось — они отмечены как **[НЕ ВЕРИФИЦИРОВАНО]**.

---

## A. ОБЪЯСНЕНИЕ ЧЕРЕЗ КОНТРАСТ

### 1. Schwartz & Bransford (1998), «A Time for Telling»

**Точная ссылка:** Schwartz, D. L., & Bransford, J. D. (1998). A Time for Telling. *Cognition and Instruction*, 16(4), 475–522. DOI: [10.1207/s1532690xci1604_4](https://doi.org/10.1207/s1532690xci1604_4). ERIC: [EJ582423](https://eric.ed.gov/?id=EJ582423). Цитирований по OpenAlex: **1022**.
*Авторитетность: Cognition and Instruction — топовый рецензируемый журнал по когнитивным наукам об обучении; Бренсфорд — редактор доклада NRC «How People Learn».*

**Абстракт (verbatim, из издательской записи через OpenAlex):**
> «Suggestions for improving text understanding often prescribe activating prior knowledge, a prescription that may be problematic if students do not have the relevant prior knowledge to begin with. […] We propose that analyzing contrasting cases can help learners generate the differentiated knowledge structures that enable them to understand a text deeply. Noticing the distinctions between contrasting cases creates a "time for telling"; learners are prepared to be told the significance of the distinctions they have discovered.»

**Дизайн (из абстракта, verbatim):**
> «In 3 classroom studies, college students analyzed contrasting cases that consisted of simplified experimental designs and data from classic psychology experiments. They then received a lecture or text on the psychological phenomena highlighted in the experiments. Approximately 1 week later, the students predicted outcomes for a hypothetical experiment…»

**Условия сравнения (verbatim):** генерация различий между контрастными кейсами + текст/лекция дала более точные предсказания, чем контрольные условия:
> «(a) reading about the distinctions between the cases and hearing a lecture, (b) summarizing a relevant text and hearing a lecture, and (c) analyzing the contrasting cases twice without receiving a lecture.»

**Механизм — ключевая цитата про «ботаника»:**
> «We argue that analyzing the contrasting cases increased students' abilities to discern specific features that differentiated classes of psychological phenomena, much as a botanist can distinguish subspecies of a given flower. This differentiated knowledge prepared the students to understand deeply an explanation of the relevant psychological principles when it was presented to them.»

**Вывод для «лекций» (verbatim):**
> «…there is a place for lectures and readings in the classroom if students have sufficiently differentiated domain knowledge to use the expository materials in a generative manner.»

**Почему «сначала рассказать» проваливается.** Не потому, что лекции плохи, а потому, что у новичка нет *дифференцированной* структуры знания: слова лектора не за что зацепить. Различия существуют объективно, но перцептивно не выделены (это прямая линия к Gibson & Gibson 1955 — обучение как **дифференциация**, а не аккумуляция).

**Статус:** **[ПОДТВЕРЖДЕНО ИССЛЕДОВАНИЯМИ]** — 3 классных эксперимента + тысяча цитирований + независимые репликации (см. ниже). Оговорка: эффект проявляется на *трансфере* и предсказании новых случаев, а **не** на фактологических тестах — в оригинале все условия по фактам равны.

**Примечание о доступе:** PDF на `aaalab.stanford.edu` (лаборатория Шварца) сейчас недоступен — домен не резолвится. Абстракт верифицирован через OpenAlex + ERIC.

---

### 2. Schwartz & Martin (2004), «Inventing to Prepare for Future Learning»

**Точная ссылка:** Schwartz, D. L., & Martin, T. (2004). Inventing to Prepare for Future Learning: The Hidden Efficiency of Encouraging Original Student Production in Statistics Instruction. *Cognition and Instruction*, 22(2), 129–184. DOI: [10.1207/s1532690xci2202_1](https://doi.org/10.1207/s1532690xci2202_1). Цитирований: **757**.

**Абстракт (verbatim, ключевые места):**
> «Two studies on teaching descriptive statistics to 9th-grade students examined whether invention activities may prepare students to learn. […] an embedded assessment experiment crossed the factors of instructional method by type of transfer test, with 1 test including resources for learning and 1 not. A "tell-and-practice" instructional condition led to the same transfer results as an invention condition when there was no learning resource, but the invention condition did better than the tell-and-practice condition when there was a learning resource.»

**Это ключевая методологическая находка (двойной трансфер):** если мерить обычным «изолированным» тестом, invention-условие выглядит *не лучше*. Разница появляется **только** когда тест содержит ресурс для обучения. То есть PFL — это не «лучше учат», а «лучше готовы учиться дальше». Study 2 — репликация силами обычных учителей.

**Задача:** контрастные кейсы — данные бейсбольных питчинг-машин, студенты изобретают «индекс надёжности» (фактически — mean deviation / стандартизацию).

**Развитие линии:** Schwartz, D. L., Chase, C. C., Oppezzo, M. A., & Chin, D. B. (2011). Practicing versus inventing with contrasting cases: The effects of telling first on learning and transfer. *Journal of Educational Psychology*, 103(4), 759–775. DOI: [10.1037/a0025140](https://doi.org/10.1037/a0025140). Цитирований: 458.
Абстракт (verbatim):
> «Being told procedures and concepts before problem solving can inadvertently undermine the learning of deep structures in physics. […] Both groups exhibited equal proficiency at using the formulas on word problems. However, ICC students better learned the ratio structure of the physical phenomena and transferred more frequently to semantically unrelated topics that also have a ratio structure (e.g., spring constant).» N = 128 (Эксп. 1), N = 120 (Эксп. 2).

**Статус:** **[ПОДТВЕРЖДЕНО ИССЛЕДОВАНИЯМИ]**, с важным уточнением ниже.

---

### 2b. Каков реальный статус доказательств для «problem solving before instruction» (PS-I / PFL)?

Это важно, потому что тема идеологически спорная.

**За:** Sinha, T., & Kapur, M. (2021). When Problem Solving Followed by Instruction Works: Evidence for Productive Failure. *Review of Educational Research*, 91(5). DOI: [10.3102/00346543211019105](https://doi.org/10.3102/00346543211019105). OA-PDF: journals.sagepub.com. Мета-анализ **53 исследований, 166 сравнений**.
> «Our results showed a significant, moderate effect in favor of PS-I (Hedge's g 0.36 [95% confidence interval 0.20; 0.51]). The effects were even stronger (Hedge's g ranging between 0.37 and 0.58) when PS-I was implemented with high fidelity to the principles of Productive Failure. […] Contrasting trends were, however, observed for younger age learners (second to fifth graders) and for the learning of domain-general skills, for which effect sizes favored I-PS.»

**Против (классический контраргумент):** Kirschner, P. A., Sweller, J., & Clark, R. E. (2006). Why Minimal Guidance During Instruction Does Not Work: An Analysis of the Failure of Constructivist, Discovery, Problem-Based, Experiential, and Inquiry-Based Teaching. *Educational Psychologist*, 41(2), 75–86. DOI: [10.1207/s15326985ep4102_1](https://doi.org/10.1207/s15326985ep4102_1). Цитирований: **6799**.
> «Evidence for the superiority of guided instruction is explained in the context of our knowledge of human cognitive architecture, expert–novice differences, and cognitive load. […] minimally guided instruction is less effective and less efficient than instructional approaches that place a strong emphasis on guidance of the student learning process. The advantage of guidance begins to recede only when learners have sufficiently high prior knowledge to provide "internal" guidance.»

**Теоретический синтез:** Loibl, K., Roll, I., & Rummel, N. (2017). Towards a Theory of When and How Problem Solving Followed by Instruction Supports Learning. *Educational Psychology Review*, 29, 693–715. DOI: [10.1007/s10648-016-9379-x](https://doi.org/10.1007/s10648-016-9379-x). Цитирований: 271.

**Статус:** **[ПОДТВЕРЖДЕНО, но с ограничениями]**. g ≈ 0.36 — умеренный эффект; работает для концептуального понимания и трансфера, **не** работает для младших школьников и общих навыков; критично зависит от того, что подготовительная фаза именно контрастная/сравнительная, а не просто «поиграйте сами».

⚠️ **Прямая проекция на техническое письмо ("тексты не эксперименты").** Всё вышеперечисленное — про *активность* учащегося. Аналог в документации («сначала покажи два конфузящих примера, потом объясни разницу») — это **[СПОРНО / экстраполяция]**, а не подтверждённый результат: читатель документации не обязательно проделывает работу по различению.

---

### 3. Теория вариации Фéренса Мартона

**Первоисточники:**
- Marton, F., & Booth, S. (1997). *Learning and Awareness*. Mahwah, NJ: Lawrence Erlbaum.
- Marton, F. (2015). *Necessary Conditions of Learning*. New York: Routledge. ISBN 9780415739146.
- Marton, F., & Tsui, A. B. M. (2004). *Classroom Discourse and the Space of Learning*. LEA.
- Marton, F., & Pang, M. F. (2006). On some necessary conditions of learning. *Journal of the Learning Sciences*, 15(2), 193–220.

**Верифицированный вторичный первоисточник (открытый PDF, скачан и прочитан):** Kullberg, A., Runesson Kempe, U., & Marton, F. (2017). What is made possible to learn when using the variation theory of learning in teaching mathematics? *ZDM Mathematics Education*, 49(4), 559–569. DOI: [10.1007/s11858-017-0858-4](https://doi.org/10.1007/s11858-017-0858-4). PDF: `https://variationtheory.com/wp-content/uploads/2018/07/What-is-made-possible-to-learn-when-using-the-variation-theory-Kullberg-Kempe-Marton-2017.pdf`
*Авторитетность: Мартон — соавтор статьи; ZDM — ведущий журнал по дидактике математики.*

#### Базовые понятия (verbatim из Kullberg, Runesson Kempe & Marton 2017, p. 560)

**Object of learning** — «provides answers to the question 'What is to be learned?' in three ways: it defines (1) the content, (2) the educational objective, and (3) what needs to be learned (critical aspects).» Различают *intended* / *enacted* / *lived* object of learning.

**Critical aspects** — те аспекты, которые обучающийся ещё не различает, но обязан различить, чтобы понять объект. Это не «важные темы», а конкретные точки, где отсутствует различение.

**Discernment как необходимое условие:**
> «…the very core idea of variation theory is that discernment is a necessary condition of learning: what aspects we attend to or discern are of decisive significance for how we understand or experience the object of learning. Discernment cannot happen without the learner having experienced variation, however.»

**Обучение = дифференциация, а не аккумуляция:**
> «Learning, from a variation theory point of view, implies differentiation rather than accumulation (cf., Gibson and Gibson 1955).»
(Заметьте — это та же ссылка на Гибсонов, что и у Шварца/Бренсфорда. Две традиции сходятся.)

**Тезис «различие раньше сходства» — цитата Marton & Pang (2013), приведённая verbatim в статье (p. 560):**
> «You cannot possibly understand what Chinese is simply by listening to different people speaking Chinese if you have never heard another language, and you cannot possibly understand what virtue is by inspecting different examples of the same degree of virtue. Nor can you understand what a linear equation is by looking only at linear equations.» (p. 25)

#### Четыре паттерна вариации — точные определения

| Паттерн | Что варьирует / что инвариантно | Что делает |
|---|---|---|
| **CONTRAST** (контраст) | варьирует сам критический аспект, фон удерживается | даёт значение: «чтобы пережить нечто *как* нечто, нужно сравнить это с другим» |
| **GENERALIZATION** (обобщение) | целевой аспект **инвариантен**, всё остальное варьирует | отделяет определяющий аспект от конкретного экземпляра |
| **SEPARATION** (разделение) | один аспект варьирует, остальные инвариантны | выделяет отдельный аспект из целого (изоляция переменной) |
| **FUSION** (слияние) | несколько критических аспектов варьируют **одновременно** | восстанавливает целостность: понимание объекта как целого |

**Verbatim про contrast (p. 560):**
> «…to understand the concept of a linear function y = mx + b one needs to know how it differs from non-linear functions. Otherwise it is merely a synonym for 'function'. Similarly, a triangle must be compared to a circle or any other shape to have a meaning of its own. In variation theory, comparing two concepts involves a particular pattern of variation called 'contrast'. One could argue that this is similar to counter examples… In lesson designs premised on variation theory, contrast (which could be a counter example) is used with a specific aim: to help learners acquire novel meanings by opening up appropriate dimensions of variation.»

**Verbatim про generalization (p. 560):**
> «Contrast has to be followed by generalization. To generalize the idea of a function, for instance, one must experience sameness, certain defining aspects, of different functions. […] As far as this pattern of variation is concerned, the targeted aspect is kept invariant while other aspects vary.»

**Verbatim про fusion (p. 560):**
> «When dimensions of variation corresponding to several critical aspects are opened up simultaneously, fusion can take place.»

**Порядок — прототип последовательности (Marton 2015, p. 263), цитируется verbatim:**
> «…starting with the undivided object of learning, usually a problem to solve aiming at getting the learners acquainted with the situation or what is to be mastered, followed by contrast, generalization and finally fusion.»

То есть: **проблема → контраст → обобщение → (разделение) → слияние.** Contrast предшествует generalization; separation предшествует fusion.

#### Прямая проекция на структуру объяснительного текста
1. **Contrast** = «X — это не Y», раздел "Commonly confused with".
2. **Generalization** = 3–4 непохожих примера, где X всё ещё X (разные языки, разные масштабы).
3. **Separation** = минимальные пары: меняем ровно один параметр, всё остальное фиксируем (идеально ложится на diff, на «before/after»-фрагменты кода).
4. **Fusion** = финальный реалистичный кейс, где все аспекты играют одновременно.

#### Learning Study / Lesson Study (Швеция, Гонконг)
- Pang, M. F., & Lo, M. L. (2011). Learning study: helping teachers to use theory, develop professionally, and produce new knowledge to be shared. *Instructional Science*, 40(3), 589–606. DOI: [10.1007/s11251-011-9191-4](https://doi.org/10.1007/s11251-011-9191-4). OA-PDF на Springer.
  > «The learning study approach is essentially a kind of lesson study with an explicit learning theory—the variation theory of learning.»
- Pang, M. F., & Marton, F. (2005). Learning Theory as Teaching Resource: Enhancing Students' Understanding of Economic Concepts. *Instructional Science*, 33, 159–191. DOI: [10.1007/s11251-005-2811-0](https://doi.org/10.1007/s11251-005-2811-0). OA-PDF доступен.

#### Статус доказательств теории вариации — честно

**[СПОРНО]** — и это главное, что надо знать перед тем, как на неё опираться.

- **За:** сотни learning studies в Швеции, Гонконге, материковом Китае; фиксируется устойчивая связь между тем, какие паттерны вариации *фактически* были развёрнуты в уроке, и тем, что ученики усвоили. Механизм (различение через вариацию) независимо подтверждён экспериментальной когнитивной психологией — см. §3b ниже про interleaving.
- **Против:** методология learning study системно слабая — дизайны часто **без контрольной группы и без рандомизации**, эффекты меряются pre/post внутри класса; понятие «critical aspect» критикуют за концептуальную расплывчатость (нет независимого критерия, что является критическим аспектом, кроме постфактум-анализа). Теория **не имеет мета-анализа** и почти не имеет RCT. Есть недавняя попытка — Springer, *Instructional Science* (2025), DOI [10.1007/s11251-025-09721-y](https://doi.org/10.1007/s11251-025-09721-y), «Testing the use of variation theory in teaching critical thinking—a field experimental study» — но полный текст за пейволом, содержимое **[НЕ ВЕРИФИЦИРОВАНО]**.
- Сами авторы это признают: «there is not a one-to-one correspondence between teaching and learning. Even if it is made possible to learn certain things in a lesson, students may not learn.»

**Итог:** теория вариации — это **сильная порождающая рамка для дизайна объяснений** с сомнительным независимым эмпирическим статусом, но с сильным механистическим подтверждением из соседней области (см. далее). Используйте как эвристику проектирования, не как «доказанный метод».

---

### 3b. Почему «X — это не Y» и non-examples работают: экспериментальные данные

#### Tennyson & Park — концепт-обучение, matched non-examples

**Точная ссылка:** Tennyson, R. D., & Park, O. (1980). The Teaching of Concepts: A Review of Instructional Design Research Literature. *Review of Educational Research*, 50(1), 55–70. DOI: [10.3102/00346543050001055](https://doi.org/10.3102/00346543050001055). Цитирований: 167.

**Абстракт (verbatim, через OpenAlex):**
> «Reviewed are recent studies directly related to the teaching of concepts. The relationship of this educational research work with that in experimental psychology is defined with extended interpretation given to specifying a set of guidelines for design of concept learning environments. A four-step process for concept teaching is proposed from the literature. First, the taxonomical structure of the content should be determined. Second, a concept definition should be prepared in terms of the critical attributes, and examples should be selected on the basis of critical and variable attributes. Third, examples should be arranged in rational sets by appropriate manipulation of the attributes. Fourth, the presentation order of the rational sets should be arranged according to the divergency and difficulty level among examples of the concept. Areas of further research on concept teaching are identified.»

**Читайте внимательно — это дословно те же четыре паттерна Мартона, только на языке ID-1970-х:**
- «critical attributes» = critical aspects
- **matched example/non-example pair** (пример и не-пример, отличающиеся *минимально*, ровно по критическому атрибуту) = **CONTRAST + SEPARATION**
- **divergent examples** (примеры, максимально различные по *переменным* атрибутам, но одинаковые по критическим) = **GENERALIZATION**
- «rational set» = набор, где эти отношения выстроены системно

**Прикладной вывод:** «matched non-example» — это не «плохой пример». Это пример, который отличается от целевого понятия **ровно по одному критическому атрибуту**, с максимальным сходством по всему остальному. Именно поэтому «Rate limiting — это не throttling: разница ровно в том, что…» работает, а «Rate limiting — это не сортировка» бесполезно.

**Статус:** **[ПОДТВЕРЖДЕНО ИССЛЕДОВАНИЯМИ]** для обучения понятиям, но база — исследования 1960–1970-х (Markle & Tiemann, Merrill & Tennyson, Klausmeier). Современных репликаций мало. Родственные линии — «discrimination training» из поведенческой психологии и «concept attainment» Брунера. Соблюдайте историческую оговорку: это старая, но многократно воспроизведённая литература.

#### Kornell & Bjork (2008) — interleaving и индуктивное обучение категориям ⭐

**Точная ссылка:** Kornell, N., & Bjork, R. A. (2008). Learning Concepts and Categories: Is Spacing the "Enemy of Induction"? *Psychological Science*, 19(6), 585–592. DOI: [10.1111/j.1467-9280.2008.02127.x](https://doi.org/10.1111/j.1467-9280.2008.02127.x). Цитирований: **598**.
*Авторитетность: Psychological Science; Роберт Бьорк — автор концепции «desirable difficulties», один из самых цитируемых исследователей памяти.*

**Абстракт (verbatim):**
> «Inductive learning -- that is, learning a new concept or category by observing exemplars -- happens constantly, for example, when a baby learns a new word or a doctor classifies x-rays. What influence does the spacing of exemplars have on induction? Compared with massing, spacing enhances long-term recall, but we expected spacing to hamper induction by making the commonalities that define a concept or category less apparent. We asked participants to study multiple paintings by different artists, with a given artist's paintings presented consecutively (massed) or interleaved with other artists' paintings (spaced). We then tested induction by asking participants to indicate which studied artist (Experiments 1a and 1b) or whether any studied artist (Experiment 2) painted each of a series of new paintings. Surprisingly, induction profited from spacing, even though massing apparently created a sense of fluent learning: Participants rated massing as more effective than spacing, even after their own test performance had demonstrated the opposite.»

**Почему это критично для технического письма.** Два независимых вывода:
1. **Чередование конфузящихся категорий бьёт блочную подачу** при задаче *различения*. Это прямое экспериментальное подтверждение «юкстапозиции» — размещать похожие понятия рядом, а не в отдельных главах.
2. **Метакогнитивная иллюзия.** Испытуемые *считали* блочную подачу лучше — даже после того, как их собственные результаты доказали обратное. Перевод на документацию: «одна тема — одна страница, всё аккуратно разложено по полочкам» ощущается читателем как более понятное, но хуже учит различать. Читательские отзывы («так понятнее!») здесь — ненадёжный сигнал.

**Механизм:** Birnbaum, M. S., Kornell, N., Bjork, E. L., & Bjork, R. A. (2013). Why interleaving enhances inductive learning: The roles of discrimination and retrieval. *Memory & Cognition*, 41, 392–402. DOI: [10.3758/s13421-012-0272-7](https://doi.org/10.3758/s13421-012-0272-7). OA-PDF на Springer. Вывод: главный движок — именно **discrimination** (возможность заметить различия между смежно предъявленными категориями), а не просто распределение во времени.

**Изоляция interleaving от spacing:** Taylor, K., & Rohrer, D. (2010). The effects of interleaved practice. *Applied Cognitive Psychology*, 24(6), 837–848. DOI: [10.1002/acp.1598](https://doi.org/10.1002/acp.1598).
> «Previous research shows that interleaving rather than blocking practice of different skills (e.g. abcbcacab instead of aaabbbccc) usually improves subsequent test performance. Yet interleaving, but not blocking, ensures that practice of any particular skill is distributed, or spaced, because any two opportunities to practice the same task are not consecutive. Hence, because spaced practice typically improves test performance, the previously observed test benefits of interleaving may be due to spacing rather than interleaving per se. In the experiment reported herein, children practiced four kinds of mathematics problems in an order that was interleaved or blocked, and the degree of spacing was fixed. The interleaving of practice impaired practice session performance yet doubled scores on a test given one day later. An analysis of the errors suggested that interleaving boosted test scores by improving participants' ability to pair each problem with the appropriate procedure.»

(«Impaired practice performance yet doubled test scores» — эталонный пример desirable difficulty.)

Также: Rohrer, D., Dedrick, R. F., & Stershic, S. (2015). Interleaved practice improves mathematics learning. *Journal of Educational Psychology*, 107(3), 900–908. DOI: [10.1037/edu0000001](https://doi.org/10.1037/edu0000001). N = 126, 7-й класс, 3 месяца. **Cohen's d = 0.42 (немедленный тест), 0.79 (через 30 дней).**

#### Мета-анализ interleaving — здесь важен нюанс ⚠️

**Brunmair, M., & Richter, T. (2019). Similarity matters: A meta-analysis of interleaved learning and its moderators.** *Psychological Bulletin*, 145(11), 1029–1052. DOI: [10.1037/bul0000209](https://doi.org/10.1037/bul0000209). PMID: 31556629. **59 исследований, 238 размеров эффекта, 158 выборок.**

Абстракт (verbatim, через PubMed):
> «An interleaved presentation of items (as opposed to a blocked presentation) has been proposed to foster inductive learning (interleaving effect). A meta-analysis of the interleaving effect (based on 59 studies with 238 effect sizes nested in 158 samples) was conducted to quantify the magnitude of the interleaving effect, to test its generalizability across different settings and learning materials, and to examine moderators that could augment the theoretical models of interleaved learning. A multilevel meta-analysis revealed a moderate overall interleaving effect (Hedges' g = 0.42). Interleaved practice was best for studies using paintings (g = 0.67) and other visual materials. Results for studies using mathematical tasks revealed a small interleaving effect (g = 0.34), whereas **results for expository texts and tastes were ambiguous with nonsignificant overall effects**. An advantage of blocking compared with interleaving was found for studies based on words (g = -0.39). A multiple metaregression analysis revealed **stronger interleaving effects for learning material more similar between categories, for learning material less similar within categories, and for more complex learning material**. These results are consistent with the theoretical account of interleaved learning, most notably with the sequential theory of attention (attentional bias framework). We conclude that interleaving can effectively foster inductive learning but that the setting and the type of learning material must be considered. The interleaved learning, however, **should be used with caution in certain conditions, especially for expository texts and words**.»

**Это прямо бьёт по нашей теме и это надо сказать честно.** Технический текст — это **expository text**, а именно на экспозиторных текстах эффект интерливинга оказался **незначимым**. Значит:
- Общий принцип **[ПОДТВЕРЖДЕНО]**: контраст помогает различению, и чем **выше межкатегорийное сходство**, тем сильнее эффект. То есть «commonly confused with» оправдан ровно тогда, когда понятия действительно легко спутать.
- Перенос конкретно на прозаический документационный текст — **[СПОРНО]**. Экспериментальная база interleaving построена на картинах, задачах, экземплярах, а не на абзацах прозы.
- Практический вывод: контраст в документации должен подаваться **экземплярами** (два фрагмента кода, две конфигурации, две трассы), а не двумя абзацами описательной прозы. Первое опирается на подтверждённую науку, второе — нет.

#### Ещё один нюанс: «слишком разные» примеры вредны
В Kullberg/Runesson Kempe/Marton (2017, p. 561) приводится:
> «It has been argued that differences in the examples used that are too difficult to align can be less beneficial for student learning (Gentner and Markman 1994).»

То есть контраст работает через **структурное выравнивание**. «X — это не Y» бесполезно, если X и Y невозможно поставить в соответствие по общей схеме. Правило: контрастируйте только то, что выравнивается.

---

### 4. Diátaxis и паттерн «commonly confused with»

**Первоисточник:** [diataxis.fr](https://diataxis.fr/) — Daniele Procida. Исходная версия — документационная система Divio: [docs.divio.com/documentation-system/explanation/](https://docs.divio.com/documentation-system/explanation/) (авторство Procida там подтверждено на странице). Прочитаны напрямую: `/explanation/`, `/compass/`, `/foundations/`, `/how-to-use-diataxis/`.

**Определение объяснения (verbatim с diataxis.fr/explanation/):**
> «Explanation is a discursive treatment of a subject, that permits reflection. Explanation is understanding-oriented.»
> «Reflection occurs after something else, and depends on something else, yet at the same time brings something new.»
> «The perspective of explanation is higher and wider than that of the other three types.»
> «It's documentation that it makes sense to read while away from the product itself.»

**Компас (verbatim-таблица с /compass/):**

| | приобретение навыка (study) | применение навыка (work) |
|---|---|---|
| **действие** | Tutorial | How-to guide |
| **познание** | **Explanation** | Reference |

Две оси: *action/cognition* («practical steps, doing» vs «theoretical or propositional knowledge, thinking») и *acquisition/application* («study» vs «work»). Из /foundations/: «There are only two dimensions, and they don't just cover the entire territory, they define it.»

**Что Diátaxis прямо говорит про контекст, «почему» и контраст — это самое важное для нашей темы:**
> «Explanation should **explain why things are so — design decisions, historical reasons, technical constraints.**»
> «Explanation **can and must consider alternatives, counter-examples or multiple different approaches** to the same question… contrary opinions.»
> «Make connections to other things, even to things outside the immediate topic, if that helps.»
> «Keep explanation closely bounded» — чтобы объяснение не поглотило туториал и справочник.

**Вывод:** Diátaxis **явно санкционирует и контраст, и историю проблемы**, но только внутри квадранта Explanation — и явно запрещает тащить это в how-to и reference. Это самая прямая нормативная поддержка обоих паттернов из нашего исследования, которую можно процитировать.

**Статус:** **[ФОЛЬКЛОР/МНЕНИЕ — высококачественное ремесленное знание]**. Diátaxis не имеет и не претендует на эмпирическую валидацию. На /foundations/ есть уклончивая формулировка «underpinned by a systematic description and analysis of generalised user needs», но это не исследование — это аналитическая дедукция из двух осей. При этом фреймворк принят Django, Cloudflare, Gatsby, Canonical, Google — так что это очень широко валидированная *практика*, но не доказательство.

**Про «commonly confused with» как самостоятельный паттерн документации:** отдельного первоисточника, который бы его формулировал и обосновывал, найти **не удалось**. Ближайшее — предписание Diátaxis про «alternatives, counter-examples». Сам паттерн — **[ФОЛЬКЛОР]** с сильной теоретической подпоркой (Мартон + Tennyson & Park + Kornell & Bjork), но без прямых исследований на документации.

---

## B. ОБЪЯСНЕНИЕ ЧЕРЕЗ ИСТОРИЮ ПРОБЛЕМЫ

### 5. Генетический (историко-генетический) метод

#### Эрнст Мах — самая ранняя внятная формулировка ⭐ (verbatim, скачано и проверено)

**Точная ссылка:** Mach, E. *The Science of Mechanics: A Critical and Historical Account of Its Development* (нем. оригинал 1883; англ. пер. T. J. McCormack), гл. II «The Principles of Dynamics», pp. 254–255.
Проверенный полный текст: archive.org, идентификатор `scienceofmechani011018mbp`, файл `_djvu.txt`.

**Verbatim (я вычитал этот абзац в скачанном тексте):**
> «We shall recognise also that not only a knowledge of the ideas that have been accepted and cultivated by subsequent teachers is necessary for the historical understanding of a science, but also that the rejected and transient thoughts of the inquirers, nay even apparently erroneous notions, may be very important and very instructive. **The historical investigation of the development of a science is most needful, lest the principles treasured up in it become a system of half-understood prescripts, or worse, a system of prejudices.** Historical investigation not only promotes the understanding of that which now is, but also brings new possibilities before us, by showing that which exists to be in great measure conventional and accidental.»

Это точнейшая формулировка мотивации «истории проблемы» для документации: без истории API/протокол/конфиг превращается в «систему полупонятых предписаний, или, хуже, систему предрассудков» — то есть в карго-культ. И вторая половина — историческое рассмотрение показывает, что существующее «в значительной мере условно и случайно», то есть **изменяемо**.

#### Отто Тёплиц — «генетический метод» как термин в преподавании

**Немецкий оригинал:** Toeplitz, O. (1949). *Die Entwicklung der Infinitesimalrechnung: Eine Einleitung in die Infinitesimalrechnung nach der genetischen Methode*, Erster Band. Aus dem Nachlaß hrsg. von Gottfried Köthe. Grundlehren der mathematischen Wissenschaften, Bd. LVI. Berlin/Göttingen/Heidelberg: Springer. DOI: [10.1007/978-3-642-49782-7](https://doi.org/10.1007/978-3-642-49782-7). (Издано посмертно; Тёплиц умер в 1940.) Верифицировано через Crossref, включая рецензию в ZAMM 1950, DOI 10.1002/zamm.19500300708.

**Английское издание:** Toeplitz, O. (2007). *The Calculus: A Genetic Approach*, with a new foreword by David Bressoud. University of Chicago Press. DOI: [10.7208/chicago/9780226806693.001.0001](https://doi.org/10.7208/chicago/9780226806693.001.0001). (Первое англ. изд. — 1963.)

**Суть тезиса Тёплица (по докладу 1926/27 г. и предисловию к книге):** учить анализу не в логически-дедуктивном порядке (предел → непрерывность → производная), а в порядке, в котором эти понятия *возникали как ответы на конкретные затруднения*. Важно: Тёплиц явно отличал **«прямой» генетический метод** (буквально излагать историю студентам) от **«косвенного»** (историю изучает *преподаватель*, чтобы понять, где источники трудностей, и перестроить изложение — а сами исторические имена и даты могут в тексте не появиться). Практически вся ценность — во втором.

**Проекция на документацию:** «косвенный генетический метод» — это ровно то, что нужно техническому писателю. Не «в 2014 году мы приняли RFC…», а «эта опция существует потому, что наивное решение ломается вот так — смотрите». История нужна автору, чтобы найти критический аспект; в текст попадает *проблема*, а не хронология.

#### Пойа и другие сторонники
Дж. Пойа отстаивал «генетический принцип» в *Mathematical Discovery* (1962–65). Точная формулировка и страницу подтвердить в этой сессии не удалось — **[НЕ ВЕРИФИЦИРОВАНО]**, не цитируйте дословно.

#### HPM (History and Pedagogy of Mathematics)
- Аффилированная с ICMI исследовательская группа (осн. 1976).
- **ICMI Study 10:** Fauvel, J., & van Maanen, J. (Eds.) (2000). *History in Mathematics Education: The ICMI Study*. New ICMI Study Series 6, Kluwer/Springer. DOI: [10.1007/0-306-47220-1](https://doi.org/10.1007/0-306-47220-1). Дискуссионный документ: Fauvel & van Maanen (1997), *Educational Studies in Mathematics*, DOI [10.1023/a:1003038421040](https://doi.org/10.1023/a:1003038421040).
- Классификация заявляемых мотивов: Jankvist, U. T. (2009). A categorization of the "whys" and "hows" of using history in mathematics education. *Educational Studies in Mathematics*, 71(3), 235–261. DOI: [10.1007/s10649-008-9174-9](https://doi.org/10.1007/s10649-008-9174-9). Цитирований: 257. Ключевое различение: история как **инструмент** (tool — помогает выучить математику) vs история как **цель** (goal — сама по себе предмет изучения).
- Современный обзор поля: Chorlay, R., Clark, K. M., & Tzanakis, C. (2022). History of mathematics in mathematics education: Recent developments in the field. *ZDM*, 54(7). DOI: [10.1007/s11858-022-01442-7](https://doi.org/10.1007/s11858-022-01442-7). Open Access.

#### Каков реальный статус доказательств генетического метода? — плохой ⚠️

**Bütüner, S. Ö. (2015). Impact of Using History of Mathematics on Students' Mathematics Attitude: A Meta-Analysis Study.** *European Journal of Science and Mathematics Education*, 3(4). DOI: [10.30935/scimath/9442](https://doi.org/10.30935/scimath/9442). OA-PDF: scimath.net.

Абстракт (verbatim):
> «6 studies with a total effect size of 14 that comply with coding protocol and comprise statistical values necessary for meta-analysis are combined via meta-analysis method among 53 studies on history of mathematics since 2000. […] **Average effect size is found d = 0.095 (lower limit and upper limit of confidence interval at 95% are −0.693 and 0.951, respectively) in favor of experimental group, as positive and at negligible level.**»

**Читаем прямо:** из 53 работ по истории математики в образовании только **6** вообще годились для мета-анализа. Эффект **d = 0.095**, доверительный интервал **[−0.69; +0.95]** — уверенно включает ноль. Это статистически неотличимо от «никакого эффекта», и это на самом *лёгком* исходе (аттитюды, не достижения).

**Статус генетического/исторического метода: [СПОРНО, склоняясь к ФОЛЬКЛОРУ].**
- Как **эвристика для автора** (изучи историю проблемы, чтобы понять, где лежат критические аспекты) — правдоподобно и поддержано аргументом Маха; риска нет.
- Как **приём изложения, повышающий понимание у читателя** — эмпирически **не подтверждено**. Литература HPM состоит преимущественно из нормативных эссе, дизайн-кейсов и историко-философских аргументов, а не из контролируемых испытаний. Ни одного мета-анализа по *достижениям* (не аттитюдам) найти не удалось.
- ⚠️ Отдельно: старый биогенетический аргумент («онтогенез повторяет филогенез» — обучение ребёнка должно повторять историю вида, восходит к Геккелю/Спенсеру и подхвачен Клейном) **дискредитирован**. Фройденталь заменил его на «guided reinvention» — управляемое переизобретение, что *не* то же самое, что следование исторической хронологии. Не опирайтесь на биогенетический аргумент.

---

### 6. Мотивационный нарратив «зачем это существует» в техническом письме

#### Лесли Лампорт — «State the Problem Before Describing the Solution» ⭐ (скачано, прочитано целиком)

**Точная ссылка:** Lamport, L. (1978). State the Problem Before Describing the Solution. *IEEE Transactions on Software Engineering*, SE-4(5), 428–429. PDF (сайт автора, скачан и прочитан): [lamport.azurewebsites.net/pubs/state-the-problem.pdf](https://lamport.azurewebsites.net/pubs/state-the-problem.pdf)
*Авторитетность: Лампорт — лауреат премии Тьюринга (2013), автор LaTeX, Paxos, TLA+.*

**Verbatim (заметка на 1 страницу, привожу почти целиком):**
> «After several years of writing papers in computer science, I discovered the basic expository rule embodied in the title of this note. As obvious as this rule may seem, there are fields in which it is seldom observed. (Computer networking is one example.) A typical paper in such a field is organized as follows:
> (1) a brief informal statement of the problem;
> (2) the solution;
> (3) a statement and proof of the precise correctness properties satisfied by the solution.
> In order to abide by the rule, the following organization should instead be used:
> (1) a brief informal statement of the problem;
> (2) the precise correctness conditions required of a solution;
> (3) the solution;
> (4) a proof that the solution satisfies the requisite conditions.
> Although it may not be obvious at first glance, there is a profound difference between these two approaches. In the first, the precise correctness conditions can be (and usually are) **stated in terms of the solution itself**. Some results are proved about the solution, but **it is often not clear exactly what problem is being solved. This makes the comparison of two different solutions rather difficult.** With the second approach, one is forced to specify the precise problem to be solved independently of the method used in the solution. This can be a surprisingly difficult and enlightening task. **It has on several occasions led me to discover that a "correct" algorithm did not really accomplish what I wanted it to.** I strongly urge everyone to observe the rule.
> (I am ignoring as unworthy of consideration the disturbingly large number of papers that never even attempt a precise statement of what problem they are solving.)»

**Комментарий самого Лампорта в его библиографии (проверено на [lamport.azurewebsites.net/pubs/pubs.html](https://lamport.azurewebsites.net/pubs/pubs.html)):**
> «The title says it all. This one-page note is as relevant today as when I wrote it… Replace 'describing the solution' by 'writing the program'.»

**Почему это лучший источник для «problem-first».** Аргумент Лампорта — не педагогический, а **эпистемологический**: если задача формулируется после решения, она неизбежно формулируется *в терминах решения*, и тогда (а) её нельзя сравнить с альтернативами, (б) нельзя обнаружить, что решают не ту задачу. Это ровно тот же аргумент, что у Мартона про contrast (без альтернативы нет значения) и у Честертона про забор (без исходной цели нельзя судить). Три независимые традиции сходятся в одну точку.

**Статус:** **[ФОЛЬКЛОР/МНЕНИЕ — но с логическим, а не эмпирическим обоснованием]**, от высшего возможного авторитета в области. Эмпирических испытаний «problem-first vs solution-first» в техническом письме не существует.

#### Пол Халмош — «How to Write Mathematics» ⭐ (PDF скачан, прочитан)

**Точная ссылка:** Halmos, P. R. (1970). How to Write Mathematics. *L'Enseignement Mathématique*, 16, 123–152. Также в: Steenrod, Halmos, Schiffer & Dieudonné, *How to Write Mathematics*, AMS, 1973.
PDF, который я скачал и вычитал: [sites.math.washington.edu/~lind/Resources/Halmos.pdf](https://sites.math.washington.edu/~lind/Resources/Halmos.pdf)

**§3 «Say something» (verbatim):**
> «It might seem unnecessary to insist that in order to say something well you must have something to say, but it's no joke. […] To have something to say is by far the most important ingredient of good exposition.»

**§4 «Speak to someone» (verbatim):**
> «The second principle of good writing is to write for someone. When you decide to write something, ask yourself who it is that you want to reach. […] The problems are much the same in any case; **what varies is the amount of motivation you need to put in**, the extent of informality you may allow yourself, the fussiness of the detail that is necessary, and the number of times things have to be repeated.»
> «I like to specify my audience not only in some vague, large sense… but also in a very specific, personal sense. It helps me to think of a person… a deliberately obtuse, friendly colleague, and then to keep him in mind as I write.»

**§5 — конкретное раньше общего (verbatim), прямая опора для «истории проблемы»:**
> «**The heart of mathematics consists of concrete examples and concrete problems. Big general theories are usually afterthoughts based on small but profound insights; the insights themselves come from concrete special cases. The moral is that it's best to organize your work around the central, crucial examples and counterexamples.**»
> «Where the reader needs experienced guidance is in the discovery of the things the proof does **not** prove; what are the appropriate counterexamples and where do we go from here?»

(Заметьте: Халмош требует **контрпримеров** — это независимое переоткрытие принципа контраста в норме письма.)

**§7 «Write in spirals» — спиральный метод *написания* (verbatim):**
> «The best way to start writing, perhaps the only way, is to write on the spiral plan. According to the spiral plan the chapters get written and re-written in the order 1, 2, 1, 2, 3, 1, 2, 3, 4, etc. You think you know how to write Chapter 1, but after you've done it and gone on to Chapter 2, you'll realize that you could have done a better job on Chapter 2 if you had done Chapter 1 differently.»

**§8 «Organize always» — спиральный план *организации* (verbatim), и вот это ключевое:**
> «Begin with whatever you have chosen as your basic concept—vector spaces, say—and do right by it: **motivate it, define it, give examples, and give counterexamples.** That's Section 1. In Section 2 introduce the first related concept that you propose to study—linear dependence, say—and do right by it: motivate it, define it, give examples, and give counterexamples, **and then, this is the important point, review Section 1, as nearly completely as possible, from the point of view of Section 2.** […] In Section 3 introduce your next concept… and, after clearing it up in the customary manner, review Sections 1 and 2 from the point of view of the new concept. **It works, it works like a charm.**»

**Обратите внимание на порядок Халмоша: motivate → define → examples → counterexamples.** Мотивация (зачем это) идёт **первой**, определение — второй, контрпримеры — последними. Это ровно шаблон, объединяющий обе наши темы: история проблемы открывает, контраст закрывает.

Также §12 (о теоремах, verbatim):
> «This is not to say the theorem is to appear with no introductory comments, preliminary definitions, and helpful motivations. **All that comes first**; the statement comes next; and the proof comes last.»

**Статус:** **[ФОЛЬКЛОР/МНЕНИЕ]** — сам Халмош в §1 честно пишет: «This is a subjective essay, and its title is misleading; a more honest title might be HOW I WRITE MATHEMATICS.» Но это самое влиятельное эссе о математическом письме за XX век.

#### Кнут / Ларраби / Робертс — «Mathematical Writing» ⭐ (PDF скачан, прочитан)

**Точная ссылка:** Knuth, D. E., Larrabee, T., & Roberts, P. M. (1989). *Mathematical Writing*. MAA Notes No. 14, Mathematical Association of America. Исходно — отчёт Stanford CS Report STAN-CS-88-1193 (курс CS 209, весна 1987).
PDF, который я скачал и вычитал: [jmlr.csail.mit.edu/reviewing-papers/knuth_mathematical_writing.pdf](https://jmlr.csail.mit.edu/reviewing-papers/knuth_mathematical_writing.pdf)

**Правило 12 из «Minicourse on Technical Writing» (verbatim):**
> «**Motivate the reader for what follows.** In the example of §, Lemma 1 is motivated by the fact that its converse is true. Definition 1 is motivated only by decree; this is somewhat riskier.
> **Perhaps the most important principle of good writing is to keep the reader uppermost in mind: What does the reader know so far? What does the reader expect next and why?**
> When describing the work of other people it is sometimes safe to provide motivation by simply stating that it is "interesting" or "remarkable"; but it is best to let the results speak for themselves **or to give reasons why the things seem interesting or remarkable**.»

**Правило 4 (verbatim, конец):** «Even better would be to replace the first sentence by a more suggestive motivation, **tying the theorem up with the previous discussion**.»

**Правило 11 (verbatim):** «**Try to state things twice, in complementary ways**, especially when giving a definition. This reinforces the reader's understanding.» — это, по сути, кустарная версия паттерна CONTRAST/SEPARATION Мартона.

**Конкретный пример редактирования из «Concrete Mathematics» (verbatim, §«Preparing books for publication», p. 15) — «сначала почему, потом значимость»:**
> «(Before) The general rule is ( … ) and it is particularly valuable because ( … ). The transformation in (5.12) is called ( … ). It is easily proved since ( … and … ).»
> «Reading this at speed and in context made it clear that **readers would be hanging on their chairs wondering why the rule was true; so we should first tell them why, before stressing the rule's significance**:»
> «(After) The general rule is ( … ) and it is easily proved since ( … and … ). [new paragraph] Identity (5.12) is particularly valuable because ( … ). It is called ( … ).»

**Контрапункт от Херба Вильфа (verbatim, p. 59) — важно для баланса:**
> «**A little motivation is good, but readers don't like too much.** Presenting examples that do not yield desired results can be quite useful, but the technique loses its charm after a small number of such examples. (Far from overdoing this technique, many writers will introduce mysteriously convenient starting points for their theorems. "Whenever I see 'Consider the following …' I know the author really means to say 'Here comes something from the left field bleachers.'")»

Это единственный найденный первоисточник, прямо предупреждающий о **передозировке** мотивационным нарративом. Полезен как ограничитель.

**Статус:** **[ФОЛЬКЛОР/МНЕНИЕ]** — конспект семинара, но участники (Кнут, Вильф, Мэри-Клэр ван Леунен, Ланни Форджи, Джефф Ульман) — редкой авторитетности.

---

### 7. «Chesterton's Fence» — точный оригинал ⭐

**Точная ссылка:** Chesterton, G. K. (1929). *The Thing: Why I Am a Catholic*, глава IV «The Drift from Domesticity». Лондон: Sheed & Ward. Проверенный полный текст (издание 1946 г.): archive.org, идентификатор `in.ernet.dli.2015.475818`, файл `2015.475818.The-Thing1946_djvu.txt`, пассаж на стр. **29–30**. Я скачал этот файл и вычитал абзац построчно.

**Verbatim (OCR исправлен по очевидным сканерным артефактам — «deformii^g»→«deforming», «‘Tf»→«"If», «judgo»→«judge», «arc»→«are»):**

> «In the matter of reforming things, as distinct from deforming them, there is one plain and simple principle; a principle which will probably be called a paradox. There exists in such a case a certain institution or law; let us say, for the sake of simplicity, a fence or gate erected across a road. The more modern type of reformer goes gaily up to it and says, "I don't see the use of this; let us clear it away." To which the more intelligent type of reformer will do well to answer: **"If you don't see the use of it, I certainly won't let you clear it away. Go away and think. Then, when you can come back and tell me that you do see the use of it, I may allow you to destroy it."**
>
> This paradox rests on the most elementary common sense. **The gate or fence did not grow there. It was not set up by somnambulists who built it in their sleep. It is highly improbable that it was put there by escaped lunatics who were for some reason loose in the street. Some person had some reason for thinking it would be a good thing for somebody. And until we know what the reason was, we really cannot judge whether the reason was reasonable.** It is extremely probable that we have overlooked some whole aspect of the question, if something set up by human beings like ourselves seems to be entirely meaningless and mysterious. There are reformers who get over this difficulty by assuming that all their fathers were fools; but if that be so, we can only say that folly appears to be a hereditary disease.
>
> But the truth is that **nobody has any business to destroy a social institution until he has really seen it as an historical institution. If he knows how it arose, and what purposes it was supposed to serve, he may really be able to say that they were bad purposes, or that they have since become bad purposes, or that they are purposes which are no longer served.** But if he simply stares at the thing as a senseless monstrosity that has somehow sprung up in his path, it is he and not the traditionalist who is suffering from an illusion. We might even say that he is seeing things in a nightmare.»

**Что обычно цитируют неправильно:**
1. Сам Честертон **никогда не называл это «Chesterton's Fence»** — имя дано задним числом (популяризовано в 2000-х, во многом через сообщество LessWrong и через Rationality-литературу).
2. Часто цитируют укороченно «go away and think», выбрасывая **третий абзац** — а именно он и есть самое ценное для документации: **«until he has really seen it as an historical institution»**. Честертон формулирует не запрет на изменение, а **предусловие компетентности**: чтобы получить право менять, надо реконструировать исходное назначение. И он прямо перечисляет три легитимных исхода реконструкции — цели были плохи изначально / стали плохи / больше не обслуживаются. То есть забор **можно** сносить, просто после разбора, а не вместо него.

**Как это ложится на документацию.** Аргумент Честертона — точный близнец аргумента Лампорта: нельзя оценить решение, не восстановив задачу. Практическая норма:
- **[Норма 1]** Прежде чем описывать *как* менять компонент, объясните, *зачем* он появился. Иначе документация производит читателей, которые не имеют права её применять.
- **[Норма 2]** Формат комментария/ADR «Chesterton fence note»: (а) какая проблема была, (б) какое наивное решение ломается и как, (в) при каких условиях этот забор можно убрать. Пункт (в) — прямое следствие третьего абзаца и почти всегда пропускается.
- Заметьте, что (б) — это **matched non-example** по Tennyson & Park, а (в) — условие обобщения. Паттерн «история проблемы» и паттерн «контраст» на практике — одна конструкция.

**Статус:** **[ФОЛЬКЛОР/МНЕНИЕ]** — риторический аргумент 1929 года, не исследование. Но текст первоисточника выше **верифицирован дословно**, что уже редкость: подавляющее большинство сетевых цитирований воспроизводят только первый абзац и часто перевирают формулировки.

---

## C. БОНУС

### 8. «Explain Like I'm Five» как антипаттерн

#### Правило самого сабреддита — источник получить не удалось ⚠️

Известная формулировка правила r/explainlikeimfive: *«LI5 means friendly, simplified and layperson-accessible explanations — not responses aimed at literal five-year-olds.»*

**[НЕ ВЕРИФИЦИРОВАНО]** — reddit.com, old.reddit.com, `about/rules.json` и три зеркала (redlib/libreddit/safereddit) в этой сессии вернули 403/502/503. Формулировка приведена по памяти и **должна быть перепроверена** перед публикацией. Ирония, впрочем, содержательная: **само сообщество, породившее термин, вынуждено было ввести правило против буквального его прочтения** — это лучший из возможных аргументов, что ELI5 в буквальном смысле есть антипаттерн, признанный изнутри.

#### «Lies-to-children» — Стюарт и Коэн

**Первоисточники:**
- Cohen, J., & Stewart, I. (1994). *The Collapse of Chaos: Discovering Simplicity in a Complex World*. Viking. — **здесь термин введён впервые** (не в «Науке Плоского мира», как часто пишут).
- Stewart, I., & Cohen, J. (1997). *Figments of Reality: The Evolution of the Curious Mind*. Cambridge University Press.
- Pratchett, T., Stewart, I., & Cohen, J. (1999). *The Science of Discworld*. Ebury Press. — здесь термин популяризован.

**Verbatim (Figments of Reality, 1997, через сверенную статью Wikipedia «Lie-to-children»):**
> «[a]ny description suitable for human minds to grasp must be *some* type of lie-to-children.»

**Verbatim (The Science of Discworld, 1999) — авторы защищают резкое слово «ложь»:**
> «it is for the best possible reasons, but it is still a lie.»

**Verbatim (Пратчетт, интервью):**
> «Most of us need just 'enough' knowledge of the sciences, and it's delivered to us in metaphors and analogies **that bite us in the bum if we think they're the same as the truth**.»

**Канонические примеры:** модель атома Бора до квантовой механики; кислоты по Аррениусу до Брёнстеда–Лоури; «из 2 нельзя вычесть 3» до отрицательных чисел.

**Ключевой тезис — и он двусторонний.** Упрощение **неизбежно** (никакое описание не влезает в голову целиком), поэтому вопрос не «упрощать или нет», а:
1. **Является ли упрощение стадией лестницы или тупиком?** Модель Бора — стадия: она *переписывается* следующим слоем. Плохой ELI5 даёт метафору, из которой некуда идти дальше.
2. **Помечено ли упрощение как упрощение?** Именно непомеченность — то, что «кусает за задницу».
Родственное понятие — **лестница Витгенштейна** (*Tractatus* 6.54: отбросить лестницу, взобравшись по ней).

**Статус:** **[ФОЛЬКЛОР/МНЕНИЕ]** — это концептуальный аппарат научно-популярных писателей, не исследовательская программа. Но термин точен и полезен, и первоисточник и датировка (1994, не 1999) верифицированы.

#### Дидактическая транспозиция — академический аналог

**Первоисточник:** Chevallard, Y. (1985). *La transposition didactique: du savoir savant au savoir enseigné*. Grenoble: La Pensée Sauvage.
Современное изложение: Chevallard, Y., & Bosch, M. (2020). Didactic Transposition in Mathematics Education. В: *Encyclopedia of Mathematics Education*, Springer. DOI: [10.1007/978-3-030-15789-0_48](https://doi.org/10.1007/978-3-030-15789-0_48).

**Суть.** Знание претерпевает цепочку трансформаций: *savoir savant* (учёное знание) → *savoir à enseigner* (знание, подлежащее преподаванию) → *savoir enseigné* (фактически преподанное знание). Каждый переход — институциональная деформация, не нейтральная. Ключевые патологии, названные Шевалляром:
- **«créativité didactique»** — в преподавании возникают объекты, которых **нет** в исходной дисциплине (изобретённые ради удобства изложения и не имеющие референта).
- Знание деконтекстуализируется, деперсонализируется и разворачивается в линейную последовательность — теряя ровно ту «историю проблемы», ради которой оно существовало.

**Почему это точно бьёт в тему.** Плохой ELI5 — это **неконтролируемая дидактическая транспозиция**: писатель порождает объяснительную сущность («представьте, что база данных — это шкаф с папками»), которой нет в системе; читатель принимает её за систему и строит на ней ложные выводы. Разница между «прогрессивным уточнением моделей» и «ложью детям» ровно в том, отслеживает ли автор транспозицию и предусмотрел ли следующий слой.

**Статус:** **[ПОДТВЕРЖДЕНО как теоретическая рамка / СПОРНО как каузальное утверждение]**. Дидактическая транспозиция — общепринятая аналитическая рамка во франкоязычной дидактике и в ATD (Anthropological Theory of the Didactic), с огромной описательной литературой; но это **описательная** теория (что происходит со знанием), а не экспериментально проверенное предписание.

**Практический вывод для документации.** Не «упрощай меньше», а:
- каждое упрощение снабжать **маркером** («грубо говоря»; «на самом деле сложнее — см. §X»);
- проектировать **следующий слой** заранее: если упрощение нельзя уточнить, не вводя противоречия с уже сказанным, — это не лестница, а тупик, переписывайте;
- избегать метафор, порождающих сущности, которых нет в системе.

---

### 9. Rubber duck debugging

#### Происхождение — верифицировано частично

**Первоисточник:** Hunt, A., & Thomas, D. (1999). *The Pragmatic Programmer: From Journeyman to Master*. Addison-Wesley. Глава 3, раздел «Debugging», подраздел **«Rubber Ducking»**.

Каноническая формулировка (широко воспроизводимая, в т.ч. на Wikipedia — я сверил через WebFetch статью «Rubber duck debugging»):
> «…the simple act of explaining, step by step, what the code is supposed to do often causes the problem to leap off the screen and announce itself.»

Сноска о происхождении названия: во время учёбы Дэйва Томаса в Imperial College (Лондон) научный сотрудник по имени **Greg Pugh** носил с собой маленькую жёлтую резиновую уточку и ставил её на терминал во время кодирования. Имя Greg Pugh подтверждено в статье Wikipedia.

⚠️ **Оговорка:** дословная цитата из книги не верифицирована по самому изданию (книга не в открытом доступе). Официальный список из 100 tips на [pragprog.com/tips/](https://pragprog.com/tips/) я проверил — **«rubber ducking» там отсутствует как нумерованный tip**; ближайшие по теме — Tip #31 (failing test before fixing), #32 (read the damn error message), #34 (Don't Assume It—Prove It). То есть это раздел текста, а не пронумерованный принцип. Не приписывайте ему номер tip.
Сайт [rubberduckdebugging.com](https://rubberduckdebugging.com/) подтверждает происхождение из *The Pragmatic Programmer* (1999) и уточняет, что домен зарегистрирован в 2008 г. после поста Энди Ханта 2002 г. на lists.ethernal.org.

**Статус происхождения:** **[ФОЛЬКЛОР]** — байка о Greg Pugh не документирована независимо.

#### Есть ли научная поддержка? — Да, косвенная, но сильная ⭐

Резиновая уточка как таковая не исследовалась. Но её механизм — **self-explanation effect** — одна из самых надёжно установленных вещей в педагогической психологии.

**Классика 1:** Chi, M. T. H., Bassok, M., Lewis, M. W., Reimann, P., & Glaser, R. (1989). Self-Explanations: How Students Study and Use Examples in Learning to Solve Problems. *Cognitive Science*, 13(2), 145–182. DOI: [10.1207/s15516709cog1302_1](https://doi.org/10.1207/s15516709cog1302_1). Цитирований: **1687**. OA-PDF на Wiley.
> «"Good" students learn with understanding: They generate many explanations which refine and expand the conditions for the action parts of the example solutions, and relate these actions to principles in the text. These self-explanations are guided by accurate monitoring of their own understanding and misunderstanding. […] "Poor" students do not generate sufficient self-explanations, **monitor their learning inaccurately**, and subsequently rely heavily on examples.»

**Классика 2 (каузальная, а не корреляционная):** Chi, M. T. H., de Leeuw, N., Chiu, M.-H., & LaVancher, C. (1994). Eliciting Self-Explanations Improves Understanding. *Cognitive Science*, 18(3), 439–477. DOI: [10.1207/s15516709cog1803_3](https://doi.org/10.1207/s15516709cog1803_3). Цитирований: 735. OA-PDF на Wiley.
> «Without any extensive training, 14 eighth-grade students were merely asked to self-explain after reading each line of a passage on the human circulatory system. Ten students in the control group read the same text twice, but were not prompted to self-explain. […] The prompted group had a greater gain from the pretest to the posttest. […] **High explainers all achieved the correct mental model of the circulatory system, whereas many of the unprompted students as well as the low explainers did not.**»

(Обратите внимание: контроль — **двукратное перечитывание**. То есть эффект не от лишнего времени.)

**Мета-анализ:** Bisra, K., Liu, Q., Nesbit, J. C., Salimi, F., & Winne, P. H. (2018). Inducing Self-Explanation: a Meta-Analysis. *Educational Psychology Review*, 30(3), 703–725. DOI: [10.1007/s10648-018-9434-x](https://doi.org/10.1007/s10648-018-9434-x). Цитирований: 270.
**69 размеров эффекта из 64 отчётов, случайные эффекты, взвешенный средний g = 0.55**, закодировано 20 модераторов. Вывод авторов: «self-explanation prompts are a potentially powerful intervention across a range of instructional conditions».

**Независимая экспертная оценка:** Dunlosky, J., Rawson, K. A., Marsh, E. J., Nathan, M. J., & Willingham, D. T. (2013). Improving Students' Learning With Effective Learning Techniques. *Psychological Science in the Public Interest*, 14(1), 4–58. DOI: [10.1177/1529100612453266](https://doi.org/10.1177/1529100612453266). Цитирований: 3072. (Self-explanation и interleaved practice отнесены к категории **moderate utility** — ниже, чем practice testing и distributed practice, но выше, чем highlighting/rereading/summarization.)

**Статус:** **[ПОДТВЕРЖДЕНО ИССЛЕДОВАНИЯМИ]** для механизма (самообъяснение, g ≈ 0.55), **[ФОЛЬКЛОР]** для конкретного ритуала с уточкой и для его происхождения.

**Тонкость, которую обычно упускают.** У Chi et al. (1989) слабые студенты отличались не только меньшим числом самообъяснений, но и **неточным мониторингом собственного понимания**. Уточка ценна ровно тем, что принудительная вербализация ломает иллюзию понимания — тот же самый механизм, что и метакогнитивная иллюзия у Kornell & Bjork (испытуемые считали блочную подачу лучше вопреки собственным результатам). Это, кстати, аргумент **для автора документации**: если вы не можете объяснить, зачем существует эта опция, вы не понимаете её — и это отказ Честертонова забора в чистом виде.

---

## СВОДНАЯ ТАБЛИЦА СТАТУСОВ

| # | Утверждение | Статус | Лучший источник |
|---|---|---|---|
| 1 | Анализ контрастных кейсов до объяснения → лучший трансфер | **[ПОДТВЕРЖДЕНО]** | Schwartz & Bransford 1998 (3 эксп.); Sinha & Kapur 2021 (мета, g=0.36) |
| 2 | Эффект виден только на трансфере/PFL-тестах, не на фактах | **[ПОДТВЕРЖДЕНО]** | Schwartz & Martin 2004 (embedded assessment) |
| 3 | «Сначала рассказать» подрывает усвоение глубокой структуры | **[ПОДТВЕРЖДЕНО, с оговорками]** | Schwartz et al. 2011 (JEP, N=128/120) |
| 4 | То же переносится на *чтение прозы* документации | **[СПОРНО — экстраполяция]** | нет прямых исследований |
| 5 | Четыре паттерна вариации (contrast/generalization/separation/fusion) | **[СПОРНО — рамка без RCT]** | Marton 2015; Kullberg et al. 2017 |
| 6 | Различие должно предшествовать сходству | **[СПОРНО, но сходится с §7-8]** | Marton & Pang 2013, p. 25 |
| 7 | Matched non-examples / divergent examples в обучении понятиям | **[ПОДТВЕРЖДЕНО, база 1960–70-х]** | Tennyson & Park 1980, RER |
| 8 | Interleaving > blocking для различения категорий | **[ПОДТВЕРЖДЕНО]** | Kornell & Bjork 2008; Brunmair & Richter 2019 (g=0.42, 59 иссл.) |
| 9 | …но на экспозиторных текстах эффект **незначим** | **[ПОДТВЕРЖДЕНО — негативный результат]** | Brunmair & Richter 2019 |
| 10 | Эффект растёт с межкатегорийным сходством | **[ПОДТВЕРЖДЕНО]** | Brunmair & Richter 2019 (метарегрессия) |
| 11 | Ощущение «так понятнее» — ненадёжный сигнал | **[ПОДТВЕРЖДЕНО]** | Kornell & Bjork 2008 (метакогн. иллюзия) |
| 12 | Explanation должно давать «why», альтернативы, контрпримеры | **[ФОЛЬКЛОР — качественная норма]** | diataxis.fr/explanation/ (Procida) |
| 13 | «Commonly confused with» как паттерн документации | **[ФОЛЬКЛОР]** | первоисточника нет; косвенно Diátaxis |
| 14 | Генетический/исторический метод повышает понимание | **[СПОРНО → ФОЛЬКЛОР]** | Bütüner 2015: **d=0.095, CI [−0.69; 0.95]**, n=6 |
| 15 | История нужна **автору**, чтобы найти критические аспекты | **[ФОЛЬКЛОР/МНЕНИЕ, правдоподобно]** | Mach 1883; «косвенный» метод Тёплица |
| 16 | «Онтогенез повторяет филогенез» в обучении | **[ОПРОВЕРГНУТО]** | заменён на «guided reinvention» Фройденталя |
| 17 | Задачу надо формулировать до решения | **[ФОЛЬКЛОР — логический аргумент]** | Lamport 1978, IEEE TSE SE-4(5) |
| 18 | motivate → define → examples → counterexamples | **[ФОЛЬКЛОР]** | Halmos 1970, §8 |
| 19 | «Сначала почему, потом значимость» | **[ФОЛЬКЛОР]** | Knuth et al. 1989, правило 12 + пример из Concrete Math |
| 20 | Мотивации можно переборщить | **[ФОЛЬКЛОР — полезный ограничитель]** | Wilf в Knuth et al. 1989, p. 59 |
| 21 | Chesterton's fence — текст верифицирован дословно | **[ФОЛЬКЛОР/МНЕНИЕ; текст ПОДТВЕРЖДЁН]** | Chesterton 1929, «The Drift from Domesticity», pp. 29–30 |
| 22 | ELI5 в буквальном смысле — антипаттерн | **[ФОЛЬКЛОР]**; правило сабреддита **[НЕ ВЕРИФИЦИРОВАНО]** | reddit недоступен из сессии |
| 23 | Упрощение неизбежно; вопрос — помечено ли оно | **[ФОЛЬКЛОР/МНЕНИЕ]** | Cohen & Stewart 1994; Figments 1997 |
| 24 | Дидактическая транспозиция деформирует знание | **[ПОДТВЕРЖДЕНО как рамка, СПОРНО как предписание]** | Chevallard 1985 |
| 25 | Rubber duck: происхождение (Greg Pugh) | **[ФОЛЬКЛОР]** | Hunt & Thomas 1999, гл. 3 «Rubber Ducking» |
| 26 | Механизм (self-explanation) работает | **[ПОДТВЕРЖДЕНО]** | Bisra et al. 2018, **g = 0.55**, 69 ES; Chi et al. 1994 |

---

## ЧТО ДОСТАТЬ НЕ УДАЛОСЬ

1. **Полный текст Schwartz & Bransford 1998** — PDF на `aaalab.stanford.edu` мёртв (домен не резолвится), Taylor & Francis отдаёт 403. Верифицированы полный абстракт (OpenAlex + ERIC) и все ключевые формулировки, но **не** N, конкретные наборы данных классических психологических экспериментов и статистика по каждому из трёх исследований.
2. **Правило r/explainlikeimfive** — reddit.com/old.reddit.com/зеркала недоступны (403/502/503). Формулировка приведена по памяти, требует перепроверки.
3. **Дословный текст «Rubber Ducking» из The Pragmatic Programmer** — книга закрыта; цитата взята из сверенной Wikipedia, не из издания.
4. Бюджет WebSearch сессии исчерпан (200/200); дальнейшая работа велась через прямые WebFetch и API (OpenAlex, Crossref, PubMed/eutils, archive.org).

## ГЛАВНОЕ НАБЛЮДЕНИЕ

Три независимые традиции — экспериментальная когнитивная психология (Шварц/Бренсфорд, Бьорк), феноменография (Мартон) и ремесленная норма технического письма (Лампорт, Халмош, Кнут, Честертон) — сходятся к **одному** утверждению, ни разу друг на друга не ссылаясь:

> **Значение возникает только из различения, а различение требует альтернативы. Поэтому и «X — это не Y», и «вот какую проблему это решало» — это одна и та же операция: предъявление альтернативы, относительно которой объясняемое обретает смысл.**

Лампорт: без независимой формулировки задачи нельзя сравнить два решения. Честертон: без исходной цели нельзя судить о заборе. Мартон: без не-линейных функций «линейная функция» — синоним «функции». Kornell & Bjork: категории различаются, когда предъявлены смежно.

Эмпирическая прочность при этом распределена крайне неравномерно: **сильнее всего — self-explanation (g=0.55) и interleaving (g=0.42)**; **умеренно — PS-I/PFL (g=0.36)**; **практически нулевая — исторический метод (d=0.095, CI включает ноль)**; **отсутствует — для Diátaxis и всех норм технического письма**. И отдельно стоит помнить негативный результат Brunmair & Richter: на **экспозиторных текстах** interleaving не сработал — так что контраст в документации надо строить на **экземплярах** (два конфига, два стектрейса, два диффа), а не на двух абзацах прозы.
