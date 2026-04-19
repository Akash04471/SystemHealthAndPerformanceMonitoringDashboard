import { useEffect, useMemo, useState } from "react";
import {
  acknowledgeAlert,
  getDashboardSnapshot,
  login,
  refreshAuthToken,
  resolveAlert
} from "./api";

const initialState = {
  loading: false,
  error: "",
  token: "",
  refreshToken: "",
  lastUpdated: "",
  liveMode: true,
  liveStatus: "offline",
  summary: null,
  alerts: [],
  anomalies: []
};

export function App() {
  const [email, setEmail] = useState("admin@example.com");
  const [password, setPassword] = useState("admin123");
  const [state, setState] = useState(initialState);
  const [alertStatusFilter, setAlertStatusFilter] = useState("all");
  const [alertSeverityFilter, setAlertSeverityFilter] = useState("all");
  const [alertServiceFilter, setAlertServiceFilter] = useState("all");
  const [anomalySeverityFilter, setAnomalySeverityFilter] = useState("all");
  const [anomalyServiceFilter, setAnomalyServiceFilter] = useState("all");
  const [refreshSeconds, setRefreshSeconds] = useState(15);

  function toDisplayError(error, fallback = "Unknown error") {
    if (!(error instanceof Error)) {
      return fallback;
    }

    if (error.message.startsWith("401:")) {
      return "Session expired. Please load dashboard again.";
    }

    return error.message;
  }

  async function withTokenRetry(action, overrideToken) {
    const token = overrideToken ?? state.token;
    try {
      return await action(token);
    } catch (error) {
      const isUnauthorized = error instanceof Error && error.message.startsWith("401:");
      if (!isUnauthorized || !state.refreshToken) {
        throw error;
      }

      const refreshed = await refreshAuthToken(state.refreshToken);
      const nextAccessToken = refreshed.access_token;
      const nextRefreshToken = refreshed.refresh_token;

      setState((current) => ({
        ...current,
        token: nextAccessToken,
        refreshToken: nextRefreshToken,
        error: ""
      }));

      return action(nextAccessToken);
    }
  }

  const cards = useMemo(() => {
    if (!state.summary) {
      return [];
    }

    return [
      { label: "Open Alerts", value: state.summary.open_alert_count },
      { label: "Recent Anomalies", value: state.summary.recent_anomaly_count },
      { label: "Critical", value: state.summary.alerts_by_severity.critical ?? 0 },
      { label: "High", value: state.summary.alerts_by_severity.high ?? 0 }
    ];
  }, [state.summary]);

  const alertServiceOptions = useMemo(() => {
    return Array.from(new Set(state.alerts.map((alert) => alert.service_key))).sort();
  }, [state.alerts]);

  const anomalyServiceOptions = useMemo(() => {
    return Array.from(new Set(state.anomalies.map((anomaly) => anomaly.service_key))).sort();
  }, [state.anomalies]);

  const filteredAlerts = useMemo(() => {
    return state.alerts.filter((alert) => {
      if (alertStatusFilter !== "all" && alert.status !== alertStatusFilter) {
        return false;
      }
      if (alertSeverityFilter !== "all" && alert.severity !== alertSeverityFilter) {
        return false;
      }
      if (alertServiceFilter !== "all" && alert.service_key !== alertServiceFilter) {
        return false;
      }
      return true;
    });
  }, [alertServiceFilter, alertSeverityFilter, alertStatusFilter, state.alerts]);

  const filteredAnomalies = useMemo(() => {
    return state.anomalies.filter((anomaly) => {
      if (anomalySeverityFilter !== "all" && anomaly.severity !== anomalySeverityFilter) {
        return false;
      }
      if (anomalyServiceFilter !== "all" && anomaly.service_key !== anomalyServiceFilter) {
        return false;
      }
      return true;
    });
  }, [anomalyServiceFilter, anomalySeverityFilter, state.anomalies]);

  async function loadDashboard(token, markLive = false) {
    try {
      const snapshot = await withTokenRetry((validToken) => getDashboardSnapshot(validToken), token);
      setState((current) => ({
        ...current,
        summary: snapshot.summary,
        alerts: snapshot.alerts,
        anomalies: snapshot.anomalies,
        lastUpdated: new Date().toISOString(),
        liveStatus: markLive ? "live" : current.liveStatus
      }));
    } catch (error) {
      if (markLive) {
        setState((current) => ({
          ...current,
          liveStatus: "error",
          error: error instanceof Error ? error.message : "Unknown error"
        }));
        return;
      }

      throw error;
    }
  }

  async function handleLogin(event) {
    event.preventDefault();
    setState((current) => ({ ...current, loading: true, error: "" }));

    try {
      const tokenResponse = await login(email, password);
      const token = tokenResponse.access_token;
      const refreshToken = tokenResponse.refresh_token;
      setState((current) => ({ ...current, liveStatus: "connecting" }));
      await loadDashboard(token, true);

      setState((current) => ({
        ...current,
        loading: false,
        error: "",
        token,
        refreshToken
      }));
    } catch (error) {
      setState((current) => ({
        ...current,
        loading: false,
        error: toDisplayError(error)
      }));
    }
  }

  useEffect(() => {
    if (!state.token || !state.liveMode) {
      return;
    }

    setState((current) => ({ ...current, liveStatus: current.liveStatus === "offline" ? "connecting" : current.liveStatus }));
    const interval = window.setInterval(() => {
      loadDashboard(state.token, true).catch((error) => {
        setState((current) => ({
          ...current,
          liveStatus: "error",
          error: toDisplayError(error)
        }));
      });
    }, Math.max(5, refreshSeconds) * 1000);

    return () => {
      window.clearInterval(interval);
    };
  }, [refreshSeconds, state.liveMode, state.token]);

  useEffect(() => {
    if (!state.token || !state.liveMode) {
      return;
    }

    const timeout = window.setTimeout(() => {
      setState((current) => ({
        ...current,
        liveStatus: current.liveStatus === "offline" ? "connecting" : current.liveStatus
      }));
    }, 0);

    return () => window.clearTimeout(timeout);
  }, [state.liveMode, state.token]);

  async function manualRefresh() {
    if (!state.token) {
      return;
    }

    setState((current) => ({ ...current, loading: true, error: "", liveStatus: "connecting" }));
    try {
      await loadDashboard(state.token, true);
      setState((current) => ({ ...current, loading: false }));
    } catch (error) {
      setState((current) => ({
        ...current,
        loading: false,
        liveStatus: "error",
        error: toDisplayError(error)
      }));
    }
  }

  async function handleAcknowledge(alertId) {
    if (!state.token) {
      return;
    }

    setState((current) => ({ ...current, loading: true, error: "" }));
    try {
      await withTokenRetry((validToken) => acknowledgeAlert(validToken, alertId));
      await loadDashboard(state.token, true);
      setState((current) => ({ ...current, loading: false }));
    } catch (error) {
      setState((current) => ({
        ...current,
        loading: false,
        error: toDisplayError(error)
      }));
    }
  }

  async function handleResolve(alertId) {
    if (!state.token) {
      return;
    }

    setState((current) => ({ ...current, loading: true, error: "" }));
    try {
      await withTokenRetry((validToken) => resolveAlert(validToken, alertId));
      await loadDashboard(state.token, true);
      setState((current) => ({ ...current, loading: false }));
    } catch (error) {
      setState((current) => ({
        ...current,
        loading: false,
        error: toDisplayError(error)
      }));
    }
  }

  return (
    <main className="page">
      <section className="auth-box">
        <h1>Phase 3 Frontend</h1>
        <p>Connects to your live Phase 2 backend.</p>
        <form onSubmit={handleLogin} className="auth-form">
          <input value={email} onChange={(e) => setEmail(e.target.value)} placeholder="Admin email" />
          <input
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Admin password"
            type="password"
          />
          <button type="submit" disabled={state.loading}>
            {state.loading ? "Loading..." : "Load Dashboard"}
          </button>
        </form>
        <div className="status-row">
          {state.token ? <small>Token loaded</small> : null}
          {state.token ? <small>Live: {state.liveStatus}</small> : null}
          {state.lastUpdated ? <small>Last update: {new Date(state.lastUpdated).toLocaleTimeString()}</small> : null}
        </div>
        <div className="control-row">
          <label>
            <span>Auto-refresh</span>
            <input
              type="checkbox"
              checked={state.liveMode}
              onChange={(event) =>
                setState((current) => ({
                  ...current,
                  liveMode: event.target.checked,
                  liveStatus: event.target.checked && current.token ? "connecting" : "offline"
                }))
              }
            />
          </label>
          <label>
            <span>Refresh seconds</span>
            <input
              type="number"
              min={5}
              max={120}
              value={refreshSeconds}
              onChange={(event) => setRefreshSeconds(Number(event.target.value) || 15)}
            />
          </label>
          <button type="button" onClick={manualRefresh} disabled={!state.token || state.loading}>
            Refresh now
          </button>
        </div>
        {state.error ? <p className="error">{state.error}</p> : null}
      </section>

      <section className="cards">
        {cards.map((card) => (
          <article className="card" key={card.label}>
            <span>{card.label}</span>
            <strong>{card.value}</strong>
          </article>
        ))}
      </section>

      <section className="grid">
        <article className="panel">
          <div className="panel-header">
            <h2>Recent Alerts</h2>
            <span>{filteredAlerts.length} shown</span>
          </div>
          <div className="filter-row">
            <label>
              <span>Status</span>
              <select value={alertStatusFilter} onChange={(event) => setAlertStatusFilter(event.target.value)}>
                <option value="all">All</option>
                <option value="open">Open</option>
                <option value="acknowledged">Acknowledged</option>
                <option value="resolved">Resolved</option>
              </select>
            </label>
            <label>
              <span>Severity</span>
              <select value={alertSeverityFilter} onChange={(event) => setAlertSeverityFilter(event.target.value)}>
                <option value="all">All</option>
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
                <option value="critical">Critical</option>
              </select>
            </label>
            <label>
              <span>Service</span>
              <select value={alertServiceFilter} onChange={(event) => setAlertServiceFilter(event.target.value)}>
                <option value="all">All</option>
                {alertServiceOptions.map((serviceKey) => (
                  <option key={serviceKey} value={serviceKey}>
                    {serviceKey}
                  </option>
                ))}
              </select>
            </label>
          </div>
          <ul>
            {filteredAlerts.slice(0, 8).map((alert) => (
              <li key={alert.id}>
                <div>
                  <b>{alert.severity.toUpperCase()}</b> {alert.service_key} - {alert.title}
                </div>
                <div>
                  <small>Status: {alert.status}</small>
                </div>
                <div className="alert-actions">
                  <button
                    type="button"
                    disabled={state.loading || alert.status === "acknowledged" || alert.status === "resolved"}
                    onClick={() => handleAcknowledge(alert.id)}
                  >
                    Acknowledge
                  </button>
                  <button
                    type="button"
                    disabled={state.loading || alert.status === "resolved"}
                    onClick={() => handleResolve(alert.id)}
                  >
                    Resolve
                  </button>
                </div>
              </li>
            ))}
          </ul>
        </article>

        <article className="panel">
          <div className="panel-header">
            <h2>Recent Anomalies</h2>
            <span>{filteredAnomalies.length} shown</span>
          </div>
          <div className="filter-row">
            <label>
              <span>Severity</span>
              <select
                value={anomalySeverityFilter}
                onChange={(event) => setAnomalySeverityFilter(event.target.value)}
              >
                <option value="all">All</option>
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
                <option value="critical">Critical</option>
              </select>
            </label>
            <label>
              <span>Service</span>
              <select
                value={anomalyServiceFilter}
                onChange={(event) => setAnomalyServiceFilter(event.target.value)}
              >
                <option value="all">All</option>
                {anomalyServiceOptions.map((serviceKey) => (
                  <option key={serviceKey} value={serviceKey}>
                    {serviceKey}
                  </option>
                ))}
              </select>
            </label>
          </div>
          <ul>
            {filteredAnomalies.slice(0, 8).map((anomaly) => (
              <li key={anomaly.id}>
                {anomaly.service_key} - {anomaly.metric_name} (score: {anomaly.score})
              </li>
            ))}
          </ul>
        </article>
      </section>
    </main>
  );
}