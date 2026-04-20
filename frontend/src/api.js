const baseUrl = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

function buildApiError(response, text) {
  const requestId = response.headers.get("x-request-id") ?? "";

  let detail = text;
  try {
    const parsed = JSON.parse(text);
    if (parsed && typeof parsed === "object" && typeof parsed.detail === "string") {
      detail = parsed.detail;
    }
  } catch {
    // Keep raw text as detail when body is not JSON.
  }

  const error = new Error(`${response.status}: ${detail}`);
  error.status = response.status;
  error.detail = detail;
  error.requestId = requestId;
  return error;
}

async function parseJsonResponse(response) {
  if (!response.ok) {
    const text = await response.text();
    throw buildApiError(response, text);
  }

  return response.json();
}

async function request(path, token) {
  const response = await fetch(`${baseUrl}${path}`, {
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json"
    }
  });

  return parseJsonResponse(response);
}

export async function login(email, password) {
  const response = await fetch(`${baseUrl}/api/v1/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password })
  });

  return parseJsonResponse(response);
}

export async function refreshAuthToken(refreshToken) {
  const response = await fetch(`${baseUrl}/api/v1/auth/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: refreshToken })
  });

  return parseJsonResponse(response);
}

export async function getSummary(token) {
  return request("/api/v1/dashboard/summary", token);
}

export async function getAlerts(token) {
  return request("/api/v1/alerts", token);
}

export async function getAnomalies(token) {
  return request("/api/v1/anomalies", token);
}

export async function acknowledgeAlert(token, alertId) {
  const response = await fetch(`${baseUrl}/api/v1/alerts/${alertId}/ack`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json"
    }
  });

  return parseJsonResponse(response);
}

export async function resolveAlert(token, alertId) {
  const response = await fetch(`${baseUrl}/api/v1/alerts/${alertId}/resolve`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json"
    }
  });

  return parseJsonResponse(response);
}

export async function getDashboardSnapshot(token) {
  const [summary, alerts, anomalies] = await Promise.all([
    getSummary(token),
    getAlerts(token),
    getAnomalies(token)
  ]);

  return {
    summary,
    alerts: alerts.items,
    anomalies: anomalies.items
  };
}