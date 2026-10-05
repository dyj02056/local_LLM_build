---
name: 질의 영수증 (Query Receipt)
description: A local Text-to-SQL demo where every question prints a thermal POS receipt on a charcoal counter.
colors:
  counter: "#24272b"
  counter-2: "#2d3136"
  counter-3: "#363b41"
  counter-line: "#454b52"
  counter-ink: "#eceae6"
  counter-mute: "#a9adb3"
  slot: "#15171a"
  paper: "#f3f3f0"
  paper-shade: "#e3e3de"
  ink: "#26272a"
  ink-mute: "#64656a"
  thermal: "#c23a2b"
  thermal-soft: "#f0a093"
typography:
  display:
    fontFamily: "Nanum Gothic Coding, ui-monospace, monospace"
    fontSize: "13.5px"
    fontWeight: 700
    lineHeight: 1.55
    letterSpacing: "0.6em"
  headline:
    fontFamily: "Pretendard Variable, Pretendard, system-ui, sans-serif"
    fontSize: "17px"
    fontWeight: 700
    lineHeight: 1.3
    letterSpacing: "-0.025em"
  title:
    fontFamily: "Pretendard Variable, Pretendard, system-ui, sans-serif"
    fontSize: "14px"
    fontWeight: 600
    lineHeight: 1.43
  body:
    fontFamily: "Pretendard Variable, Pretendard, system-ui, sans-serif"
    fontSize: "15px"
    fontWeight: 400
    lineHeight: 1.5
    fontFeature: "\"tnum\" 1"
  receipt:
    fontFamily: "Nanum Gothic Coding, ui-monospace, monospace"
    fontSize: "13.5px"
    fontWeight: 400
    lineHeight: 1.55
    fontFeature: "\"tnum\" 1"
  label:
    fontFamily: "Nanum Gothic Coding, ui-monospace, monospace"
    fontSize: "0.8em"
    fontWeight: 700
    lineHeight: 1.6
    letterSpacing: "0.05em"
  caption:
    fontFamily: "Nanum Gothic Coding, ui-monospace, monospace"
    fontSize: "12px"
    fontWeight: 400
    lineHeight: 1
rounded:
  none: "0px"
  cell: "3px"
  tab: "4px"
  segment: "5px"
  control: "6px"
  pill: "9999px"
spacing:
  hair: "4px"
  sm: "8px"
  md: "12px"
  gutter: "16px"
  lg: "24px"
  gutter-wide: "32px"
  xl: "40px"
  2xl: "56px"
components:
  button-print:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.ink}"
    rounded: "{rounded.control}"
    height: "52px"
    typography: "{typography.headline}"
  button-print-disabled:
    backgroundColor: "{colors.counter-3}"
    textColor: "{colors.counter-mute}"
  input-field:
    backgroundColor: "{colors.counter-2}"
    textColor: "{colors.counter-ink}"
    rounded: "{rounded.control}"
    padding: "12px 14px"
    typography: "{typography.body}"
  select-field:
    backgroundColor: "{colors.counter-2}"
    textColor: "{colors.counter-ink}"
    rounded: "{rounded.control}"
    height: "44px"
    padding: "0 12px"
  segment-active:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.ink}"
    rounded: "{rounded.segment}"
    padding: "8px 4px"
  segment-idle:
    textColor: "{colors.counter-mute}"
    rounded: "{rounded.segment}"
    padding: "8px 4px"
  nav-tab-active:
    backgroundColor: "{colors.counter-3}"
    textColor: "{colors.counter-ink}"
    rounded: "{rounded.tab}"
    padding: "6px 12px"
  nav-tab-idle:
    textColor: "{colors.counter-mute}"
    rounded: "{rounded.tab}"
    padding: "6px 12px"
  filter-chip-active:
    backgroundColor: "{colors.counter-ink}"
    textColor: "{colors.counter}"
    rounded: "{rounded.tab}"
    padding: "4px 10px"
  catalog-cell:
    backgroundColor: "{colors.counter-2}"
    textColor: "{colors.counter-mute}"
    rounded: "{rounded.cell}"
    typography: "{typography.caption}"
  catalog-cell-selected:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.ink}"
    rounded: "{rounded.cell}"
  switch-on:
    backgroundColor: "{colors.paper}"
    rounded: "{rounded.pill}"
    height: "28px"
    width: "48px"
  switch-off:
    backgroundColor: "{colors.counter-2}"
    rounded: "{rounded.pill}"
    height: "28px"
    width: "48px"
  receipt:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.ink}"
    rounded: "{rounded.none}"
    padding: "24px 24px 36px"
    width: "calc(42ch + 3rem)"
    typography: "{typography.receipt}"
  receipt-section-label:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.paper}"
    rounded: "{rounded.none}"
    padding: "0 6px"
    typography: "{typography.label}"
  receipt-void-tag:
    backgroundColor: "{colors.thermal}"
    textColor: "{colors.paper}"
    rounded: "{rounded.none}"
    padding: "0 4px"
