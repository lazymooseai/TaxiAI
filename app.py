import { useState, useEffect, useRef } from "react";

const AREAS = ["Rautatieasema","Kamppi","Pasila","Lentokenttä","Eteläsatama","Kallio","Olympiastadion","Tikkurila","Vuosaari","Katajanokka","Messukeskus","Hakaniemi","Kauppatori","Erottaja","Länsisatama"];

const AGENT_DEFS = [
  {name:"DisruptionAgent", ttl:120,  emoji:"⚠️",  label:"Häiriöt"},
  {name:"TrainAgent",      ttl:120,  emoji:"🚆",  label:"Junat"},
  {name:"FlightAgent",     ttl:300,  emoji:"✈️",  label:"Lennot"},
  {name:"FerryAgent",      ttl:480,  emoji:"⛴️",  label:"Lautat"},
  {name:"WeatherAgent",    ttl:600,  emoji:"🌤️",  label:"Sää"},
  {name:"EventsAgent",     ttl:1800, emoji:"📅",  label:"Tapahtumat"},
  {name:"SocialMediaAgent",ttl:300,  emoji:"📰",  label:"Uutiset"},
  {name:"OCRDispatchAgent",ttl:1800, emoji:"📸",  label:"Välitys"},
  {name:"PreorderTracker", ttl:300,  emoji:"📊",  label:"Ennakot"},
];

function seeded(seed) {
  let s = seed;
  return () => { s = (s * 1664525 + 1013904223) & 0xffffffff; return (s >>> 0) / 0xffffffff; };
}

function buildSignals(scenario, sloc) {
  const rng = seeded(scenario * 1337 + 42);
  const signals = [];
  const now = Date.now();

  const templates = {
    0: [{area:"Rautatieasema",score:35,urgency:9,reason:"🚨 LAKKO: metro seisoo — kaikki vaihtavat taksihin!",agent:"DisruptionAgent"},
        {area:"Pasila",score:20,urgency:7,reason:"🚆 IC123 myöhässä 28min, 340 matkustajaa saapuu",agent:"TrainAgent"},
        {area:"Kamppi",score:12,urgency:5,reason:"📊 Historia: LASIPALATSI — 2.8 ennakkoa klo 19:00",agent:"PreorderTracker"}],
    1: [{area:"Lentokenttä",score:28,urgency:8,reason:"✈️ AY001 Lontoo +65min, 389 matkustajaa saapuu T2",agent:"FlightAgent"},
        {area:"Eteläsatama",score:18,urgency:6,reason:"⛴️ Viking Grace saapuu 15min, ~1800 matkustajaa",agent:"FerryAgent"},
        {area:"Tikkurila",score:14,urgency:5,reason:"🚆 S54 saapuu 8min, 210 matkustajaa",agent:"TrainAgent"}],
    2: [{area:"Olympiastadion",score:32,urgency:8,reason:"🏥 Meilahti: pääkallokeli +1°C, liukkaus 90%, kaatumisia!",agent:"WeatherAgent"},
        {area:"Kallio",score:22,urgency:7,reason:"🏥 Kalasatama päivystys: tihkusade jäällä, ruuhkautuu",agent:"WeatherAgent"},
        {area:"Rautatieasema",score:15,urgency:6,reason:"🆘 PÄIVYSTYS RUUHKASSA — 8 osumaa liukkaudesta uutisissa",agent:"SocialMediaAgent"}],
    3: [{area:"Olympiastadion",score:30,urgency:8,reason:"🎵 Flow Festival loppuu 15min — 40 000 ihmistä poistuu!",agent:"EventsAgent"},
        {area:"Pasila",score:20,urgency:6,reason:"🕐 +1h ALUE AKTIVOITUU: Ydinkeskusta — 3 tolppaa aktiivisena",agent:"PreorderTracker"},
        {area:"Messukeskus",score:16,urgency:5,reason:"📊 Historia: MESSUKESKUS — tyypillisesti 3.1 tilausta nyt",agent:"PreorderTracker"}],
  };

  const tmpl = templates[scenario] || templates[0];
  tmpl.forEach(t => {
    const areaIdx = AREAS.indexOf(t.area);
    const distKm = sloc ? Math.sqrt(Math.pow((sloc[0]-60.17)*111,2) + Math.pow((sloc[1]-24.94)*65,2)) : 5;
    const locBonus = distKm < 1 ? 15 : distKm < 3 ? 8 : distKm < 7 ? 3 : 0;
    signals.push({...t, score: t.score + locBonus, expires: now + 30*60*1000});
  });
  return signals;
}

