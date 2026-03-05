import { useState, useEffect } from "react";

// MCE Color Palette
const C = {
  bg: "#F5F6F8",
  navy: "#0F1C2E",
  navyLight: "#1A2942",
  gold: "#B8760A",
  critical: "#DC2626",
  criticalBg: "#FEF2F2",
  warning: "#EA580C",
  warningBg: "#FFF7ED",
  healthy: "#059669",
  healthyBg: "#F0FDF4",
  blue: "#2563EB",
  blueBg: "#EFF6FF",
  gray: "#64748B",
  grayBg: "#F8FAFC",
  border: "#E2E8F0",
  textPrimary: "#0F172A",
  textSec: "#475569",
  textMuted: "#94A3B8",
};

const API_BASE = "/api";

interface Asset {
  id: string;
  name: string;
  site: string;
  type: string;
  vibration: number;
  temp: number;
  status: string;
  lastUpdated: string;
  hoursSinceMaint: number;
  predictedFailure: string | null;
}

interface Stats {
  critical_count: number;
  warning_count: number;
  healthy_count: number;
  total_assets: number;
  total_sites: number;
  total_work_orders: number;
  p1_count: number;
  available_techs: number;
  fleet_availability: number;
}

interface WorkOrder {
  id: string;
  assetId: string;
  createdAt: string;
  priority: string;
  status: string;
  technician: string;
  failureDate: string;
  failureType: string;
  requiredParts: string;
  procedureSteps: string;
  safetyChecklist: string;
  repairSummary: string;
  estimatedHours: number;
  updatedAt: string;
}

