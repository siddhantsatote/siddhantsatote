#!/usr/bin/env python3
"""
generate_cards.py
Redesigns GitHub Profile README as a stack of animated SVG cards.
Matches aesthetic: Warm stone off-white cards, Instrument Serif & Space Mono typography,
scanline halftone vector portrait, and vibrant electric blue brand accents.
"""

import os
import sys
import json
import base64
import io
import re
import html
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from collections import defaultdict
from fontTools import subset

# -----------------------------------------------------------------------------
# Configuration & Flags
# -----------------------------------------------------------------------------
STATIC_MODE = os.environ.get("STATIC", "").strip() in ("1", "true", "True") or "--static" in sys.argv
USERNAME = os.environ.get("GITHUB_USER", "siddhantsatote")

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cards")
DATA_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "contributions.json")
FONTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "fonts")
ASCII_SOURCE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "siddh-ascii.svg")

# Ensure directories exist
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
os.makedirs(FONTS_DIR, exist_ok=True)

def xml_esc(val) -> str:
    """Safely escapes text for inclusion inside XML elements and attributes."""
    if val is None:
        return ""
    return html.escape(str(val), quote=True)

# -----------------------------------------------------------------------------
# Font Management & pyftsubset Subsetting
# -----------------------------------------------------------------------------
FONT_URLS = {
    "InstrumentSerif-Regular.ttf": "https://raw.githubusercontent.com/google/fonts/main/ofl/instrumentserif/InstrumentSerif-Regular.ttf",
    "InstrumentSerif-Italic.ttf": "https://raw.githubusercontent.com/google/fonts/main/ofl/instrumentserif/InstrumentSerif-Italic.ttf",
    "SpaceMono-Regular.ttf": "https://raw.githubusercontent.com/google/fonts/main/ofl/spacemono/SpaceMono-Regular.ttf",
}

def ensure_master_fonts():
    """Ensure master TrueType fonts are downloaded."""
    import urllib.request
    for fname, url in FONT_URLS.items():
        dest = os.path.join(FONTS_DIR, fname)
        if not os.path.exists(dest):
            print(f"Downloading master font {fname}...")
            urllib.request.urlretrieve(url, dest)

def subset_to_woff_b64(font_filename: str, chars: str) -> str:
    """Subset a font to only the given raw characters and return as base64 WOFF."""
    font_path = os.path.join(FONTS_DIR, font_filename)
    if not os.path.exists(font_path):
        ensure_master_fonts()

    options = subset.Options()
    options.flavor = "woff"
    options.hinting = False
    options.desubroutinize = True
    options.drop_tables += ["name", "OS/2"]

    # Deduplicate raw chars & ensure basic whitespace and punctuation
    unique_text = "".join(sorted(set(chars + " 0123456789.,:-/&→↗•★")))

    font = subset.load_font(font_path, options)
    subsetter = subset.Subsetter(options=options)
    subsetter.populate(text=unique_text)
    subsetter.subset(font)

    buf = io.BytesIO()
    font.save(buf)
    return base64.b64encode(buf.getvalue()).decode("ascii")

# -----------------------------------------------------------------------------
# Data Loading & Statistics
# -----------------------------------------------------------------------------
def load_contributions():
    """Load contributions from data/contributions.json or fetch if missing."""
    if not os.path.exists(DATA_FILE) or "--fetch" in sys.argv:
        print("Fetching fresh contribution data...")
        import urllib.request
        url = f"https://github-contributions-api.jogruber.de/v4/{USERNAME}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    else:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

    conts = data.get("contributions", [])
    if not conts:
        raise ValueError("No contributions found in data file.")

    # Calculate metrics
    sorted_conts = sorted(conts, key=lambda x: x["date"])
    dates = [c["date"] for c in sorted_conts]
    latest_dt = datetime.strptime(max(dates), "%Y-%m-%d").date()
    one_year_ago = latest_dt - timedelta(days=365)

    last_365 = [c for c in sorted_conts if datetime.strptime(c["date"], "%Y-%m-%d").date() >= one_year_ago]
    total_365 = sum(c["count"] for c in last_365)
    active_days = sum(1 for c in last_365 if c["count"] > 0)
    busiest_day_entry = max(last_365, key=lambda x: x["count"])
    busiest_count = busiest_day_entry["count"]
    busiest_date = datetime.strptime(busiest_day_entry["date"], "%Y-%m-%d").strftime("%b %d, %Y")

    # Streaks
    longest_streak = 0
    curr_streak = 0
    streak = 0
    for c in sorted_conts:
        if c["count"] > 0:
            streak += 1
            longest_streak = max(longest_streak, streak)
        else:
            streak = 0

    c_streak = 0
    for c in reversed(sorted_conts):
        if c["count"] > 0:
            c_streak += 1
        elif c["date"] == str(latest_dt) and c["count"] == 0:
            continue
        else:
            break
    curr_streak = c_streak

    # Monthly breakdown for the last 12 months
    monthly = defaultdict(int)
    for c in last_365:
        m_key = c["date"][:7] # YYYY-MM
        monthly[m_key] += c["count"]

    # Guarantee 12 months sorted
    month_keys = sorted(monthly.keys())
    if len(month_keys) > 12:
        month_keys = month_keys[-12:]

    monthly_stats = []
    month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    for mk in month_keys:
        dt = datetime.strptime(mk + "-01", "%Y-%m-%d")
        monthly_stats.append({
            "key": mk,
            "label": month_names[dt.month - 1],
            "count": monthly[mk],
            "is_current": (mk == latest_dt.strftime("%Y-%m"))
        })

    max_month = max((m["count"] for m in monthly_stats), default=1)

    return {
        "raw_contributions": sorted_conts,
        "last_365": last_365,
        "total_365": total_365,
        "active_days": active_days,
        "total_days": len(last_365),
        "busiest_count": busiest_count,
        "busiest_date": busiest_date,
        "longest_streak": longest_streak,
        "current_streak": curr_streak,
        "monthly_stats": monthly_stats,
        "max_month": max_month,
        "latest_dt": latest_dt
    }

