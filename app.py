import streamlit as st
import time
import math
from datetime import datetime

# --- 1. ASETUKSET JA VAKIOT ---
st.set_page_config(page_title="Helsinki Taxi AI v1.0", layout="wide")

[span_4](start_span)AREAS = ["Rautatieasema", "Kamppi", "Pasila", "Lentokenttä", "Eteläsatama", "Kallio", "Olympiastadion", "Tikkurila", "Vuosaari", "Katajanokka", "Messukeskus", "Hakaniemi", "Kauppatori", "Erottaja", "Länsisatama"] #[span_4](end_span)

AGENT_DEFS = [
    [span_5](start_span){"name": "DisruptionAgent", "ttl": 120,  "emoji": "⚠️", "label": "Häiriöt"}, #[span_5](end_span)
    [span_6](start_span){"name": "TrainAgent",      "ttl": 120,  "emoji": "🚆", "label": "Junat"}, #[span_6](end_span)
    [span_7](start_span){"name": "FlightAgent",     "ttl": 300,  "emoji": "✈️", "label": "Lennot"}, #[span_7](end_span)
    [span_8](start_span){"name": "FerryAgent",      "ttl": 480,  "emoji": "⛴️", "label": "Lautat"}, #[span_8](end_span)
    [span_9](start_span){"name": "WeatherAgent",    "ttl": 600,  "emoji": "🌤️", "label": "Sää"}, #[span_9](end_span)
    [span_10](start_span){"name": "EventsAgent",     "ttl": 1800, "emoji": "📅", "label": "Tapahtumat"}, #[span_10](end_span)
    [span_11](start_span){"name": "SocialMediaAgent","ttl": 300,  "emoji": "📰", "label": "Uutiset"}, #[span_11](end_span)
    [span_12](start_span){"name": "OCRDispatchAgent","ttl": 1800, "emoji": "📸", "label": "Välitys"}, #[span_12](end_span)
    [span_13](start_span){"name": "PreorderTracker", "ttl": 300,  "emoji": "📊", "label": "Ennakot"}, #[span_13](end_span)
]

SCENARIOS = [
    [span_14](start_span){"id": 0, "label": "🚇 Metro-lakko",      "desc": "Lakko pysäyttää metron — ruuhka siirtyy takseille"}, #[span_14](end_span)
    [span_15](start_span){"id": 1, "label": "✈️  Lentokenttäruuhka", "desc": "Myöhästynyt lento + laiva + juna samaan aikaan"}, #[span_15](end_span)
    [span_16](start_span){"id": 2, "label": "🧊 Pääkallokeli",      "desc": "Tihkusade jäällä — sairaalapäivystykset täyttyvät"}, #[span_16](end_span)
    [span_17](start_span){"id": 3, "label": "🎵 Festivaali loppuu", "desc": "40 000 ihmistä poistuu Olympiastadionilta"}, #[span_17](end_span)
]

[span_18](start_span)COLORS = {"red": "#FF4B4B", "gold": "#FFD700", "blue": "#00B4D8"} #[span_18](end_span)

# --- 2. TILA JA MUISTI ---
# [span_19](start_span)Alustetaan sovelluksen tila (vastaa Reactin useState -hookeja)[span_19](end_span)
if "scenario" not in st.session_state:
    st.session_state.scenario = 0
if "cards" not in st.session_state:
    st.session_state.cards = []
if "signals" not in st.session_state:
    st.session_state.signals = []
if "slippery" not in st.session_state:
    st.session_state.slippery = 0

