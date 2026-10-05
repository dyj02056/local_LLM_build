# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

React + Vite + Tailwind CSS (user choice). The built static bundle is served by the existing FastAPI app, so the demo runs as one server. Local run plus Docker Compose (API + UI + Ollama).

## Users

Primary: interviewers and hiring managers evaluating a developer job candidate's portfolio. They meet the product through the GitHub README (screenshots/GIF) or by running it locally for a few minutes. They want to see quickly that the fine-tuning actually works, that execution is safe, and that the candidate measured results honestly.

## Product Purpose

A local Text-to-SQL demo: a Korean or English natural-language question becomes SQL from a locally served LLM (Ollama, CPU), runs against a read-only SQLite database, and returns a result table. Success is that a reviewer can ask a question, see the generated SQL and results, compare the base model with the fine-tuned model, and find the measured evaluation results without reading code.

## Positioning

Everything runs locally with a 3B model fine-tuned by the author (QLoRA on Spider), and every claim is backed by the author's own measurements, including negative results: Spider EX 61.8% → 73.4%, self-correction +1.0%p, and a self-built Korean shop evaluation where fine-tuning scored lower (71% → 66%) because multi-join accuracy dropped.

## Operating Context

- Models: `qwen2.5-coder:3b` (base) and `text2sql-ft` (fine-tuned) on a local Ollama server, CPU only; one generation takes about 5–8 s, so waiting is part of the experience.
- Databases: the Korean virtual shop DB (`shop`, default) and 20 Spider dev databases (English questions).
- Reviewers may watch on a laptop screen or a README GIF; mobile is secondary but must not break.

## Capabilities and Constraints

- Ask a question against a selected DB; show generated SQL, result rows (max 200), and generation/execution time.
- Side-by-side comparison of base vs fine-tuned model for the same question (about 2× the wait).
- Self-correction toggle: on an execution error, retry with the SQLite error message (max 2 rounds) and show the attempts.
- Evaluation dashboard with the measured results from README (Spider, self-correction ablation, Korean eval, loss curve).
- Safety: SQLite opened read-only, authorizer allows only SELECT/READ/FUNCTION, 5 s timeout, `db_id` path validation.
- UI language: Korean.

## Evidence on Hand

- README.md results tables and analyses; `docs/loss_curve.png`.
- `outputs/` evaluation files are gitignored, so the dashboard must use numbers committed in the repo, not live outputs.
- No testimonials, users, or deployment metrics exist; do not invent any.

## Product Principles

1. Show, don't claim: every number on screen comes from a reproducible measurement in the repo.
2. Honest about limits: negative and null results are shown as prominently as wins.
3. The wait is real: a CPU LLM takes seconds, so progress must be visible and never feel frozen.
4. Safety is visible: show that execution is read-only and restricted, not just say it.