# -----------------------------------------------------------------------------
# Scanline Halftone Portrait Generator
# -----------------------------------------------------------------------------
def generate_scanline_portrait(start_x=530, start_y=55, target_w=340, target_h=310):
    """
    Renders a horizontal scanline vector portrait
    from the pre-masked ASCII density matrix, matching the halftone aesthetic.
    """
    if not os.path.exists(ASCII_SOURCE):
        return "", ""

    with open(ASCII_SOURCE, "r", encoding="utf-8") as f:
        content = f.read()

    lines = re.findall(r"<text[^>]*>(.*?)</text>", content)
    if not lines:
        return "", ""

    # Density mapping
    def get_cls(ch):
        if ch in "`.:-=": return 1
        if ch in "+*c": return 2
        if ch in "s#": return 3
        if ch in "%@": return 4
        return 0

    cols = len(lines[0])
    rows = len(lines)
    char_w = target_w / cols
    line_h = target_h / rows

    paths = {1: [], 2: [], 3: [], 4: []}

    for r, line in enumerate(lines):
        y = start_y + r * line_h
        c_start = None
        curr_cls = 0
        for c, ch in enumerate(line):
            cls = get_cls(ch)
            if cls != curr_cls:
                if curr_cls > 0:
                    x1 = start_x + c_start * char_w
                    x2 = start_x + c * char_w
                    paths[curr_cls].append(f"M{x1:.1f} {y:.1f}H{x2:.1f}")
                curr_cls = cls
                c_start = c
        if curr_cls > 0:
            x1 = start_x + c_start * char_w
            x2 = start_x + len(line) * char_w
            paths[curr_cls].append(f"M{x1:.1f} {y:.1f}H{x2:.1f}")

    d1 = " ".join(paths[1])
    d2 = " ".join(paths[2])
    d3 = " ".join(paths[3])
    d4 = " ".join(paths[4])

    if STATIC_MODE:
        anim_css = ""
    else:
        anim_css = """
        .p-l1 { animation: pFade 0.8s cubic-bezier(0.16,1,0.3,1) 0.3s forwards; }
        .p-l2 { animation: pFade 0.8s cubic-bezier(0.16,1,0.3,1) 0.4s forwards; }
        .p-l3 { animation: pFade 0.8s cubic-bezier(0.16,1,0.3,1) 0.5s forwards; }
        .p-l4 { animation: pFade 0.8s cubic-bezier(0.16,1,0.3,1) 0.6s forwards; }
        @keyframes pFade { from { opacity: 0; } to { opacity: 1; } }
        """

    opacity1 = "1" if STATIC_MODE else "0"
    opacity2 = "1" if STATIC_MODE else "0"
    opacity3 = "1" if STATIC_MODE else "0"
    opacity4 = "1" if STATIC_MODE else "0"

    svg_markup = f"""
    <g stroke="#6e6e6a" stroke-linecap="round">
      <path class="p-l1" d="{d1}" stroke-width="1.0" opacity="{0.55 if STATIC_MODE else opacity1}" />
      <path class="p-l2" d="{d2}" stroke-width="1.8" opacity="{0.75 if STATIC_MODE else opacity2}" />
      <path class="p-l3" d="{d3}" stroke-width="2.8" opacity="{0.90 if STATIC_MODE else opacity3}" />
      <path class="p-l4" d="{d4}" stroke-width="3.8" opacity="{1.00 if STATIC_MODE else opacity4}" />
    </g>
    """
    return svg_markup, anim_css

# -----------------------------------------------------------------------------
# Card Renderers
# -----------------------------------------------------------------------------

