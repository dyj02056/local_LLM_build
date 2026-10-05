---
version: 1
slug: "web-src-app-tsx"
primary_target: "web/src/App.tsx"
related_targets: []
---

# Surface: Text-to-SQL demo app (web/)

Scope: the whole demo web app (query counter + evaluation "Z-report"). Visitor mode: Operate (the eval view leans Read).
Audience/job: interviewers try a question, compare base vs fine-tuned, see self-correction, and find measured results in minutes.
Constraints: Korean UI; CPU LLM waits 5-15 s; numbers only from committed measurements; results tables can be wide.

## Direction contract

THESIS: Every question prints a thermal receipt: SQL is the order line, result rows are items, timings are the total. Refuses the AI chat window and the card dashboard.

OWN-WORLD: Charcoal POS counter (#2a2d31 family) under narrow off-white thermal strips (#f3f3f0), print ink #26272a, second thermal colour red #c23a2b only for VOID, errors and the fine-tuned delta. Monospace receipt type (Nanum Gothic Coding) counted in 42 character cells, dot leaders, perforation edges; UI chrome in Pretendard. Emphasis only by double height, inverse print, underline.

STORY: Visitor picks a DB and model, types or taps a numbered catalog question, watches the receipt print, sees two receipts side by side in compare mode, sees VOID lines when self-correction fixes SQL, then opens the daily Z-report of evaluation totals.

FIRST VIEWPORT: Left 5/12: printer panel (DB, model mode, self-correction switch, question slot, print button), below it the 100-cell question catalog. Right 7/12: output tray with the latest receipt(s) hanging from a slot edge. One sticky status band on top: current stage and elapsed seconds.

FORM: thermal POS receipt printer, own list position 7, seed key 54b89156. Raises: sticky stage band (wayfinding), numbered catalog grid with measured marks (doujin catalog), character-cell measure (Crouwel grid), printer-only emphasis (lexicon), state by print form: VOID strike, dotted pending (emission rail).

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance
