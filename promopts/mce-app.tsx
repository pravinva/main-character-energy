import { useState, useEffect } from "react";

const C = {
  bg:           "#F4F6F9",
  surface:      "#FFFFFF",
  surfaceAlt:   "#F8F9FB",
  border:       "#DDE2EA",
  borderStrong: "#C4CAD6",
  navy:         "#0D2240",
  navyMid:      "#1A3A6A",
  navyLight:    "#E8EDF5",
  gold:         "#B8760A",
  goldLight:    "#FDF3E0",
  goldBorder:   "#E8C060",
  critical:     "#C0251A",
  criticalBg:   "#FDF1F0",
  criticalBdr:  "#F0C0BC",
  warning:      "#B86010",
  warningBg:    "#FDF5ED",
  warningBdr:   "#EDD090",
  healthy:      "#1A6E40",
  healthyBg:    "#EDF7F1",
  healthyBdr:   "#90D0A8",
  textPrimary:  "#0D1A2A",
  textSec:      "#485A70",
  textMuted:    "#8090A8",
  white:        "#FFFFFF",
};

const ASSETS = [
  { id:"WT-001", name:"Wind Turbine Alpha-1",   site:"Hunter Valley",   type:"Wind Turbine",    vibration:92.4, temp:78,  status:"CRITICAL", lastMaint:"2025-09-14", model:"Vestas V150",       technician:"J. Okafor" },
  { id:"WT-002", name:"Wind Turbine Alpha-2",   site:"Hunter Valley",   type:"Wind Turbine",    vibration:54.1, temp:62,  status:"HEALTHY",  lastMaint:"2025-11-02", model:"Vestas V150",       technician:"J. Okafor" },
  { id:"WT-003", name:"Wind Turbine Bravo-1",   site:"Bungendore",      type:"Wind Turbine",    vibration:88.7, temp:81,  status:"CRITICAL", lastMaint:"2025-08-20", model:"Siemens SG 5.0",   technician:"R. Patel" },
  { id:"GT-001", name:"Gas Turbine Unit 4",     site:"Tallawarra",      type:"Gas Turbine",     vibration:41.2, temp:412, status:"HEALTHY",  lastMaint:"2025-12-01", model:"GE 7HA.02",         technician:"S. Nguyen" },
  { id:"GT-002", name:"Gas Turbine Unit 5",     site:"Tallawarra",      type:"Gas Turbine",     vibration:67.9, temp:438, status:"WARNING",  lastMaint:"2025-10-15", model:"GE 7HA.02",         technician:"S. Nguyen" },
  { id:"SS-001", name:"Substation Omega",       site:"Newcastle Grid",  type:"Substation",      vibration:12.3, temp:55,  status:"HEALTHY",  lastMaint:"2026-01-10", model:"ABB AIS 420kV",     technician:"M. Torres" },
  { id:"SS-002", name:"Substation Delta",       site:"Wollongong Grid", type:"Substation",      vibration:85.1, temp:71,  status:"CRITICAL", lastMaint:"2025-07-30", model:"Siemens 8DQ1",      technician:"M. Torres" },
  { id:"WT-004", name:"Wind Turbine Bravo-2",   site:"Bungendore",      type:"Wind Turbine",    vibration:49.8, temp:59,  status:"HEALTHY",  lastMaint:"2025-12-18", model:"Siemens SG 5.0",   technician:"R. Patel" },
  { id:"SP-001", name:"Solar Array Block C",    site:"Broken Hill",     type:"Solar Array",     vibration:5.2,  temp:48,  status:"HEALTHY",  lastMaint:"2026-02-01", model:"SunPower X22",      technician:"A. Walsh" },
  { id:"SP-002", name:"Solar Inverter Farm 2",  site:"Broken Hill",     type:"Solar Inverter",  vibration:82.3, temp:91,  status:"CRITICAL", lastMaint:"2025-09-05", model:"SMA Sunny Central", technician:"A. Walsh" },
  { id:"GT-003", name:"Gas Turbine Unit 6",     site:"Tallawarra",      type:"Gas Turbine",     vibration:38.6, temp:401, status:"HEALTHY",  lastMaint:"2026-01-22", model:"GE 7HA.02",         technician:"S. Nguyen" },
  { id:"WT-005", name:"Wind Turbine Charlie-1", site:"Crookwell",       type:"Wind Turbine",    vibration:61.4, temp:65,  status:"WARNING",  lastMaint:"2025-11-28", model:"Enercon E-126",     technician:"L. Kim" },
  { id:"HY-001", name:"Hydro Unit 1",           site:"Snowy Mountains", type:"Hydro Turbine",   vibration:22.1, temp:34,  status:"HEALTHY",  lastMaint:"2026-02-14", model:"Voith FT-92",       technician:"D. Huang" },
  { id:"HY-002", name:"Hydro Unit 2",           site:"Snowy Mountains", type:"Hydro Turbine",   vibration:31.7, temp:37,  status:"HEALTHY",  lastMaint:"2026-02-14", model:"Voith FT-92",       technician:"D. Huang" },
  { id:"WT-006", name:"Wind Turbine Charlie-2", site:"Crookwell",       type:"Wind Turbine",    vibration:77.2, temp:72,  status:"WARNING",  lastMaint:"2025-10-09", model:"Enercon E-126",     technician:"L. Kim" },
];