---

# Design System: 질의 영수증 (Query Receipt)

## Overview

**Creative North Star: "The Thermal Receipt Counter"**

Every question prints a receipt. The screen is a charcoal point-of-sale counter; the work comes out of a printer slot as narrow off-white thermal strips. Generated SQL is the order line, result rows are the items, and generation and execution times add up to a total. The evaluation view is the same printer's end-of-day Z-report. The world refuses both the AI chat window and the card dashboard: nothing on screen is a chat bubble, and nothing is a floating shadowed card in a grid.

Two materials, two typefaces, and almost no colour. The counter (UI chrome, controls, the question catalog) is set in Pretendard in cool charcoal tones. The paper (receipts, the Z-tape, the report detail tape) is set in Nanum Gothic Coding, measured in character cells (42 columns for a receipt), and decorated only with what a thermal head can print: dashes, double rules, dot leaders, double-height type, inverse print, underline, and a second thermal colour, red, reserved for VOID, errors and the fine-tuned regression. Density is that of a working tool: compact, legible, numbers in tabular figures.

Waiting is part of the product (a CPU LLM takes seconds), so state is shown by print form: dotted pending lines while the model writes, sections that reveal top-down as if printed, a struck-through VOID line when self-correction replaces SQL, and a sticky status band with the current stage and an elapsed-seconds clock.

**Key Characteristics:**
- Charcoal counter (dark, cool, low-chroma) under warm off-white thermal paper; dark color-scheme only.
- Receipt type is monospace, counted in character cells, with a 42ch receipt measure.
- Emphasis only by double height, inverse print, underline and bold; never by tint or size ramps on paper.
- One accent: thermal red, used only for VOID, errors, and negative results.
- Paper has a torn zigzag bottom edge and lifts off the counter with a soft drop shadow; everything else is flat.
- State is expressed as print form (dotted pending, strike-through VOID, solid vs dotted marks), not as colour.

## Colors

A near-monochrome two-material palette, cool charcoal counter and warm thermal paper, with a single red thermal accent.

### Primary
- **Thermal Red** (thermal): the second colour of a two-colour thermal printer. Used on paper for VOID tags (inverse), struck-through superseded SQL, execution and connection errors, the fine-tuned regression row and its dumbbell, and the Korean "파인튜닝 효과" total on the Z-tape. Also the text-selection background and the input caret on the counter.
- **Soft Thermal** (thermal-soft): the legible form of thermal red on the dark counter. Used for counter-side error text, the "results differ" compare tag, the Ollama-disconnected notice, and the pulsing stage pip in the status band.

### Neutral
- **Counter Charcoal** (counter): the page background and status band (at 95% opacity). Also the theme-color.
- **Raised Counter** (counter-2): control wells: select, textarea, segmented control track, idle catalog cells, switch track off.
- **Pressed Counter** (counter-3): hover fill for counter controls, the active nav tab, and the disabled print button.
- **Counter Seam** (counter-line): 1px borders on counter controls, the status band's bottom rule, the catalog preview outline, scrollbar thumbs.
- **Counter Ink** (counter-ink): primary text on the counter, focus outline colour, active filter chip fill.
- **Counter Mute** (counter-mute): secondary text, helper copy, idle tabs and cells, hover border on controls.
- **Printer Slot** (slot): the near-black slot rail receipts hang from.
- **Thermal Paper** (paper): receipt and tape background; also the "lit" state on the counter (active model segment, selected catalog cell, switch on, the print button).
- **Paper Shade** (paper-shade): chart gridlines and bar tracks on paper, scrollbar thumbs inside receipts.
- **Print Ink** (ink): all type and rules on paper; the fill of inverse-print labels.
- **Faded Ink** (ink-mute): secondary print: meta keys, footnotes, notes, row counts, the raw loss trace.

### Named Rules
**The Second Colour Rule.** Thermal red appears only where a two-colour printer would use it: VOID, failure, and a measured regression. It never decorates, never marks a win, and never fills a button.

**The Lit Paper Rule.** On the counter, "selected" or "ready" is shown by switching a control to paper with ink type (the active segment, the selected cell, the switch, the print button), not by adding a hue.

## Typography

**Display Font:** Nanum Gothic Coding 700 (with ui-monospace, monospace)
**Body Font:** Pretendard Variable (with Pretendard, system-ui, sans-serif)
**Label/Mono Font:** Nanum Gothic Coding 400/700

