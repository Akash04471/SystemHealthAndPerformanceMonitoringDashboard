import { describe, expect, it, beforeEach, vi } from "vitest";
import * as api from "./api";

const mockJson = { items: [] };

beforeEach(() => {
  vi.restoreAllMocks();
  global.fetch = vi.fn();
});

describe("api client", () => {
  it("requests dashboard summary, alerts, and anomalies for a dashboard snapshot", async () => {
    global.fetch
      .mockResolvedValueOnce({ ok: true, json: async () => ({ open_alert_count: 1, recent_anomaly_count: 2, alerts_by_severity: {} }) })
      .mockResolvedValueOnce({ ok: true, json: async () => ({ items: [{ id: 1, title: "Alert 1" }] }) })
      .mockResolvedValueOnce({ ok: true, json: async () => ({ items: [{ id: 10, metric_name: "cpu_percent", score: 1.5 }] }) });

    const snapshot = await api.getDashboardSnapshot("test-token");

    expect(snapshot.summary.open_alert_count).toBe(1);
    expect(snapshot.alerts).toHaveLength(1);
    expect(snapshot.anomalies).toHaveLength(1);
    expect(global.fetch).toHaveBeenCalledTimes(3);
    expect(global.fetch).toHaveBeenNthCalledWith(
      1,
      "http://127.0.0.1:8000/api/v1/dashboard/summary",
      expect.objectContaining({
        headers: expect.objectContaining({ Authorization: "Bearer test-token" })
      })
    );
    expect(global.fetch).toHaveBeenNthCalledWith(
      2,
      "http://127.0.0.1:8000/api/v1/alerts",
      expect.objectContaining({ headers: expect.objectContaining({ Authorization: "Bearer test-token" }) })
    );
    expect(global.fetch).toHaveBeenNthCalledWith(
      3,
      "http://127.0.0.1:8000/api/v1/anomalies",
      expect.objectContaining({ headers: expect.objectContaining({ Authorization: "Bearer test-token" }) })
    );
  });
});