const WORK_ORDERS = [
  { id:"WO-2026-0041", assetId:"WT-001", priority:"P1", status:"DISPATCHED",  createdAt:"2026-03-05T02:14:00Z", technician:"J. Okafor", eta:"2026-03-05T08:00:00Z",
    repairSummary:"Anomalous vibration at 92.4 Hz indicates high-probability main shaft bearing failure. Immediate replacement required to prevent gearbox cascade damage. Asset has been offline since 02:14 UTC.",
    parts:[{sku:"SKF-7320-BA",desc:"Main shaft bearing assembly",qty:1},{sku:"MOB-GR-LC2",desc:"High-load bearing grease cartridge",qty:3},{sku:"TW-SET-120",desc:"Torque wrench set (80–120 Nm)",qty:1},{sku:"SEAL-VS-150",desc:"V-ring shaft seal",qty:2}],
    steps:["Isolate turbine and confirm zero-energy state via LOTO procedure WP-VT-001","Remove nacelle access panel and document pre-work condition with photographic record","Extract faulty bearing using hydraulic puller HP-4400 — record extraction torque","Clean and inspect bearing housing for scoring or ovality — reject if >0.05 mm deviation","Press-fit replacement SKF-7320-BA bearing to 95 Nm per Vestas torque spec VS-150-T09","Apply 3 grease cartridges MOB-GR-LC2 to lubrication points per diagram L-07","Reassemble nacelle and perform manual rotation check before energisation","Conduct 30-minute run-up test at 10%, 50%, 100% rated speed — log vibration at each stage"],
    safety:[{item:"Arc flash PPE Category 2 (minimum 8 cal/cm²)",mandatory:true},{item:"Full body harness and lanyard rated to 140 kg — nacelle work at 90 m",mandatory:true},{item:"Lockout/Tagout — confirm all 6 isolation points locked before entry",mandatory:true},{item:"Wind speed must be <11 m/s for nacelle access — verify before climb",mandatory:true},{item:"Two-person entry rule applies — do not enter nacelle unaccompanied",mandatory:true}] },
  { id:"WO-2026-0042", assetId:"WT-003", priority:"P1", status:"IN_PROGRESS", createdAt:"2026-03-05T02:17:00Z", technician:"R. Patel",   eta:"2026-03-05T09:30:00Z",
    repairSummary:"Vibration at 88.7 Hz consistent with blade imbalance or pitch actuator fault on Unit Bravo-1. Recommend blade inspection and pitch system diagnostics on site.",
    parts:[{sku:"PITCH-ACT-SG5",desc:"Pitch actuator seal kit",qty:1},{sku:"BLD-BLNC-WT",desc:"Blade balancing weight set",qty:1},{sku:"HYD-FL-ISO46",desc:"Hydraulic fluid ISO 46 (20 L)",qty:2}],
    steps:["Shut down turbine via SCADA and confirm blade feathering to 90 degrees","Perform external blade visual inspection from ground using inspection binoculars","Access hub via tower interior — confirm LOTO on all three pitch drives","Inspect pitch actuator seals for hydraulic weeping — replace kit if weeping present","Check blade root bolts for correct torque — re-torque to 650 Nm","Perform manual blade balance check per Siemens procedure SG5-MAINT-BLD-003","Log all measurements to CMMS before departure"],
    safety:[{item:"Arc flash PPE Category 2",mandatory:true},{item:"Full body harness — mandatory for all hub work",mandatory:true},{item:"LOTO — all three pitch drive isolation points",mandatory:true},{item:"Confined space entry procedure for tower base",mandatory:false}] },
  { id:"WO-2026-0043", assetId:"SS-002", priority:"P1", status:"DISPATCHED",  createdAt:"2026-03-05T02:19:00Z", technician:"M. Torres",  eta:"2026-03-05T07:00:00Z",
    repairSummary:"Vibration at 85.1 Hz in Substation Delta switchgear bay exceeds Siemens 8DQ1 operational threshold. Probable loose bus bar connections or transformer tank resonance. Risk of flashover if unresolved.",
    parts:[{sku:"BB-CONN-8DQ1",desc:"Bus bar connection hardware set",qty:1},{sku:"INS-WRAP-HV",desc:"High-voltage insulation tape 10 m rolls",qty:4},{sku:"COND-GREASE",desc:"Conductive anti-oxidant grease",qty:2}],
    steps:["Coordinate outage window with AEMO — minimum 2-hour notice","De-energise and ground all three phases per Siemens GIS procedure 8DQ1-DE-001","Inspect all bus bar compression joints — re-torque to 25 Nm Cu-Al spec","Apply conductive grease to all joint faces before reassembly","Perform insulation resistance test (IR > 1000 MΩ at 5 kV) on all phases","Check transformer mounting bolts and damper pad condition","Re-energise and monitor vibration for 15 minutes before handback"],
    safety:[{item:"Arc flash PPE Category 4 (minimum 40 cal/cm²) — 420 kV substation",mandatory:true},{item:"Rubber insulating gloves Class 4, tested within 6 months",mandatory:true},{item:"Grounding and shorting devices applied before any contact",mandatory:true},{item:"Exclude zone 3 m minimum for all non-essential personnel",mandatory:true},{item:"Works authorisation from AEMO required before de-energisation",mandatory:true}] },
  { id:"WO-2026-0044", assetId:"SP-002", priority:"P2", status:"DISPATCHED",  createdAt:"2026-03-05T02:21:00Z", technician:"A. Walsh",   eta:"2026-03-05T11:00:00Z",
    repairSummary:"Solar Inverter Farm 2 showing 82.3 Hz vibration and elevated internal temperature of 91°C. Likely cooling fan failure causing thermal runaway risk. Efficiency down 14% over 72 hours.",
    parts:[{sku:"FAN-SMA-SC500",desc:"Cooling fan assembly SMA SC500kW",qty:2},{sku:"THERM-PASTE-SL",desc:"Thermal interface compound 100 g",qty:1},{sku:"FILT-AIR-SMA",desc:"Air filter media replacement kit",qty:1}],
    steps:["Isolate inverter from DC array and AC grid per SMA shutdown procedure SC-SD-001","Allow 10-minute capacitor discharge period — confirm voltage <50 V before opening enclosure","Remove and inspect all cooling fans — replace any fan showing bearing noise or blade damage","Clean heat sink fins and apply fresh thermal interface compound to IGBT modules","Replace air filter media","Perform dielectric strength test on DC isolation before reconnection","Re-energise and verify internal temperature stabilises below 65°C at rated power"],
    safety:[{item:"PPE Category 1 — DC voltage present during capacitor discharge",mandatory:true},{item:"Confirm array disconnected from DC input before enclosure entry",mandatory:true},{item:"Sunscreen SPF 50+ and UV protective clothing — Broken Hill site",mandatory:false}] },
  { id:"WO-2026-0045", assetId:"GT-002", priority:"P2", status:"DISPATCHED",  createdAt:"2026-03-05T02:22:00Z", technician:"S. Nguyen",  eta:"2026-03-05T13:00:00Z",
    repairSummary:"Gas Turbine Unit 5 vibration at 67.9 Hz with exhaust temperature at 438°C is above normal operating band. Pattern suggests compressor fouling or stage 1 blading wear.",
    parts:[{sku:"BORE-KIT-7HA",desc:"GE 7HA borescope port access kit",qty:1},{sku:"COMP-WASH-GE",desc:"Compressor online wash solution 5 L",qty:2},{sku:"SEAL-GAS-HT",desc:"High-temperature combustor seal set",qty:1}],
    steps:["Reduce unit to minimum load and coordinate with dispatch for inspection window","Perform online compressor wash per GE procedure 7HA-OPS-CW-002","After wash, bring unit to full load and re-measure vibration and exhaust temp","If symptoms persist, schedule borescope inspection of stages 1–4","Document all borescope findings with image capture — upload to CMMS","Assess need for offline compressor wash or blading replacement"],
    safety:[{item:"Hearing protection mandatory — gas turbine enclosure >105 dB",mandatory:true},{item:"Hot surface awareness — all surfaces >60°C must be labelled",mandatory:true},{item:"Confined space permit required for enclosure entry at low load",mandatory:true}] },
];