export default function App() {
  const [activeTab, setActiveTab] = useState<"dashboard" | "workorders">("dashboard");
  const [assets, setAssets] = useState<Asset[]>([]);
  const [workOrders, setWorkOrders] = useState<WorkOrder[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [lastUpdated, setLastUpdated] = useState<string>("");

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [assetsRes, workOrdersRes, statsRes] = await Promise.all([
          fetch(`${API_BASE}/assets`),
          fetch(`${API_BASE}/work-orders`),
          fetch(`${API_BASE}/dashboard-stats`),
        ]);
        const assetsData = await assetsRes.json();
        const workOrdersData = await workOrdersRes.json();
        const statsData = await statsRes.json();
        setAssets(assetsData);
        setWorkOrders(workOrdersData);
        setStats(statsData);
        setLastUpdated(new Date().toLocaleString());
      } catch (err) {
        console.error("Failed to fetch data:", err);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, []);

  const getAssetPrefix = (type: string): string => {
    const prefixes: Record<string, string> = {
      wind_turbine: "WT",
      gas_turbine: "GT",
      substation: "SS",
      solar_inverter: "SP",
      hydro_unit: "HY",
    };
    return prefixes[type] || "AS";
  };

  const getStatusColor = (status: string) => {
    if (status === "CRITICAL") return { border: C.critical, bg: C.criticalBg, text: C.critical };
    if (status === "WARNING") return { border: C.warning, bg: C.warningBg, text: C.warning };
    if (status === "HEALTHY") return { border: C.healthy, bg: C.healthyBg, text: C.healthy };
    return { border: C.gray, bg: C.grayBg, text: C.gray };
  };

  const getVibrationBarWidth = (hz: number): number => {
    return Math.min((hz / 100) * 100, 100);
  };

  return (
    <div style={{ minHeight: "100vh", backgroundColor: C.bg, fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" }}>
      {/* Header */}
      <div style={{ backgroundColor: "white", borderBottom: `1px solid ${C.border}`, padding: "12px 24px" }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", maxWidth: "1600px", margin: "0 auto" }}>
          {/* Logo */}
          <div style={{ display: "flex", alignItems: "center", gap: "32px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <svg width="32" height="32" viewBox="0 0 32 32" fill="none">
                <path d="M6 4 L14 4 L10 16 L18 16 L8 28 L10 18 L2 18 Z" fill={C.gold} />
              </svg>
              <div>
                <div style={{ fontFamily: "Georgia, serif", fontSize: "18px", fontWeight: 700, color: C.navy, letterSpacing: "-0.5px" }}>MCE</div>
                <div style={{ fontSize: "9px", color: C.textMuted, letterSpacing: "2px", marginTop: "-2px" }}>MAIN CHARACTER ENERGY</div>
              </div>
            </div>

            {/* Tabs */}
            <div style={{ display: "flex", gap: "4px" }}>
              <button
                onClick={() => setActiveTab("dashboard")}
                style={{
                  padding: "8px 16px",
                  backgroundColor: activeTab === "dashboard" ? C.navy : "transparent",
                  color: activeTab === "dashboard" ? "white" : C.textSec,
                  border: "none",
                  borderRadius: "6px",
                  fontSize: "14px",
                  fontWeight: 500,
                  cursor: "pointer"
                }}
              >
                Fleet Dashboard
              </button>
              <button
                onClick={() => setActiveTab("workorders")}
                style={{
                  padding: "8px 16px",
                  backgroundColor: activeTab === "workorders" ? C.navy : "transparent",
                  color: activeTab === "workorders" ? "white" : C.textSec,
                  border: "none",
                  borderRadius: "6px",
                  fontSize: "14px",
                  fontWeight: 500,
                  cursor: "pointer"
                }}
              >
                Work Orders
              </button>
            </div>
          </div>

          {/* Right side */}
          <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "6px", fontSize: "13px", color: C.textMuted }}>
              <div style={{ width: "6px", height: "6px", borderRadius: "50%", backgroundColor: C.healthy, animation: "pulse 2s infinite" }}></div>
              Live · AEST
            </div>
            <div style={{ padding: "4px 12px", backgroundColor: C.criticalBg, color: C.critical, borderRadius: "6px", fontSize: "13px", fontWeight: 600 }}>
              {stats?.critical_count || 0} Critical
            </div>
          </div>
        </div>
      </div>

      {/* Hero Section */}
      <div style={{ backgroundColor: C.navy, color: "white", padding: "32px 24px" }}>
        <div style={{ maxWidth: "1600px", margin: "0 auto" }}>
          {activeTab === "dashboard" ? (
            <>
              <div style={{ fontSize: "13px", fontWeight: 600, letterSpacing: "2px", opacity: 0.7, marginBottom: "8px" }}>FLEET DASHBOARD</div>
              <div style={{ fontSize: "16px", opacity: 0.9 }}>{stats?.total_assets || 0} monitored assets across {stats?.total_sites || 0} generation sites</div>
            </>
          ) : (
            <>
              <div style={{ fontSize: "13px", fontWeight: 600, letterSpacing: "2px", opacity: 0.7, marginBottom: "8px" }}>WORK ORDERS</div>
              <div style={{ fontSize: "16px", opacity: 0.9 }}>{stats?.total_work_orders || 0} active work orders ({stats?.p1_count || 0} Priority 1)</div>
            </>
          )}
        </div>
      </div>

      {/* Main Content */}
      <div style={{ maxWidth: "1600px", margin: "0 auto", padding: "32px 24px" }}>
        {activeTab === "dashboard" && (
          <>
        {/* KPI Cards */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: "16px", marginBottom: "32px" }}>
          {/* Critical Assets */}
          <div style={{ backgroundColor: "white", border: `2px solid ${C.critical}`, borderRadius: "12px", padding: "24px" }}>
            <div style={{ fontSize: "12px", fontWeight: 600, color: C.textMuted, letterSpacing: "1px", marginBottom: "12px" }}>CRITICAL ASSETS</div>
            <div style={{ fontSize: "48px", fontWeight: 700, color: C.critical, lineHeight: 1, marginBottom: "8px" }}>{stats?.critical_count || 0}</div>
            <div style={{ fontSize: "13px", color: C.textSec }}>Require immediate dispatch</div>
          </div>

          {/* Active Work Orders */}
          <div style={{ backgroundColor: "white", border: `2px solid ${C.warning}`, borderRadius: "12px", padding: "24px" }}>
            <div style={{ fontSize: "12px", fontWeight: 600, color: C.textMuted, letterSpacing: "1px", marginBottom: "12px" }}>ACTIVE WORK ORDERS</div>
            <div style={{ fontSize: "48px", fontWeight: 700, color: C.warning, lineHeight: 1, marginBottom: "8px" }}>{stats?.total_work_orders || 0}</div>
            <div style={{ fontSize: "13px", color: C.textSec }}>{stats?.p1_count || 0} at Priority 1</div>
          </div>

          {/* Fleet Availability */}
          <div style={{ backgroundColor: "white", border: `2px solid ${C.blue}`, borderRadius: "12px", padding: "24px" }}>
            <div style={{ fontSize: "12px", fontWeight: 600, color: C.textMuted, letterSpacing: "1px", marginBottom: "12px" }}>FLEET AVAILABILITY</div>
            <div style={{ fontSize: "48px", fontWeight: 700, color: C.blue, lineHeight: 1, marginBottom: "8px" }}>{stats?.fleet_availability.toFixed(1) || 0}%</div>
            <div style={{ fontSize: "13px", color: C.textSec }}>{(stats?.healthy_count || 0) + (stats?.warning_count || 0)} of {stats?.total_assets || 0} assets monitored</div>
          </div>

          {/* First-Time Fix Rate */}
          <div style={{ backgroundColor: "white", border: `2px solid ${C.healthy}`, borderRadius: "12px", padding: "24px" }}>
            <div style={{ fontSize: "12px", fontWeight: 600, color: C.textMuted, letterSpacing: "1px", marginBottom: "12px" }}>FIRST-TIME FIX RATE</div>
            <div style={{ fontSize: "48px", fontWeight: 700, color: C.healthy, lineHeight: 1, marginBottom: "8px" }}>91.4%</div>
            <div style={{ fontSize: "13px", color: C.textSec }}>Rolling 90-day average</div>
          </div>
        </div>

        {/* Asset Fleet */}
        <div style={{ backgroundColor: "white", borderRadius: "12px", border: `1px solid ${C.border}`, overflow: "hidden" }}>
          {/* Header */}
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "20px 24px", borderBottom: `1px solid ${C.border}` }}>
            <div style={{ fontSize: "14px", fontWeight: 600, color: C.textPrimary, letterSpacing: "1px" }}>ASSET FLEET</div>
            <div style={{ fontSize: "13px", color: C.textMuted }}>{lastUpdated}</div>
          </div>

          {/* Asset Grid */}
          <div style={{ padding: "24px", display: "grid", gridTemplateColumns: "repeat(5, 1fr)", gap: "16px" }}>
            {assets.map((asset) => {
              const statusColors = getStatusColor(asset.status);
              const prefix = getAssetPrefix(asset.type);
              const displayId = `${prefix}-${asset.id.split("-")[1]}`;

              return (
                <div
                  key={asset.id}
                  style={{
                    backgroundColor: statusColors.bg,
                    border: `2px solid ${statusColors.border}`,
                    borderRadius: "8px",
                    padding: "16px",
                    transition: "all 0.2s",
                  }}
                >
                  {/* Header */}
                  <div style={{ marginBottom: "8px" }}>
                    <div style={{ fontSize: "13px", fontWeight: 600, color: statusColors.text, marginBottom: "2px" }}>{displayId}</div>
                    <div style={{ fontSize: "12px", fontWeight: 600, color: C.textPrimary, marginBottom: "4px" }}>{asset.name.split(" ").slice(0, 3).join(" ")}</div>
                    <div style={{ fontSize: "11px", color: C.textMuted }}>{asset.site.split(",")[0]}</div>
                  </div>

                  {/* Vibration Bar */}
                  <div style={{ marginTop: "12px" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "4px" }}>
                      <div style={{ fontSize: "10px", color: C.textMuted }}>VIBRATION</div>
                      <div style={{ fontSize: "13px", fontWeight: 600, color: statusColors.text }}>{asset.vibration.toFixed(1)} Hz</div>
                    </div>
                    <div style={{ height: "4px", backgroundColor: C.border, borderRadius: "2px", overflow: "hidden" }}>
                      <div
                        style={{
                          height: "100%",
                          width: `${getVibrationBarWidth(asset.vibration)}%`,
                          backgroundColor: statusColors.border,
                          transition: "width 0.3s",
                        }}
                      />
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
        </>
        )}

        {activeTab === "workorders" && (
          <div style={{ backgroundColor: "white", borderRadius: "12px", border: `1px solid ${C.border}`, overflow: "hidden" }}>
            {/* Header */}
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "20px 24px", borderBottom: `1px solid ${C.border}` }}>
              <div style={{ fontSize: "14px", fontWeight: 600, color: C.textPrimary, letterSpacing: "1px" }}>ACTIVE WORK ORDERS</div>
              <div style={{ fontSize: "13px", color: C.textMuted }}>{lastUpdated}</div>
            </div>

            {/* Work Orders List */}
            <div style={{ padding: "24px" }}>
              {workOrders.length === 0 ? (
                <div style={{ textAlign: "center", padding: "48px 24px", color: C.textMuted }}>
                  <div style={{ fontSize: "48px", marginBottom: "16px" }}>📋</div>
                  <div style={{ fontSize: "16px", fontWeight: 600, marginBottom: "8px" }}>No Active Work Orders</div>
                  <div style={{ fontSize: "14px" }}>All assets are operational</div>
                </div>
              ) : (
                <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
                  {workOrders.map((wo) => {
                    const priorityColor = wo.priority === "P1" ? C.critical : wo.priority === "P2" ? C.warning : C.blue;
                    const priorityBg = wo.priority === "P1" ? C.criticalBg : wo.priority === "P2" ? C.warningBg : C.blueBg;
                    const statusColor = wo.status === "IN_PROGRESS" ? C.blue : wo.status === "DISPATCHED" ? C.warning : C.gray;

                    return (
                      <div
                        key={wo.id}
                        style={{
                          backgroundColor: "white",
                          border: `2px solid ${C.border}`,
                          borderRadius: "12px",
                          padding: "24px",
                          transition: "all 0.2s",
                        }}
                      >
                        {/* Header Row */}
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "16px" }}>
                          <div>
                            <div style={{ display: "flex", gap: "12px", alignItems: "center", marginBottom: "8px" }}>
                              <span style={{ fontSize: "18px", fontWeight: 700, color: C.navy }}>{wo.id}</span>
                              <span
                                style={{
                                  padding: "4px 12px",
                                  backgroundColor: priorityBg,
                                  color: priorityColor,
                                  borderRadius: "6px",
                                  fontSize: "12px",
                                  fontWeight: 700,
                                }}
                              >
                                {wo.priority}
                              </span>
                              <span
                                style={{
                                  padding: "4px 12px",
                                  backgroundColor: C.blueBg,
                                  color: statusColor,
                                  borderRadius: "6px",
                                  fontSize: "12px",
                                  fontWeight: 600,
                                }}
                              >
                                {wo.status.replace("_", " ")}
                              </span>
                            </div>
                            <div style={{ fontSize: "14px", color: C.textSec }}>
                              Asset: <span style={{ fontWeight: 600, color: C.navy }}>{wo.assetId}</span> · Failure Type: <span style={{ fontWeight: 600 }}>{wo.failureType}</span>
                            </div>
                          </div>
                          <div style={{ textAlign: "right" }}>
                            <div style={{ fontSize: "13px", color: C.textMuted, marginBottom: "4px" }}>Assigned To</div>
                            <div style={{ fontSize: "14px", fontWeight: 600, color: C.navy }}>{wo.technician}</div>
                          </div>
                        </div>

                        {/* AI Summary */}
                        <div style={{ backgroundColor: C.grayBg, borderRadius: "8px", padding: "16px", marginBottom: "16px" }}>
                          <div style={{ fontSize: "11px", fontWeight: 600, color: C.textMuted, letterSpacing: "1px", marginBottom: "8px" }}>AI REPAIR SUMMARY</div>
                          <div style={{ fontSize: "14px", color: C.textPrimary, lineHeight: "1.5" }}>{wo.repairSummary}</div>
                        </div>

                        {/* Details Grid */}
                        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "16px" }}>
                          <div>
                            <div style={{ fontSize: "11px", fontWeight: 600, color: C.textMuted, letterSpacing: "1px", marginBottom: "4px" }}>REQUIRED PARTS</div>
                            <div style={{ fontSize: "13px", color: C.textPrimary }}>{wo.requiredParts}</div>
                          </div>
                          <div>
                            <div style={{ fontSize: "11px", fontWeight: 600, color: C.textMuted, letterSpacing: "1px", marginBottom: "4px" }}>ESTIMATED DURATION</div>
                            <div style={{ fontSize: "13px", color: C.textPrimary }}>{wo.estimatedHours} hours</div>
                          </div>
                          <div>
                            <div style={{ fontSize: "11px", fontWeight: 600, color: C.textMuted, letterSpacing: "1px", marginBottom: "4px" }}>PREDICTED FAILURE</div>
                            <div style={{ fontSize: "13px", color: C.textPrimary }}>{new Date(wo.failureDate).toLocaleDateString()}</div>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.5; }
        }
        button:hover {
          opacity: 0.9;
        }
      `}</style>
    </div>
  );
}
