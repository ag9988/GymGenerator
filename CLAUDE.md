# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is a personal projects folder, not a software package. There is no build system, package manager, or test suite. Work here falls into three categories:

1. **Document projects** (`Tilka Resume/`) — `.docx`, `.pdf`, and `.pptx` files for resume and presentation work.
2. **Gym planning** (`gym planning/`) — Excel workout trackers and a standalone HTML web app.
3. **Travel planner** (`travel/travel-widget.html`) — A standalone HTML travel itinerary app that uses the Claude API for document scanning.

## Sync rule (critical)

After every edit to `gym planning/workout-generator.html`, copy it to both sync targets before committing:

```bash
cp "gym planning/workout-generator.html" "gym planning/index.html"
cp "gym planning/workout-generator.html" "index.html"
```

`workout-generator.html` is the source of truth. The other two are served copies.

## Gym Workout App (`gym planning/workout-generator.html`)

A zero-dependency, single-file HTML/CSS/JS app. No build step — open directly in a browser. Primary persistence is via `localStorage` key `gymgen-history` (JSON array of sessions). Optional iCloud file sync writes the same JSON array to a user-selected file via the File System Access API; the file handle is persisted across reloads via IndexedDB (`gymgen-sync` database, `store` object store, key `'fh'`). There is no server or shared state — each device is isolated unless the user explicitly configures sync.

### Architecture

Everything lives in one file in three logical sections:

**Data layer** (constants, defined before state):
- `EXERCISES` — keyed by `upper | lower | full`; each entry holds `sets` (per difficulty) and `reps` (per goal).
- `SWAPS` — keyed by exercise name; each entry has `{ similar: [ex, ex], easier: ex }`. Alternatives carry only `name`, `muscles`, `type` and inherit `sets`/`reps` from the replaced exercise.
- `CHART_COLORS` — 10-color palette used by the trends SVG, indexed by exercise position in `allEx`.
- `GOAL_PARAMS`, `TYPE_COUNTS`, `TYPE_NAMES` — lookup tables for generation logic.

**State variables:**
- `selectedType`, `selectedDiff`, `selectedGoal`, `selectedUnit` — user selections; `selectedUnit` defaults to `'lb'`.
- `currentPlan` — array of `{ exercise, sets[] }` where each set is `{ weight, reps, done }`.
- `swapTarget`, `_swapOptions` — ephemeral swap sheet state.
- `trendType`, `activeExSet` — trends panel state; `activeExSet` is a `Set` of exercise names to highlight (empty = show all).
- Timer state: `timerInterval`, `timerSeconds`, `timerRunning`, `timerMax`.
- `fileHandle` — active `FileSystemFileHandle` for iCloud sync (null if not set up); `_pendingHandle` — saved handle awaiting re-permission after page reload.

**Render pipeline:**
`generateWorkout()` → `renderPlan()` → `renderExercise()` → `renderSets(idx)`

Re-rendering a single exercise's sets (after add/delete/done toggle) goes through `renderSets(idx)` only, not the full pipeline.

**Init sequence** (bottom of `<script>`): `restoreSessionState()` → `renderTimer()` → `renderCalendar()` → `renderCycleCard()` → `renderLoadDashboard()` → `initFileSync()` → `generateAppIcon()`

### Key behaviors