// ─── LOGO ──────────────────────────────────────────────────────────────────
const MCELogo = () => (
  <svg width="160" height="36" viewBox="0 0 160 36" fill="none" xmlns="http://www.w3.org/2000/svg">
    {/* Bolt / arc mark */}
    <path d="M6 4 L14 4 L10 16 L18 16 L8 32 L10 20 L2 20 Z" fill="#B8760A"/>
    {/* MCE wordmark */}
    <text x="26" y="25" fontFamily="Georgia, 'Times New Roman', serif" fontSize="20" fontWeight="700" fill="#0D2240" letterSpacing="-0.5">MCE</text>
    {/* Rule */}
    <line x1="26" y1="29" x2="118" y2="29" stroke="#DDE2EA" strokeWidth="1"/>
    {/* Sub text */}
    <text x="26" y="35" fontFamily="-apple-system, sans-serif" fontSize="7.5" fill="#8090A8" letterSpacing="2.5">MAIN CHARACTER ENERGY</text>
  </svg>
);

// ─── PRIMITIVES ─────────────────────────────────────────────────────────────
const pill = (status) => {
  const m = {
    CRITICAL:    { label:"Critical",     bg:C.criticalBg, color:C.critical, border:C.criticalBdr },
    WARNING:     { label:"Warning",      bg:C.warningBg,  color:C.warning,  border:C.warningBdr  },
    HEALTHY:     { label:"Operational",  bg:C.healthyBg,  color:C.healthy,  border:C.healthyBdr  },
    DISPATCHED:  { label:"Dispatched",   bg:"#EEF3FB",    color:"#2A5CB8",  border:"#B8CCEC"     },
    IN_PROGRESS: { label:"In Progress",  bg:"#EAF6F4",    color:"#1A7A6A",  border:"#90D0C8"     },
    COMPLETE:    { label:"Complete",     bg:C.healthyBg,  color:C.healthy,  border:C.healthyBdr  },
  }[status] || { label:status, bg:C.surfaceAlt, color:C.textMuted, border:C.border };
  return (
    <span style={{ display:"inline-block", padding:"2px 9px", borderRadius:2, fontSize:10.5, fontWeight:600, letterSpacing:"0.05em", textTransform:"uppercase", background:m.bg, color:m.color, border:`1px solid ${m.border}` }}>
      {m.label}
    </span>
  );
};

const PriorityMark = ({ p }) => {
  const c = {P1:C.critical, P2:C.warning, P3:C.healthy}[p]||C.textMuted;
  return <span style={{ display:"inline-flex", alignItems:"center", gap:5, fontSize:11, fontWeight:700, color:c, letterSpacing:"0.06em" }}><span style={{ width:7, height:7, borderRadius:"50%", background:c }}/>{p}</span>;
};

