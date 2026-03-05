import { useState, useEffect } from "react";

// MCE Color Palette
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

const API_BASE = "/api";

// ─── LOGO ──────────────────────────────────────────────────────────────────
const MCELogo = () => (
  <svg width="160" height="36" viewBox="0 0 160 36" fill="none">
    <path d="M6 4 L14 4 L10 16 L18 16 L8 32 L10 20 L2 20 Z" fill="#B8760A"/>
    <text x="26" y="25" fontFamily="Georgia, 'Times New Roman', serif" fontSize="20" fontWeight="700" fill="#0D2240" letterSpacing="-0.5">MCE</text>
    <line x1="26" y1="29" x2="118" y2="29" stroke="#DDE2EA" strokeWidth="1"/>
    <text x="26" y="35" fontFamily="-apple-system, sans-serif" fontSize="7.5" fill="#8090A8" letterSpacing="2.5">MAIN CHARACTER ENERGY</text>
  </svg>
);

// ─── PRIMITIVES ─────────────────────────────────────────────────────────────
const pill = (status: string) => {
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

const PriorityMark = ({ p }: { p: string }) => {
  const c = {P1:C.critical, P2:C.warning, P3:C.healthy}[p]||C.textMuted;
  return <span style={{ display:"inline-flex", alignItems:"center", gap:5, fontSize:11, fontWeight:700, color:c, letterSpacing:"0.06em" }}><span style={{ width:7, height:7, borderRadius:"50%", background:c }}/>{p}</span>;
};

const VibBar = ({ val }: { val: number }) => {
  const pct = Math.min(100,(val/120)*100);
  const col = val>80?C.critical:val>60?C.warning:C.healthy;
  return (
    <div style={{ display:"flex", alignItems:"center", gap:8 }}>
      <div style={{ flex:1, height:2, background:C.border, borderRadius:1 }}>
        <div style={{ width:`${pct}%`, height:"100%", background:col, borderRadius:1 }}/>
      </div>
      <span style={{ fontSize:10.5, color:col, fontWeight:600, minWidth:42, textAlign:"right", fontVariantNumeric:"tabular-nums" }}>{val.toFixed(1)} Hz</span>
    </div>
  );
};

const KPI = ({ label, value, sub, color }: any) => (
  <div style={{ background:C.surface, border:`1px solid ${C.border}`, borderRadius:5, padding:"18px 22px", borderTop:`3px solid ${color||C.navy}` }}>
    <div style={{ fontSize:10, color:C.textMuted, letterSpacing:"0.12em", textTransform:"uppercase", marginBottom:8, fontWeight:600 }}>{label}</div>
    <div style={{ fontSize:28, fontWeight:300, color:color||C.textPrimary, fontVariantNumeric:"tabular-nums", lineHeight:1 }}>{value}</div>
    {sub && <div style={{ fontSize:11, color:C.textMuted, marginTop:5 }}>{sub}</div>}
  </div>
);

const HR = () => <div style={{ height:1, background:C.border, margin:"0 -22px" }}/>;

const Btn = ({ children, variant="primary", onClick, small }: any) => {
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
function Dashboard({ assets, workOrders, stats, onAsset, onOrder }: any) {
  const sites = [...new Set(assets.map((a:any)=>a.site))];

  return (
    <div style={{ display:"flex", flexDirection:"column", gap:20 }}>
      <div style={{ display:"grid", gridTemplateColumns:"repeat(4,1fr)", gap:12 }}>
        <KPI label="Critical Assets"    value={stats.critical_count}  sub="Require immediate dispatch"  color={C.critical}/>
        <KPI label="Active Work Orders" value={stats.total_work_orders} sub={`${stats.p1_count} at Priority 1`} color={C.gold}/>
        <KPI label="Fleet Availability" value={`${stats.fleet_availability}%`} sub={`${stats.total_assets} assets monitored`}/>
        <KPI label="Technicians Ready"  value={stats.available_techs} sub="Available for dispatch" color={C.healthy}/>
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
            {assets.map((a:any) => {
              const bc = a.status==="CRITICAL"?C.criticalBdr:a.status==="WARNING"?C.warningBdr:C.border;
              const bg = a.status==="CRITICAL"?C.criticalBg:a.status==="WARNING"?C.warningBg:C.surfaceAlt;
              const vc = a.status==="CRITICAL"?C.critical:a.status==="WARNING"?C.warning:C.textMuted;
              return (
                <button key={a.id} onClick={()=>onAsset(a)} style={{ background:bg, border:`1px solid ${bc}`, borderRadius:4, padding:"9px 8px", textAlign:"left", cursor:"pointer", transition:"box-shadow 0.15s" }}
                  onMouseEnter={(e:any)=>e.currentTarget.style.boxShadow="0 2px 8px rgba(13,34,64,0.12)"}
                  onMouseLeave={(e:any)=>e.currentTarget.style.boxShadow="none"}>
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
            {sites.map((site:string) => {
              const sa = assets.filter((a:any)=>a.site===site);
              const sc = sa.filter((a:any)=>a.status==="CRITICAL").length;
              const sw = sa.filter((a:any)=>a.status==="WARNING").length;
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

          {/* Fleet Status */}
          <div style={{ background:C.surface, border:`1px solid ${C.border}`, borderRadius:5 }}>
            <div style={{ padding:"14px 20px" }}>
              <span style={{ fontSize:11, fontWeight:700, color:C.textPrimary, letterSpacing:"0.06em", textTransform:"uppercase" }}>Fleet Status</span>
            </div>
            <HR/>
            <div style={{ padding:"12px 20px", display:"flex", flexDirection:"column", gap:10 }}>
              {[
                ["Critical",C.critical,stats.critical_count],
                ["Warning",C.warning,stats.warning_count],
                ["Operational",C.healthy,stats.healthy_count]
              ].map(([l,col,v]:any)=>(
                <div key={l} style={{ display:"flex", alignItems:"center", gap:10 }}>
                  <div style={{ width:80, fontSize:11, color:C.textSec }}>{l}</div>
                  <div style={{ flex:1, height:5, background:C.border, borderRadius:2 }}>
                    <div style={{ width:`${(v/stats.total_assets)*100}%`, height:"100%", background:col, borderRadius:2 }}/>
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
          <Btn variant="ghost" small>View All</Btn>
        </div>
        <HR/>
        <table style={{ width:"100%", borderCollapse:"collapse" }}>
          <thead>
            <tr style={{ background:C.surfaceAlt }}>
              {["Work Order","Asset","Site","Priority","Status"].map(h=>(
                <th key={h} style={{ padding:"8px 20px", textAlign:"left", fontSize:9.5, fontWeight:700, color:C.textMuted, letterSpacing:"0.1em", textTransform:"uppercase", borderBottom:`1px solid ${C.border}` }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {workOrders.slice(0,5).map((w:any)=>{
              const a = assets.find((x:any)=>x.id===w.assetId);
              return (
                <tr key={w.id} onClick={()=>onOrder(w)} style={{ borderBottom:`1px solid ${C.border}`, cursor:"pointer" }}
                  onMouseEnter={(e:any)=>e.currentTarget.style.background=C.navyLight}
                  onMouseLeave={(e:any)=>e.currentTarget.style.background="transparent"}>
                  <td style={{ padding:"11px 20px", fontSize:11.5, fontWeight:700, color:C.navyMid, fontFamily:"monospace" }}>{w.id}</td>
                  <td style={{ padding:"11px 20px" }}>
                    <div style={{ fontSize:12, color:C.textPrimary, fontWeight:500 }}>{a?.name || w.assetId}</div>
                  </td>
                  <td style={{ padding:"11px 20px", fontSize:11.5, color:C.textSec }}>{a?.site}</td>
                  <td style={{ padding:"11px 20px" }}><PriorityMark p={w.priority}/></td>
                  <td style={{ padding:"11px 20px" }}>{pill(w.status)}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ─── APP SHELL ───────────────────────────────────────────────────────────────
export default function App() {
  const [assets, setAssets] = useState([]);
  const [workOrders, setWorkOrders] = useState([]);
  const [stats, setStats] = useState<any>({});
  const [loading, setLoading] = useState(true);
  const [selAsset, setSelAsset] = useState(null);
  const [live, setLive] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [assetsRes, ordersRes, statsRes] = await Promise.all([
          fetch(`${API_BASE}/assets`),
          fetch(`${API_BASE}/work-orders`),
          fetch(`${API_BASE}/dashboard-stats`)
        ]);

        setAssets(await assetsRes.json());
        setWorkOrders(await ordersRes.json());
        setStats(await statsRes.json());
        setLoading(false);
      } catch (err) {
        console.error("Failed to fetch data:", err);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const t = setInterval(()=>setLive(p=>!p), 2200);
    return ()=>clearInterval(t);
  }, []);

  const critical = assets.filter((a:any)=>a.status==="CRITICAL").length;

  if (loading) {
    return (
      <div style={{ minHeight:"100vh", background:C.bg, display:"flex", alignItems:"center", justifyContent:"center" }}>
        <div style={{ fontSize:14, color:C.textMuted }}>Loading MCE Operations...</div>
      </div>
    );
  }

  return (
    <div style={{ minHeight:"100vh", background:C.bg, color:C.textPrimary, fontFamily:"-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif", fontSize:14 }}>
      {/* Top nav */}
      <div style={{ background:C.surface, borderBottom:`1px solid ${C.border}`, padding:"0 28px", display:"flex", alignItems:"center", height:58, position:"sticky", top:0, zIndex:100, boxShadow:"0 1px 4px rgba(13,34,64,0.06)" }}>
        <MCELogo/>
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
        <div style={{ fontSize:11, color:"rgba(255,255,255,0.45)", letterSpacing:"0.06em", textTransform:"uppercase", marginBottom:4 }}>Fleet Dashboard</div>
        <div style={{ fontSize:11, color:"rgba(255,255,255,0.55)" }}>{stats.total_assets} monitored assets across {stats.total_sites} generation sites</div>
      </div>

      {/* Content */}
      <div style={{ padding:"24px 28px", maxWidth:1480, margin:"0 auto" }}>
        <Dashboard assets={assets} workOrders={workOrders} stats={stats} onAsset={setSelAsset} onOrder={()=>{}}/>
      </div>

      <div style={{ padding:"18px 28px", borderTop:`1px solid ${C.border}`, display:"flex", justifyContent:"space-between", fontSize:10, color:C.textMuted, letterSpacing:"0.07em", textTransform:"uppercase" }}>
        <span>Main Character Energy · Agentic Field Management Platform · v1.0.0</span>
        <span>Databricks Unity Catalog · Lakebase · Agent Bricks</span>
      </div>
    </div>
  );
}