- **History & persistence** — `localStorage` key `gymgen-history` is an array of session objects. Each session has `{ id, date, type, diff, goal, unit, exercises[] }`. `date` is stored as `toLocaleString()` output; `new Date(sess.date)` parses it back correctly in the same browser. `unit` is required for correct display and conversion of saved weights.
- **Weight pre-population** — `getPrevSession(exerciseName)` returns `{ sets, unit }` from the most recent matching session. `convertWeight(value, fromUnit, toUnit)` normalises across unit changes. Both `generateWorkout()` and `confirmSwap()` call these to pre-fill set weights.
- **Unit toggle** — `selectUnit()` converts all currently-entered weights in `currentPlan` in-place, then calls `renderPlan()`. The unit is written into each history session so old entries always display in their original unit.
- **Exercise swap** — the ⇄ button opens `.swap-modal` (bottom sheet) with 2 similar + 1 easier alternative from `SWAPS[exercise.name]`. `confirmSwap()` replaces the exercise, inherits volume params from the original, and pre-fills weights from history.
- **Compound-first ordering** — `generateWorkout()` separates compounds from isolations, shuffles each group independently, then merges.
- **Rest timer** — auto-starts when `toggleSetDone()` marks a set done.
- **Calendar** — `renderCalendar()` builds a 28-day grid starting on the Sunday 3 full weeks before the current week's Sunday (always a clean 4×7 layout). `dateKey(d)` returns `YYYY-MM-DD`. `getWorkoutDayMap()` groups history sessions by `dateKey`. Clicking a workout day calls `openDayDetail(d, sessions)` which opens the day detail bottom sheet. `renderCalendar()` is called on init and after `finishWorkout()`.
- **Trends** — `getVolumeByExercise(type)` filters history to sessions of `type`, computes per-exercise volume as `Σ(weight × reps)` across completed sets, and normalises to `selectedUnit` using `convertWeight`. `buildTrendSVG(data, showEx, allEx)` returns a raw SVG string rendered into `#trends-body`. Chart dots are `r="7"` for touch friendliness. On desktop, `onmouseenter`/`onmouseleave` trigger `showTrendTip` / `hideTrendTip`; on mobile, `ontouchstart` triggers `toggleTrendTip` which toggles the fixed-position `#trend-tooltip` div (z-index 400) and auto-hides it after 3 s. The trends panel is `560px` wide on desktop and `100%` on mobile (`≤ 600px`).
- **Portrait lock** — A `.rotate-msg` overlay div (fixed, z-index 9999, black background) is hidden by default and shown via `@media screen and (orientation: landscape) and (max-width: 1024px)`. It displays an animated tilting 📱 icon (`@keyframes tilt` ±20°). No JS is needed to show the overlay — it is pure CSS. However, returning to portrait triggers `location.reload()` via the `resize` listener to fix browser reflow corruption; the in-progress workout is preserved across that reload via `sessionStorage` (see below).
- **Orientation / session restore** — A `resize` listener tracks `_wasLandscape` (initialised from `window.innerWidth > window.innerHeight`). When the device enters landscape, `saveSessionState()` snapshots `{ currentPlan, selectedType, selectedDiff, selectedGoal, selectedUnit }` into `sessionStorage` key `gymgen-session`. When returning to portrait, `location.reload()` fires. On the reloaded page, `restoreSessionState()` (called first in init) reads `gymgen-session`, re-applies all state variables, re-syncs the pill/card UI **without** calling `selectUnit()` (which would double-convert weights), then calls `renderPlan()` if `currentPlan` is non-empty. The key is deleted from `sessionStorage` immediately after reading. Saved history in `localStorage` is never touched by this flow.
- **Export / Import** — `exportData()` downloads `gymgen-history.json` via a Blob URL. `importData(event)` reads the file, calls `mergeHistories(local, imported)` to deduplicate by session `id`, then writes via `saveHistory()`. `triggerImport()` opens the hidden `#import-file` input.
- **iCloud File Sync** — `saveHistory(h)` writes to both localStorage and the sync file (if `fileHandle` is set). On init, `initFileSync()` restores the handle from IndexedDB, calls `queryPermission` silently (no gesture required), and merges the file's history with localStorage if permission is already granted. If permission was lost (page reload), `updateSyncUI('reconnect')` shows a Reconnect button; tapping it calls `reconnectSync()` which calls `requestPermission` (requires user gesture). `mergeHistories(a, b)` deduplicates by `id` (Date.now()), sorted ascending. **iOS Safari does not support the File System Access API** (`showSaveFilePicker` / `showOpenFilePicker`) — the sync button is non-functional on mobile Safari; `updateSyncUI('unsupported')` handles this gracefully. The app must be hosted at an HTTP(S) URL (e.g. Netlify) for Safari on iOS to open it at all — local HTML files cannot be opened directly.
- **iOS Home Screen Icon** — `generateAppIcon()` draws a 180×180 canvas (black bg, subtle pink radial glow, "Dr.G" in `#ff2d55` at 68px bold, "G Y M" subtitle in muted white) and sets `<link rel="apple-touch-icon" id="app-icon">` href to the canvas data URL. Apple meta tags in `<head>` enable full-screen mode (`apple-mobile-web-app-capable`), set the home screen title to "Dr.G Gym", and use `black-translucent` status bar.
- **Training Load (LP)** — `calcLoadPoints(session)` checks `session.sessionLP` first (RPE-based and free sessions), then cardio formula (run: `miles×(12/pace)×10`; cycle: `miles×4`; hike: `(miles×0.6+elevFt/1500)×10`; swim: `meters/8`), then gym volume (`volLbs/500`). The load dashboard (`renderLoadDashboard()`) shows a 28-day bar chart and rolling avg. The trends Load tab (`buildLoadTrendSVG()`) shows daily/weekly LP bars with a 7-day rolling average polyline and a previous-period dashed reference line.
- **Free Workout** — `type: 'free'` sessions have no exercises. `startFreeSession()` starts a live elapsed timer. `endFreeSession()` opens `#free-end-modal` (RPE, optional HR, optional notes). LP = `durationMin × RPE / 4` stored as `session.sessionLP`. Session object: `{ type:'free', sessionLP, free:{ durationMin, rpe, avgHR, notes }, exercises:[] }`. The "Finish Workout & Save" button is hidden during free sessions — saving is done only via the end-session modal.
- **Breathwork** — `type: 'breathwork'` sessions have no exercises. `startBreathworkSession()` shows an animated breathing circle controlled by CSS `transform: scale()` transitions. Three patterns defined in `BREATHWORK_PATTERNS`: `box` (4-4-4-4), `478` (4-7-8), `sigh` (5-2-7). Each phase has `{ label, duration, toScale }`. A countdown timer runs via `setInterval` every 1s; phase advance via `setTimeout`. `_endBreathworkSession()` saves `{ type:'breathwork', sessionLP:0, free:{ durationMin, pattern, rounds }, exercises:[] }`. LP is always 0. The "Finish Workout & Save" button is hidden during breathwork — `_endBreathworkSession()` is triggered by an "End Session" button. `finishWorkout()` has a guard to early-return for both `free` and `breathwork` types.
- **Header layout** — The top bar has a `.header-actions` flex container with a `.header-stack` column of three small buttons (Data, PRs, History) on the left and a larger `.btn-trends-main` pink Trends button on the right. Data opens `.overflow-menu` (dropdown with Clear, Export, Import, iCloud Sync). Total width matches the main content area.
- **Retroactive migrations** — When a formula changes, add a new IIFE at the bottom of `<script>` gated by a versioned `localStorage` key (e.g. `'gymgen-cardio-lp-v3'`). The IIFE rewrites affected sessions in `gymgen-history` and sets the key so it only runs once per browser.
- **SVG icons** — All UI icons live in the `ICONS` constant (24×24 viewBox, `stroke-width:1.75`, `stroke-linecap/linejoin:round`, `fill:none`). `typeIcon(type)` returns the SVG string for a session type; falls back to `ICONS.bolt`. Do not use emoji in the DOM — emoji are reserved for canvas rendering only (`TYPE_NAMES[type].emoji`).