**Character:** A plain Korean grotesk runs the machine; a Korean coding monospace is what the machine prints. The pairing keeps every printed number on a character grid and every control label quiet. Tabular figures are on everywhere.

### Hierarchy
- **Display** (700, receipt size, scaled 2x vertically, 0.6em tracking): receipt and Z-tape headers ("질의영수증", "Z정산") and totals lines. Height doubles while width stays the cell width, the way a thermal printer emphasises.
- **Headline** (Pretendard 700, 17px, tight tracking): the wordmark in the status band and the print button label; the empty-tray message uses 600 at 18px.
- **Title** (Pretendard 600, 14px): control labels, legends and the catalog heading on the counter.
- **Body** (Pretendard 400, 15px; 16px in the textarea with relaxed leading): counter copy and helper text at 14px in counter-mute; helper paragraphs capped at 46-52ch.
- **Receipt** (Nanum Gothic Coding 400, 13.5px / 1.55; Z-report 1.6): everything on paper. SQL lines wrap with a 2ch hanging indent; meta keys sit in an 8ch column.
- **Label** (Nanum Gothic Coding 700, 0.8em, wider tracking, inverse ink-on-paper): receipt section labels (질문, SQL, 결과); Z-report segment titles use the same inverse form at full size.
- **Caption** (Nanum Gothic Coding 400, 11-13px): catalog cell numbers, model hints under segments, catalog score line, compare tag.

### Named Rules
**The Printer Emphasis Rule.** On paper, emphasis is double height, inverse print, underline (1.5px, 4px offset) or bold. No larger font sizes, no colour tints except the Second Colour.

**The Character Cell Rule.** Paper is measured in ch: receipts are 42ch plus 3rem padding, the detail tape 88ch plus 4rem, gaps between table columns 2ch.

## Layout

A single centered stage up to 1440px wide with 16px side gutters (32px from md). On the counter view at lg and above, a 5/12 : 7/12 grid with a 56px gap: the left column (printer panel, then the 100-cell catalog) is sticky below the status band; the right column is the output tray. Below lg it stacks, and printing scrolls the tray into view. The Z-report view uses a 42ch+3rem sticky summary tape beside a wide detail tape.

The status band is sticky, 56px tall, and carries logo, view tabs, the live stage with elapsed seconds, and the connection state; on mobile the stage drops to a second row while printing. The catalog is a fixed 10-column grid of square cells with a 4px gap. Vertical rhythm on the counter is 24px between form groups, 8px label to field, 40px between panel and catalog and between tray entries. Compare mode places two receipts side by side (2 columns at lg, 20px gap) with a compare tag under them.

Breakpoints are Tailwind defaults (sm 640px, md 768px, lg 1024px). Wide result tables scroll horizontally inside the paper rather than widening it.

## Elevation & Depth

Flat counter, lifted paper. Counter surfaces never cast shadows; depth there comes from three tonal steps (counter, counter-2, counter-3) and 1px seams. Paper is the only thing that floats: a soft, diffuse drop shadow under its masked silhouette, so the shadow follows the zigzag edge. The printer slot is the one recessed element, an inset rail.

### Shadow Vocabulary
- **Paper lift** (`filter: drop-shadow(0 10px 18px rgb(10 12 14 / 0.35))`): every receipt and report tape.
- **Slot recess** (`box-shadow: inset 0 2px 3px rgb(0 0 0 / 0.6)`): the printer slot rail above the output tray.

### Named Rules
**The Only Paper Floats Rule.** If it is not thermal paper, it sits flat on the counter.

## Shapes

Two shape languages. The counter is gently rounded: 6px on fields, selects, the segmented track and the print button; 5px on segments; 4px on tabs and filter chips; 3px on catalog cells; full pills only for the switch. Paper has no corner radius at all: straight sides and a torn bottom edge cut as an 8px zigzag (CSS mask), the receipt's perforation. Rules on paper are 1.5px dashed (55% opacity), 3px double for totals and between report segments, and 1.5px dotted leaders between an item and its value.

## Components

### Buttons
Tactile and literal: the print button is a strip of paper you press.
- **Shape:** gently rounded (6px), 52px tall, full width of the panel.
- **Primary (print):** paper fill, ink text, 17px bold Pretendard, bold printer icon at 22px; label changes to "인쇄 중" while busy and "두 장 인쇄" in compare mode.
- **Hover / Active:** brightens to white on hover; on press, translates down 1px and scales to 0.99 with the expo-out ease over 200ms.
- **Disabled:** pressed-counter fill, counter-mute text, not-allowed cursor.
- **Text buttons on paper:** dotted underline at 4px offset ("모두 보기"), darken to ink on hover.

### Chips
- **Style:** view tabs and difficulty filters are 4px-rounded text buttons. Idle is counter-mute text with a pressed-counter hover; the active view tab is pressed-counter with semibold counter-ink; the active filter inverts to counter-ink fill with counter text.