def render_hero_card():
    """Card 1: Hero Card with Name, Role Pill, Bio, Link, and Scanline Portrait."""
    portrait_svg, portrait_css = generate_scanline_portrait(start_x=545, start_y=55, target_w=330, target_h=310)

    # Raw text content to subset
    mono_raw = "■ FULL-STACK & AI SYSTEMS BUILDER siddhantsatote.github.io ↗"
    serif_raw = "Siddhant Satote"

    mono_b64 = subset_to_woff_b64("SpaceMono-Regular.ttf", mono_raw)
    serif_b64 = subset_to_woff_b64("InstrumentSerif-Regular.ttf", serif_raw)
    italic_b64 = subset_to_woff_b64("InstrumentSerif-Italic.ttf", serif_raw)

    if STATIC_MODE:
        anim_css = ""
        eyebrow_anim = ""
        name_anim = ""
        name2_anim = ""
        bio_anim = ""
        link_anim = ""
    else:
        anim_css = f"""
        @keyframes fadeUp {{
          0% {{ opacity: 0; transform: translateY(14px); }}
          100% {{ opacity: 1; transform: translateY(0); }}
        }}
        .eyebrow {{ opacity: 0; animation: fadeUp 0.6s cubic-bezier(0.16, 1, 0.3, 1) 0.1s forwards; }}
        .title-1 {{ opacity: 0; animation: fadeUp 0.7s cubic-bezier(0.16, 1, 0.3, 1) 0.25s forwards; }}
        .title-2 {{ opacity: 0; animation: fadeUp 0.7s cubic-bezier(0.16, 1, 0.3, 1) 0.35s forwards; }}
        .bio     {{ opacity: 0; animation: fadeUp 0.7s cubic-bezier(0.16, 1, 0.3, 1) 0.45s forwards; }}
        .link    {{ opacity: 0; animation: fadeUp 0.7s cubic-bezier(0.16, 1, 0.3, 1) 0.55s forwards; }}
        {portrait_css}
        """
        eyebrow_anim = 'class="eyebrow"'
        name_anim = 'class="title-1"'
        name2_anim = 'class="title-2"'
        bio_anim = 'class="bio"'
        link_anim = 'class="link"'

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 920 420" width="920" height="420">
  <defs>
    <style>
      @font-face {{
        font-family: 'Space Mono';
        src: url('data:font/woff;charset=utf-8;base64,{mono_b64}') format('woff');
        font-weight: 400;
        font-style: normal;
      }}
      @font-face {{
        font-family: 'Instrument Serif';
        src: url('data:font/woff;charset=utf-8;base64,{serif_b64}') format('woff');
        font-weight: 400;
        font-style: normal;
      }}
      @font-face {{
        font-family: 'Instrument Serif Italic';
        src: url('data:font/woff;charset=utf-8;base64,{italic_b64}') format('woff');
        font-weight: 400;
        font-style: italic;
      }}
      {anim_css}
      @media (prefers-reduced-motion: reduce) {{
        *, .eyebrow, .title-1, .title-2, .bio, .link, .p-l1, .p-l2, .p-l3, .p-l4 {{
          animation: none !important;
          opacity: 1 !important;
          transform: none !important;
        }}
      }}
    </style>
  </defs>

  <!-- Card Container Background -->
  <rect x="1" y="1" width="918" height="418" rx="24" fill="#f6f6f4" stroke="#e3e3de" stroke-width="1.5"/>

  <!-- Eyebrow Pill -->
  <g {eyebrow_anim}>
    <rect x="48" y="52" width="9" height="9" rx="2" fill="#2b5cff"/>
    <text x="68" y="60" font-family="'Space Mono', monospace" font-size="11" font-weight="700" letter-spacing="1.8" fill="#6b7280">{xml_esc('FULL-STACK & AI SYSTEMS ENGINEER')}</text>
  </g>

  <!-- Name Headline -->
  <g>
    <text x="48" y="165" {name_anim} font-family="'Instrument Serif', serif" font-size="88" fill="#111110" font-weight="400">Siddhant</text>
    <text x="48" y="248" {name2_anim} font-family="'Instrument Serif Italic', 'Instrument Serif', serif" font-style="italic" font-size="88" fill="#111110" font-weight="400">Satote</text>
  </g>

  <!-- Bio One-liner -->
  <g {bio_anim}>
    <text x="48" y="306" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif" font-size="16" fill="#4b5563">I build AI products, full-stack software,</text>
    <text x="48" y="332" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif" font-size="16" fill="#4b5563">and lead hackathon communities.</text>
  </g>

  <!-- Website Link with Arrow -->
  <g {link_anim}>
    <text x="48" y="378" font-family="'Space Mono', monospace" font-size="13" font-weight="500" fill="#2b5cff">siddhantsatote.github.io &#x2197;</text>
  </g>

  <!-- Halftone Scanline Portrait -->
  {portrait_svg}
