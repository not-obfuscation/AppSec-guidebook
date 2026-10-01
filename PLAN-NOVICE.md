# Plan: novice-facing delivery rework

Date: 2026-10-01. Source: research mission `.review/research-09/`
(reports d1, d2, w1–w6), synthesis `research/09-novice-delivery.md` and
`research/10-site-and-product.md`, register `journal/RESEARCH-NOVICE-2026-10.md`
(section "Решения оператора"). Operator decisions were taken interactively;
this file is the binding work plan.

## Standing directive: the guidebook must read alive

Final texts (topics, site pages, generated blocks) must not contain registry
tags or numbering like RN-01, machine-stamped formulas, or officialese.
Registry identifiers stay in `journal/` and `.review/` only — they never
leak into `content/`, norms, or the site.

## Operator decisions (9)

1. **Entry order** — variant (b): add a three-sentence attack intro to
   `content/stage-0/csp.md`, `cors.md`, `security-headers.md`. The full
   stage-0 reorder is deferred until after the first text wave.
2. **Check formula** — variant (a): replace the "author six months ago"
   check formula with a new novice-anchored one (persona unchanged); remove
   "test on real readers" from PLAYBOOK 5.4 item 18, 11.3 item 10, 11.4 and
   from metrics. Contradicts SCOPE.md §1 today.
3. **Six stamped formulas** — variant (a): remove all six from PLAYBOOK,
   SCHEMA and templates, then clean the corpus. The six: YAML linter rule in
   L1 topics; catalog numbers (ASVS/WSTG) in the "Зачем" section; the fixed
   prequestion opener; the block-0 disclaimer; the intro-closing announcement;
   "Verify that" (1037 occurrences in 160 topics).
4. **Self-check and returns** — variant (a): full rewrite of rules 23–24 and
   35 in `research/09`, linters `C-BODY-SELFCHECK` and `C-BODY-RETURN`, then
   ~160 "Проверь себя" blocks and ~38 returns edited by eye.
5. **Removed playbook items** — variant (b): restore only what generates
   without new prose: the "Повтор" spaced-repetition block, mixed exercises,
   stage summary pages. Projects and Parsons problems stay removed.
6. **Freeze** — variant (b): under the tooling freeze, only defects may be
   fixed: `tools/build_site.py:746` (review-date arithmetic), contrast,
   glossary links (norm 9.5 item 14 — currently 0 links from 188 pages),
   the overdue badge (9.6 item 20).
7. **Primary sources** — variant (a): all three: a "Первоисточники" list with
   URLs per topic, a verification journal kept off-site with a lab-run
   script, and a "На чём проверено" block without dates.
8. **Navigation** — variant (b): "можно отложить" markers on deferrable
   topics (already permitted by `SCOPE.md:80`) and a note in SCOPE.md §4
   recording cloud topics as excluded. No "Start here" page.
9. **`cors.md:67`** — variant (a): fix the factual cookie-attribute error
   now, outside any campaign (verified against
   draft-ietf-httpbis-rfc6265bis-22; PLAYBOOK 11.3 item 11 requires factual
   fixes within a week).

## Work order

### Phase 0 — point fixes, no norm changes

1. Fix `content/stage-0/cors.md:67` (sentence plus cookie attributes in the
   example).
2. Add the three-sentence attack intros to `csp.md`, `cors.md`,
   `security-headers.md` (decision 1).
3. Site defects under decision 6: `tools/build_site.py:746` (also check
   `:792` and `:487`/`:521–523` from the register), contrast fix, glossary
   links, overdue badge.
4. Wrong link in `STYLE.md:394`.
5. Update stale statuses in `PLAN-FINISH.md`, `PLAN-REORG.md`,
   `PLAN-VOICE.md`.

### Phase 1 — norms

1. New check formula; drop reader-testing clauses (decision 2).
2. Remove the six formulas from PLAYBOOK, SCHEMA, `templates/` (decision 3);
   adjust linters that enforce them.
3. Rewrite self-check/return rules; rewrite `C-BODY-SELFCHECK` and
   `C-BODY-RETURN` (decision 4).
4. Restore the generatable items in PLAYBOOK and `tools/build_site.py`
   (decision 5).
5. "Первоисточники", verification journal + lab-run script, "На чём
   проверено" (decision 7) — schema fields, templates, builder support.
6. "можно отложить" markers and the SCOPE.md §4 cloud note (decision 8).

### Phase 2 — content waves

- Wave 1: machine replacement of "Verify that" in 160 topics; eye passes over
  the 62/50/33-topic formula sets.
- Wave 2: rewrite the ~160 self-check blocks and ~38 returns by eye.
- After wave 1, revisit the deferred stage-0 reorder (decision 1, variant a).

## Gates and records

- Every change lands only if `make check` passes (gate: `tools/check.py`);
  site changes additionally pass `tools/check_site.mjs` and the build via
  `build/mkdocs.yml`. Environments are not interchangeable: `.venv-tools`
  for the gate, `.venv-site` for the site.
- Each phase ends with a journal snapshot in `journal/`, newest on top in
  `HANDOFF.md`.
- Research agents keep git read-only; only the operator commits.

## Pending infrastructure decisions (outside this plan)

- `make check` depends on the network: `semgrep --validate`
  (`tools/lint_code.py:182`) pulls `p/semgrep-rule-lints` from semgrep.dev
  and intermittently fails on the 120 s timeout. Options: vendor the rule
  pack locally, or replace with an offline check (e.g. `semgrep --test`).
- `make toc` is broken (missing `.smgr/` directory).