### Cards / Containers
There are no cards. The only outlined container on the counter is the catalog preview readout: 6px radius, 1px counter-line border, no fill, 14px x 10px padding, live region. All content containers are paper (see Receipt).

### Inputs / Fields
- **Style:** raised-counter fill, 1px counter-line border, 6px radius, counter-ink text; textarea 16px with relaxed leading, vertical resize; select 44px tall.
- **Focus:** the textarea border shifts to counter-ink; other controls take the global 2px counter-ink outline at 2px offset. The caret is thermal red.
- **Hover:** border lightens to counter-mute.
- **Error:** counter-side error copy in soft thermal below the field.

### Navigation
The sticky status band: solid counter ground, 1px counter-line bottom seam, 56px tall. Two view tabs (계산대 / 정산 리포트). The right side is a status region: a pulsing square thermal-soft pip, the job number and stage, an elapsed clock in receipt type, and the Ollama connection state.

### Segmented Model Control
A three-way radio group in a raised-counter track with 4px inner padding. The active segment turns to lit paper with ink type; each segment carries a Pretendard 15px label over an 11px receipt-type hint (model name or "약 2배 시간"). Focus draws a 2px counter-ink outline around the segment.

### Self-correction Switch
48 x 28px pill. Off: raised-counter track, counter-line border, counter-mute knob. On: paper track and border with an ink knob that slides 20px with the expo-out ease over 300ms.

### Question Catalog (signature)
100 numbered square cells in a 10-column grid, set in receipt type. Each cell carries two 3px marks at its foot, baseline on the left and fine-tuned on the right: a solid bar for correct, a dotted bar for wrong, so the measured result reads by print form, not colour. Selected cells turn to lit paper; press scales to 0.95. A difficulty filter and a live score line sit above; a readout box below previews the hovered or selected question.

### Receipt (signature)
A 42ch thermal strip with zigzag bottom edge and paper lift. Order: double-height title with a faded store line, dashed rule, meta lines (No. zero-padded to 4, 일시, DB, 모델 with the fine-tuned name in inverse, 자동수정), the question, SQL one clause per line, results table with dashed header rule and right-aligned numbers (12 rows previewed), then dot-leader timing lines, a double rule, and a double-height total. Superseded SQL is struck through in thermal red with an inverse "VOID n차" tag and the error. While printing, three dotted pending lines (100%, 80%, 60%) stand in for the body next to a live elapsed clock. Each section reveals top-down via clip-path over 420ms with a 110ms stagger.

### Z-report Tape (signature)
The evaluation view. A sticky summary tape (Z정산) of dot-leader before/after lines with double-height effect totals, the Korean regression total printed in thermal red; and a wide detail tape of segments split by 3px double rules, each with an inverse title. Tables use dashed header rules, underline for the best row, thermal red rows for regressions, ink bars on paper-shade tracks, and dumbbells (hollow dot = baseline, filled dot = fine-tuned, red when it got worse). The loss chart is a single ink line over a faded raw trace on paper-shade gridlines with an inverse-print tooltip.

## Do's and Don'ts

### Do:
- **Do** put every result, measurement and generated artifact on thermal paper (paper on counter), set in Nanum Gothic Coding at 13.5px.
- **Do** measure paper in character cells: 42ch receipts, 2ch column gaps, 8ch meta keys, 2ch hanging indent for wrapped SQL.
- **Do** emphasise on paper only with double height (scaleY 2), inverse print (ink fill, paper text), 1.5px underline at 4px offset, or bold.
- **Do** reserve thermal red for VOID, errors and measured regressions; use soft thermal for the same meanings on the counter.
- **Do** show state by print form: dotted pending lines while waiting, strike-through for superseded SQL, solid vs dotted marks for right vs wrong.
- **Do** mark "selected" on the counter by switching the control to lit paper with ink type.
- **Do** separate paper sections with 1.5px dashed rules and totals with 3px double rules; connect items to values with dotted leaders.
- **Do** keep tabular figures on everywhere and keep an elapsed clock visible whenever a model is generating.

### Don't:
- **Don't** render a chat window: no message bubbles, avatars or typing indicators.
- **Don't** build a card dashboard: no shadowed, rounded cards in a grid; only paper floats.
- **Don't** round paper corners or give paper a border; its edges are straight sides and a zigzag tear.
- **Don't** use thermal red for wins, primary actions or decoration.
- **Don't** introduce a second hue or gradients; the palette is two neutral families plus thermal red.
- **Don't** emphasise on paper with larger font sizes or coloured highlights.
- **Don't** put shadows on counter controls; depth on the counter is tonal (counter, counter-2, counter-3).