</svg>"""
    return svg

def render_tile(category: str, headline: str, description: str, bg_color: str, text_color: str, arrow_color: str, delay_s: float):
    """Renders one of the three colored linked tiles (380x340)."""
    # Raw texts for font subsetting
    mono_raw = f"{category} → ↗"
    italic_raw = headline

    mono_b64 = subset_to_woff_b64("SpaceMono-Regular.ttf", mono_raw)
    italic_b64 = subset_to_woff_b64("InstrumentSerif-Italic.ttf", italic_raw)

    if STATIC_MODE:
        anim_css = ""
        elem_anim = ""
    else:
        anim_css = f"""
        @keyframes tileEntrance {{
          0% {{ opacity: 0; transform: translateY(16px); }}
          100% {{ opacity: 1; transform: translateY(0); }}
        }}
        .tile-content {{ opacity: 0; animation: tileEntrance 0.7s cubic-bezier(0.16, 1, 0.3, 1) {delay_s:.2f}s forwards; }}
        """
        elem_anim = 'class="tile-content"'

    # Split description into lines cleanly
    words = description.split(" ")
    lines = []
    curr = []
    for w in words:
        if len(" ".join(curr + [w])) <= 34:
            curr.append(w)
        else:
            lines.append(" ".join(curr))
            curr = [w]
    if curr:
        lines.append(" ".join(curr))

    desc_spans = ""
    for idx, l in enumerate(lines):
        y_pos = 250 + idx * 24
        desc_spans += f'<text x="36" y="{y_pos}" font-family="-apple-system, BlinkMacSystemFont, \'Segoe UI\', Roboto, sans-serif" font-size="14.5" fill="{text_color}" opacity="0.94">{xml_esc(l)}</text>\n'

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 380 340" width="380" height="340">
  <defs>
    <style>
      @font-face {{
        font-family: 'Space Mono';
        src: url('data:font/woff;charset=utf-8;base64,{mono_b64}') format('woff');
        font-weight: 400;
        font-style: normal;
      }}
      @font-face {{
        font-family: 'Instrument Serif Italic';
        src: url('data:font/woff;charset=utf-8;base64,{italic_b64}') format('woff');
        font-weight: 400;
        font-style: italic;
      }}
      {anim_css}
      @media (prefers-reduced-motion: reduce) {{
        *, .tile-content {{
          animation: none !important;
          opacity: 1 !important;
          transform: none !important;
        }}
      }}
    </style>
  </defs>

  <!-- Background -->
  <rect x="0" y="0" width="380" height="340" rx="22" fill="{bg_color}"/>

  <g {elem_anim}>
    <!-- Top Tracker Category & Arrow -->
    <text x="36" y="52" font-family="'Space Mono', monospace" font-size="13" font-weight="700" letter-spacing="2" fill="{text_color}">{xml_esc(category)}</text>
    <text x="344" y="52" font-family="'Space Mono', monospace" font-size="20" font-weight="400" fill="{arrow_color}" text-anchor="end">&#x2192;</text>

    <!-- Center Serif Italic Headline -->
    <text x="36" y="160" font-family="'Instrument Serif Italic', 'Instrument Serif', serif" font-style="italic" font-size="46" fill="{text_color}">{xml_esc(headline)}</text>

    <!-- Bottom Description -->
    {desc_spans}
  </g>
</svg>"""
    return svg

