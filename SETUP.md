# Animated Profile README System

A stack of animated, editorial SVG cards for Siddhant Satote's GitHub profile (`siddhantsatote/siddhantsatote`).

Inspired by modern high-contrast editorial typography (Instrument Serif and Space Mono), with vector halftone scanlines, interactive cards, dynamic contribution analytics, and daily GitHub Action automation.

---

## 🗂 Architecture

```
├── .github/
│   └── workflows/
│       └── update-cards.yml       # Daily GitHub Action workflow (06:17 UTC)
├── cards/
│   ├── hero.svg                   # Hero banner: name, bio, site, vector halftone portrait
│   ├── tile-build.svg             # Linked tile 1: Build (40+ repos) [32.5% width]
│   ├── tile-lead.svg              # Linked tile 2: Lead (AtherHacks) [32.5% width]
│   ├── tile-explore.svg           # Linked tile 3: Systems (AI & Avionics) [32.5% width]
│   ├── contributions-chart.svg    # 12-Month bar chart with streak & active days stats
│   ├── repo-trucktalk.svg         # Featured repo: TruckTalk AI
│   ├── repo-codesentinel.svg      # Featured repo: Code Sentinel
│   ├── repo-soulspace.svg         # Featured repo: SoulSpace
│   └── contrib-graph.svg          # 52-Week contribution graph in brand electric blue
├── data/
│   └── contributions.json         # Cached contribution data refreshed by the Action
├── fonts/
│   ├── InstrumentSerif-Regular.ttf
│   ├── InstrumentSerif-Italic.ttf
│   └── SpaceMono-Regular.ttf
├── scripts/
│   └── generate_cards.py          # Unified Python script generating all cards
├── requirements.txt               # Dependencies: fonttools, brotli, pillow, requests
└── README.md                      # GitHub profile entry point
```

---

## 🚀 Local Generation & Commands

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Render Cards (Animated)
```bash
python scripts/generate_cards.py
```

### 3. Fetch Fresh Data & Render
```bash
python scripts/generate_cards.py --fetch
```

### 4. STATIC Mode (Screenshot / Preview Frame)
```bash
# Windows PowerShell
$env:STATIC="1"; python scripts/generate_cards.py; Remove-Item Env:STATIC

# Linux / macOS
STATIC=1 python scripts/generate_cards.py
```
In `STATIC=1` mode, all CSS keyframes and delays are suppressed, rendering the crisp final frame immediately for screenshotting or static viewing.

---

## ⚙️ Features & Specifications

- **Compatibility with GitHub `<img>` Tags**: Cards are embedded via `<img>` tags. All fonts are dynamically subsetted using `pyftsubset` (`fonttools`) and embedded inline as base64 WOFF data URIs. No external web font requests are blocked.
- **Top-to-Bottom Staggered Cascade**: Delays cascade seamlessly from the hero card down through the tiles, monthly charts, featured repositories, and contribution heatmap.
- **Accessibility & Reduced Motion**: Automatically disables animations under `@media (prefers-reduced-motion: reduce)`.
- **Automated Daily Sync**: `.github/workflows/update-cards.yml` fetches latest commit counts daily at 06:17 UTC, recalculates monthly totals and streaks, and commits refreshed SVGs.
