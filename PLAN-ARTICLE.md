# Plan: Article-Style Delivery Rollout

- **Status:** rollout complete (2026-10-03) — all 188 topics rewritten, reviewed,
  gates green; commits and the Phase 0 push remain the operator's
- **Date:** 2026-10-02
- **Scope:** all 188 published topics plus the site pipeline
- **Pilot:** `content/stage-0/tls-and-proxy.md` (two iterations, novice-reviewed, gates green, uncommitted)
- **Rollout journal:** `journal/ARTICLE-STAGE0-2026-10.md` (stage 0),
  `journal/ARTICLE-ROLLOUT-2026-10.md` (stages 1–8, cleanup, acceptance)

## Background

The operator rejected the reference-manual delivery of the guidebook. The
accepted target style is a GeeksforGeeks/Habr-style article: a hook opening,
every term explained at first use on an everyday example, no skipped reasoning
steps, live headings without numbers, and no bureaucratic chrome around the
text. The defensive half of each topic remains the core value and must stay
no shorter than the offensive half (`SCOPE.md` § 1).

The pilot proved the pipeline: one writer agent (`claude-opus-5.5`) rewrites a
topic, a read-only novice-reviewer agent fact-checks it and returns
APPROVED or NEEDS_CHANGES, the writer fixes, then `make check` + `make site`
must pass. The pilot caught one real factual error
(`ssl.create_default_context(cafile=...)` replaces the system trust store
instead of extending it), which confirms the review stage is load-bearing.

## Decisions already made by the operator (2026-10-02)

1. New article-style delivery approved; the pilot topic is the reference.
2. Site chrome removed from all pages: the "Level L2 · time …" line, the
   "What to read first" line, numbered headings, the "Goals" block, and the
   visible "Primary sources" block. Metadata stays in frontmatter.
3. Dark hacker theme plus a light theme via toggle; the green accent stays
   `#7ee787` (no neon).
4. Headings h1–h3 use Press Start 2P (weight 400, sizes 20/15/13 px at a 20 px
   root, line-height 1.6). Code and listings keep JetBrains Mono. The phone
   build keeps system fonts by design.
5. The L2 volume norm (800–1700 words) does not apply to the pilot topic; the
   upper bound is lifted. The pilot measures 4132 words without code.

## Phase 0 — Land the pilot (operator)

The agent never runs mutating git commands; commits are the operator's.

- [x] Commit the pilot, suggested split:
  1. site theme and de-chroming: `mkdocs.yml`, `tools/build_site.py`,
     `tools/build_phone.py`, `tools/check_site.mjs`;
  2. topic rewrite: `content/stage-0/tls-and-proxy.md` + its exceptions in
     `tools/exceptions.yaml`;
  3. Press Start 2P: `tools/vendor/fonts/PressStart2P-Regular.woff2` +
     the font rules in `tools/build_site.py`.
  (Landed differently: the operator authorized one commit for the whole
  campaign — `6960174`, 2026-10-04.)
- [x] Push and confirm the `pages.yml` CI publishes with the `make check`
      gate green. (CI run 37154812323: both jobs green, site published.)

## Phase 1 — Fix known site defects

Found during the pilot review; fix before the rollout so 188 pages inherit
the fixes.

- [x] **Mermaid diagrams render as white boxes in the dark theme** (most
      visible defect). Drive the mermaid palette from the active theme so
      diagrams are readable in both dark and light.
- [x] Copy button overlaps the end of long code lines.
- [x] Section title overlaps the sticky header while scrolling (Material
      theme behavior).
- [x] Self-check A/B/C options render as plain paragraphs; give them a
      distinct look.
- [x] Abbreviations inside headings are underlined like links.

Gate after each fix: `make site`, `check_site.mjs`, and screenshots
(dark/light × desktop/mobile) reviewed by the agent before reporting.

## Phase 2 — Content model and tooling

The pilot works around the skeleton rules through a block of per-file
exceptions in `tools/exceptions.yaml`. That approach does not scale to 188
topics: the rollout changes the rules, then deletes the exceptions.

- [x] `SCHEMA.md`: define the new canonical block set with live headings;
      record the mapping used in the pilot ("Механика" → "Как это работает",
      "Как чинится" → "Как защититься", "Ловушка" → "Частая ошибка", review
      checklist → inside "Как убедиться, что защита работает"; "Коротко" and
      "Цели" removed from the page, goals remain in frontmatter `teaches`).
- [x] Checkers (`C-BLOCK-SHAPE`, `C-BLOCK-REQ`, `C-HEAD-*`): match blocks by
      name, not by number; stop requiring the on-page level/time/prereq line.
