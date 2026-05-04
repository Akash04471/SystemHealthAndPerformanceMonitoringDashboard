import React, { useState, useEffect, useReducer } from "react";
import { login, getDashboardSnapshot, acknowledgeAlert, resolveAlert } from "./api";
import { HistoryChart } from "./components/HistoryChart";

const initialState = {
  token: localStorage.getItem("token"),
  summary: null,
  alerts: [],
  anomalies: [],
  history: [],
  predictions: [],
  loading: true,
  error: null
};

function reducer(state, action) {
  switch (action.type) {
    case "AUTH_SUCCESS":
      return { ...state, token: action.payload, error: null };
    case "FETCH_SUCCESS":
      return { 
        ...state, 
        ...action.payload, 
        loading: false, 
        error: null 
      };
    case "FETCH_ERROR":
      return { ...state, loading: false, error: action.payload };
    case "LOGOUT":
      return { ...initialState, token: null };
    default:
      return state;
  }
}

export function App() {
  const [state, dispatch] = useReducer(reducer, initialState);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [severityFilter, setSeverityFilter] = useState("all");

  useEffect(() => {
    if (state.token) {
      const fetchData = async () => {
        try {
          const data = await getDashboardSnapshot(state.token);
          dispatch({ type: "FETCH_SUCCESS", payload: data });
        } catch (err) {
          dispatch({ type: "FETCH_ERROR", payload: err.message });
          if (err.message.includes("401")) dispatch({ type: "LOGOUT" });
        }
      };
      fetchData();
      const interval = setInterval(fetchData, 10000);
      return () => clearInterval(interval);
    }
  }, [state.token]);

  const handleLogin = async (e) => {
    e.preventDefault();
    try {
      const data = await login(email, password);
      localStorage.setItem("token", data.access_token);
      dispatch({ type: "AUTH_SUCCESS", payload: data.access_token });
    } catch (err) {
      dispatch({ type: "FETCH_ERROR", payload: "Invalid credentials" });
    }
  };

  const filteredAlerts = state.alerts.filter(a => 
    severityFilter === "all" || a.severity === severityFilter
  );

  if (!state.token) {
    return (
      <div className="dashboard-container" style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '80vh' }}>
        <article className="panel" style={{ width: '100%', maxWidth: '400px' }}>
          <header style={{ border: 'none', textAlign: 'center', paddingBottom: '30px' }}>
            <div style={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'center' }}>
              <span className="system-pulse" style={{ width: '8px', height: '8px' }}></span>
              <h1 className="brand-title" style={{ fontSize: '2.5rem' }}>CRONACORE</h1>
            </div>
            <p className="brand-tagline" style={{ fontSize: '0.6rem', letterSpacing: '0.3em' }}>The Core of System Observability</p>
          </header>
          <form onSubmit={handleLogin}>
            <div style={{ marginBottom: "15px" }}>
              <input 
                className="auth-form input" 
                type="email" 
                placeholder="Email" 
                value={email} 
                onChange={(e) => setEmail(e.target.value)} 
                required 
              />
            </div>
            <div style={{ marginBottom: "25px" }}>
              <input 
                className="auth-form input" 
                type="password" 
                placeholder="Password" 
                value={password} 
                onChange={(e) => setPassword(e.target.value)} 
                required 
              />
            </div>
            <button className="auth-form button" style={{ width: "100%" }} type="submit">
              Sign In to Core
            </button>
            {state.error && <p style={{ color: "var(--accent-danger)", marginTop: "15px", textAlign: 'center' }}>{state.error}</p>}
          </form>
        </article>
      </div>
    );
  }

  return (
    <div className="dashboard-container">
      <header>
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
          <div style={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'center' }}>
            <span className="system-pulse"></span>
            <h1 className="brand-title">CRONACORE</h1>
          </div>
          <p className="brand-tagline">The Core of System Observability</p>
        </div>
        <div style={{ position: 'absolute', top: '20px', right: '40px' }}>
          <button 
            className="auth-form button" 
            style={{ background: 'transparent', color: 'var(--text-muted)', border: '1px solid var(--border)', fontSize: '0.65rem' }}
            onClick={() => { localStorage.removeItem("token"); dispatch({ type: "LOGOUT" }); }}
          >
            Terminal Logout
          </button>
        </div>
      </header>

      <section className="grid">
        <article className="panel" style={{ animationDelay: '0.1s' }}>
          <div className="panel-header">
            <h2>Open Alerts</h2>
            <span style={{ color: 'var(--accent-em)', fontWeight: '700' }}>Live</span>
          </div>
          <div className="metric-value">
            {state.summary?.open_alert_count || 0}
          </div>
        </article>
        <article className="panel" style={{ animationDelay: '0.2s' }}>
          <div className="panel-header">
            <h2>Anomalies</h2>
            <span>Recent (24h)</span>
          </div>
          <div className="metric-value">
            {state.summary?.recent_anomaly_count || 0}
          </div>
        </article>
        <article className="panel" style={{ animationDelay: '0.3s' }}>
          <div className="panel-header">
            <h2>Critical</h2>
            <span style={{ color: 'var(--accent-danger)' }}>Action Required</span>
          </div>
          <div className="metric-value" style={{ background: 'linear-gradient(180deg, #fff 0%, var(--accent-danger) 100%)', webkitBackgroundClip: 'text' }}>
            {state.summary?.alerts_by_severity?.critical || 0}
          </div>
        </article>
        <article className="panel" style={{ animationDelay: '0.4s' }}>
          <div className="panel-header">
            <h2>High</h2>
            <span style={{ color: 'var(--accent-warn)' }}>Active</span>
          </div>
          <div className="metric-value" style={{ background: 'linear-gradient(180deg, #fff 0%, var(--accent-warn) 100%)', webkitBackgroundClip: 'text' }}>
            {state.summary?.alerts_by_severity?.high || 0}
          </div>
        </article>
      </section>

      <section className="grid" style={{ marginTop: "30px" }}>
        <article className="panel" style={{ gridColumn: "span 1", animationDelay: '0.5s' }}>
          <div className="panel-header">
            <h2>Active Alerts</h2>
            <span>{state.alerts.length} total</span>
          </div>
          <div className="control-row" style={{ marginBottom: '20px' }}>
            <select className="auth-form input" style={{ padding: '4px 8px' }} onChange={(e) => setSeverityFilter(e.target.value)}>
              <option value="all">All Severity</option>
              <option value="critical">Critical</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
            </select>
          </div>
          <ul style={{ maxHeight: '500px', overflowY: 'auto', paddingRight: '10px' }}>
            {filteredAlerts.length === 0 ? <p style={{color: 'var(--text-muted)'}}>No active alerts.</p> : filteredAlerts.map((alert) => (
              <div key={alert.id} className={`data-row severity-${alert.severity}`}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{fontWeight: '700', fontSize: '0.9rem'}}>{alert.service_key}</span>
                  <span className={`chip chip-${alert.severity === 'critical' || alert.severity === 'high' ? 'danger' : 'blue'}`}>
                    {alert.severity}
                  </span>
                </div>
                <div style={{fontSize: '0.85rem', opacity: 0.9}}>{alert.title}</div>
                <div style={{display: 'flex', gap: '8px', marginTop: '12px'}}>
                  <button className="auth-form button" style={{padding: '6px 12px', fontSize: '0.65rem'}} onClick={() => acknowledgeAlert(state.token, alert.id)}>Acknowledge</button>
                  <button className="auth-form button" style={{padding: '6px 12px', fontSize: '0.65rem', background: 'transparent', color: 'var(--text-muted)', border: '1px solid var(--border)'}} onClick={() => resolveAlert(state.token, alert.id)}>Resolve</button>
                </div>
              </div>
            ))}
          </ul>
        </article>

        <article className="panel" style={{ gridColumn: "span 1", animationDelay: '0.6s' }}>
          <div className="panel-header">
            <h2>System Anomalies</h2>
            <span>{state.anomalies.length} total</span>
          </div>
          <ul style={{ maxHeight: '600px', overflowY: 'auto', paddingRight: '10px' }}>
            {state.anomalies.length === 0 ? <p style={{color: 'var(--text-muted)'}}>No anomalies detected.</p> : state.anomalies.slice(0, 10).map((anomaly) => (
              <div key={anomaly.id} className="data-row" style={{ borderLeft: '2px solid var(--accent-warn)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{fontWeight: '700', fontSize: '0.85rem'}}>{anomaly.service_key}</span>
                  <span className="chip chip-warn">SCORE: {Number(anomaly.score).toFixed(2)}</span>
                </div>
                <div style={{fontSize: '0.8rem', color: 'var(--text-muted)'}}>
                  Metric: <span style={{color: 'var(--text-primary)'}}>{anomaly.metric_name}</span>
                </div>
                <div style={{fontSize: '0.7rem', marginTop: '4px', opacity: 0.5}}>
                  {new Date(anomaly.ts).toLocaleString()}
                </div>
              </div>
            ))}
          </ul>
        </article>

        <article className="panel" style={{ animationDelay: '0.7s' }}>
          <div className="panel-header">
            <h2>Agent Status</h2>
            <span style={{ color: 'var(--text-muted)' }}>Core Health</span>
          </div>
          <div style={{ marginTop: "15px" }}>
            <div className="agent-table-row" style={{ color: 'var(--text-muted)', fontSize: '0.65rem', textTransform: 'uppercase', borderBottom: '1px solid var(--border)' }}>
              <span>Service</span>
              <span>Last Pulse</span>
              <span>Status</span>
            </div>
            {state.summary?.last_ingestion_by_service?.length === 0 ? (
              <p style={{ color: "var(--text-muted)", padding: '20px' }}>No agents connected.</p>
            ) : (
              state.summary?.last_ingestion_by_service?.map((agent) => (
                <div key={agent.service_key} className="agent-table-row">
                  <span style={{ fontWeight: "700", fontSize: '0.85rem' }}>{agent.service_key}</span>
                  <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
                    {agent.last_seen_at ? new Date(agent.last_seen_at).toLocaleTimeString() : "N/A"}
                  </span>
                  <span className={`chip chip-${agent.status === 'online' ? 'em' : 'danger'}`} style={{ fontSize: '0.55rem', textAlign: 'center' }}>
                    {agent.status}
                  </span>
                </div>
              ))
            )}
          </div>
        </article>
      </section>

      <section className="grid" style={{ marginTop: "30px" }}>
        <article className="panel" style={{ gridColumn: "span 2", animationDelay: '0.8s' }}>
          <div className="panel-header">
            <h2>System Trends (7 Days)</h2>
            <button 
              className="auth-form button" 
              style={{ padding: '6px 16px', fontSize: '0.8rem', background: 'var(--bg-panel-alt)', border: '1px solid var(--border)', color: 'var(--text-primary)' }}
              onClick={() => window.open(`http://127.0.0.1:8000/api/v1/analytics/report/csv?token=${state.token}`, '_blank')}
            >
              Export System Report
            </button>
          </div>
          <HistoryChart data={state.history} />
        </article>

        <article className="panel" style={{ gridColumn: "span 1", animationDelay: '0.9s' }}>
          <div className="panel-header">
            <h2>Predictive Insights</h2>
            <span style={{ color: 'var(--accent-blue)' }}>AI Forecasting</span>
          </div>
          <div style={{ marginTop: "10px" }}>
            {state.predictions.length === 0 ? (
              <p style={{ color: "var(--text-muted)" }}>Analyzing telemetry data...</p>
            ) : (
              state.predictions.map((pred, i) => (
                <div key={i} className="prediction-card">
                  <div style={{ fontWeight: '700', fontSize: '0.9rem', marginBottom: '5px' }}>
                    {pred.service_key} | {pred.metric}
                  </div>
                  <div style={{ fontSize: '0.85rem' }}>
                    Days until 100%: <span style={{ color: pred.days_to_threshold < 7 ? 'var(--accent-danger)' : 'var(--accent-em)', fontWeight: '700' }}>
                      {pred.days_to_threshold === Infinity ? "STABLE" : pred.days_to_threshold.toFixed(1)}
                    </span>
                  </div>
                  <div style={{ height: '4px', width: '100%', background: 'var(--bg-base)', marginTop: '8px', borderRadius: '2px' }}>
                    <div style={{ 
                      height: '100%', 
                      width: `${Math.min(100, (1/pred.days_to_threshold)*500)}%`, 
                      background: 'var(--accent-em)',
                      borderRadius: '2px'
                    }}></div>
                  </div>
                </div>
              ))
            )}
          </div>
        </article>
      </section>
    </div>
  );
}