def render_contributions_chart_card(data):
    """Card 3: 12-Month Bar Chart + Right-side Streak, Active Days & Busiest Day Stats."""
    stats = data["monthly_stats"]
    total = f"{data['total_365']:,}"
    longest = str(data["longest_streak"])
    active = f"{data['active_days']}"
    total_d = f"{data['total_days']}"
    busiest_cnt = str(data["busiest_count"])

    # Fonts subsetting raw text
    all_text = f"THE LAST 12 MONTHS ON GITHUB {total} contributions {longest} days current streak and the longest {active}/{total_d} with a commit {busiest_cnt} on busiest day Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec 0123456789"
    mono_b64 = subset_to_woff_b64("SpaceMono-Regular.ttf", all_text)
    serif_b64 = subset_to_woff_b64("InstrumentSerif-Regular.ttf", all_text)
    italic_b64 = subset_to_woff_b64("InstrumentSerif-Italic.ttf", all_text)

    # Find peak month
    peak_idx = 0
    max_cnt = 0
    for idx, m in enumerate(stats):
        if m["count"] >= max_cnt:
            max_cnt = m["count"]
            peak_idx = idx

    # Build bars
    chart_start_x = 48
    bar_width = 30
    bar_gap = 12
    baseline_y = 350
    max_h = 160

    bars_svg = ""
    scale = (max_h / max_cnt) if max_cnt > 0 else 1

    for i, m in enumerate(stats):
        x = chart_start_x + i * (bar_width + bar_gap)
        h = max(int(m["count"] * scale), 6) if m["count"] > 0 else 4
        y = baseline_y - h
        is_peak = (i == peak_idx)
        is_curr = m["is_current"]

        if is_peak:
            fill = "#2b5cff" # Vibrant electric blue
        elif is_curr:
            fill = "#d4d4d0" # Muted stone
        else:
            fill = "#141413" # Deep charcoal

        delay = 0.2 + (i * 0.05)

        if STATIC_MODE:
            anim_bar = ""
            tag_peak = ""
        else:
            anim_bar = f'style="transform-origin: {x + bar_width/2}px {baseline_y}px; animation: barGrow 0.6s cubic-bezier(0.16, 1, 0.3, 1) {delay:.2f}s backwards;"'
            tag_peak = f'style="opacity: 0; animation: fadeUp 0.5s ease-out {delay + 0.3:.2f}s forwards;"'

        bars_svg += f'<rect x="{x}" y="{y}" width="{bar_width}" height="{h}" rx="6" fill="{fill}" {anim_bar}/>\n'

        # Peak indicator text on top
        if is_peak:
            bars_svg += f'<text x="{x + bar_width/2}" y="{y - 10}" {tag_peak} font-family="\'Space Mono\', monospace" font-size="11" font-weight="700" fill="#2b5cff" text-anchor="middle">{m["count"]:,}</text>\n'

        # Month label below
        bars_svg += f'<text x="{x + bar_width/2}" y="{baseline_y + 24}" font-family="\'Space Mono\', monospace" font-size="11" fill="#71717a" text-anchor="middle">{xml_esc(m["label"])}</text>\n'

    if STATIC_MODE:
        anim_css = ""
        stats_anim = ""
        r1_anim = ""
        r2_anim = ""
        r3_anim = ""
    else:
        anim_css = """
        @keyframes fadeUp {
          from { opacity: 0; transform: translateY(12px); }
          to { opacity: 1; transform: translateY(0); }
        }
        @keyframes barGrow {
          from { transform: scaleY(0); }
          to { transform: scaleY(1); }
        }
        .st-card { opacity: 0; animation: fadeUp 0.6s cubic-bezier(0.16, 1, 0.3, 1) 0.15s forwards; }
        .st-r1 { opacity: 0; animation: fadeUp 0.6s cubic-bezier(0.16, 1, 0.3, 1) 0.35s forwards; }
        .st-r2 { opacity: 0; animation: fadeUp 0.6s cubic-bezier(0.16, 1, 0.3, 1) 0.45s forwards; }
        .st-r3 { opacity: 0; animation: fadeUp 0.6s cubic-bezier(0.16, 1, 0.3, 1) 0.55s forwards; }
        """
        stats_anim = 'class="st-card"'
        r1_anim = 'class="st-r1"'
        r2_anim = 'class="st-r2"'
        r3_anim = 'class="st-r3"'

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 920 420" width="920" height="420">
  <defs>
    <style>
      @font-face {{
        font-family: 'Space Mono';
        src: url('data:font/woff;charset=utf-8;base64,{mono_b64}') format('woff');
        font-weight: 400;
        font-style: normal;
      }}
      @font-face {{
        font-family: 'Instrument Serif';
        src: url('data:font/woff;charset=utf-8;base64,{serif_b64}') format('woff');
        font-weight: 400;
        font-style: normal;
      }}
      @font-face {{
        font-family: 'Instrument Serif Italic';
        src: url('data:font/woff;charset=utf-8;base64,{italic_b64}') format('woff');
        font-weight: 400;
        font-style: italic;
      }}
      {anim_css}
      @media (prefers-reduced-motion: reduce) {{
        *, .st-card, .st-r1, .st-r2, .st-r3, rect, text {{
          animation: none !important;
          opacity: 1 !important;
          transform: none !important;
        }}
      }}
    </style>
  </defs>

  <!-- Card Background -->
  <rect x="1" y="1" width="918" height="418" rx="24" fill="#f6f6f4" stroke="#e3e3de" stroke-width="1.5"/>

  <!-- Left Header -->
  <g {stats_anim}>
    <text x="48" y="58" font-family="'Space Mono', monospace" font-size="11" font-weight="700" letter-spacing="1.8" fill="#6b7280">THE LAST 12 MONTHS ON GITHUB</text>
    <text x="48" y="128">
      <tspan font-family="'Instrument Serif', serif" font-size="64" fill="#111110">{xml_esc(total)}</tspan>
      <tspan font-family="'Instrument Serif Italic', 'Instrument Serif', serif" font-style="italic" font-size="64" fill="#111110"> contributions</tspan>
    </text>
  </g>

  <!-- 12-Month Bar Chart -->
  {bars_svg}

  <!-- Vertical Divider separating chart and stats -->
  <line x1="600" y1="50" x2="600" y2="370" stroke="#e8e8e4" stroke-width="1"/>

  <!-- Right Column Metrics -->
  <!-- Metric 1: Streak -->
  <g {r1_anim}>
    <text x="640" y="112">
      <tspan font-family="'Instrument Serif', serif" font-size="46" fill="#111110">{xml_esc(longest)}</tspan>
      <tspan font-family="'Instrument Serif Italic', 'Instrument Serif', serif" font-style="italic" font-size="46" fill="#111110"> days</tspan>
    </text>
    <text x="640" y="136" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="13" fill="#6b7280">current streak, and the longest</text>
  </g>

  <line x1="640" y1="165" x2="870" y2="165" stroke="#e3e3de" stroke-width="1"/>

  <!-- Metric 2: Active Days -->
  <g {r2_anim}>
    <text x="640" y="222">
      <tspan font-family="'Instrument Serif', serif" font-size="46" fill="#111110">{xml_esc(active)}</tspan>
      <tspan font-family="'Instrument Serif', serif" font-size="46" fill="#9ca3af"> / {xml_esc(total_d)}</tspan>
    </text>
    <text x="640" y="246" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="13" fill="#6b7280">days with a commit</text>
  </g>

  <line x1="640" y1="275" x2="870" y2="275" stroke="#e3e3de" stroke-width="1"/>

  <!-- Metric 3: Busiest Day -->
  <g {r3_anim}>
    <text x="640" y="332" font-family="'Instrument Serif', serif" font-size="46" fill="#111110">{xml_esc(busiest_cnt)}</text>
    <text x="640" y="356" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="13" fill="#6b7280">on the busiest day</text>
  </g>
</svg>"""
    return svg

def render_featured_repo_card(repo_name: str, category_tag: str, description: str, tags: list, delay_s: float):
    """Renders one featured repo card matching the aesthetic."""
    text_sample = f"{repo_name} {category_tag} {description} {' '.join(tags)} ↗ ★ Public Updated 2026"
    mono_b64 = subset_to_woff_b64("SpaceMono-Regular.ttf", text_sample)
    serif_b64 = subset_to_woff_b64("InstrumentSerif-Regular.ttf", text_sample)
    italic_b64 = subset_to_woff_b64("InstrumentSerif-Italic.ttf", text_sample)

    if STATIC_MODE:
        anim_css = ""
        card_anim = ""
    else:
        anim_css = f"""
        @keyframes repoFadeUp {{
          from {{ opacity: 0; transform: translateY(14px); }}
          to {{ opacity: 1; transform: translateY(0); }}
        }}
        .repo-card {{ opacity: 0; animation: repoFadeUp 0.6s cubic-bezier(0.16, 1, 0.3, 1) {delay_s:.2f}s forwards; }}
        """
        card_anim = 'class="repo-card"'

    # Render tag badges
    pills_svg = ""
    curr_x = 48
    for t in tags:
        pill_w = len(t) * 7.5 + 20
        pills_svg += f"""
        <rect x="{curr_x}" y="145" width="{pill_w:.1f}" height="26" rx="6" fill="#ebebe8" stroke="#deded9" stroke-width="1"/>
        <text x="{curr_x + pill_w/2:.1f}" y="162" font-family="'Space Mono', monospace" font-size="11" fill="#4b5563" text-anchor="middle">{xml_esc(t)}</text>
        """
        curr_x += pill_w + 10

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 920 200" width="920" height="200">
  <defs>
    <style>
      @font-face {{
        font-family: 'Space Mono';
        src: url('data:font/woff;charset=utf-8;base64,{mono_b64}') format('woff');
        font-weight: 400;
        font-style: normal;
      }}
      @font-face {{
        font-family: 'Instrument Serif Italic';
        src: url('data:font/woff;charset=utf-8;base64,{italic_b64}') format('woff');
        font-weight: 400;
        font-style: italic;
      }}
      {anim_css}
      @media (prefers-reduced-motion: reduce) {{
        *, .repo-card {{
          animation: none !important;
          opacity: 1 !important;
          transform: none !important;
        }}
      }}
    </style>
  </defs>

  <!-- Card Background -->
  <rect x="1" y="1" width="918" height="198" rx="20" fill="#f6f6f4" stroke="#e3e3de" stroke-width="1.5"/>

  <g {card_anim}>
    <!-- Top Category Tracker & Arrow Link -->
    <text x="48" y="42" font-family="'Space Mono', monospace" font-size="11" font-weight="700" letter-spacing="1.5" fill="#6b7280">{xml_esc(category_tag)}</text>
    <text x="872" y="46" font-family="'Space Mono', monospace" font-size="20" fill="#2b5cff" text-anchor="end">&#x2197;</text>

    <!-- Repo Name in Serif Italic -->
    <text x="48" y="88" font-family="'Instrument Serif Italic', 'Instrument Serif', serif" font-style="italic" font-size="38" fill="#111110">{xml_esc(repo_name)}</text>

    <!-- Description -->
    <text x="48" y="122" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="15" fill="#4b5563">{xml_esc(description)}</text>

    <!-- Tech Stack Pills -->
    {pills_svg}

    <!-- Right-aligned Star / Metadata -->
    <text x="872" y="162" font-family="'Space Mono', monospace" font-size="11" fill="#71717a" text-anchor="end">&#x2605; Public Repository</text>
  </g>
</svg>"""
    return svg

