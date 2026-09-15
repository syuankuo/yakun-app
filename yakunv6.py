"""
Ya Kun app — a single-file, multi-page Python Dash application.

Run with:   python app.py
Then open:  http://127.0.0.1:8050

IMPORTANT — images:
The three images are read directly off disk from a folder literally named
"assets", placed in the same folder as this file, and embedded into the
page as base64 data. Your project folder should look like this:

    yakun app/
        yakun v5.py   (this file)
        requirements.txt
        Procfile
        assets/
            yakun logo.png
            yakun 1for1.png
            yakun rotating deals.png

The three encode_image() calls below must match those filenames
character-for-character (spaces, capitalization, extension) — if yours
are .jpg instead of .png, change the ".png" strings accordingly.

Pages (real URLs, not anchors):
  /          Home
  /tiers     My Tier
  /deals     Deals
  /order     Order
  /rewards   Rewards
  /profile   Profile
"""

import random
from datetime import datetime, timedelta

import dash
from dash import Dash, html, dcc, Input, Output, State, ctx, no_update

# ---------------------------------------------------------------------------
# Domain data
# ---------------------------------------------------------------------------

TIERS = [
    ("Kopi Novice", 0),
    ("Kopi Apprentice", 25),
    ("Kopi Master", 75),
    ("Kopi Legend", 150),
]

TIER_COLORS = [
    ("#C9B38A", "#2E1B10"),
    ("#D98F3E", "#FFFDF8"),
    ("#A31E22", "#FFFDF8"),
    ("#2E1B10", "#F0A93A"),
]

TIER_REWARDS = {
    "Kopi Novice": {
        "level_up": [("☕", "Standard points on every order"), ("\U0001f4f1", "Mobile ordering unlocked")],
        "birthday": [("\U0001f382", "10% off your birthday order")],
    },
    "Kopi Apprentice": {
        "level_up": [("\U0001f4cf", "Free size upgrade, once a month"), ("⏰", "Access to rotating deals")],
        "birthday": [("\U0001f382", "A free drink on your birthday")],
    },
    "Kopi Master": {
        "level_up": [("⚡", "Priority collection on mobile orders"),
                     ("✨", "Early access to seasonal drinks"),
                     ("☕", "A free drink every quarter")],
        "birthday": [("\U0001f382", "Free drink + free size upgrade")],
    },
    "Kopi Legend": {
        "level_up": [("☕", "A free drink every month"),
                     ("\U0001f680", "Faster points on every order"),
                     ("\U0001f388", "Invitations to tasting events")],
        "birthday": [("\U0001f382", "Free drink + free kaya toast set")],
    },
}

REWARDS = [
    ("Kaya toast slice", 180),
    ("Soft-boiled egg", 180),
    ("Size upgrade", 190),
    ("Free hot kopi", 300),
    ("Free iced kopi", 300),
]

DRINK_IDS = {
    "order-drink-kopi": "Kopi",
    "order-drink-kopi-c": "Kopi C",
    "order-drink-kopi-o": "Kopi O",
    "order-drink-teh": "Teh",
    "order-drink-teh-c": "Teh C",
    "order-drink-teh-o": "Teh O",
    "order-drink-milo": "Milo",
    "order-drink-horlicks": "Horlicks",
}

PRICES = {
    "Kopi":     {"Reg (Hot)": 2.2, "Large (Hot)": 3.0, "Reg (Cold)": 3.2, "Large (Cold)": 4.3},
    "Kopi O":   {"Reg (Hot)": 2.0, "Large (Hot)": 2.8, "Reg (Cold)": 3.1, "Large (Cold)": 4.2},
    "Kopi C":   {"Reg (Hot)": 2.4, "Large (Hot)": 3.2, "Reg (Cold)": 3.4, "Large (Cold)": 4.5},
    "Teh":      {"Reg (Hot)": 2.2, "Large (Hot)": 3.0, "Reg (Cold)": 3.2, "Large (Cold)": 4.3},
    "Teh O":    {"Reg (Hot)": 2.0, "Large (Hot)": 2.8, "Reg (Cold)": 3.1, "Large (Cold)": 4.2},
    "Teh C":    {"Reg (Hot)": 2.4, "Large (Hot)": 3.2, "Reg (Cold)": 3.4, "Large (Cold)": 4.5},
    "Milo":     {"Reg (Hot)": 2.6, "Large (Hot)": 3.4, "Reg (Cold)": 3.5, "Large (Cold)": 4.7},
    "Horlicks": {"Reg (Hot)": 2.6, "Large (Hot)": 3.4, "Reg (Cold)": 3.5, "Large (Cold)": 4.7},
}