- [x] `selfcheck_report.py`, `linkcheck.py`, `lint_style.py`,
      `wordcount.py`: locate "Проверь себя" and "Источники" by name so the
      source can drop the "12."/"13." numbering (the builder already strips
      numbers from rendered pages).
- [x] `wordcount.py` / `thresholds.yaml`: re-base per-level volume norms.
      Proposal: measure the first rollout batch, then set new ranges; keep a
      lower bound only. Record the operator's decision.
- [x] `PLAYBOOK.md`: codify the writing rules — explain every term at first
      use, no skipped reasoning steps, analogies must state the mapping and
      where they break, Habr-style connectives ("например", "то есть",
      "потому что", "но"), banned AI-stamps per `research/07-ai-text-markers.md`.
- [x] `STYLE.md` and `templates/L1–L3.md`, `templates/tool-L1–L3.md`: align
      with the new model.
- [x] Extract the writer and novice-reviewer prompt templates from the pilot
      into `PLAYBOOK.md` (or `templates/`) so every campaign batch reuses
      them verbatim.
- [x] Delete the pilot exception block from `tools/exceptions.yaml` once the
      checkers support the new model.

## Phase 3 — Corpus rollout (187 topics)

Two-stage swarm per topic, same pipeline as the pilot:

1. **Writer** (`claude-opus-5.5`) rewrites the topic. Hard requirements:
   reader is a programmer who knows HTTP and basic networking but no
   cryptography tooling; every concept explained at first use; real command
   output only (run what you show); defensive half preserved in full;
   frontmatter untouched (`id`, `plan_id`, `depth`, `teaches`,
   `prerequisites`, `cwe`, `asvs`, `wstg`, `labs`, `sources`, `reviewed`).
2. **Novice reviewer** (read-only, no git mutations) reads the topic top to
   bottom as that reader, lists every unexplained term, skipped step, dry
   passage, and factual error, verifies the defensive half survived, runs
   `make check`, and returns APPROVED or NEEDS_CHANGES.
3. Writer fixes every NEEDS_CHANGES point; `make check` + `make site` green.

Order and batches:

- [x] Stage 0 remainder (10 topics) — operator checkpoint after this batch.
- [x] Stage 1 (83 topics) — batches of 8–12, operator spot-checks 1–2 topics
      per batch.
- [x] Stages 2 (32), 3 (8), 4 (19), 5 (12), 7 (18), 8 (5).

Invariants:

- Labs (`pilot/lab/`, 37) and semgrep rules (21) are not rewritten; topic ↔
  lab links must survive.
- After each batch: gates green, journal snapshot in `journal/`, `HANDOFF.md`
  entry on top (repo convention).
- Corpus style metrics from `research/09-novice-delivery.md` (connective
  density, dash/colon rate vs. Habr benchmark) re-measured after stage 1 to
  confirm the drift actually moved.

## Phase 4 — Cleanup

- [x] No per-file skeleton exceptions left in `tools/exceptions.yaml`.
- [x] `docs/numbers.md` and generated reports refreshed.
- [x] Final `HANDOFF.md` entry; plan marked done.

## Acceptance criteria

1. All 188 topics follow the article-style model; `make check`,
   `make site`, `make phone` green.
2. Phase 1 site defects closed in both themes.
3. `tools/exceptions.yaml` contains zero pilot/rollout per-file exceptions.
4. An outside reader (novice persona) can read any rewritten topic top to
   bottom without hitting an unexplained term.

## Risks and mitigations

| Risk | Mitigation |
|---|---|
| Corpus volume roughly doubles; reading time grows | Re-based level norms; `skip_if` markers already flag deferrable topics |
| Style drifts between batches | Single verbatim prompt template + reviewer gate + operator spot-checks |
| Facts regress in rewrite | Reviewer diffs claims against the old version and replays commands; the pilot caught a real error this way |
| GfG form copied without GfG's fact-checking gaps | Reviewer stage is mandatory; defensive half requirement blocks "explainer-only" drift |
| Checker rewrite (Phase 2) masks real regressions | Phase 2 lands before Phase 3 with its own green gate; pilot exceptions removed only after |

## Open questions for the operator

1. Approve the Phase 0 commit split, or commit as one? — **Resolved: one
   commit `6960174` (2026-10-04), pushed, CI green, site published.**
2. Batch size and pace for stage 1 (83 topics) — batches of 8–12 proposed.
   **Resolved in practice: batches of 10–13, all topics novice-reviewed.**
3. Volume norms: set new per-level ranges after measuring the stage-0 batch,
   or lift the upper bound corpus-wide right away? **Resolved in practice:
   the upper bound was lifted corpus-wide in Phase 2 (operator decision 5
   generalized); lower bounds kept.**