def render_contribution_graph_card(data):
    """Card 5: 52-Week Contribution Heatmap in Brand Blue."""
    conts = data["raw_contributions"]

    # Raw text subsetting
    all_text = "Every day, in blue REFRESHED DAILY less more Dec Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov"
    mono_b64 = subset_to_woff_b64("SpaceMono-Regular.ttf", all_text)
    serif_b64 = subset_to_woff_b64("InstrumentSerif-Regular.ttf", all_text)
    italic_b64 = subset_to_woff_b64("InstrumentSerif-Italic.ttf", all_text)

    # Blue Theme Palette
    PALETTE = {
        0: "#ebebe8", # Base subtle light gray
        1: "#b8d1ff", # Soft ice blue
        2: "#70a3ff", # Sky royal blue
        3: "#2b5cff", # Electric blue
        4: "#003ad6"  # Deep vivid cobalt
    }

    # Slice the last 52 full weeks
    latest_c = conts[-1]
    latest_dt = datetime.strptime(latest_c["date"], "%Y-%m-%d").date()

    target_start_dt = latest_dt - timedelta(days=52 * 7)
    days_to_sunday = (target_start_dt.weekday() + 1) % 7
    start_dt = target_start_dt - timedelta(days=days_to_sunday)

    sub_conts = [c for c in conts if datetime.strptime(c["date"], "%Y-%m-%d").date() >= start_dt]
    # Pad to Sunday if needed
    first_dt = datetime.strptime(sub_conts[0]["date"], "%Y-%m-%d").date()
    pad_days = (first_dt.weekday() + 1) % 7
    padded = [{"date": "", "count": 0, "level": 0, "is_pad": True}] * pad_days + sub_conts

    start_x = 48
    start_y = 100
    cell_size = 11.5
    cell_gap = 3.5
    col_step = cell_size + cell_gap
    row_step = cell_size + cell_gap

    cells_svg = ""
    month_labels = []
    month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    last_month = -1

    for idx, item in enumerate(padded):
        w_idx = idx // 7
        d_idx = idx % 7 # 0 = Sun, 6 = Sat
        x = start_x + w_idx * col_step
        y = start_y + d_idx * row_step

        if item.get("is_pad"):
            continue

        # Month label detection
        if d_idx == 0 and item.get("date"):
            dt = datetime.strptime(item["date"], "%Y-%m-%d")
            if dt.month != last_month:
                month_labels.append({"name": month_names[dt.month - 1], "x": x})
                last_month = dt.month

        lvl = item.get("level", 0)
        color = PALETTE.get(lvl, PALETTE[0])
        delay = 0.05 + (w_idx * 0.015) + (d_idx * 0.005)

        if STATIC_MODE:
            cell_anim = ""
        else:
            cell_anim = f'style="opacity: 0; animation: cellIn 0.35s ease-out {delay:.3f}s forwards;"'

        cnt_str = f"{item['count']} contributions" if item['count'] != 1 else "1 contribution"
        cells_svg += f'<rect x="{x:.1f}" y="{y:.1f}" width="{cell_size}" height="{cell_size}" rx="2.5" fill="{color}" {cell_anim}><title>{xml_esc(cnt_str)} on {xml_esc(item.get("date", ""))}</title></rect>\n'

    # Month labels SVG
    month_svg = ""
    for m in month_labels:
        month_svg += f'<text x="{m["x"]:.1f}" y="{start_y + 7 * row_step + 18}" font-family="\'Space Mono\', monospace" font-size="10.5" fill="#71717a">{xml_esc(m["name"])}</text>\n'

    # Legend at bottom right
    leg_x = start_x + 52 * col_step - 140
    leg_y = start_y + 7 * row_step + 10
    legend_svg = f"""
    <g transform="translate({leg_x:.1f}, {leg_y:.1f})">
      <text x="0" y="9" font-family="'Space Mono', monospace" font-size="10" fill="#71717a">less</text>
      <rect x="34" y="0" width="{cell_size}" height="{cell_size}" rx="2.5" fill="{PALETTE[0]}"/>
      <rect x="49" y="0" width="{cell_size}" height="{cell_size}" rx="2.5" fill="{PALETTE[1]}"/>
      <rect x="64" y="0" width="{cell_size}" height="{cell_size}" rx="2.5" fill="{PALETTE[2]}"/>
      <rect x="79" y="0" width="{cell_size}" height="{cell_size}" rx="2.5" fill="{PALETTE[3]}"/>
      <rect x="94" y="0" width="{cell_size}" height="{cell_size}" rx="2.5" fill="{PALETTE[4]}"/>
      <text x="112" y="9" font-family="'Space Mono', monospace" font-size="10" fill="#71717a">more</text>
    </g>
    """

    if STATIC_MODE:
        anim_css = ""
        header_anim = ""
    else:
        anim_css = """
        @keyframes headerFade {
          from { opacity: 0; transform: translateY(10px); }
          to { opacity: 1; transform: translateY(0); }
        }
        @keyframes cellIn {
          from { opacity: 0; transform: scale(0.6); }
          to { opacity: 1; transform: scale(1); }
        }
        .heat-header { opacity: 0; animation: headerFade 0.6s cubic-bezier(0.16, 1, 0.3, 1) 0.1s forwards; }
        """
        header_anim = 'class="heat-header"'

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 920 270" width="920" height="270">
  <defs>
    <style>
      @font-face {{
        font-family: 'Space Mono';
        src: url('data:font/woff;charset=utf-8;base64,{mono_b64}') format('woff');
        font-weight: 400;
        font-style: normal;
      }}
      @font-face {{
        font-family: 'Instrument Serif';
        src: url('data:font/woff;charset=utf-8;base64,{serif_b64}') format('woff');
        font-weight: 400;
        font-style: normal;
      }}
      @font-face {{
        font-family: 'Instrument Serif Italic';
        src: url('data:font/woff;charset=utf-8;base64,{italic_b64}') format('woff');
        font-weight: 400;
        font-style: italic;
      }}
      {anim_css}
      @media (prefers-reduced-motion: reduce) {{
        *, .heat-header, rect, text {{
          animation: none !important;
          opacity: 1 !important;
          transform: none !important;
        }}
      }}
    </style>
  </defs>

  <!-- Card Background -->
  <rect x="1" y="1" width="918" height="268" rx="24" fill="#f6f6f4" stroke="#e3e3de" stroke-width="1.5"/>

  <!-- Card Header -->
  <g {header_anim}>
    <text x="48" y="58">
      <tspan font-family="'Instrument Serif', serif" font-size="38" fill="#111110">Every day, </tspan>
      <tspan font-family="'Instrument Serif Italic', 'Instrument Serif', serif" font-style="italic" font-size="38" fill="#2b5cff">in blue</tspan>
    </text>
    <text x="872" y="56" font-family="'Space Mono', monospace" font-size="11" font-weight="700" letter-spacing="2" fill="#6b7280" text-anchor="end">REFRESHED DAILY</text>
  </g>

  <!-- Heatmap Cells -->
  {cells_svg}

  <!-- Month Labels -->
  {month_svg}

  <!-- Legend -->
  {legend_svg}