### Design system

The app uses an iOS dark-mode aesthetic. CSS variables (all in `:root`):

| Token | Value | Use |
|---|---|---|
| `--bg` | `#000000` | Page background |
| `--surface` | `#1c1c1e` | Cards, panels |
| `--surface2` | `#2c2c2e` | Inputs, secondary fills |
| `--surface3` | `#3a3a3c` | Hover states |
| `--sep` | `rgba(84,84,88,0.65)` | Hairline separators |
| `--accent` | `#ff2d55` | iOS hot pink — primary actions, active states |
| `--text2` | `rgba(235,235,245,0.6)` | Secondary labels |
| `--text3` | `rgba(235,235,245,0.3)` | Tertiary / disabled |
| `--green` | `#32d74b` | iOS green — completed states, calendar highlights |
| `--blue` | `#0a84ff` | Compound exercise tags |
| `--red` | `#ff453a` | Destructive actions |

There are no `--border`, `--muted`, or `--accent2` tokens — do not use them. Borders are replaced by background-tone differentiation and `var(--sep)` hairlines. Spring easing `cubic-bezier(0.34,1.56,0.64,1)` is used for interactive scale transforms; `cubic-bezier(0.25,0.46,0.45,0.94)` for directional transitions.

### Session types

| `type` | Generator | LP source |
|---|---|---|
| `upper`, `lower`, `full` | Random compound-first from `EXERCISES[type]` | gym volume formula |
| `group_a`, `group_b`, `group_c` | Fixed lists from `EXERCISES.group_a/b/c` | gym volume formula |
| `run`, `cycle`, `hike`, `swim` | Cardio log modal; `CARDIO_TYPES` set | cardio formula in `calcLoadPoints` |
| `free` | Live timer; no exercises | `session.sessionLP` = `durationMin × RPE / 4` |
| `breathwork` | Animated breathing circle; pattern picker | `session.sessionLP` = 0 |

`isCardio(type)` returns true for the four cardio types. `free` and `breathwork` always have `session.sessionLP` set (0 for breathwork), so they skip the gym volume branch in `calcLoadPoints`. `generateWorkout()` early-returns for both: `startFreeSession()` / `startBreathworkSession()`. `finishWorkout()` has a guard that returns immediately for `free` and `breathwork`.

### Extending exercises

Add entries to `EXERCISES.upper`, `EXERCISES.lower`, or `EXERCISES.full`:

```js
{
  name: 'Exercise Name',
  muscles: 'Primary, Secondary',
  type: 'compound' | 'isolation',
  sets: { beginner: 3, intermediate: 4, advanced: 5 },
  reps: { strength: '4-6', hypertrophy: '8-12', endurance: '15-20' },
}
```

Then add a corresponding `SWAPS` entry (required for the swap sheet):

```js
'Exercise Name': {
  similar: [
    { name: '...', muscles: '...', type: 'compound' },
    { name: '...', muscles: '...', type: 'compound' },
  ],
  easier: { name: '...', muscles: '...', type: 'compound' },
},
```

## Travel Widget (`travel/travel-widget.html`)

A zero-dependency, single-file HTML/CSS/JS app. No build step — open directly in a browser. Shares the same iOS dark-mode design system as the gym app (same CSS variables, same component patterns).

### Persistence

- `localStorage` key `tripgen-data` — `{ trips: [] }` where each trip has `{ id, name, startDate, endDate, items[] }`.
- Each item has `{ id, type, date, time, notes, ...type-specific fields }`.
- No iCloud sync; no IndexedDB.

### Architecture

Two screens (home → trip) animated with CSS `translateX`. All UI is rendered into sheet overlays (bottom sheets) — one per function: `sheet-new-trip`, `sheet-category`, `sheet-add-item`, `sheet-detail`, `sheet-scan-review`.

**Item types:** `flight`, `hotel`, `restaurant`, `sight`, `appointment`, `insurance`, `visa`. Each has a dedicated set of fields rendered in `_renderItemSheet()` and displayed in `_renderDetailSheet()`. `itemName()` and `itemSub()` derive the timeline display strings from whichever fields are populated.

**PDF attachments:** stored as base64 in `item.pdfData`; viewable via `viewAttachedPdf()`. Capped at 4 MB.

### Claude API integration (document scanner)

The **Scan** button (trip screen header) accepts `.pdf`, `.ics`, `.html`, `.eml`, `.txt` files and sends them to the Anthropic API for extraction.

- **Config:** `CLAUDE_API_KEY` and `CLAUDE_MODEL` constants at the top of the `<script>` block. The key is hardcoded — treat the file as a secret.
- **Flow:** `triggerScan()` → `handleFiles()` → `_parseWithClaude()` → `_renderScanReview()` → `addSelectedScanItems()`.
- **PDFs** are sent as `type: "document"` with base64 source. **All other files** are stripped of HTML tags then sent as `type: "text"`.
- `_parseWithClaude()` calls `POST /v1/messages`, strips any markdown code fences from the response, and JSON-parses the result into an array of item objects matching the schema above.
- The `_CLAUDE_PROMPT` constant defines the extraction schema; update it if adding new item types or fields.
- Errors surface via `toast()` — the catch block is intentionally not silent.

### Design system

Identical tokens to the gym app. Do not add `--border`, `--muted`, or `--accent2` — they don't exist. Use `var(--sep)` for hairlines and background-tone differentiation instead of borders.

## Amyzing Ankitures (`index.html` in amyzing-ankitures repo)

A zero-dependency, single-file HTML/CSS/JS app for shared list management across two iPhones. Deployed to GitHub Pages at `https://ag9988.github.io/amyzing-ankitures/`. Primary persistence is `localStorage`; optional iCloud file sync via File System Access API.

### Architecture

One HTML file with three logical sections:

**Data layer:**
- `CATEGORIES` — object mapping category keys to emoji + labels (`restaurants`, `hikes`, `things`, `events`).
- Item schema: `{ id, category, name, notes, date, time, done, timestamp }`.
- `date` format: `YYYY-MM-DD` (HTML5 date input).
- `time` format: `HH:MM` (HTML5 time input).

**State variables:**
- `selectedCategory` — currently active category pill.
- `items` — array of all items (all categories).
- `fileHandle` — active `FileSystemFileHandle` for iCloud sync (null if not set up).
- `_pendingHandle` — saved handle awaiting permission re-grant after page reload.
- `_wasLandscape` — orientation tracking for session restore.

**Render pipeline:**
`renderItems()` → filter by `selectedCategory` → display in list, optionally showing date/time and iCal download button.

**Init sequence:** `restoreSessionState()` → `renderItems()` → `setupEventListeners()` → `setupMenuButton()` → `initFileSync()` → `generateAppIcon()` → `setupOrientationListener()` → `updateSyncUI()`.

### Key behaviors

- **Persistence** — `localStorage` key `shared-list-data` holds JSON array of all items (all categories, all statuses). Timestamp on each item for conflict resolution during sync.
- **Categories** — Four mutually exclusive categories via pill buttons. Only one active at a time. Category is immutable once item is created.
- **Dates and times** — Optional. Date field uses native iOS date picker (no custom calendar). Time field is independent of date. Both stored as strings in item.
- **iCal export per item** — Items with dates show a 📅 button. Clicking calls `downloadIcal(itemId)`, which generates a `.ics` file with item name, date/time, notes, and category. File downloads immediately.
- **iCal export (all events)** — Menu → "📅 Export iCal (All Events)" generates one `.ics` file containing all items with dates across all categories. Named with today's date: `amyzing-ankitures-events-YYYY-MM-DD.ics`.
- **iCloud File Sync** — Mirrors gym app: `initFileSync()` restores handle from IndexedDB, merges iCloud file with localStorage on init. `saveData()` writes to both. `mergeHistories()` deduplicates by `id`. On iOS Safari, show `updateSyncUI('unsupported')`. User must share an iCloud Drive folder between both users, then both tap Menu → iCloud Sync and pick the same file.
- **Menu button** — Three-dot icon in top-right. Uses direct `onclick` handler (not `addEventListener`), set in `setupMenuButton()`. Toggles `.menu-dropdown.active` class. Menu items: Export Data (JSON), Export iCal (all events), Import Data, iCloud Sync, Clear All.
- **Category pill styling** — Active pill is `--accent` (#ff006e, hot pink). Inactive pills are `--surface2` (dark purple). Horizontal scroll if needed.
- **Item list** — Checkbox (unchecked = not done, green ✓ = done, grayed out). Item name (strikethrough if done). Date in cyan if present: "📅 Aug 15, 2026 at 19:30". Notes in smaller text. Delete button (×). iCal download button (📅) if date exists.
- **Orientation handling** — Same as gym app: landscape triggers `saveSessionState()` to `sessionStorage` key `shared-list-session`, then `location.reload()` on portrait return. `restoreSessionState()` re-applies category selection without re-rendering.
- **Miami Vice theme** — Dark purple background (`#0a0e27`), hot pink accents (`--accent: #ff006e`), cyan highlights (`--cyan: #00d9ff`), purple secondary accents (`--accent2: #9d4edd`), orange tertiary (`--accent3: #ff6b35`).

### Design system

**Miami Vice color palette** (different from gym/travel apps):

| Token | Value | Use |
|---|---|---|
| `--bg` | `#0a0e27` | Page background (dark purple) |
| `--surface` | `#1a1a3e` | Cards, panels |
| `--surface2` | `#2d1b4e` | Inputs, secondary fills |
| `--surface3` | `#3d2b5e` | Hover states |
| `--sep` | `rgba(255,107,211,0.2)` | Hairline separators (pink-tinted) |
| `--accent` | `#ff006e` | Hot pink — primary actions, active pills |
| `--accent2` | `#9d4edd` | Purple — secondary accents, today indicator |
| `--accent3` | `#ff6b35` | Orange — tertiary accents |
| `--cyan` | `#00d9ff` | Cyan — date/time text, weekday labels |
| `--text` | `#ebebf5` | Primary text |
| `--text2` | `rgba(235,235,245,0.6)` | Secondary labels |
| `--text3` | `rgba(235,235,245,0.3)` | Tertiary / disabled |
| `--green` | `#32d74b` | Completed states (checkbox) |
| `--red` | `#ff453a` | Destructive actions (delete) |

Uses spring easing `cubic-bezier(0.34,1.56,0.64,1)` for interactive transforms.