SIZE_IDS = {
    "order-size-reg-hot": "Reg (Hot)",
    "order-size-large-hot": "Large (Hot)",
    "order-size-reg-cold": "Reg (Cold)",
    "order-size-large-cold": "Large (Cold)",
}
SUGAR_IDS = {
    "order-sugar-less": "Less Sugar",
    "order-sugar-none": "No Sugar",
}

NAV_ITEMS = [
    ("/", "nav-home", "Home", "\U0001f3e0"),
    ("/tiers", "nav-tiers", "My Tier", "⭐"),
    ("/order", "nav-order", "Order", "☕"),
    ("/rewards", "nav-rewards", "Rewards", "\U0001f381"),
    ("/profile", "nav-profile", "Profile", "\U0001f464"),
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def current_tier(cups):
    tier = TIERS[0]
    for name, min_cups in TIERS:
        if cups >= min_cups:
            tier = (name, min_cups)
    return tier


def next_tier(cups):
    cur = current_tier(cups)
    idx = TIERS.index(cur)
    return TIERS[idx + 1] if idx + 1 < len(TIERS) else None


def next_occurrence(target_hour, allowed_weekdays):
    now = datetime.now()
    for i in range(8):
        candidate = (now + timedelta(days=i)).replace(hour=target_hour, minute=0, second=0, microsecond=0)
        if candidate.weekday() in allowed_weekdays and candidate > now:
            return candidate
    return now + timedelta(days=1)


def format_duration(delta):
    total = int(delta.total_seconds())
    if total <= 0:
        return "00:00:00"
    h, rem = divmod(total, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


MIDWEEK_END = next_occurrence(17, [1, 2])  # next Tue/Wed, 5pm
EXAM_END = datetime.now() + timedelta(hours=62)

# ---------------------------------------------------------------------------
# App + styling
# ---------------------------------------------------------------------------

FONT_URL = (
    "https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,400;"
    "0,9..144,500;0,9..144,600;0,9..144,700;1,9..144,500&family=Plus+Jakarta+Sans:"
    "ital,wght@0,400;0,500;0,600;0,700;0,800;1,500&display=swap"
)

app = Dash(__name__, use_pages=True, pages_folder="", external_stylesheets=[FONT_URL],
           title="Ya Kun", suppress_callback_exceptions=True)
server = app.server

import base64
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def encode_image(filename):
    path = os.path.join(BASE_DIR, "assets", filename)
    with open(path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode()
    ext = filename.rsplit(".", 1)[-1]
    return f"data:image/{ext};base64,{encoded}"

LOGO_SRC = app.get_asset_url("yakun logo.png")
PROMO_1FOR1_SRC = app.get_asset_url("yakun 1for1.png")
ROTATING_DEALS_SRC = app.get_asset_url("yakun rotating deals.png")

CSS = """
<style>
:root{
  --coffee:#3B2418; --kopi-red:#A31E22; --kopi-red-dark:#7E1519;
  --pandan:#5F7A3D; --egg-yolk:#F0A93A; --egg-yolk-dark:#D6902A; --toast-gold:#D98F3E;
  --cream:#FBF1E1; --cream-deep:#F3E4CC; --paper:#FFFDF8;
  --line:rgba(59,36,24,0.16); --line-strong:rgba(59,36,24,0.32);
  --font-display:'Fraunces', ui-serif, Georgia, serif;
  --font-body:'Plus Jakarta Sans', ui-sans-serif, system-ui, sans-serif;
  --radius-s:8px; --radius-m:14px; --radius-l:22px;
}
*{ box-sizing:border-box; }
body{ margin:0; background:#E7DCC6; color:var(--coffee); font-family:var(--font-body); line-height:1.5; }
h1,h2,h3,h4{ font-family:var(--font-display); color:var(--coffee); margin:0 0 0.4em; font-weight:600; line-height:1.15; }
h1{ font-size:1.7rem; } h2{ font-size:1.3rem; } h3{ font-size:1.1rem; } h4{ font-size:1rem; margin:0; }
p{ margin:0 0 0.8em; }
a{ color:var(--kopi-red); }
.tiny{ font-size:0.76rem; opacity:0.75; }

.app-shell{ width:100%; max-width:430px; margin:0 auto; min-height:100vh; background:var(--cream);
            display:flex; flex-direction:column; box-shadow:0 30px 80px rgba(0,0,0,0.28); position:relative; }
@media (max-width:480px){ .app-shell{ box-shadow:none; } }

.app-topbar{ position:sticky; top:0; z-index:20; background:var(--paper); padding:16px 18px;
             border-bottom:1px solid var(--line); display:flex; justify-content:space-between; align-items:center; }
.app-topbar .greeting{ font-family:var(--font-display); font-weight:600; font-size:1.05rem; }
.app-topbar .tier-chip{ font-size:0.72rem; font-weight:700; color:var(--kopi-red); }
.topbar-logo{ height:30px; width:auto; display:block; }

.page-area{ flex:1; overflow-y:auto; padding:1.2rem; }

.bottom-nav{ position:sticky; bottom:0; z-index:20; display:flex; justify-content:space-around;
             background:var(--paper); border-top:1px solid var(--line); padding:0.55rem 0.2rem 0.75rem; }
.nav-item{ display:flex; flex-direction:column; align-items:center; gap:2px; text-decoration:none;
           color:var(--coffee); opacity:0.5; font-size:0.65rem; font-weight:700; }
.nav-item.is-active{ opacity:1; color:var(--kopi-red); }
.nav-emoji{ font-size:1.1rem; }

.btn{ display:inline-flex; align-items:center; justify-content:center; gap:0.5rem; padding:0.8rem 1.3rem;
      border-radius:999px; font-weight:700; font-size:0.9rem; text-decoration:none; cursor:pointer;
      border:2px solid transparent; }
.btn-primary{ background:var(--kopi-red); color:var(--paper); width:100%; }
.btn-ghost{ background:transparent; border-color:var(--line-strong); color:var(--coffee); }

.card{ background:var(--paper); border:1px solid var(--line); border-radius:var(--radius-m); padding:1rem; }

/* ---- home ---- */
.home-hero{ background:var(--coffee); color:var(--paper); border-radius:var(--radius-l); padding:1.3rem; margin-bottom:1.2rem; }
.home-hero h1{ color:var(--paper); }
.home-hero .tier-link{ display:inline-flex; align-items:center; gap:0.4rem; margin-top:0.7rem;
                        background:rgba(255,255,255,0.14); padding:0.45rem 0.85rem; border-radius:999px;
                        font-size:0.78rem; font-weight:700; color:var(--egg-yolk); text-decoration:none; }
.quick-grid{ display:grid; grid-template-columns:1fr 1fr; gap:0.8rem; margin-bottom:1.2rem; }
.quick-tile{ background:var(--paper); border:1px solid var(--line); border-radius:var(--radius-m); padding:1rem;
             text-decoration:none; color:var(--coffee); display:flex; flex-direction:column; gap:0.4rem; }
.quick-tile .emoji{ font-size:1.5rem; }
.quick-tile .tile-title{ font-weight:700; font-size:0.92rem; }

.promo-banner{ display:block; margin-bottom:1.2rem; text-decoration:none; }
.promo-banner img{ width:100%; height:auto; border-radius:var(--radius-l); display:block; }

/* ---- tiers ---- */
.tiers-headline{ text-align:center; font-weight:700; color:var(--kopi-red); margin-bottom:1.2rem; font-size:1rem; }
.stepper{ position:relative; padding:0 10px; margin-bottom:1.6rem; }
.stepper-line{ position:absolute; top:9px; left:10px; right:10px; height:3px; background:var(--line-strong); border-radius:2px; }
.stepper-line-fill{ position:absolute; top:9px; left:10px; height:3px; background:var(--kopi-red); border-radius:2px; transition:width .6s ease; }
.stepper-dots{ display:flex; justify-content:space-between; position:relative; }
.stepper-dot-wrap{ display:flex; flex-direction:column; align-items:center; gap:0.45rem; width:60px; }
.stepper-dot{ width:20px; height:20px; border-radius:50%; background:var(--cream-deep); border:3px solid var(--cream); z-index:2; }
.stepper-dot.is-reached{ background:var(--kopi-red); }
.stepper-num{ font-size:0.7rem; font-weight:700; }
.stepper-label{ font-size:0.66rem; opacity:0.75; text-align:center; }

.tier-carousel{ display:flex; gap:0.8rem; overflow-x:auto; padding-bottom:0.5rem; margin-bottom:1.5rem; scroll-snap-type:x mandatory; }
.tier-card{ flex:0 0 76%; scroll-snap-align:start; border-radius:var(--radius-l); padding:1.2rem; position:relative; min-height:130px; }
.tier-card .ribbon{ position:absolute; top:0.8rem; left:0.8rem; background:rgba(255,255,255,0.22); font-size:0.65rem;
                     font-weight:800; padding:0.25rem 0.65rem; border-radius:999px; }
.tier-card .tier-name{ margin:1.7rem 0 0.2rem; font-family:var(--font-display); font-weight:600; font-size:1.15rem; }
.tier-card .cups-line{ font-size:0.8rem; opacity:0.9; }
.tier-card .unlock-line{ font-size:0.74rem; opacity:0.75; margin-top:0.25rem; }

.reward-section{ margin-bottom:1.4rem; }
.reward-section h4{ margin-bottom:0.6rem; }
.gift-row{ display:flex; align-items:center; gap:0.8rem; background:var(--paper); border:1px solid var(--line);
           border-radius:var(--radius-s); padding:0.7rem 0.9rem; margin-bottom:0.5rem; }
.gift-emoji{ font-size:1.15rem; }

/* ---- deals ---- */
.deal-card{ background:var(--paper); border:1px solid var(--line); border-radius:var(--radius-m); padding:1rem; margin-bottom:0.9rem; }
.deal-card h4{ margin-bottom:0.2rem; }
.countdown{ display:inline-block; margin-top:0.6rem; font-weight:800; background:var(--coffee); color:var(--egg-yolk);
            padding:0.3rem 0.7rem; border-radius:var(--radius-s); font-size:0.85rem; }

/* ---- order ---- */
.drink-grid{ display:grid; grid-template-columns:1fr 1fr; gap:0.6rem; margin:0.9rem 0; }
.drink-tile{ border:2px solid var(--line); border-radius:var(--radius-s); background:#E9E4DA; padding:0.7rem;
             text-align:center; cursor:pointer; font-size:0.85rem; font-weight:600; color:#8B8478; }
.drink-tile.is-selected{ background:var(--coffee); color:var(--paper); }
.drink-tile.is-selected.accent-red{ border-color:var(--kopi-red); }
.drink-tile.is-selected.accent-green{ border-color:var(--pandan); }
.drink-tile.is-selected.accent-gold{ border-color:var(--egg-yolk); }
.badge-line{ display:flex; align-items:center; gap:0.5rem; font-size:0.78rem; margin:0.7rem 0; }
.lock-dot{ width:8px; height:8px; border-radius:50%; background:var(--line-strong); flex:none; }
.lock-dot.is-unlocked{ background:var(--pandan); }
.order-msg{ font-size:0.8rem; font-weight:700; color:var(--pandan); min-height:1.2em; margin-top:0.7rem; text-align:center; }
.order-page{ padding-bottom:10rem; }

.order-action-bar{ position:absolute; left:0; right:0; bottom:64px; z-index:15;
                    background:var(--coffee); color:var(--paper); padding:0.8rem 1.2rem;
                    border-top-left-radius:var(--radius-l); border-top-right-radius:var(--radius-l); }
.order-pickup-line{ font-size:0.72rem; opacity:0.85; margin-bottom:0.5rem; display:flex; align-items:center; gap:0.35rem; }
.order-action-row{ display:flex; align-items:center; gap:0.8rem; }
.order-bag{ position:relative; width:42px; height:42px; border-radius:50%; background:rgba(255,255,255,0.12);
            display:flex; align-items:center; justify-content:center; font-size:1.2rem; flex:none; }
.order-bag .bag-count{ position:absolute; top:-4px; right:-4px; background:var(--egg-yolk); color:var(--coffee);
                        font-size:0.65rem; font-weight:800; border-radius:999px; min-width:18px; height:18px;
                        display:flex; align-items:center; justify-content:center; padding:0 4px; }
.order-add-btn{ flex:1; background:var(--kopi-red); color:var(--paper); border:none; border-radius:999px;
                padding:0.85rem 1rem; font-weight:700; font-size:0.92rem; cursor:pointer; }
.order-add-btn:disabled{ background:rgba(255,255,255,0.15); color:rgba(255,255,255,0.5); cursor:not-allowed; }

/* ---- rewards ---- */
.reward-tile{ display:flex; justify-content:space-between; align-items:center; gap:0.6rem; background:var(--paper);
              border:1px solid var(--line); border-radius:var(--radius-s); padding:0.7rem 0.85rem; margin-bottom:0.55rem; }
.reward-tile .cost{ font-size:0.72rem; opacity:0.7; }
.redeem-btn{ border:none; background:var(--egg-yolk); color:var(--coffee); font-weight:700; font-size:0.74rem;
             padding:0.4rem 0.75rem; border-radius:999px; cursor:pointer; }
.surprise-banner{ background:var(--pandan); color:var(--paper); border-radius:var(--radius-s); padding:0.75rem 0.9rem;
                   margin-bottom:0.9rem; font-size:0.82rem; font-weight:600; }
.redeem-msg{ font-size:0.8rem; font-weight:700; color:var(--pandan); min-height:1.2em; text-align:center; }

/* ---- profile ---- */
.referral-box{ background:var(--coffee); color:var(--paper); border-radius:var(--radius-m); padding:1.1rem; margin-bottom:1.1rem; }
.referral-code{ font-weight:800; font-size:1.1rem; background:rgba(255,255,255,0.1); padding:0.55rem 0.75rem;
                border-radius:var(--radius-s); display:flex; justify-content:space-between; align-items:center; margin-top:0.6rem; }
.referral-code button{ border:none; background:var(--egg-yolk); color:var(--coffee); font-weight:700;
                        padding:0.35rem 0.65rem; border-radius:var(--radius-s); font-size:0.72rem; cursor:pointer; }
.setting-row{ display:flex; justify-content:space-between; align-items:center; padding:0.7rem 0; border-top:1px solid var(--line); font-size:0.85rem; }
.switch{ width:38px; height:22px; border-radius:999px; background:var(--cream-deep); position:relative; cursor:pointer; border:none; }
.switch::after{ content:""; position:absolute; top:2px; left:2px; width:18px; height:18px; border-radius:50%; background:var(--paper); }
.switch.is-on{ background:var(--pandan); }
.switch.is-on::after{ left:18px; }
</style>
"""

app.index_string = (
    """<!DOCTYPE html>
<html>
<head>
{%metas%}
<title>{%title%}</title>
{%favicon%}
{%css%}
"""
    + CSS
    + """
</head>
<body>
{%app_entry%}
<footer>
{%config%}
{%scripts%}
{%renderer%}
</footer>
</body>
</html>
"""
)

# ---------------------------------------------------------------------------
# Page layouts
# ---------------------------------------------------------------------------


def home_layout():
    return html.Div([
        html.Div(className="home-hero", children=[
            html.H1("Good day, SY"),
            html.P("Order ahead and redeem rewards!",
                   style={"opacity": 0.9, "marginBottom": 0}),
            dcc.Link("My tier: —", href="/tiers", id="home-tier-chip", className="tier-link"),
        ]),

        dcc.Link(className="promo-banner", href="/deals", children=[
            html.Img(src=PROMO_1FOR1_SRC),
        ]),

        dcc.Link(className="promo-banner", href="/deals", children=[
            html.Img(src=ROTATING_DEALS_SRC),
        ]),
    ])


def tiers_layout():
    stepper_dots = []
    for i, (name, min_cups) in enumerate(TIERS):
        stepper_dots.append(html.Div(className="stepper-dot-wrap", children=[
            html.Div(id=f"tiers-dot-{i}", className="stepper-dot"),
            html.Div(str(min_cups), className="stepper-num"),
            html.Div(name.replace("Kopi ", ""), className="stepper-label"),
        ]))

    tier_cards = [
        html.Div(id=f"tiers-card-{i}", className="tier-card",
                  style={"background": TIER_COLORS[i][0], "color": TIER_COLORS[i][1]})
        for i in range(len(TIERS))
    ]

    return html.Div([
        html.H1("My Tier"),
        html.P("Every cup counts as one stamp. Your tier resets every 12 months.", className="tiny"),
        html.Div(id="tiers-headline", className="tiers-headline", style={"marginTop": "1rem"}),
        html.Div(className="stepper", children=[
            html.Div(className="stepper-line"),
            html.Div(id="tiers-stepper-fill", className="stepper-line-fill"),
            html.Div(className="stepper-dots", children=stepper_dots),
        ]),
        html.Div(className="tier-carousel", children=tier_cards),
        html.Div(className="reward-section", children=[
            html.H4("Level Up Rewards"),
            html.Div(id="tiers-levelup-list"),
        ]),
        html.Div(className="reward-section", children=[
            html.H4("Birthday Gifts"),
            html.Div(id="tiers-birthday-list"),
        ]),
    ])


def deals_layout():
    return html.Div([
        html.H1("Deals"),
        html.P("Offers that change through the week — open the app to catch them.", className="tiny"),
        html.Div(className="deal-card", children=[
            html.H4("Midweek 1-for-1"),
            html.P("Tuesday & Wednesday, 3–5pm. Bring a friend.", className="tiny", style={"margin": 0}),
            html.Span(id="deals-countdown-midweek", className="countdown", children="—"),
        ]),
        html.Div(className="deal-card", children=[
            html.H4("Refer a friend"),
            html.P("You both get a free size upgrade on their first order.", className="tiny", style={"margin": 0}),
            dcc.Link("Get your code", href="/profile", className="redeem-btn",
                     style={"display": "inline-block", "marginTop": "0.6rem", "textDecoration": "none"}),
        ]),
    ])


def order_layout():
    return html.Div(className="order-page", children=[
        html.H1("Order"),
        html.P("Pick a drink", className="tiny", style={"marginTop": 0}),
        html.Div(className="drink-grid", children=[
            html.Button(label, id=did, n_clicks=0, className="drink-tile")
            for did, label in DRINK_IDS.items()
        ]),
        html.P("Size", className="tiny", style={"marginTop": "1rem"}),
        html.Div(className="drink-grid", children=[
            html.Button(label, id=sid, n_clicks=0, className="drink-tile")
            for sid, label in SIZE_IDS.items()
        ]),
        html.P("Customization", className="tiny", style={"marginTop": "1rem"}),
        html.Div(className="drink-grid", children=[
            html.Button(label, id=cid, n_clicks=0, className="drink-tile")
            for cid, label in SUGAR_IDS.items()
        ]),
        html.Div(className="badge-line", children=[
            html.Span(id="order-priority-dot", className="lock-dot"),
            html.Span(["Priority collection ", html.Span("(unlocks at Kopi Master)", className="tiny")]),
        ]),

        html.Div(className="order-action-bar", children=[
            html.Div(className="order-pickup-line", children=[
                html.Span("\U0001f4cd"),
                html.Span("Pick up at Ang Mo Kio Hub"),
            ]),
            html.Div(className="order-action-row", children=[
                html.Div(className="order-bag", children=[
                    html.Span("\U0001f45c"),
                    html.Span("0", id="order-bag-count", className="bag-count"),
                ]),
                html.Button("Select a drink and size", id="order-add-btn", n_clicks=0,
                            className="order-add-btn", disabled=True),
            ]),
        ]),

    ])



def rewards_layout():
    reward_tiles = [
        html.Div(className="reward-tile", children=[
            html.Div([html.Strong(name), html.Div(f"{cost} points", className="cost")]),
            html.Button("Redeem", id=f"rewards-redeem-{i}", n_clicks=0, className="redeem-btn"),
        ])
        for i, (name, cost) in enumerate(REWARDS)
    ]
    return html.Div([
        html.H1("Rewards"),
        html.Div(id="rewards-surprise-banner", className="surprise-banner", style={"display": "none"},
                 children="Enjoy a free size upgrade on us \u2014 once a day."),

        html.Div(className="card", style={"marginBottom": "1rem"}, children=[
            html.Strong(id="rewards-points-balance", children="240"), " ",
            html.Span("points available", className="tiny"),
            html.Div("$1 spent = 10 points earned", className="tiny", style={"marginTop": "0.3rem"}),
        ]),
        *reward_tiles,
        html.Div(id="rewards-redeem-msg", className="redeem-msg"),
    ])


def profile_layout():
    return html.Div([
        html.H1("Profile"),
        html.Div(className="referral-box", children=[
            html.Div("Your referral code", className="tiny", style={"color": "var(--paper)", "opacity": 0.85}),
            html.Div(className="referral-code", children=[
                html.Span("YAKUN-WJ294"),
                html.Button("Copy", id="profile-copy-btn", n_clicks=0),
            ]),
            html.Div(id="profile-copy-msg", className="tiny", style={"color": "var(--egg-yolk)", "marginTop": "0.5rem", "minHeight": "1.2em"}),
            html.P("Share it — you both get a free size upgrade when they order.",
                   className="tiny", style={"color": "var(--paper)", "opacity": 0.85, "margin": "0.5rem 0 0"}),
        ]),
        html.Div(className="card", style={"marginBottom": "1rem"}, children=[
            html.Strong("SY"),
            html.Div(id="profile-tier-line", className="tiny"),
        ]),
        html.Div([
            html.Div(className="setting-row", children=[html.Span("Push notifications"),
                     html.Button(id="profile-switch-push", n_clicks=0, className="switch is-on")]),
            html.Div(className="setting-row", children=[html.Span("Deal reminders"),
                     html.Button(id="profile-switch-deals", n_clicks=0, className="switch is-on")]),
            html.Div(className="setting-row", children=[html.Span("Marketing emails"),
                     html.Button(id="profile-switch-marketing", n_clicks=0, className="switch")]),
        ]),
    ])


dash.register_page("home", path="/", layout=home_layout)
dash.register_page("tiers", path="/tiers", layout=tiers_layout)
dash.register_page("deals", path="/deals", layout=deals_layout)
dash.register_page("order", path="/order", layout=order_layout)
dash.register_page("rewards", path="/rewards", layout=rewards_layout)
dash.register_page("profile", path="/profile", layout=profile_layout)

# ---------------------------------------------------------------------------
# App-level shell (persists across page navigation)
# ---------------------------------------------------------------------------

app.layout = html.Div(className="app-shell", children=[
    dcc.Location(id="url"),
    dcc.Store(id="progress-store", data={"points": 240, "cups": 42}),
    dcc.Store(id="selection-store", data={"drink": None, "size": None, "sugar": None}),
    dcc.Store(id="settings-store", data={"push": True, "deals": True, "marketing": False}),
    dcc.Store(id="cart-store", data=0),
    dcc.Store(id="surprise-store", data=False),
    dcc.Interval(id="countdown-interval", interval=1000, n_intervals=0),

    html.Div(className="app-topbar", children=[
        html.Img(src=LOGO_SRC, className="topbar-logo"),
        html.Div(id="topbar-points-text", className="tier-chip", children="240 pts"),
    ]),

    html.Div(className="page-area", children=dash.page_container),

    html.Nav(className="bottom-nav", children=[
        dcc.Link(id=nid, href=href, className="nav-item", children=[
            html.Div(emoji, className="nav-emoji"), html.Div(label),
        ])
        for href, nid, label, emoji in NAV_ITEMS
    ]),
])

# ---------------------------------------------------------------------------
# Callbacks
# ---------------------------------------------------------------------------


@app.callback(
    [Output(nid, "className") for _, nid, _, _ in NAV_ITEMS],
    Input("url", "pathname"),
)
def highlight_nav(pathname):
    return ["nav-item is-active" if href == pathname else "nav-item" for href, _, _, _ in NAV_ITEMS]


@app.callback(Output("topbar-points-text", "children"), Input("progress-store", "data"))
def render_topbar_points(progress):
    return f"{progress['points']} pts"


@app.callback(Output("home-tier-chip", "children"), Input("progress-store", "data"))
def render_home_tier_chip(progress):
    return f"My tier: {current_tier(progress['cups'])[0]}"


@app.callback(Output("profile-tier-line", "children"), Input("progress-store", "data"))
def render_profile_tier_line(progress):
    return f"{current_tier(progress['cups'])[0]} · {progress['cups']} cups this cycle"


@app.callback(
    Output("tiers-headline", "children"),
    Output("tiers-stepper-fill", "style"),
    [Output(f"tiers-dot-{i}", "className") for i in range(len(TIERS))],
    [Output(f"tiers-card-{i}", "children") for i in range(len(TIERS))],
    Output("tiers-levelup-list", "children"),
    Output("tiers-birthday-list", "children"),
    Input("progress-store", "data"),
)
def render_tiers_page(progress):
    cups = progress["cups"]
    cur_name, cur_min = current_tier(cups)
    nxt = next_tier(cups)

    if nxt:
        headline = f"{max(0, nxt[1] - cups)} more cups to {nxt[0]}!"
        pct = min(100, round((cups - cur_min) / (nxt[1] - cur_min) * 100)) if nxt[1] != cur_min else 100
    else:
        headline = "You've reached the top tier!"
        pct = 100
    fill_style = {"width": f"{pct}%"}

    dot_classes = ["stepper-dot is-reached" if cups >= min_c else "stepper-dot" for _, min_c in TIERS]

    cards = []
    for i, (name, min_c) in enumerate(TIERS):
        if name == cur_name:
            ribbon, unlock = "MY TIER", "Valid for this 12-month cycle"
        elif cups >= min_c:
            ribbon, unlock = "ACHIEVED", "Already unlocked"
        else:
            ribbon, unlock = None, f"Unlocks at {min_c} cups"
        card_children = []
        if ribbon:
            card_children.append(html.Div(ribbon, className="ribbon"))
        card_children.append(html.Div(name, className="tier-name"))
        card_children.append(html.Div(f"Current accumulated cups: {cups}", className="cups-line"))
        card_children.append(html.Div(unlock, className="unlock-line"))
        cards.append(card_children)

    def gift_rows(items):
        return [html.Div(className="gift-row", children=[
            html.Span(emoji, className="gift-emoji"), html.Span(text),
        ]) for emoji, text in items]

    level_up = gift_rows(TIER_REWARDS[cur_name]["level_up"])
    birthday = gift_rows(TIER_REWARDS[cur_name]["birthday"])

    return (headline, fill_style, *dot_classes, *cards, level_up, birthday)


@app.callback(
    Output("selection-store", "data"),
    [Input(did, "n_clicks") for did in DRINK_IDS]
    + [Input(sid, "n_clicks") for sid in SIZE_IDS]
    + [Input(cid, "n_clicks") for cid in SUGAR_IDS],
    State("selection-store", "data"),
    prevent_initial_call=True,
)

def update_selection(*args):
    sel = dict(args[-1])
    triggered = ctx.triggered_id
    if triggered in DRINK_IDS:
        label = DRINK_IDS[triggered]
        sel["drink"] = None if sel.get("drink") == label else label
    elif triggered in SIZE_IDS:
        label = SIZE_IDS[triggered]
        sel["size"] = None if sel.get("size") == label else label
    elif triggered in SUGAR_IDS:
        label = SUGAR_IDS[triggered]
        sel["sugar"] = None if sel.get("sugar") == label else label
    return sel


@app.callback(
    [Output(did, "className") for did in DRINK_IDS]
    + [Output(sid, "className") for sid in SIZE_IDS]
    + [Output(cid, "className") for cid in SUGAR_IDS],
    Input("selection-store", "data"),
)
def render_selection(sel):
    drink_classes = ["drink-tile is-selected accent-red" if label == sel["drink"] else "drink-tile"
                      for label in DRINK_IDS.values()]
    size_classes = ["drink-tile is-selected accent-green" if label == sel["size"] else "drink-tile"
                     for label in SIZE_IDS.values()]
    sugar_classes = ["drink-tile is-selected accent-gold" if label == sel["sugar"] else "drink-tile"
                      for label in SUGAR_IDS.values()]
    return (*drink_classes, *size_classes, *sugar_classes)


@app.callback(
    Output("order-priority-dot", "className"),
    Input("progress-store", "data"),
)
def render_priority_dot(progress):
    return "lock-dot is-unlocked" if progress["cups"] >= TIERS[2][1] else "lock-dot"


@app.callback(
    Output("progress-store", "data", allow_duplicate=True),
    Output("cart-store", "data"),
    Input("order-add-btn", "n_clicks"),
    State("progress-store", "data"),
    State("selection-store", "data"),
    State("cart-store", "data"),
    prevent_initial_call=True,
)
def add_to_cart(n_clicks, progress, selection, cart):
    drink, size = selection.get("drink"), selection.get("size")
    if not drink or not size:
        return no_update, no_update
    progress = dict(progress)
    progress["cups"] += 1
    return progress, cart + 1


@app.callback(
    Output("progress-store", "data", allow_duplicate=True),
    Output("rewards-redeem-msg", "children"),
    [Input(f"rewards-redeem-{i}", "n_clicks") for i in range(len(REWARDS))],
    State("progress-store", "data"),
    prevent_initial_call=True,
)
def redeem_reward(*args):
    progress = dict(args[-1])
    triggered = ctx.triggered_id
    idx = int(triggered.split("-")[-1])
    name, cost = REWARDS[idx]
    if progress["points"] >= cost:
        progress["points"] -= cost
        return progress, f"Redeemed: {name}"
    return no_update, "Not enough points yet"


@app.callback(Output("rewards-points-balance", "children"), Input("progress-store", "data"))
def render_points_balance(progress):
    return str(progress["points"])


@app.callback(
    Output("surprise-store", "data"),
    Input("url", "pathname"),
    State("surprise-store", "data"),
)
def maybe_trigger_surprise(pathname, already_shown):
    if pathname == "/rewards" and not already_shown and random.random() < 0.6:
        return True
    return no_update


@app.callback(Output("rewards-surprise-banner", "style"), Input("surprise-store", "data"))
def render_surprise(shown):
    return {"display": "block"} if shown else {"display": "none"}


@app.callback(
    Output("settings-store", "data"),
    Input("profile-switch-push", "n_clicks"),
    Input("profile-switch-deals", "n_clicks"),
    Input("profile-switch-marketing", "n_clicks"),
    State("settings-store", "data"),
    prevent_initial_call=True,
)
def toggle_settings(a, b, c, settings):
    key_map = {"profile-switch-push": "push", "profile-switch-deals": "deals", "profile-switch-marketing": "marketing"}
    key = key_map.get(ctx.triggered_id)
    settings = dict(settings)
    if key:
        settings[key] = not settings[key]
    return settings


@app.callback(
    Output("profile-switch-push", "className"),
    Output("profile-switch-deals", "className"),
    Output("profile-switch-marketing", "className"),
    Input("settings-store", "data"),
)
def render_settings(settings):
    def cls(key):
        return "switch is-on" if settings[key] else "switch"
    return cls("push"), cls("deals"), cls("marketing")


@app.callback(
    Output("deals-countdown-midweek", "children"),
    Input("countdown-interval", "n_intervals"),
)
def tick(_n):
    now = datetime.now()
    return format_duration(MIDWEEK_END - now)

@app.callback(
    Output("order-add-btn", "children"),
    Output("order-add-btn", "disabled"),
    Input("selection-store", "data"),
)
def render_add_button(sel):
    drink, size = sel.get("drink"), sel.get("size")
    if drink and size:
        price = PRICES[drink][size]
        return f"Add to Order \u00b7 ${price:.2f}", False
    return "Select a drink and size", True


@app.callback(Output("order-bag-count", "children"), Input("cart-store", "data"))
def render_bag_count(cart):
    return str(cart)


app.clientside_callback(
    """
    function(n_clicks) {
        if (!n_clicks) { return window.dash_clientside.no_update; }
        var code = "YAKUN-WJ294";
        if (navigator.clipboard) { navigator.clipboard.writeText(code); }
        return "Code copied";
    }
    """,
    Output("profile-copy-msg", "children"),
    Input("profile-copy-btn", "n_clicks"),
)

# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True, port=8050)