# --- 3. LIIKETOIMINTALOGIIKKA ---
def build_signals(scenario_id, sloc=None):
    """Generoi agenttien havaitsemat signaalit valitun skenaarion perusteella."""
    [span_20](start_span)signals = [] #[span_20](end_span)
    now = int(time.time() * 1000)

    templates = {
        [span_21](start_span)0: [{"area": "Rautatieasema", "score": 35, "urgency": 9, "reason": "🚨 LAKKO: metro seisoo — kaikki vaihtavat taksihin!", "agent": "DisruptionAgent"}, #[span_21](end_span)
            [span_22](start_span){"area": "Pasila", "score": 20, "urgency": 7, "reason": "🚆 IC123 myöhässä 28min, 340 matkustajaa saapuu", "agent": "TrainAgent"}, #[span_22](end_span)
            [span_23](start_span){"area": "Kamppi", "score": 12, "urgency": 5, "reason": "📊 Historia: LASIPALATSI — 2.8 ennakkoa klo 19:00", "agent": "PreorderTracker"}], #[span_23](end_span)
        [span_24](start_span)1: [{"area": "Lentokenttä", "score": 28, "urgency": 8, "reason": "✈️ AY001 Lontoo +65min, 389 matkustajaa saapuu T2", "agent": "FlightAgent"}, #[span_24](end_span)
            [span_25](start_span){"area": "Eteläsatama", "score": 18, "urgency": 6, "reason": "⛴️ Viking Grace saapuu 15min, ~1800 matkustajaa", "agent": "FerryAgent"}, #[span_25](end_span)
            [span_26](start_span){"area": "Tikkurila", "score": 14, "urgency": 5, "reason": "🚆 S54 saapuu 8min, 210 matkustajaa", "agent": "TrainAgent"}], #[span_26](end_span)
        [span_27](start_span)2: [{"area": "Olympiastadion", "score": 32, "urgency": 8, "reason": "🏥 Meilahti: pääkallokeli +1°C, liukkaus 90%, kaatumisia!", "agent": "WeatherAgent"}, #[span_27](end_span)
            [span_28](start_span){"area": "Kallio", "score": 22, "urgency": 7, "reason": "🏥 Kalasatama päivystys: tihkusade jäällä, ruuhkautuu", "agent": "WeatherAgent"}, #[span_28](end_span)
            [span_29](start_span){"area": "Rautatieasema", "score": 15, "urgency": 6, "reason": "🆘 PÄIVYSTYS RUUHKASSA — 8 osumaa liukkaudesta uutisissa", "agent": "SocialMediaAgent"}], #[span_29](end_span)
        [span_30](start_span)3: [{"area": "Olympiastadion", "score": 30, "urgency": 8, "reason": "🎵 Flow Festival loppuu 15min — 40 000 ihmistä poistuu!", "agent": "EventsAgent"}, #[span_30](end_span)
            [span_31](start_span){"area": "Pasila", "score": 20, "urgency": 6, "reason": "🕐 +1h ALUE AKTIVOITUU: Ydinkeskusta — 3 tolppaa aktiivisena", "agent": "PreorderTracker"}, #[span_31](end_span)
            [span_32](start_span){"area": "Messukeskus", "score": 16, "urgency": 5, "reason": "📊 Historia: MESSUKESKUS — tyypillisesti 3.1 tilausta nyt", "agent": "PreorderTracker"}], #[span_32](end_span)
    }

    [span_33](start_span)tmpl = templates.get(scenario_id, templates[0]) #[span_33](end_span)
    for t in tmpl:
        dist_km = 5
        if sloc:
            [span_34](start_span)dist_km = math.sqrt(((sloc[0]-60.17)*111)**2 + ((sloc[1]-24.94)*65)**2) #[span_34](end_span)
        [span_35](start_span)loc_bonus = 15 if dist_km < 1 else (8 if dist_km < 3 else (3 if dist_km < 7 else 0)) #[span_35](end_span)
        
        new_signal = t.copy()
        [span_36](start_span)new_signal["score"] += loc_bonus #[span_36](end_span)
        [span_37](start_span)new_signal["expires"] = now + 30 * 60 * 1000 #[span_37](end_span)
        signals.append(new_signal)
        
    [span_38](start_span)return signals #[span_38](end_span)

def build_cards(signals):
    """Kokoaa signaalit ja priorisoi alueet kojelautaa varten."""
    by_area = {}
    [span_39](start_span)for s in signals: #[span_39](end_span)
        area = s["area"]
        if area not in by_area:
            [span_40](start_span)by_area[area] = {"area": area, "score": 0, "urgency": 0, "reasons": [], "signals": []} #[span_40](end_span)
        [span_41](start_span)by_area[area]["score"] += s["score"] #[span_41](end_span)
        [span_42](start_span)by_area[area]["urgency"] = max(by_area[area]["urgency"], s["urgency"]) #[span_42](end_span)
        [span_43](start_span)by_area[area]["reasons"].append(s["reason"]) #[span_43](end_span)
        [span_44](start_span)by_area[area]["signals"].append(s) #[span_44](end_span)

    # [span_45](start_span)Lajittelu korkeimpien pisteiden mukaan[span_45](end_span)
    sorted_areas = sorted(by_area.values(), key=lambda x: x["score"], reverse=True)
    [span_46](start_span)override = next((x for x in sorted_areas if x["urgency"] >= 9), None) #[span_46](end_span)

    [span_47](start_span)card1 = override if override else (sorted_areas[0] if len(sorted_areas) > 0 else None) #[span_47](end_span)
    
    # [span_48](start_span)Etsitään uniikit alueet seuraaviin kortteihin[span_48](end_span)
    [span_49](start_span)card2 = next((x for x in sorted_areas if card1 and x["area"] != card1["area"]), None) #[span_49](end_span)
    if not card2 and len(sorted_areas) > 1: card2 = sorted_areas[1]

    [span_50](start_span)card3 = next((x for x in sorted_areas if card1 and card2 and x["area"] != card1["area"] and x["area"] != card2["area"]), None) #[span_50](end_span)
    if not card3 and len(sorted_areas) > 2: card3 = sorted_areas[2]

    cards = []
    if card1:
        [span_51](start_span)cards.append({**card1, "rank": 1, "color": "red", "label": "KRIITTISIN", "pred": False}) #[span_51](end_span)
    if card2:
        [span_52](start_span)cards.append({**card2, "rank": 2, "color": "gold", "label": "KORKEA", "pred": False}) #[span_52](end_span)
    if card3:
        [span_53](start_span)cards.append({**card3, "rank": 3, "color": "blue", "label": "ENNAKOIVA", "pred": True}) #[span_53](end_span)

    return cards