function buildCards(signals) {
  const byArea = {};
  signals.forEach(s => {
    if (!byArea[s.area]) byArea[s.area] = {area:s.area,score:0,urgency:0,reasons:[],signals:[]};
    byArea[s.area].score   += s.score;
    byArea[s.area].urgency  = Math.max(byArea[s.area].urgency, s.urgency);
    byArea[s.area].reasons.push(s.reason);
    byArea[s.area].signals.push(s);
  });
  const sorted = Object.values(byArea).sort((a,b)=>b.score-a.score);
  const override = sorted.find(x=>x.urgency>=9);
  const card1 = override || sorted[0];
  const card2 = sorted.find(x=>x.area !== card1?.area) || sorted[1];
  const card3 = sorted.find(x=>x.area !== card1?.area && x.area !== card2?.area) || sorted[2];
  return [
    card1 ? {...card1, rank:1, color:"red",  label:"KRIITTISIN", pred:false} : null,
    card2 ? {...card2, rank:2, color:"gold", label:"KORKEA",     pred:false} : null,
    card3 ? {...card3, rank:3, color:"blue", label:"ENNAKOIVA",  pred:true}  : null,
  ].filter(Boolean);
}

const COLORS = {red:"#FF4B4B", gold:"#FFD700", blue:"#00B4D8"};
const SCENARIOS = [
  {id:0, label:"🚇 Metro-lakko",      desc:"Lakko pysäyttää metron — ruuhka siirtyy takseille"},
  {id:1, label:"✈️  Lentokenttäruuhka", desc:"Myöhästynyt lento + laiva + juna samaan aikaan"},
  {id:2, label:"🧊 Pääkallokeli",      desc:"Tihkusade jäällä — sairaalapäivystykset täyttyvät"},
  {id:3, label:"🎵 Festivaali loppuu", desc:"40 000 ihmistä poistuu Olympiastadionilta"},
];

