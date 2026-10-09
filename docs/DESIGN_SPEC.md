# PACE design specification

## Palette and tokens

| Token | Light | Dark | Purpose |
|---|---|---|---|
| `--canvas` | `#f7f8fa` | `#0e131d` | Page background |
| `--surface` | `#ffffff` | `#161e2b` | Panels/cards |
| `--surface-alt` | `#f0f2f6` | `#202a3a` | Quiet interactive background |
| `--text` | `#172233` | `#eff3fa` | Primary text |
| `--muted` | `#566579` | `#b0bbcc` | Secondary text |
| `--accent` | `#2359b8` | `#87adff` | One primary interactive accent |
| `--accent-weak` | `#eaf1ff` | `#20345a` | Selected state surface |
| `--border` | `#dce1e9` | `#354155` | Dividers and controls |

Primary body text and muted body text exceed WCAG AA normal-text contrast against the main card surface by numeric calculation. This does **not** constitute a completed WCAG audit of every visual state, graphic, tooltip, disabled control or responsive view.

## Typography

A system UI font stack, with Inter as the first optional installed font; no external font download or tracking request. Headings have tight tracking and moderate weights (700–750); labels 11–13px; body text 14px with ~1.8 line-height where readability matters.

## Spacing, radius, elevation

4px increments around an 8px base: 4, 8, 12, 16, 24, 32, 48px. Radius tokens 7px, 11px, 16px. Borders are 1px and shadows are minimal. No gradients used for background decoration; skeleton loading shimmer is the only animated gradient.

## Component library

Complete implementations reside in `frontend/src/components/ui.jsx`: `Button`, `Input`, `Card`, `Tabs`, `Modal`, `Toast`, `Skeleton`, `Badge`, `Tooltip`. Lucide is the icon library. `ThemeContext.jsx` persists the setting and supports system preference detection.

## Layout and accessibility

Left navigation for Coding/Literacy/Research, central conversation and composer, optional host telemetry card, settings modal, mobile drawer. All primary controls are native semantic elements with visible focus, dialog keyboard handling, labels, and reduced-motion CSS. Chat uses polite ARIA live logging. No claims of screenshot, browser, screen-reader, or contrast-validation coverage beyond code inspection and token checks.

## UX states

API connecting, waking, unavailable; model unavailable/quota exhausted; upload progress; uploaded document ready; chat empty/loading/streaming; session history loading; telemetry unavailable; retry connection; mutation toasts. The hosted fast-mode service yields incremental actual model output through a Gradio generator; the API forwards the deltas over SSE. Hosted Review mode buffers the first pass and yields the final revised answer only. Local actor-only mode streams output; local independent-critic Review returns a completed revision.