def run_simulation(scenario_id):
    """Simuloi agenttien asynkronista ajoa ja kokoaa tulokset."""
    [span_54](start_span)st.session_state.signals = build_signals(scenario_id) #[span_54](end_span)
    [span_55](start_span)st.session_state.cards = build_cards(st.session_state.signals) #[span_55](end_span)
    [span_56](start_span)st.session_state.slippery = 0.9 if scenario_id == 2 else 0 #[span_56](end_span)

# --- 4. KÄYTTÖLIITTYMÄ (UI) ---
# [span_57](start_span)Yläpalkki[span_57](end_span)
header_col1, header_col2 = st.columns([1, 1])
with header_col1:
    [span_58](start_span)st.title("Helsinki Taxi AI v1.0") #[span_58](end_span)
    [span_59](start_span)st.caption(f"{datetime.now().strftime('%d.%m.%Y %H:%M:%S')} · Helsinki 🇫🇮") #[span_59](end_span)

with header_col2:
    [span_60](start_span)if st.session_state.slippery >= 0.6: #[span_60](end_span)
        [span_61](start_span)st.error(f"🧊 PÄÄKALLOKELI {int(st.session_state.slippery * 100)}%") #[span_61](end_span)

# [span_62](start_span)Välilehdet[span_62](end_span)
[span_63](start_span)tab1, tab2, tab3 = st.tabs(["🏠 Kojelauta", "📡 Agentit", "🎮 Simulaatio"]) #[span_63](end_span)

[span_64](start_span)with tab1: #[span_64](end_span)
    st.subheader("CEO Kojelauta")
    if not st.session_state.cards:
        st.info("Aja simulaatio nähdäksesi tulokset kojelaudalla.")
    else:
        cols = st.columns(len(st.session_state.cards))
        [span_65](start_span)for idx, card in enumerate(st.session_state.cards): #[span_65](end_span)
            with cols[idx]:
                [span_66](start_span)st.markdown(f"**{card['label']}**") #[span_66](end_span)
                if card.get('pred'):
                    [span_67](start_span)st.caption("∿ ENNUSTE") #[span_67](end_span)
                [span_68](start_span)st.metric(label=card["area"], value=f"{int(card['score'])} p") #[span_68](end_span)
                [span_69](start_span)st.write(card["reasons"][0][:90]) #[span_69](end_span)

[span_70](start_span)with tab2: #[span_70](end_span)
    st.markdown("### Agenttien tila")
    [span_71](start_span)st.caption("9 agenttia ajetaan asyncio.gather():lla rinnakkain. Yksi kaatunut ei kaada muita.") #[span_71](end_span)
    [span_72](start_span)for agent in AGENT_DEFS: #[span_72](end_span)
        agent_signals = [s for s in st.session_state.signals if s["agent"] == agent["name"]]
        status_color = "green" if len(agent_signals) > 0 else "gray"
        [span_73](start_span)[span_74](start_span)st.markdown(f"**{agent['emoji']} {agent['label']}** ({agent['name']}) - TTL: {agent['ttl']}s") #[span_73](end_span)[span_74](end_span)
        if len(agent_signals) > 0:
            [span_75](start_span)st.success(f"{len(agent_signals)} signaalia löydetty") #[span_75](end_span)
            for sig in agent_signals:
                 [span_76](start_span)st.write(f"- {sig['area']}: {sig['reason'][:80]}") #[span_76](end_span)
        st.divider()

[span_77](start_span)with tab3: #[span_77](end_span)
    st.markdown("### Valitse Skenaario")
    [span_78](start_span)st.caption("Valitse skenaario ja aja simulaatio — näet kuinka agentit reagoivat eri tilanteisiin.") #[span_78](end_span)
    
    selected_scenario = st.selectbox(
        "Skenaariot", 
        options=[s["id"] for s in SCENARIOS], 
        format_func=lambda x: next(s["label"] for s in SCENARIOS if s["id"] == x)
    [span_79](start_span)) #[span_79](end_span)
    
    [span_80](start_span)st.write(next(s["desc"] for s in SCENARIOS if s["id"] == selected_scenario)) #[span_80](end_span)
    
    [span_81](start_span)if st.button("▶ Aja CEO (Simuloi)"): #[span_81](end_span)
        [span_82](start_span)[span_83](start_span)with st.spinner("⚙️ Agentit laskevat..."): #[span_82](end_span)[span_83](end_span)
            time.sleep(1)  # Simuloidaan verkkopyyntöjen/mallien viivettä
            st.session_state.scenario = selected_scenario
            run_simulation(selected_scenario)
        st.success("Laskenta valmis! Katso tulokset Kojelauta-välilehdeltä.")