</svg>"""
    return svg

# -----------------------------------------------------------------------------
# Main Generator
# -----------------------------------------------------------------------------
def main():
    print(f"🎨 Generating animated profile cards for {USERNAME}...")
    if STATIC_MODE:
        print("📸 STATIC=1 mode active: rendering crisp final frame without keyframes.")

    ensure_master_fonts()
    data = load_contributions()

    cards = {}

    # 1. Hero Card
    print("-> Rendering hero.svg...")
    cards["hero.svg"] = render_hero_card()

    # 2. Three Linked Tiles
    print("-> Rendering tile-build.svg...")
    cards["tile-build.svg"] = render_tile(
        category="BUILD",
        headline="40+ repos",
        description="TruckTalk AI, Code Sentinel, SoulSpace, and production MERN architectures.",
        bg_color="#265bf6",
        text_color="#ffffff",
        arrow_color="#ffffff",
        delay_s=0.25
    )

    print("-> Rendering tile-lead.svg...")
    cards["tile-lead.svg"] = render_tile(
        category="LEAD",
        headline="AtherHacks",
        description="Lead @ AtherHacks Hackathon Community, mentoring builders & organizing hackathons.",
        bg_color="#e93d25",
        text_color="#ffffff",
        arrow_color="#ffffff",
        delay_s=0.35
    )

    print("-> Rendering tile-explore.svg...")
    cards["tile-explore.svg"] = render_tile(
        category="SYSTEMS",
        headline="AI & Hardware",
        description="Groq LLMs, ESP32 avionics, Computer Vision, and VLSI digital design at Alard Pune.",
        bg_color="#f7b613",
        text_color="#141413",
        arrow_color="#141413",
        delay_s=0.45
    )

    # 3. Monthly Contributions Chart Card
    print("-> Rendering contributions-chart.svg...")
    cards["contributions-chart.svg"] = render_contributions_chart_card(data)

    # 4. 52-Week Contribution Graph Card
    print("-> Rendering contrib-graph.svg...")
    cards["contrib-graph.svg"] = render_contribution_graph_card(data)

    # Validate XML and write all cards to disk
    for filename, content in cards.items():
        try:
            ET.fromstring(content)
        except Exception as err:
            raise RuntimeError(f"XML Validation Error in {filename}: {err}")

        out_path = os.path.join(OUTPUT_DIR, filename)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(content)
        size_kb = len(content) / 1024
        print(f"  ✓ Valid XML: Saved {filename} ({size_kb:.1f} KB)")

    print("✨ All cards rendered & validated successfully into cards/!")

if __name__ == "__main__":
    main()