export default function TaxiDemo() {
  const [scenario,  setScenario]  = useState(0);
  const [location,  setLocation]  = useState(null);
  const [agentLog,  setAgentLog]  = useState([]);
  const [cards,     setCards]     = useState([]);
  const [signals,   setSignals]   = useState([]);
  const [running,   setRunning]   = useState(false);
  const [tick,      setTick]      = useState(0);
  const [slippery,  setSlippery]  = useState(0);
  const [tab,       setTab]       = useState("kojelauta");
  const tickRef = useRef(null);

  const runCycle = (scen, loc) => {
    setRunning(true);
    setAgentLog([]);
    const sigs = buildSignals(scen, loc);
    const rng = seeded(scen * 777 + Date.now() % 1000);
    let delay = 0;
    AGENT_DEFS.forEach((a, i) => {
      delay += Math.floor(rng() * 600 + 100);
      setTimeout(() => {
        const agentSigs = sigs.filter(s => {
          if (a.name==="DisruptionAgent") return s.agent===a.name;
          if (a.name==="TrainAgent")      return s.agent===a.name;
          if (a.name==="FlightAgent")     return s.agent===a.name;
          if (a.name==="FerryAgent")      return s.agent===a.name;
          if (a.name==="WeatherAgent")    return s.agent===a.name;
          if (a.name==="EventsAgent")     return s.agent===a.name;
          if (a.name==="SocialMediaAgent")return s.agent===a.name;
          if (a.name==="PreorderTracker") return s.agent===a.name;
          return false;
        });
        setAgentLog(prev => [...prev, {
          name: a.name, emoji: a.emoji, label: a.label,
          status: "ok", signals: agentSigs.length,
          ms: Math.floor(rng()*800+100),
        }]);
        if (i === AGENT_DEFS.length - 1) {
          setSignals(sigs);
          setCards(buildCards(sigs));
          if (scen===2) setSlippery(0.9);
          else setSlippery(0);
          setRunning(false);
        }
      }, delay);
    });
  };

  useEffect(() => {
    runCycle(scenario, location);
    tickRef.current = setInterval(() => setTick(t=>t+1), 1000);
    return () => clearInterval(tickRef.current);
  }, []);

  const now = new Date();
  const hki = new Date(now.getTime() + 2*3600*1000);
  const clockStr = hki.toLocaleTimeString("fi-FI",{hour:"2-digit",minute:"2-digit",second:"2-digit"});
  const dateStr  = hki.toLocaleDateString("fi-FI",{weekday:"long",day:"numeric",month:"numeric",year:"numeric"});

  const slipperyPct = Math.round(slippery*100);

  return (
    <div style={{background:"#0e1117",minHeight:"100vh",fontFamily:"'JetBrains Mono',monospace",color:"#FAFAFA",fontSize:"14px"}}>

      {/* Yläpalkki */}
      <div style={{background:"linear-gradient(135deg,#0e1117,#1a1d27)",borderBottom:"2px solid #2a2d3d",padding:"12px 20px",display:"flex",alignItems:"center",justifyContent:"space-between",position:"sticky",top:0,zIndex:100}}>
        <div>
          <div style={{fontSize:"2.6rem",fontWeight:700,letterSpacing:"0.05em",lineHeight:1}}>{clockStr}</div>
          <div style={{fontSize:"0.82rem",color:"#888899",marginTop:2}}>{dateStr} · Helsinki 🇫🇮</div>
        </div>
        <div style={{display:"flex",gap:12,alignItems:"center"}}>
          {slippery >= 0.6 && (
            <div style={{background:"#FF4B4B22",border:"1px solid #FF4B4B",borderRadius:10,padding:"6px 14px",color:"#FF4B4B",fontSize:"0.82rem",fontWeight:600}}>
              🧊 PÄÄKALLOKELI {slipperyPct}%
            </div>
          )}
          <div style={{background:"#1a1d27",border:"1px solid #2a2d3d",borderRadius:12,padding:"8px 14px",fontSize:"0.9rem"}}>
            🌡️ {scenario===2 ? "+1°C tihkusade ⛈️" : scenario===0 ? "+4°C pilvisempi 🌧️" : "+8°C aurinkoinen ☀️"}
          </div>
          <div style={{background:"#21C55D22",border:"1px solid #21C55D44",borderRadius:12,padding:"8px 14px",fontSize:"0.78rem",color:"#21C55D"}}>
            🚕 Helsinki Taxi AI v1.0
          </div>
        </div>
      </div>

      {/* Välilehdet */}
      <div style={{display:"flex",gap:4,padding:"8px 20px",background:"#12151e",borderBottom:"1px solid #2a2d3d"}}>
        {[["kojelauta","🏠 Kojelauta"],["agentit","📡 Agentit"],["simulaatio","🎮 Simulaatio"]].map(([id,lbl])=>(
          <button key={id} onClick={()=>setTab(id)} style={{
            padding:"7px 16px",borderRadius:8,border:"none",cursor:"pointer",fontSize:"0.82rem",fontFamily:"inherit",
            background:tab===id?"#1a1d27":"transparent",
            color:tab===id?"#FAFAFA":"#888899",
            outline:tab===id?"1px solid #2a2d3d":"none",
          }}>{lbl}</button>
        ))}
      </div>

      <div style={{padding:"16px 20px",maxWidth:1200,margin:"0 auto"}}>

        {/* ── TAB: KOJELAUTA ── */}
        {tab==="kojelauta" && (
          <>
            {/* 3 korttia */}
            {running && (
              <div style={{textAlign:"center",padding:"30px",color:"#888899",fontSize:"0.9rem"}}>
                <div style={{fontSize:"1.5rem",marginBottom:8}}>⚙️</div>
                Agentit laskevat... asyncio.gather() käynnissä
              </div>
            )}
            {!running && cards.length > 0 && (
              <div style={{display:"grid",gridTemplateColumns:"1fr 1fr 1fr",gap:12,marginBottom:16}}>
                {cards.map(card => {
                  const color = COLORS[card.color];
                  return (
                    <div key={card.area} style={{background:"#1a1d27",borderRadius:16,padding:20,borderLeft:`5px solid ${color}`,position:"relative",overflow:"hidden"}}>
                      <div style={{fontSize:"0.7rem",letterSpacing:"0.15em",textTransform:"uppercase",opacity:0.7,marginBottom:4}}>
                        {card.color==="red"?"🔴":"card.color"==="gold"?"🟡":"🔵"}{" "}
                        {card.label}
                        {card.pred && <span style={{color:"#00B4D8",marginLeft:8,fontSize:"0.65rem"}}>∿ ENNUSTE</span>}
                      </div>
                      <div style={{fontSize:"1.5rem",fontWeight:700,color,marginBottom:6}}>{card.area}</div>
                      <div style={{fontSize:"0.8rem",color:"#888899",marginBottom:10}}>Pisteet: {card.score.toFixed(0)}</div>
                      <div style={{display:"inline-block",padding:"2px 10px",borderRadius:20,fontSize:"0.72rem",fontWeight:600,background:color+"22",color,marginBottom:10}}>
                        {card.urgency>=9?"⛔ OVERRIDE":card.urgency>=7?"🔴 KRIITTINEN":card.urgency>=5?"🟠 KORKEA":"🟡 NORMAALI"}
                      </div>
                      <div style={{fontSize:"0.82rem",lineHeight:1.5,borderTop:"1px solid rgba(255,255,255,0.08)",paddingTop:10}}>
                        {card.reasons[0]?.slice(0,90)}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}

            {/* Pääkallokeli-banneri */}
            {slippery >= 0.6 && (
              <div style={{background:"#1a0000",border:"1px solid #FF4B4B",borderLeft:"4px solid #FF4B4B",borderRadius:10,padding:"14px 16px",marginBottom:12}}>
                <div style={{fontWeight:700,marginBottom:8}}>🏥 Sairaalatilanne — pääkallokeli</div>
                <div style={{display:"flex",alignItems:"center",gap:12,marginBottom:10}}>
                  <span style={{fontSize:"0.82rem",color:"#888899"}}>Liukkausindeksi:</span>
                  <div style={{flex:1,background:"#2a2d3d",borderRadius:4,height:10,overflow:"hidden"}}>
                    <div style={{width:`${slipperyPct}%`,height:"100%",background:"linear-gradient(90deg,#FFD700,#FF4B4B)",borderRadius:4}}/>
                  </div>
                  <span style={{color:"#FF4B4B",fontWeight:700}}>{slipperyPct}%</span>
                </div>
                <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:8,fontSize:"0.8rem"}}>
                  {[["🔴 Meilahti","Haartmaninkatu 4"],["🔴 Peijas","Sairaalakatu 1 (Vantaa)"],["🟡 Malmi","Talvelantie 2"],["🟡 Kalasatama","Sörnäisten rantatie"]].map(([n,a])=>(
                    <div key={n}><strong>{n}</strong><br/><span style={{color:"#888899",fontSize:"0.72rem"}}>{a}</span></div>
                  ))}
                </div>
              </div>
            )}

            {/* Agenttistatus-pillerit */}
            <div style={{display:"flex",flexWrap:"wrap",gap:4,marginBottom:12}}>
              {agentLog.map(a=>(
                <span key={a.name} style={{
                  display:"inline-flex",alignItems:"center",gap:4,
                  padding:"3px 10px",borderRadius:20,fontSize:"0.72rem",
                  background:a.signals>0?"#21C55D22":"rgba(255,255,255,0.06)",
                  color:a.signals>0?"#21C55D":"#888899",
                  border:"1px solid",borderColor:a.signals>0?"#21C55D44":"transparent",
                }}>
                  {a.emoji} {a.label} {a.signals>0?`(${a.signals})`:""}
                </span>
              ))}
            </div>

            {/* Uutiset + tapahtumat */}
            <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:12}}>
              <div>
                <div style={{fontSize:"0.72rem",letterSpacing:"0.12em",textTransform:"uppercase",color:"#888899",marginBottom:8}}>📰 Tuoreet uutiset</div>
                {[
                  scenario===0&&{u:9,h:"Lakko pysäyttää metron — ruuhkaa kaikilla asemilla",s:"Yle Helsinki",t:"5min"},
                  scenario===2&&{u:7,h:"Pääkallokeli: ambulanssit ylityöllistettyjä",s:"Yle Uutiset",t:"12min"},
                  scenario===3&&{u:5,h:"Flow Festival huipussaan — 40 000 kävijää",s:"HS",t:"8min"},
                  {u:3,h:"Helsingissä aurinkoinen viikonloppu luvassa",s:"MTV",t:"34min"},
                ].filter(Boolean).map((n,i)=>(
                  <div key={i} style={{background:"#1a1d27",borderRadius:10,padding:"10px 14px",marginBottom:6,borderLeft:`3px solid ${n.u>=7?"#FF4B4B":n.u>=5?"#FF8C00":"#2a2d3d"}`,fontSize:"0.85rem"}}>
                    {n.u>=7?"🚨":n.u>=5?"⚠️":"📰"} {n.h}
                    <div style={{fontSize:"0.72rem",color:"#888899",marginTop:3}}>{n.s} · {n.t} sitten</div>
                  </div>
                ))}
              </div>
              <div>
                <div style={{fontSize:"0.72rem",letterSpacing:"0.12em",textTransform:"uppercase",color:"#888899",marginBottom:8}}>📅 Tapahtumat tänään</div>
                {[
                  scenario===3&&{t:"Flow Festival",v:"Olympiastadion",k:"🎵",state:"ending",mins:15,cap:40000},
                  scenario===1&&{t:"Viking Grace saapuu",v:"P1 Eteläsatama",k:"⛴️",state:"soon",mins:15,cap:1800},
                  {t:"SM-liiga HIFK vs TPS",v:"52 Toivonkatu",k:"🏒",state:"upcoming",mins:90,cap:8000},
                  {t:"Eduskunnan täysistunto",v:"Eduskuntatalo",k:"🏛️",state:"upcoming",mins:120,cap:200},
                ].filter(Boolean).map((e,i)=>(
                  <div key={i} style={{display:"flex",alignItems:"center",gap:10,padding:"8px 0",borderBottom:"1px solid #2a2d3d",fontSize:"0.85rem"}}>
                    <span style={{color:e.state==="ending"?"#FF4B4B":e.state==="soon"?"#FFD700":"#00B4D8",minWidth:52,fontWeight:600}}>
                      {e.state==="ending"?`⏱ ${e.mins}min`:e.state==="soon"?`🔜 ${e.mins}min`:`📅 ${e.mins}min`}
                    </span>
                    <span style={{fontSize:"1rem"}}>{e.k}</span>
                    <div>
                      <div style={{fontWeight:600}}>{e.t}</div>
                      <div style={{fontSize:"0.72rem",color:"#888899"}}>{e.v} · ~{e.cap>=1000?`${(e.cap/1000).toFixed(0)}k`:e.cap} hlö</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </>
        )}

        {/* ── TAB: AGENTIT ── */}
        {tab==="agentit" && (
          <div>
            <div style={{fontSize:"0.78rem",color:"#888899",marginBottom:12}}>
              9 agenttia ajetaan <strong style={{color:"#00B4D8"}}>asyncio.gather()</strong>:lla rinnakkain. Yksi kaatunut ei kaada muita.
            </div>
            {AGENT_DEFS.map(a=>{
              const log = agentLog.find(l=>l.name===a.name);
              return (
                <div key={a.name} style={{background:"#1a1d27",borderRadius:14,padding:"14px 16px",marginBottom:10,borderLeft:`4px solid ${log?.signals>0?"#21C55D":"#2a2d3d"}`}}>
                  <div style={{display:"flex",justifyContent:"space-between",alignItems:"center"}}>
                    <div>
                      <span style={{fontSize:"1.2rem",marginRight:8}}>{a.emoji}</span>
                      <strong>{a.label}</strong>
                      <span style={{color:"#888899",fontSize:"0.75rem",marginLeft:8}}>{a.name}</span>
                    </div>
                    <div style={{textAlign:"right",fontSize:"0.75rem"}}>
                      {log ? (
                        <>
                          <span style={{color:"#21C55D",marginRight:12}}>✓ OK {log.ms}ms</span>
                          <span style={{color:log.signals>0?"#00B4D8":"#888899"}}>{log.signals} signaalia</span>
                        </>
                      ) : <span style={{color:"#888899"}}>⏳ odottaa...</span>}
                    </div>
                  </div>
                  <div style={{fontSize:"0.75rem",color:"#888899",marginTop:6}}>
                    TTL: {a.ttl}s &nbsp;|&nbsp;
                    {a.name==="DisruptionAgent" && "HSL + Fintraffic RSS"}
                    {a.name==="TrainAgent"      && "Digitraffic HKI/PSL/TKL"}
                    {a.name==="FlightAgent"     && "Finavia EFHK, max 7 lentoa"}
                    {a.name==="FerryAgent"      && "Averio P1/P2/P3 + Suomenlinna"}
                    {a.name==="WeatherAgent"    && "FMI WFS Kaisaniemi + liukkausindeksi"}
                    {a.name==="EventsAgent"     && "Hel.fi + MyHelsinki RSS"}
                    {a.name==="SocialMediaAgent"&& "Yle + HS RSS, max 5 uutista 2h"}
                    {a.name==="OCRDispatchAgent"&& "Välitysnäyttö OCR (kuva/PDF/TXT)"}
                    {a.name==="PreorderTracker" && "Ennakkotilaushistoria (90 pv)"}
                  </div>
                  {log?.signals>0 && signals.filter(s=>s.agent===a.name).map((s,i)=>(
                    <div key={i} style={{marginTop:8,padding:"8px 10px",background:"#12151e",borderRadius:8,fontSize:"0.78rem"}}>
                      <span style={{color:"#00B4D8",marginRight:8}}>{s.area}</span>
                      <span style={{color:"#888899"}}>+{s.score.toFixed(0)}p U{s.urgency}</span>
                      <div style={{color:"#CCCCDD",marginTop:2}}>{s.reason.slice(0,80)}</div>
                    </div>
                  ))}
                </div>
              );
            })}
          </div>
        )}

        {/* ── TAB: SIMULAATIO ── */}
        {tab==="simulaatio" && (
          <div>
            <div style={{fontSize:"0.82rem",color:"#888899",marginBottom:16}}>
              Valitse skenaario ja paina <strong style={{color:"#00B4D8"}}>▶ Aja CEO</strong> — näet kuinka agentit reagoivat eri tilanteisiin.
            </div>
            <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:10,marginBottom:16}}>
              {SCENARIOS.map(s=>(
                <div key={s.id} onClick={()=>setScenario(s.id)} style={{
                  background:scenario===s.id?"#1a2a3a":"#1a1d27",
                  border:`2px solid ${scenario===s.id?"#00B4D8":"#2a2d3d"}`,
                  borderRadius:12,padding:"14px 16px",cursor:"pointer",
                }}>
                  <div style={{fontWeight:700,marginBottom:4}}>{s.label}</div>
                  <div style={{fontSize:"0.78rem",color:"#888899"}}>{s.desc}</div>
                </div>
              ))}
            </div>

            <button
              onClick={()=>runCycle(scenario, location)}
              disabled={running}
              style={{
                display:"block",width:"100%",padding:"14px",
                background:running?"#12151e":"linear-gradient(135deg,#00B4D8,#0077aa)",
                color:running?"#888899":"#FAFAFA",
                border:"none",borderRadius:12,fontFamily:"inherit",fontSize:"1rem",
                fontWeight:700,cursor:running?"default":"pointer",
                letterSpacing:"0.05em",marginBottom:20,
              }}>
              {running ? "⚙️ Agentit laskevat..." : "▶ Aja CEO"}
            </button>

            {/* Tulosnaytto */}
            {!running && cards.length > 0 && (
              <div>
                <div style={{fontSize:"0.78rem",color:"#888899",marginBottom:10}}>CEO-tulos:</div>
                {cards.map(card=>{
                  const color = COLORS[card.color];
                  return (
                    <div key={card.area} style={{display:"flex",gap:12,padding:"10px 14px",background:"#1a1d27",borderRadius:10,marginBottom:8,borderLeft:`4px solid ${color}`}}>
                      <div style={{fontSize:"1.5rem"}}>{card.color==="red"?"🔴":card.color==="gold"?"🟡":"🔵"}</div>
                      <div style={{flex:1}}>
                        <div style={{fontWeight:700,color}}>{card.area}</div>
                        <div style={{fontSize:"0.78rem",color:"#888899"}}>Pisteet: {card.score.toFixed(0)} · Urgency: {card.urgency}/10{card.pred?" · ∿ Ennuste":""}</div>
                        <div style={{fontSize:"0.8rem",marginTop:4}}>{card.reasons[0]?.slice(0,90)}</div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