const VibBar = ({ val }) => {
  const pct = Math.min(100,(val/120)*100);
  const col = val>80?C.critical:val>60?C.warning:C.healthy;
  return (
    <div style={{ display:"flex", alignItems:"center", gap:8 }}>
      <div style={{ flex:1, height:2, background:C.border, borderRadius:1 }}>
        <div style={{ width:`${pct}%`, height:"100%", background:col, borderRadius:1 }}/>
      </div>
      <span style={{ fontSize:10.5, color:col, fontWeight:600, minWidth:42, textAlign:"right", fontVariantNumeric:"tabular-nums" }}>{val} Hz</span>
    </div>
  );
};

const KPI = ({ label, value, sub, color }) => (
  <div style={{ background:C.surface, border:`1px solid ${C.border}`, borderRadius:5, padding:"18px 22px", borderTop:`3px solid ${color||C.navy}` }}>
    <div style={{ fontSize:10, color:C.textMuted, letterSpacing:"0.12em", textTransform:"uppercase", marginBottom:8, fontWeight:600 }}>{label}</div>
    <div style={{ fontSize:28, fontWeight:300, color:color||C.textPrimary, fontVariantNumeric:"tabular-nums", lineHeight:1 }}>{value}</div>
    {sub && <div style={{ fontSize:11, color:C.textMuted, marginTop:5 }}>{sub}</div>}
  </div>
);

const SectionHeader = ({ title }) => (
  <div style={{ fontSize:10, fontWeight:700, color:C.textMuted, letterSpacing:"0.12em", textTransform:"uppercase", paddingBottom:10, borderBottom:`1px solid ${C.border}`, marginBottom:14 }}>{title}</div>
);

const HR = () => <div style={{ height:1, background:C.border, margin:"0 -22px" }}/>;

const Btn = ({ children, variant="primary", onClick, small }) => {
  const styles = {
    primary: { background:C.navy, color:C.white, border:`1px solid ${C.navy}` },
    ghost:   { background:"transparent", color:C.textSec, border:`1px solid ${C.border}` },
    danger:  { background:C.critical, color:C.white, border:`1px solid ${C.critical}` },
  };
  return (
    <button onClick={onClick} style={{ ...styles[variant], padding: small?"5px 14px":"8px 18px", borderRadius:3, fontSize:11, fontWeight:600, letterSpacing:"0.06em", textTransform:"uppercase", cursor:"pointer" }}>
      {children}
    </button>
  );
};

