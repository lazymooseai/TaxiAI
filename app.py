ort streamlit as st
import time
import random
import math
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field

st.set_page_config(
    page_title="Helsinki Taxi AI",
    page_icon="🚕",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── Tumma teema ──────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&display=swap');
html, body, [class*="css"] {
    font-family: 'JetBrains Mono', monospace !important;
    background-color: #0e1117 !important;
    color: #FAFAFA !important;
}
.stApp { background-color: #0e1117 !important; }
.stButton>button {
    background: linear-gradient(135deg,#00B4D8,#0077aa) !important;
    color: #FAFAFA !important;
    border: none !important;
    border-radius: 12px !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-weight: 700 !important;
    font-size: 1rem !important;
    padding: 14px !important;
    width: 100% !important;
}
.stButton>button:disabled {
    background: #12151e !important;
    color: #888899 !important;
}
div[data-testid="stMetricValue"] { color: #FAFAFA !important; }
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: #888899 !important;
    font-family: 'JetBrains Mono', monospace !important;
}
.stTabs [aria-selected="true"] {
    background: #1a1d27 !important;
    color: #FAFAFA !important;
}
</style>
""", unsafe_allow_html=True)

# ── Vakiot ───────────────────────────────────────────────────
AREAS = [
    "Rautatieasema","Kamppi","Pasila","Lentokenttä","Eteläsatama",
    "Kallio","Olympiastadion","Tikkurila","Vuosaari","Katajanokka",
    "Messukeskus","Hakaniemi","Kauppatori","Erottaja","Länsisatama"
]

AGENT_DEFS = [
    {"name":"DisruptionAgent",  "ttl":120,  "emoji":"⚠️",  "label":"Häiriöt",    "source":"HSL + Fintraffic RSS"},
    {"name":"TrainAgent",       "ttl":120,  "emoji":"🚆",  "label":"Junat",      "source":"Digitraffic HKI/PSL/TKL"},
    {"name":"FlightAgent",      "ttl":300,  "emoji":"✈️",  "label":"Lennot",     "source":"Finavia EFHK, max 7 lentoa"},
    {"name":"FerryAgent",       "ttl":480,  "emoji":"⛴️",  "label":"Lautat",     "source":"Averio P1/P2/P3 + Suomenlinna"},
    {"name":"WeatherAgent",     "ttl":600,  "emoji":"🌤️",  "label":"Sää",        "source":"FMI WFS + liukkausindeksi"},
    {"name":"EventsAgent",      "ttl":1800, "emoji":"📅",  "label":"Tapahtumat", "source":"Hel.fi + MyHelsinki RSS"},
    {"name":"SocialMediaAgent", "ttl":300,  "emoji":"📰",  "label":"Uutiset",    "source":"Yle + HS RSS, max 5 / 2h"},
    {"name":"OCRDispatchAgent", "ttl":1800, "emoji":"📸",  "label":"Välitys",    "source":"Välitysnäyttö OCR (kuva/PDF/TXT)"},
    {"name":"PreorderTracker",  "ttl":300,  "emoji":"📊",  "label":"Ennakot",    "source":"Ennakkotilaushistoria 90 pv"},
]

COLORS = {"red":"#FF4B4B", "gold":"#FFD700", "blue":"#00B4D8"}

SCENARIOS = [
    {"id":0, "label":"🚇 Metro-lakko",        "desc":"Lakko pysäyttää metron — ruuhka siirtyy takseille"},
    {"id":1, "label":"✈️  Lentokenttäruuhka", "desc":"Myöhästynyt lento + laiva + juna samaan aikaan"},
    {"id":2, "label":"🧊 Pääkallokeli",        "desc":"Tihkusade jäällä — sairaalapäivystykset täyttyvät"},
    {"id":3, "label":"🎵 Festivaali loppuu",   "desc":"40 000 ihmistä poistuu Olympiastadionilta"},
]

TEMPLATES = {
    0: [
        {"area":"Rautatieasema","score":35,"urgency":9,"reason":"🚨 LAKKO: metro seisoo — kaikki vaihtavat taksihin!","agent":"DisruptionAgent"},
        {"area":"Pasila",       "score":20,"urgency":7,"reason":"🚆 IC123 myöhässä 28min, 340 matkustajaa saapuu","agent":"TrainAgent"},
        {"area":"Kamppi",       "score":12,"urgency":5,"reason":"📊 Historia: LASIPALATSI — 2.8 ennakkoa klo 19:00","agent":"PreorderTracker"},
    ],
    1: [
        {"area":"Lentokenttä",  "score":28,"urgency":8,"reason":"✈️ AY001 Lontoo +65min, 389 matkustajaa saapuu T2","agent":"FlightAgent"},
        {"area":"Eteläsatama",  "score":18,"urgency":6,"reason":"⛴️ Viking Grace saapuu 15min, ~1800 matkustajaa","agent":"FerryAgent"},
        {"area":"Tikkurila",    "score":14,"urgency":5,"reason":"🚆 S54 saapuu 8min, 210 matkustajaa","agent":"TrainAgent"},
    ],
    2: [
        {"area":"Olympiastadion","score":32,"urgency":8,"reason":"🏥 Meilahti: pääkallokeli +1C, liukkaus 90%, kaatumisia!","agent":"WeatherAgent"},
        {"area":"Kallio",        "score":22,"urgency":7,"reason":"🏥 Kalasatama päivystys: tihkusade jäällä, ruuhkautuu","agent":"WeatherAgent"},
        {"area":"Rautatieasema", "score":15,"urgency":6,"reason":"🆘 PÄIVYSTYS RUUHKASSA — 8 osumaa liukkaudesta uutisissa","agent":"SocialMediaAgent"},
    ],
    3: [
        {"area":"Olympiastadion","score":30,"urgency":8,"reason":"🎵 Flow Festival loppuu 15min — 40 000 ihmistä poistuu!","agent":"EventsAgent"},
        {"area":"Pasila",        "score":20,"urgency":6,"reason":"🕐 +1h ALUE AKTIVOITUU: Ydinkeskusta — 3 tolppaa aktiivisena","agent":"PreorderTracker"},
        {"area":"Messukeskus",   "score":16,"urgency":5,"reason":"📊 Historia: MESSUKESKUS — tyypillisesti 3.1 tilausta nyt","agent":"PreorderTracker"},
    ],
}

NEWS = {
    0: [
        {"u":9,"h":"Lakko pysäyttää metron — ruuhkaa kaikilla asemilla","s":"Yle Helsinki","t":"5min"},
        {"u":4,"h":"Helsingissä aurinkoinen viikonloppu luvassa","s":"MTV","t":"34min"},
    ],
    1: [
        {"u":6,"h":"AY001 myöhässä 65 minuuttia — T2 terminaali ruuhkautunut","s":"Iltalehti","t":"18min"},
        {"u":4,"h":"Helsingissä aurinkoinen viikonloppu luvassa","s":"MTV","t":"34min"},
    ],
    2: [
        {"u":8,"h":"Pääkallokeli: ambulanssit ylityöllistettyjä","s":"Yle Uutiset","t":"12min"},
        {"u":5,"h":"Liukastumisia raportoitu ympäri Helsinkiä","s":"HS","t":"22min"},
    ],
    3: [
        {"u":5,"h":"Flow Festival huipussaan — 40 000 kävijää","s":"HS","t":"8min"},
        {"u":3,"h":"Helsingissä aurinkoinen viikonloppu luvassa","s":"MTV","t":"34min"},
    ],
}

EVENTS = {
    0: [{"t":"SM-liiga HIFK vs TPS","v":"52 Toivonkatu","k":"🏒","state":"upcoming","mins":90,"cap":8000}],
    1: [
        {"t":"Viking Grace saapuu","v":"P1 Eteläsatama","k":"⛴️","state":"soon","mins":15,"cap":1800},
        {"t":"SM-liiga HIFK vs TPS","v":"52 Toivonkatu","k":"🏒","state":"upcoming","mins":90,"cap":8000},
    ],
    2: [{"t":"Eduskunnan täysistunto","v":"Eduskuntatalo","k":"🏛️","state":"upcoming","mins":120,"cap":200}],
    3: [
        {"t":"Flow Festival","v":"Olympiastadion","k":"🎵","state":"ending","mins":15,"cap":40000},
        {"t":"SM-liiga HIFK vs TPS","v":"52 Toivonkatu","k":"🏒","state":"upcoming","mins":90,"cap":8000},
    ],
}

HOSPITALS = [
    ("🔴 Meilahti",   "Haartmaninkatu 4"),
    ("🔴 Peijas",     "Sairaalakatu 1, Vantaa"),
    ("🟡 Malmi",      "Talvelantie 2"),
    ("🟡 Kalasatama", "Sörnäisten rantatie"),
    ("🟡 Jorvi",      "Turuntie 150, Espoo"),
]

# ── Session state ─────────────────────────────────────────────
if "scenario"   not in st.session_state: st.session_state.scenario   = 0
if "agent_log"  not in st.session_state: st.session_state.agent_log  = []
if "cards"      not in st.session_state: st.session_state.cards      = []
if "signals"    not in st.session_state: st.session_state.signals    = []
if "running"    not in st.session_state: st.session_state.running    = False
if "slippery"   not in st.session_state: st.session_state.slippery   = 0.0
if "initialized"not in st.session_state: st.session_state.initialized= False

# ── Logiikka ─────────────────────────────────────────────────
def build_signals(scenario: int) -> list:
    tmpl = TEMPLATES.get(scenario, TEMPLATES[0])
    return [dict(s) for s in tmpl]

def build_cards(signals: list) -> list:
    by_area = {}
    for s in signals:
        a = s["area"]
        if a not in by_area:
            by_area[a] = {"area":a,"score":0,"urgency":0,"reasons":[],"signals":[]}
        by_area[a]["score"]   += s["score"]
        by_area[a]["urgency"]  = max(by_area[a]["urgency"], s["urgency"])
        by_area[a]["reasons"].append(s["reason"])
        by_area[a]["signals"].append(s)
    sorted_areas = sorted(by_area.values(), key=lambda x: x["score"], reverse=True)
    override = next((x for x in sorted_areas if x["urgency"] >= 9), None)
    card1 = override or (sorted_areas[0] if sorted_areas else None)
    card2 = next((x for x in sorted_areas if x["area"] != (card1["area"] if card1 else "")), None)
    card3 = next((x for x in sorted_areas if x["area"] not in [(card1["area"] if card1 else ""), (card2["area"] if card2 else "")]), None)
    result = []
    if card1: result.append({**card1, "rank":1, "color":"red",  "label":"KRIITTISIN", "pred":False})
    if card2: result.append({**card2, "rank":2, "color":"gold", "label":"KORKEA",     "pred":False})
    if card3: result.append({**card3, "rank":3, "color":"blue", "label":"ENNAKOIVA",  "pred":True})
    return result

def run_cycle(scenario: int):
    sigs = build_signals(scenario)
    log  = []
    rng  = random.Random(scenario * 777 + 42)
    for a in AGENT_DEFS:
        agent_sigs = [s for s in sigs if s.get("agent") == a["name"]]
        log.append({
            "name":    a["name"],
            "emoji":   a["emoji"],
            "label":   a["label"],
            "status":  "ok",
            "signals": len(agent_sigs),
            "ms":      rng.randint(100, 900),
        })
    st.session_state.agent_log = log
    st.session_state.signals   = sigs
    st.session_state.cards     = build_cards(sigs)
    st.session_state.slippery  = 0.9 if scenario == 2 else 0.0
    st.session_state.running   = False

# Aja kerran sivun latautuessa
if not st.session_state.initialized:
    run_cycle(st.session_state.scenario)
    st.session_state.initialized = True

# ── Kello (EET) ───────────────────────────────────────────────
eet   = datetime.now(timezone(timedelta(hours=2)))
clock = eet.strftime("%H:%M:%S")
date  = eet.strftime("%A %-d.%-m.%Y").capitalize()

slippery_pct = int(st.session_state.slippery * 100)
scen = st.session_state.scenario

# ── YLÄPALKKI ────────────────────────────────────────────────
col_left, col_right = st.columns([1, 2])
with col_left:
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,#0e1117,#1a1d27);
                border-bottom:2px solid #2a2d3d;padding:16px 20px;
                border-radius:12px;margin-bottom:8px;">
        <div style="font-size:2.6rem;font-weight:700;
                    letter-spacing:0.05em;line-height:1;">{clock}</div>
        <div style="font-size:0.82rem;color:#888899;margin-top:4px;">
            {date} | Helsinki 🇫🇮</div>
    </div>""", unsafe_allow_html=True)

with col_right:
    badges = []
    if st.session_state.slippery >= 0.6:
        badges.append(f'<span style="background:#FF4B4B22;border:1px solid #FF4B4B;border-radius:10px;padding:6px 14px;color:#FF4B4B;font-size:0.82rem;font-weight:600;">🧊 PÄÄKALLOKELI {slippery_pct}%</span>')
    weather = {0:"+4C pilvisempi 🌧️", 1:"+8C aurinkoinen ☀️", 2:"+1C tihkusade ⛈️", 3:"+8C aurinkoinen ☀️"}.get(scen,"+8C ☀️")
    badges.append(f'<span style="background:#1a1d27;border:1px solid #2a2d3d;border-radius:12px;padding:8px 14px;font-size:0.9rem;">🌡️ {weather}</span>')
    badges.append('<span style="background:#21C55D22;border:1px solid #21C55D44;border-radius:12px;padding:8px 14px;font-size:0.78rem;color:#21C55D;">🚕 Helsinki Taxi AI v1.0</span>')
    st.markdown(f'<div style="display:flex;gap:12px;align-items:center;padding:16px 0;flex-wrap:wrap;">{"".join(badges)}</div>', unsafe_allow_html=True)

st.markdown("<hr style='border-color:#2a2d3d;margin:0 0 16px 0;'>", unsafe_allow_html=True)

# ── VÄLILEHDET ────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["🏠  Kojelauta", "📡  Agentit", "🎮  Simulaatio"])

# ════════════════════════════════════════════════════════════
# TAB 1 — KOJELAUTA
# ════════════════════════════════════════════════════════════
with tab1:

    # 3 KORTTIA
    if st.session_state.cards:
        cols = st.columns(3)
        for i, card in enumerate(st.session_state.cards):
            color = COLORS[card["color"]]
            rank_emoji = {"red":"🔴","gold":"🟡","blue":"🔵"}[card["color"]]
            urgency = card["urgency"]
            urg_label = "⛔ OVERRIDE" if urgency>=9 else "🔴 KRIITTINEN" if urgency>=7 else "🟠 KORKEA" if urgency>=5 else "🟡 NORMAALI"
            pred_badge = '<span style="color:#00B4D8;margin-left:8px;font-size:0.65rem;">~ ENNUSTE</span>' if card["pred"] else ""
            reason = card["reasons"][0][:90] if card["reasons"] else ""
            with cols[i]:
                st.markdown(f"""
                <div style="background:#1a1d27;border-radius:16px;padding:20px;
                            border-left:5px solid {color};min-height:180px;">
                    <div style="font-size:0.7rem;letter-spacing:0.15em;text-transform:uppercase;
                                opacity:0.7;margin-bottom:4px;">
                        {rank_emoji} {card["label"]}{pred_badge}
                    </div>
                    <div style="font-size:1.5rem;font-weight:700;color:{color};
                                margin-bottom:6px;">{card["area"]}</div>
                    <div style="font-size:0.8rem;color:#888899;margin-bottom:10px;">
                        Pisteet: {card["score"]}</div>
                    <div style="display:inline-block;padding:2px 10px;border-radius:20px;
                                font-size:0.72rem;font-weight:600;
                                background:{color}22;color:{color};margin-bottom:10px;">
                        {urg_label}
                    </div>
                    <div style="font-size:0.82rem;line-height:1.5;
                                border-top:1px solid rgba(255,255,255,0.08);padding-top:10px;">
                        {reason}
                    </div>
                </div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    # PÄÄKALLOKELI-BANNERI
    if st.session_state.slippery >= 0.6:
        hosp_html = "".join([
            f'<div><strong>{n}</strong><br>'
            f'<span style="color:#888899;font-size:0.72rem;">{a}</span></div>'
            for n, a in HOSPITALS
        ])
        bar_w = slippery_pct
        st.markdown(f"""
        <div style="background:#1a0000;border:1px solid #FF4B4B;
                    border-left:4px solid #FF4B4B;border-radius:10px;
                    padding:14px 16px;margin-bottom:12px;">
            <div style="font-weight:700;margin-bottom:8px;">
                🏥 Sairaalatilanne - pääkallokeli</div>
            <div style="display:flex;align-items:center;gap:12px;margin-bottom:10px;">
                <span style="font-size:0.82rem;color:#888899;">Liukkausindeksi:</span>
                <div style="flex:1;background:#2a2d3d;border-radius:4px;height:10px;overflow:hidden;">
                    <div style="width:{bar_w}%;height:100%;
                                background:linear-gradient(90deg,#FFD700,#FF4B4B);
                                border-radius:4px;"></div>
                </div>
                <span style="color:#FF4B4B;font-weight:700;">{slippery_pct}%</span>
            </div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;font-size:0.8rem;">
                {hosp_html}
            </div>
        </div>""", unsafe_allow_html=True)

    # AGENTTIPILLERIT
    if st.session_state.agent_log:
        pills = ""
        for a in st.session_state.agent_log:
            has = a["signals"] > 0
            bg    = "#21C55D22" if has else "rgba(255,255,255,0.06)"
            color = "#21C55D"   if has else "#888899"
            border= "#21C55D44" if has else "transparent"
            cnt   = f" ({a['signals']})" if has else ""
            pills += (f'<span style="display:inline-flex;align-items:center;gap:4px;'
                      f'padding:3px 10px;border-radius:20px;font-size:0.72rem;'
                      f'background:{bg};color:{color};border:1px solid {border};">'
                      f'{a["emoji"]} {a["label"]}{cnt}</span>')
        st.markdown(f'<div style="display:flex;flex-wrap:wrap;gap:4px;margin-bottom:12px;">{pills}</div>',
                    unsafe_allow_html=True)

    # UUTISET + TAPAHTUMAT
    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div style="font-size:0.72rem;letter-spacing:0.12em;text-transform:uppercase;color:#888899;margin-bottom:8px;">📰 Tuoreet uutiset</div>', unsafe_allow_html=True)
        for n in NEWS.get(scen, []):
            u = n["u"]
            border = "#FF4B4B" if u>=7 else "#FF8C00" if u>=5 else "#2a2d3d"
            icon   = "🚨" if u>=7 else "⚠️" if u>=5 else "📰"
            st.markdown(f"""
            <div style="background:#1a1d27;border-radius:10px;padding:10px 14px;
                        margin-bottom:6px;border-left:3px solid {border};font-size:0.85rem;">
                {icon} {n["h"]}
                <div style="font-size:0.72rem;color:#888899;margin-top:3px;">
                    {n["s"]} - {n["t"]} sitten</div>
            </div>""", unsafe_allow_html=True)

    with c2:
        st.markdown('<div style="font-size:0.72rem;letter-spacing:0.12em;text-transform:uppercase;color:#888899;margin-bottom:8px;">📅 Tapahtumat tänään</div>', unsafe_allow_html=True)
        for e in EVENTS.get(scen, []):
            state_color = {"ending":"#FF4B4B","soon":"#FFD700","upcoming":"#00B4D8"}.get(e["state"],"#888899")
            state_label = {"ending":f"⏱ {e['mins']}min","soon":f"🔜 {e['mins']}min","upcoming":f"📅 {e['mins']}min"}.get(e["state"],"")
            cap = f"{e['cap']//1000}k" if e["cap"]>=1000 else str(e["cap"])
            st.markdown(f"""
            <div style="display:flex;align-items:center;gap:10px;padding:8px 0;
                        border-bottom:1px solid #2a2d3d;font-size:0.85rem;">
                <span style="color:{state_color};min-width:52px;font-weight:600;">{state_label}</span>
                <span style="font-size:1rem;">{e["k"]}</span>
                <div>
                    <div style="font-weight:600;">{e["t"]}</div>
                    <div style="font-size:0.72rem;color:#888899;">{e["v"]} - ~{cap} hlö</div>
                </div>
            </div>""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════
# TAB 2 — AGENTIT
# ════════════════════════════════════════════════════════════
with tab2:
    st.markdown('<div style="font-size:0.78rem;color:#888899;margin-bottom:12px;">9 agenttia ajetaan <strong style="color:#00B4D8;">asyncio.gather()</strong>:lla rinnakkain. Yksi kaatunut ei kaada muita.</div>', unsafe_allow_html=True)

    for a_def in AGENT_DEFS:
        log = next((l for l in st.session_state.agent_log if l["name"] == a_def["name"]), None)
        has_sigs = log and log["signals"] > 0
        border_color = "#21C55D" if has_sigs else "#2a2d3d"
        status_html = ""
        if log:
            status_html = (f'<span style="color:#21C55D;margin-right:12px;">✓ OK {log["ms"]}ms</span>'
                          f'<span style="color:{"#00B4D8" if has_sigs else "#888899"};">{log["signals"]} signaalia</span>')
        else:
            status_html = '<span style="color:#888899;">⏳ odottaa...</span>'

        sigs_html = ""
        if has_sigs:
            for s in [sig for sig in st.session_state.signals if sig.get("agent") == a_def["name"]]:
                sigs_html += (f'<div style="margin-top:8px;padding:8px 10px;background:#12151e;'
                              f'border-radius:8px;font-size:0.78rem;">'
                              f'<span style="color:#00B4D8;margin-right:8px;">{s["area"]}</span>'
                              f'<span style="color:#888899;">+{s["score"]}p U{s["urgency"]}</span>'
                              f'<div style="color:#CCCCDD;margin-top:2px;">{s["reason"][:80]}</div></div>')

        st.markdown(f"""
        <div style="background:#1a1d27;border-radius:14px;padding:14px 16px;
                    margin-bottom:10px;border-left:4px solid {border_color};">
            <div style="display:flex;justify-content:space-between;align-items:center;">
                <div>
                    <span style="font-size:1.2rem;margin-right:8px;">{a_def["emoji"]}</span>
                    <strong>{a_def["label"]}</strong>
                    <span style="color:#888899;font-size:0.75rem;margin-left:8px;">{a_def["name"]}</span>
                </div>
                <div style="text-align:right;font-size:0.75rem;">{status_html}</div>
            </div>
            <div style="font-size:0.75rem;color:#888899;margin-top:6px;">
                TTL: {a_def["ttl"]}s &nbsp;|&nbsp; {a_def["source"]}
            </div>
            {sigs_html}
        </div>""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════
# TAB 3 — SIMULAATIO
# ════════════════════════════════════════════════════════════
with tab3:
    st.markdown('<div style="font-size:0.82rem;color:#888899;margin-bottom:16px;">Valitse skenaario ja paina <strong style="color:#00B4D8;">Aja CEO</strong> — näet kuinka agentit reagoivat eri tilanteisiin.</div>', unsafe_allow_html=True)

    sc_cols = st.columns(2)
    for i, s in enumerate(SCENARIOS):
        with sc_cols[i % 2]:
            is_sel = st.session_state.scenario == s["id"]
            border = "#00B4D8" if is_sel else "#2a2d3d"
            bg     = "#1a2a3a" if is_sel else "#1a1d27"
            if st.button(f'{s["label"]}', key=f'scen_{s["id"]}'):
                st.session_state.scenario = s["id"]
                st.rerun()
            st.markdown(f'<div style="font-size:0.78rem;color:#888899;margin-top:-8px;margin-bottom:8px;">{s["desc"]}</div>',
                        unsafe_allow_html=True)

    if st.button("▶  Aja CEO", disabled=st.session_state.running, key="run_ceo"):
        st.session_state.running = True
        run_cycle(st.session_state.scenario)
        st.rerun()

    if st.session_state.cards:
        st.markdown('<div style="font-size:0.78rem;color:#888899;margin:16px 0 10px;">CEO-tulos:</div>', unsafe_allow_html=True)
        for card in st.session_state.cards:
            color = COLORS[card["color"]]
            rank_emoji = {"red":"🔴","gold":"🟡","blue":"🔵"}[card["color"]]
            pred = " - ~ Ennuste" if card["pred"] else ""
            reason = card["reasons"][0][:90] if card["reasons"] else ""
            st.markdown(f"""
            <div style="display:flex;gap:12px;padding:10px 14px;background:#1a1d27;
                        border-radius:10px;margin-bottom:8px;border-left:4px solid {color};">
                <div style="font-size:1.5rem;">{rank_emoji}</div>
                <div style="flex:1;">
                    <div style="font-weight:700;color:{color};">{card["area"]}</div>
                    <div style="font-size:0.78rem;color:#888899;">
                        Pisteet: {card["score"]} - Urgency: {card["urgency"]}/10{pred}</div>
                    <div style="font-size:0.8rem;margin-top:4px;">{reason}</div>
                </div>
            </div>""", unsafe_allow_html=True)

# ── Autoreload kellolle ───────────────────────────────────────
time.sleep(1)
st.rerun()
