# CLAUDE.md

## Project Overview

**직장 선택 OS (Job Choice OS)** — A Korean-language single-page web application for comparing job offers across multiple criteria including compensation, work-life balance, job security, career growth, benefits, and company brand value.

- **Tech stack**: Vanilla HTML/CSS/JavaScript (no frameworks, no build tools)
- **Architecture**: Single-file monolithic SPA (`index.html`, ~1,289 lines)
- **Backend**: None — fully client-side
- **Language**: Korean UI with English variable/function names

## File Structure

```
/
├── index.html    # Entire application (HTML + CSS + JS)
└── CLAUDE.md     # This file
```

Everything lives in `index.html`. There is no `package.json`, build system, or test framework.

## Running the App

Open `index.html` directly in a browser. No server or build step required.

## Code Organization

The file is organized into sections delimited by ASCII comment headers:

```
// ━━ LANDING ━━       Landing page styles and layout
// ━━ SHARED ━━        Shared CSS utilities
// ━━ PROFILER ━━      Career value assessment questionnaire
// ━━ SEARCH ━━        Company search and selection
// ━━ BENEFITS ━━      Benefits configuration and calculation
// ━━ WORK STYLE ━━    Work arrangement (overtime, remote, flex)
// ━━ PRIORITY ━━      Priority and sacrifice selection
// ━━ COMPARE ENGINE ━━ Core comparison and report generation
// ━━ INIT ━━          Application initialization
```

Structure within `index.html`:
1. `<head>` — Meta tags, CDN font links, `<style>` block with all CSS
2. `<body>` — HTML markup for all screens (landing, profiler, input, report)
3. `<script>` — All JavaScript at the bottom

## Naming Conventions

| Type | Convention | Examples |
|------|-----------|----------|
| Variables | camelCase (often abbreviated) | `pfJob`, `wsState`, `curPri`, `benS` |
| Functions | camelCase | `doSearch()`, `compare()`, `calc()`, `renderBen()` |
| Constants | UPPER_SNAKE_CASE | `DIMS`, `OT_HRS`, `DB`, `PRIORITIES` |
| CSS classes | kebab-case (often abbreviated) | `.pf-intro`, `.ws-btn`, `.vs-card` |
| Data attributes | Short keys | `data-v`, `data-k`, `data-jid` |
| DOM IDs | camelCase or short codes | `sA`, `sB`, `tA`, `tB`, `blA`, `blB` |

Side convention: `a` = current job (현직), `b` = new job offer (이직처).

## Key Data Structures

```javascript
// 6 career value dimensions
const DIMS = ["compensation", "security", "growth", "autonomy", "impact", "flexibility"]

// Company database entries
const DB = [{ id, name, type, logo, industry, aliases, benefits, workStyle }]

// Work style state per side
const wsState = { a: { ot, wage, remote, flex }, b: { ot, wage, remote, flex } }

// Benefits per side
const benS = { a: [{ key, name, val, cat, badge, checked }], b: [...] }
```

## Key Functions

- `compare()` — Main report generation (~300 lines). Builds HTML for verdict cards, salary comparison, hourly value, WLB, 3-year projection, and bottom line.
- `calc()` — Real-time summary calculation triggered on any input change.
- `doSearch(s)` / `selComp(s, id)` — Company search and selection from DB.
- `renderBen(s)` — Render benefits list for a side.
- `setWS(s, key, val)` — Update work style state.
- `getWSHours(s)` / `getOTPay(s)` — Calculate weekly hours and overtime pay.
- `go(screenId)` — Screen navigation (SPA routing).

## Styling

- CSS custom properties for theming (dark theme): `--bg-0` through `--bg-4`, `--t1` through `--t4`
- Color accents: `--blue`, `--amber`, `--green`, `--red`, `--purple`, `--gold` (each with a `-d` dim variant)
- Responsive breakpoint: `@media(max-width:480px)`
- Animations: `fadeUp`, `slideUp` with `cubic-bezier` easing
- Fonts: Pretendard (Korean sans-serif), JetBrains Mono (numbers)

## External Dependencies (CDN)

- **Pretendard font**: `cdn.jsdelivr.net/gh/orioncactus/pretendard/...`
- **JetBrains Mono**: `fonts.googleapis.com`

No JavaScript libraries are used.

## Development Guidelines

- **Single-file constraint**: All changes go into `index.html`. Do not split into separate files without explicit request.
- **No build tools**: Changes are immediately testable by refreshing the browser.
- **Compact code style**: The codebase uses a compact/minified inline style. Match existing density when adding code — avoid verbose formatting.
- **Korean UI text**: All user-facing strings are in Korean. Variable names and comments are in English.
- **State is global**: Variables like `wsState`, `benS`, `matched`, `curPri`, `curSacrifice`, `pfResult` are global. No module system.
- **DOM updates via innerHTML**: Rendering is done by building HTML strings and assigning to `innerHTML`. Event handlers use inline `onclick`.
- **Side pattern**: Functions that operate on one job side take `s` parameter (`'a'` or `'b'`). DOM IDs follow patterns like `sA`/`sB`, `tA`/`tB`.
- **No tests**: There is no test framework. Verify changes manually in the browser.
- **Bug fix comments**: Recent fixes are annotated with `// [FIX]` comments explaining the correction.

## Common Pitfalls

- Variable shadowing in long functions (e.g., `compare()` is ~300 lines with many local variables)
- The `compare()` function validates inputs at the top — ensure new comparison logic has proper null/undefined checks
- Benefits use both `val` (numeric) and `checked` (boolean) — always check both when summing
- Overtime pay calculation differs between `'inclusive'` (포괄임금) and `'separate'` (비포괄) wage types
- Company type (`large`, `startup`, `mid`, `foreign`, `public`, `freelance`) affects stability scores, growth rates, and benefit presets