// ─── DASHBOARD ──────────────────────────────────────────────────────────────
function Dashboard({ onAsset, onOrder }) {
  const crit = ASSETS.filter(a=>a.status==="CRITICAL");
  const warn = ASSETS.filter(a=>a.status==="WARNING");
  const ok   = ASSETS.filter(a=>a.status==="HEALTHY");
  const sites = [...new Set(ASSETS.map(a=>a.site))];

  return (
    <div style={{ display:"flex", flexDirection:"column", gap:20 }}>
      <div style={{ display:"grid", gridTemplateColumns:"repeat(4,1fr)", gap:12 }}>
        <KPI label="Critical Assets"    value={crit.length}  sub="Require immediate dispatch"  color={C.critical}/>
        <KPI label="Active Work Orders" value={WORK_ORDERS.length} sub={`${WORK_ORDERS.filter(w=>w.priority==="P1").length} at Priority 1`} color={C.gold}/>
        <KPI label="Fleet Availability" value="86.7%"        sub="14 of 15 assets monitored"/>
        <KPI label="First-Time Fix Rate"value="91.4%"        sub="Rolling 90-day average"      color={C.healthy}/>
      </div>

      <div style={{ display:"grid", gridTemplateColumns:"2fr 1fr", gap:16 }}>
        {/* Asset grid */}
        <div style={{ background:C.surface, border:`1px solid ${C.border}`, borderRadius:5 }}>
          <div style={{ padding:"14px 20px", display:"flex", justifyContent:"space-between", alignItems:"center" }}>
            <span style={{ fontSize:11, fontWeight:700, color:C.textPrimary, letterSpacing:"0.06em", textTransform:"uppercase" }}>Asset Fleet</span>
            <span style={{ fontSize:10.5, color:C.textMuted }}>{new Date().toLocaleString("en-AU",{timeZone:"Australia/Sydney",hour12:false})}</span>
          </div>
          <HR/>
          <div style={{ padding:"12px 10px", display:"grid", gridTemplateColumns:"repeat(5,1fr)", gap:6 }}>
            {ASSETS.map(a => {
              const bc = a.status==="CRITICAL"?C.criticalBdr:a.status==="WARNING"?C.warningBdr:C.border;
              const bg = a.status==="CRITICAL"?C.criticalBg:a.status==="WARNING"?C.warningBg:C.surfaceAlt;
              const vc = a.status==="CRITICAL"?C.critical:a.status==="WARNING"?C.warning:C.textMuted;
              return (
                <button key={a.id} onClick={()=>onAsset(a)} style={{ background:bg, border:`1px solid ${bc}`, borderRadius:4, padding:"9px 8px", textAlign:"left", cursor:"pointer", transition:"box-shadow 0.15s" }}
                  onMouseEnter={e=>e.currentTarget.style.boxShadow="0 2px 8px rgba(13,34,64,0.12)"}
                  onMouseLeave={e=>e.currentTarget.style.boxShadow="none"}>
                  <div style={{ fontSize:9.5, fontWeight:800, color:vc, letterSpacing:"0.08em", marginBottom:2 }}>{a.id}</div>
                  <div style={{ fontSize:11, color:C.textPrimary, fontWeight:500, lineHeight:1.3, whiteSpace:"nowrap", overflow:"hidden", textOverflow:"ellipsis" }}>{a.name}</div>
                  <div style={{ fontSize:10, color:C.textMuted, marginBottom:5 }}>{a.site}</div>
                  <VibBar val={a.vibration}/>
                </button>
              );
            })}
          </div>
        </div>

        <div style={{ display:"flex", flexDirection:"column", gap:12 }}>
          {/* Sites */}
          <div style={{ background:C.surface, border:`1px solid ${C.border}`, borderRadius:5, flex:1 }}>
            <div style={{ padding:"14px 20px" }}>
              <span style={{ fontSize:11, fontWeight:700, color:C.textPrimary, letterSpacing:"0.06em", textTransform:"uppercase" }}>Generation Sites</span>
            </div>
            <HR/>
            {sites.map(site => {
              const sa = ASSETS.filter(a=>a.site===site);
              const sc = sa.filter(a=>a.status==="CRITICAL").length;
              const sw = sa.filter(a=>a.status==="WARNING").length;
              return (
                <div key={site} style={{ padding:"9px 20px", borderBottom:`1px solid ${C.border}`, display:"flex", justifyContent:"space-between", alignItems:"center" }}>
                  <div>
                    <div style={{ fontSize:12, color:C.textPrimary, fontWeight:500 }}>{site}</div>
                    <div style={{ fontSize:10.5, color:C.textMuted }}>{sa.length} assets</div>
                  </div>
                  <div style={{ display:"flex", gap:5 }}>
                    {sc>0&&<span style={{ fontSize:9.5, fontWeight:700, color:C.critical, background:C.criticalBg, border:`1px solid ${C.criticalBdr}`, borderRadius:2, padding:"2px 7px" }}>{sc} CRIT</span>}
                    {sw>0&&<span style={{ fontSize:9.5, fontWeight:700, color:C.warning, background:C.warningBg, border:`1px solid ${C.warningBdr}`, borderRadius:2, padding:"2px 7px" }}>{sw} WARN</span>}
                    {sc===0&&sw===0&&<span style={{ fontSize:9.5, fontWeight:600, color:C.healthy, background:C.healthyBg, border:`1px solid ${C.healthyBdr}`, borderRadius:2, padding:"2px 7px" }}>Clear</span>}
                  </div>
                </div>
              );
            })}
          </div>

          {/* Composition */}
          <div style={{ background:C.surface, border:`1px solid ${C.border}`, borderRadius:5 }}>
            <div style={{ padding:"14px 20px" }}>
              <span style={{ fontSize:11, fontWeight:700, color:C.textPrimary, letterSpacing:"0.06em", textTransform:"uppercase" }}>Fleet Status</span>
            </div>
            <HR/>
            <div style={{ padding:"12px 20px", display:"flex", flexDirection:"column", gap:10 }}>
              {[["Critical",C.critical,crit.length],["Warning",C.warning,warn.length],["Operational",C.healthy,ok.length]].map(([l,col,v])=>(
                <div key={l} style={{ display:"flex", alignItems:"center", gap:10 }}>
                  <div style={{ width:80, fontSize:11, color:C.textSec }}>{l}</div>
                  <div style={{ flex:1, height:5, background:C.border, borderRadius:2 }}>
                    <div style={{ width:`${(v/ASSETS.length)*100}%`, height:"100%", background:col, borderRadius:2 }}/>
                  </div>
                  <div style={{ fontSize:12, fontWeight:700, color:col, minWidth:18, textAlign:"right" }}>{v}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Recent work orders */}
      <div style={{ background:C.surface, border:`1px solid ${C.border}`, borderRadius:5 }}>
        <div style={{ padding:"14px 20px", display:"flex", justifyContent:"space-between", alignItems:"center" }}>
          <span style={{ fontSize:11, fontWeight:700, color:C.textPrimary, letterSpacing:"0.06em", textTransform:"uppercase" }}>Active Work Orders</span>
          <Btn variant="ghost" small onClick={()=>{}}>View All</Btn>
        </div>
        <HR/>
        <table style={{ width:"100%", borderCollapse:"collapse" }}>
          <thead>
            <tr style={{ background:C.surfaceAlt }}>
              {["Work Order","Asset","Site","Priority","Status","ETA"].map(h=>(
                <th key={h} style={{ padding:"8px 20px", textAlign:"left", fontSize:9.5, fontWeight:700, color:C.textMuted, letterSpacing:"0.1em", textTransform:"uppercase", borderBottom:`1px solid ${C.border}` }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {WORK_ORDERS.slice(0,4).map((w,i)=>{
              const a = ASSETS.find(x=>x.id===w.assetId);
              return (
                <tr key={w.id} onClick={()=>onOrder(w)} style={{ borderBottom:`1px solid ${C.border}`, cursor:"pointer" }}
                  onMouseEnter={e=>e.currentTarget.style.background=C.navyLight}
                  onMouseLeave={e=>e.currentTarget.style.background="transparent"}>
                  <td style={{ padding:"11px 20px", fontSize:11.5, fontWeight:700, color:C.navyMid, fontFamily:"monospace" }}>{w.id}</td>
                  <td style={{ padding:"11px 20px" }}>
                    <div style={{ fontSize:12, color:C.textPrimary, fontWeight:500 }}>{a?.name}</div>
                    <div style={{ fontSize:10.5, color:C.textMuted }}>{a?.model}</div>
                  </td>
                  <td style={{ padding:"11px 20px", fontSize:11.5, color:C.textSec }}>{a?.site}</td>
                  <td style={{ padding:"11px 20px" }}><PriorityMark p={w.priority}/></td>
                  <td style={{ padding:"11px 20px" }}>{pill(w.status)}</td>
                  <td style={{ padding:"11px 20px", fontSize:11, color:C.textMuted }}>{new Date(w.eta).toLocaleString("en-AU",{timeZone:"Australia/Sydney",hour12:false,month:"short",day:"numeric",hour:"2-digit",minute:"2-digit"})}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ─── WORK ORDERS LIST ────────────────────────────────────────────────────────
function WorkOrdersList({ onSelect }) {
  const [f, setF] = useState("ALL");
  const tabs = ["ALL","P1","P2","DISPATCHED","IN_PROGRESS"];
  const rows = WORK_ORDERS.filter(w => f==="ALL"?true:f==="P1"||f==="P2"?w.priority===f:w.status===f);
  return (
    <div style={{ display:"flex", flexDirection:"column", gap:14 }}>
      <div style={{ display:"flex", gap:3 }}>
        {tabs.map(t=>(
          <button key={t} onClick={()=>setF(t)} style={{ padding:"6px 14px", borderRadius:3, border:`1px solid ${f===t?C.navy:C.border}`, background:f===t?C.navy:"transparent", color:f===t?C.white:C.textSec, fontSize:10.5, fontWeight:600, letterSpacing:"0.06em", textTransform:"uppercase", cursor:"pointer" }}>
            {t.replace("_"," ")}
          </button>
        ))}
      </div>
      <div style={{ background:C.surface, border:`1px solid ${C.border}`, borderRadius:5, overflow:"hidden" }}>
        <table style={{ width:"100%", borderCollapse:"collapse" }}>
          <thead>
            <tr style={{ background:C.surfaceAlt }}>
              {["Work Order","Asset","Site","Priority","Status","Technician","ETA"].map(h=>(
                <th key={h} style={{ padding:"9px 18px", textAlign:"left", fontSize:9.5, fontWeight:700, color:C.textMuted, letterSpacing:"0.1em", textTransform:"uppercase", borderBottom:`1px solid ${C.border}` }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((w,i)=>{
              const a = ASSETS.find(x=>x.id===w.assetId);
              return (
                <tr key={w.id} onClick={()=>onSelect(w)} style={{ borderBottom:`1px solid ${C.border}`, cursor:"pointer", background:i%2?C.surfaceAlt:"transparent" }}
                  onMouseEnter={e=>e.currentTarget.style.background=C.navyLight}
                  onMouseLeave={e=>e.currentTarget.style.background=i%2?C.surfaceAlt:"transparent"}>
                  <td style={{ padding:"11px 18px", fontSize:11.5, fontWeight:700, color:C.navyMid, fontFamily:"monospace" }}>{w.id}</td>
                  <td style={{ padding:"11px 18px" }}>
                    <div style={{ fontSize:12, color:C.textPrimary, fontWeight:500 }}>{a?.name}</div>
                    <div style={{ fontSize:10.5, color:C.textMuted }}>{a?.model}</div>
                  </td>
                  <td style={{ padding:"11px 18px", fontSize:11.5, color:C.textSec }}>{a?.site}</td>
                  <td style={{ padding:"11px 18px" }}><PriorityMark p={w.priority}/></td>
                  <td style={{ padding:"11px 18px" }}>{pill(w.status)}</td>
                  <td style={{ padding:"11px 18px", fontSize:11.5, color:C.textSec }}>{w.technician}</td>
                  <td style={{ padding:"11px 18px", fontSize:11, color:C.textMuted }}>{new Date(w.eta).toLocaleString("en-AU",{timeZone:"Australia/Sydney",hour12:false,month:"short",day:"numeric",hour:"2-digit",minute:"2-digit"})}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ─── WORK ORDER DETAIL ───────────────────────────────────────────────────────
function WorkOrderDetail({ order, onBack }) {
  const a = ASSETS.find(x=>x.id===order.assetId);
  const [chk, setChk] = useState({});
  const toggle = k => setChk(p=>({...p,[k]:!p[k]}));

  return (
    <div style={{ display:"flex", flexDirection:"column", gap:18 }}>
      <div style={{ display:"flex", alignItems:"center", gap:12 }}>
        <Btn variant="ghost" small onClick={onBack}>Back</Btn>
        <span style={{ fontSize:12, color:C.textMuted, fontFamily:"monospace" }}>{order.id}</span>
        {pill(order.status)}
        <PriorityMark p={order.priority}/>
      </div>

      <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:14 }}>
        <div style={{ background:C.surface, border:`1px solid ${C.border}`, borderRadius:5, padding:"18px 22px" }}>
          <SectionHeader title="Asset Details"/>
          {[["Asset ID",a?.id],["Name",a?.name],["Site",a?.site],["Type",a?.type],["Model",a?.model],["Technician",order.technician]].map(([l,v])=>(
            <div key={l} style={{ display:"flex", justifyContent:"space-between", padding:"6px 0", borderBottom:`1px solid ${C.border}` }}>
              <span style={{ fontSize:11, color:C.textMuted }}>{l}</span>
              <span style={{ fontSize:11, color:C.textPrimary, fontWeight:600 }}>{v}</span>
            </div>
          ))}
          <div style={{ marginTop:14 }}>
            <div style={{ fontSize:10.5, color:C.textMuted, marginBottom:5 }}>Live Vibration Reading</div>
            <VibBar val={a?.vibration||0}/>
          </div>
        </div>

        <div style={{ background:C.surface, border:`1px solid ${C.border}`, borderRadius:5, padding:"18px 22px" }}>
          <SectionHeader title="AI Diagnostic Summary"/>
          <p style={{ fontSize:12.5, color:C.textSec, lineHeight:1.75, margin:0 }}>{order.repairSummary}</p>
        </div>
      </div>

      <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr 1fr", gap:14 }}>
        {/* Parts */}
        <div style={{ background:C.surface, border:`1px solid ${C.border}`, borderRadius:5, padding:"18px 22px" }}>
          <SectionHeader title="Required Parts"/>
          {order.parts.map(p=>(
            <div key={p.sku} style={{ padding:"8px 0", borderBottom:`1px solid ${C.border}` }}>
              <div style={{ fontSize:11.5, color:C.textPrimary, fontWeight:600 }}>{p.desc}</div>
              <div style={{ display:"flex", justifyContent:"space-between", marginTop:3 }}>
                <span style={{ fontSize:10, color:C.textMuted, fontFamily:"monospace" }}>{p.sku}</span>
                <span style={{ fontSize:10.5, color:C.gold, fontWeight:700 }}>QTY {p.qty}</span>
              </div>
            </div>
          ))}
        </div>

        {/* Steps */}
        <div style={{ background:C.surface, border:`1px solid ${C.border}`, borderRadius:5, padding:"18px 22px" }}>
          <SectionHeader title="Repair Procedure"/>
          {order.steps.map((s,i)=>(
            <div key={i} style={{ display:"flex", gap:10, padding:"6px 0", borderBottom:`1px solid ${C.border}` }}>
              <span style={{ fontSize:10, fontWeight:800, color:C.navy, minWidth:16, paddingTop:1.5, opacity:0.5 }}>{i+1}</span>
              <span style={{ fontSize:11, color:C.textSec, lineHeight:1.6 }}>{s}</span>
            </div>
          ))}
        </div>

        {/* Safety */}
        <div style={{ background:C.criticalBg, border:`1px solid ${C.criticalBdr}`, borderRadius:5, padding:"18px 22px" }}>
          <div style={{ fontSize:10, fontWeight:700, color:C.critical, letterSpacing:"0.12em", textTransform:"uppercase", paddingBottom:10, borderBottom:`1px solid ${C.criticalBdr}`, marginBottom:14 }}>Safety Compliance</div>
          <div style={{ fontSize:10.5, color:C.critical, opacity:0.7, marginBottom:12 }}>All mandatory items must be confirmed before works commence.</div>
          {order.safety.map((s,i)=>(
            <div key={i} onClick={()=>toggle(i)} style={{ display:"flex", alignItems:"flex-start", gap:9, padding:"7px 0", borderBottom:`1px solid ${C.criticalBdr}`, cursor:"pointer" }}>
              <div style={{ width:15, height:15, borderRadius:2, border:`1.5px solid ${s.mandatory?C.critical:C.border}`, background:chk[i]?(s.mandatory?C.critical:C.healthy):"white", flexShrink:0, marginTop:1, display:"flex", alignItems:"center", justifyContent:"center" }}>
                {chk[i]&&<svg width="9" height="7" viewBox="0 0 9 7"><polyline points="1,3.5 3.5,6 8,1" stroke="white" strokeWidth="1.5" fill="none" strokeLinecap="round" strokeLinejoin="round"/></svg>}
              </div>
              <span style={{ fontSize:11, color:C.textPrimary, lineHeight:1.5 }}>
                {s.item}
                {s.mandatory&&<span style={{ fontSize:9, fontWeight:700, color:C.critical, marginLeft:6, letterSpacing:"0.08em" }}>MANDATORY</span>}
              </span>
            </div>
          ))}
          <div style={{ marginTop:16, display:"flex", gap:8 }}>
            <Btn variant="danger">Start Job</Btn>
            <Btn variant="ghost">Escalate</Btn>
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── ASSET DETAIL ────────────────────────────────────────────────────────────
function AssetDetail({ asset, onBack }) {
  const col = asset.vibration>80?C.critical:asset.vibration>60?C.warning:C.healthy;
  return (
    <div style={{ display:"flex", flexDirection:"column", gap:18 }}>
      <div style={{ display:"flex", alignItems:"center", gap:12 }}>
        <Btn variant="ghost" small onClick={onBack}>Back</Btn>
        <span style={{ fontSize:16, fontWeight:500, color:C.textPrimary }}>{asset.name}</span>
        {pill(asset.status)}
      </div>
      <div style={{ display:"grid", gridTemplateColumns:"repeat(3,1fr)", gap:12 }}>
        <KPI label="Vibration" value={`${asset.vibration} Hz`} sub={asset.vibration>80?"Above critical threshold":"Within operating range"} color={col}/>
        <KPI label="Temperature" value={`${asset.temp}°C`} sub="Current sensor reading"/>
        <KPI label="Last Maintenance" value={asset.lastMaint} sub={asset.technician}/>
      </div>
      <div style={{ background:C.surface, border:`1px solid ${C.border}`, borderRadius:5, padding:"18px 22px" }}>
        <SectionHeader title="Asset Record"/>
        {[["Asset ID",asset.id],["Model",asset.model],["Site",asset.site],["Type",asset.type],["Assigned Technician",asset.technician]].map(([l,v])=>(
          <div key={l} style={{ display:"flex", justifyContent:"space-between", padding:"8px 0", borderBottom:`1px solid ${C.border}` }}>
            <span style={{ fontSize:12, color:C.textMuted }}>{l}</span>
            <span style={{ fontSize:12, color:C.textPrimary, fontWeight:600 }}>{v}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── APP SHELL ───────────────────────────────────────────────────────────────
export default function App() {
  const [nav, setNav]           = useState("dashboard");
  const [selOrder, setSelOrder] = useState(null);
  const [selAsset, setSelAsset] = useState(null);
  const [live, setLive]         = useState(true);

  useEffect(() => {
    const t = setInterval(()=>setLive(p=>!p), 2200);
    return ()=>clearInterval(t);
  }, []);

  const goOrder = o => { setSelOrder(o); setSelAsset(null); setNav("workorders"); };
  const goAsset = a => { setSelAsset(a); setSelOrder(null); };
  const critical = ASSETS.filter(a=>a.status==="CRITICAL").length;

  const navItems = [{ id:"dashboard", label:"Fleet Dashboard" },{ id:"workorders", label:"Work Orders" }];

  const crumb = selOrder ? `Work Order / ${selOrder.id}` : selAsset ? `Fleet Dashboard / ${selAsset.id}` : navItems.find(n=>n.id===nav)?.label;
  const sub = selOrder ? `${ASSETS.find(a=>a.id===selOrder.assetId)?.site} · ${selOrder.technician}` :
              selAsset ? `${selAsset.site} · ${selAsset.type}` :
              nav==="dashboard" ? `${ASSETS.length} monitored assets across ${[...new Set(ASSETS.map(a=>a.site))].length} generation sites` :
              `${WORK_ORDERS.length} active work orders · ${WORK_ORDERS.filter(w=>w.priority==="P1").length} at Priority 1`;

  return (
    <div style={{ minHeight:"100vh", background:C.bg, color:C.textPrimary, fontFamily:"-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif", fontSize:14 }}>

      {/* Top nav */}
      <div style={{ background:C.surface, borderBottom:`1px solid ${C.border}`, padding:"0 28px", display:"flex", alignItems:"center", height:58, position:"sticky", top:0, zIndex:100, boxShadow:"0 1px 4px rgba(13,34,64,0.06)" }}>
        <MCELogo/>
        <div style={{ width:1, height:28, background:C.border, margin:"0 24px" }}/>
        <nav style={{ display:"flex", gap:2 }}>
          {navItems.map(n=>(
            <button key={n.id} onClick={()=>{ setNav(n.id); setSelOrder(null); setSelAsset(null); }} style={{ padding:"6px 14px", borderRadius:3, border:"none", background:nav===n.id?C.navyLight:"transparent", color:nav===n.id?C.navyMid:C.textSec, fontSize:12, fontWeight:nav===n.id?700:400, cursor:"pointer", letterSpacing:"0.04em" }}>
              {n.label}
            </button>
          ))}
        </nav>
        <div style={{ marginLeft:"auto", display:"flex", alignItems:"center", gap:14 }}>
          <div style={{ display:"flex", alignItems:"center", gap:7, fontSize:11, color:C.textMuted }}>
            <span style={{ width:7, height:7, borderRadius:"50%", background:live?C.healthy:"#C8D8C0", display:"inline-block", transition:"background 0.5s" }}/>
            Live  ·  AEST
          </div>
          {critical>0&&(
            <div style={{ fontSize:11, fontWeight:700, color:C.critical, background:C.criticalBg, border:`1px solid ${C.criticalBdr}`, borderRadius:3, padding:"4px 12px", letterSpacing:"0.04em" }}>
              {critical} Critical
            </div>
          )}
          <div style={{ fontSize:11, color:C.textSec, background:C.surfaceAlt, border:`1px solid ${C.border}`, borderRadius:3, padding:"4px 12px" }}>
            Field Engineer
          </div>
        </div>
      </div>

      {/* Page header */}
      <div style={{ background:C.navy, padding:"16px 28px" }}>
        <div style={{ fontSize:11, color:"rgba(255,255,255,0.45)", letterSpacing:"0.06em", textTransform:"uppercase", marginBottom:4 }}>{crumb}</div>
        <div style={{ fontSize:11, color:"rgba(255,255,255,0.55)" }}>{sub}</div>
      </div>

      {/* Content */}
      <div style={{ padding:"24px 28px", maxWidth:1480, margin:"0 auto" }}>
        {nav==="dashboard" && !selAsset  && <Dashboard onAsset={goAsset} onOrder={goOrder}/>}
        {nav==="dashboard" && selAsset   && <AssetDetail asset={selAsset} onBack={()=>setSelAsset(null)}/>}
        {nav==="workorders"&& !selOrder  && <WorkOrdersList onSelect={setSelOrder}/>}
        {nav==="workorders"&& selOrder   && <WorkOrderDetail order={selOrder} onBack={()=>setSelOrder(null)}/>}
      </div>

      <div style={{ padding:"18px 28px", borderTop:`1px solid ${C.border}`, display:"flex", justifyContent:"space-between", fontSize:10, color:C.textMuted, letterSpacing:"0.07em", textTransform:"uppercase" }}>
        <span>Main Character Energy · Agentic Field Management Platform · v2.1.0</span>
        <span>Databricks Unity Catalog · Lakebase · Agent Bricks</span>
      </div>
    </div>
  );
}
