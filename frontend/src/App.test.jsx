import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { App } from "./App";
import * as api from "./api";

vi.mock("./api", () => ({
  login: vi.fn(),
  getDashboardSnapshot: vi.fn(),
  acknowledgeAlert: vi.fn(),
  resolveAlert: vi.fn(),
  refreshAuthToken: vi.fn()
}));

function makeSnapshot(overrides = {}) {
  return {
    summary: {
      open_alert_count: 2,
      recent_anomaly_count: 2,
      alerts_by_severity: {
        critical: 1,
        high: 1
      }
    },
    alerts: [
      { id: 1, severity: "low", status: "open", service_key: "svc-api", title: "API latency spike" },
      { id: 2, severity: "high", status: "resolved", service_key: "svc-db", title: "DB pressure" }
    ],
    anomalies: [
      { id: 10, severity: "high", service_key: "svc-api", metric_name: "cpu_percent", score: 2.4 },
      { id: 11, severity: "low", service_key: "svc-db", metric_name: "disk_percent", score: 1.2 }
    ],
    ...overrides
  };
}

describe("App", () => {
  beforeEach(() => {
    vi.clearAllMocks();

    api.login.mockResolvedValue({
      access_token: "access-token",
      refresh_token: "refresh-token",
      token_type: "bearer",
      expires_in: 900
    });
    api.getDashboardSnapshot.mockResolvedValue(makeSnapshot());
    api.acknowledgeAlert.mockResolvedValue({ status: "acknowledged" });
    api.resolveAlert.mockResolvedValue({ status: "resolved" });
    api.refreshAuthToken.mockResolvedValue({
      access_token: "new-access-token",
      refresh_token: "new-refresh-token",
      token_type: "bearer",
      expires_in: 900
    });
  });

  it("loads dashboard data after login", async () => {
    render(<App />);

    fireEvent.click(screen.getByRole("button", { name: "Load Dashboard" }));

    expect(await screen.findByText("Token loaded")).toBeInTheDocument();
    expect(await screen.findByText("Open Alerts")).toBeInTheDocument();
    expect(await screen.findByText("Recent Alerts")).toBeInTheDocument();
    expect(api.login).toHaveBeenCalledTimes(1);
    expect(api.getDashboardSnapshot).toHaveBeenCalled();
  });

  it("retries acknowledge action after access token 401", async () => {
    api.acknowledgeAlert
      .mockRejectedValueOnce(new Error("401: {\"detail\":\"Invalid access token\"}"))
      .mockResolvedValueOnce({ status: "acknowledged" });

    render(<App />);
    fireEvent.click(screen.getByRole("button", { name: "Load Dashboard" }));
    await screen.findByText("Token loaded");

    const acknowledgeButtons = screen.getAllByRole("button", { name: "Acknowledge" });
    const enabledAcknowledgeButton = acknowledgeButtons.find((button) => !button.hasAttribute("disabled"));
    expect(enabledAcknowledgeButton).toBeDefined();
    fireEvent.click(enabledAcknowledgeButton);

    expect(await screen.findByText("Recent Alerts")).toBeInTheDocument();
    expect(api.refreshAuthToken).toHaveBeenCalledWith("refresh-token");
    expect(api.acknowledgeAlert).toHaveBeenCalledTimes(2);
  });

  it("filters alerts by status", async () => {
    render(<App />);
    fireEvent.click(screen.getByRole("button", { name: "Load Dashboard" }));
    await screen.findByText("Token loaded");

    const alertsPanel = screen.getByText("Recent Alerts").closest("article");
    const statusSelect = within(alertsPanel).getAllByRole("combobox")[0];

    fireEvent.change(statusSelect, { target: { value: "resolved" } });

    expect(alertsPanel).toHaveTextContent("DB pressure");
    expect(alertsPanel).not.toHaveTextContent("API latency spike");
  });

  it("resolves an open alert and updates the alert status in the UI", async () => {
    api.getDashboardSnapshot
      .mockResolvedValueOnce(makeSnapshot())
      .mockResolvedValueOnce(
        makeSnapshot({
          alerts: [
            { id: 1, severity: "low", status: "resolved", service_key: "svc-api", title: "API latency spike" },
            { id: 2, severity: "high", status: "resolved", service_key: "svc-db", title: "DB pressure" }
          ]
        })
      );

    render(<App />);
    fireEvent.click(screen.getByRole("button", { name: "Load Dashboard" }));
    await screen.findByText("Token loaded");

    const resolveButtons = screen.getAllByRole("button", { name: "Resolve" });
    const enabledResolveButton = resolveButtons.find((button) => !button.hasAttribute("disabled"));
    expect(enabledResolveButton).toBeDefined();

    fireEvent.click(enabledResolveButton);

    expect(api.resolveAlert).toHaveBeenCalledWith("access-token", 1);
    await waitFor(() => expect(api.getDashboardSnapshot).toHaveBeenCalledTimes(2));

    const resolvedAlertItem = await screen.findByText(/API latency spike/);
    const resolvedAlertRow = resolvedAlertItem.closest("li");
    expect(within(resolvedAlertRow).getByText(/Status: resolved/i)).toBeInTheDocument();
    expect(within(resolvedAlertRow).getByRole("button", { name: "Resolve" })).toBeDisabled();
  });

  it("manual refresh requests a new snapshot and updates last updated text", async () => {
    render(<App />);
    fireEvent.click(screen.getByRole("button", { name: "Load Dashboard" }));
    await screen.findByText("Token loaded");

    const callsAfterLogin = api.getDashboardSnapshot.mock.calls.length;
    fireEvent.click(screen.getByRole("button", { name: "Refresh now" }));

    await waitFor(() => expect(api.getDashboardSnapshot.mock.calls.length).toBeGreaterThan(callsAfterLogin));
    expect(screen.getByText(/Last update:/)).toBeInTheDocument();
  });

  it("updates the dashboard display when a refreshed snapshot contains new ingestion data", async () => {
    api.getDashboardSnapshot
      .mockResolvedValueOnce(
        makeSnapshot({
          summary: {
            open_alert_count: 0,
            recent_anomaly_count: 0,
            alerts_by_severity: {}
          },
          alerts: [],
          anomalies: []
        })
      )
      .mockResolvedValueOnce(
        makeSnapshot({
          summary: {
            open_alert_count: 3,
            recent_anomaly_count: 1,
            alerts_by_severity: { high: 2, critical: 1 }
          },
          alerts: [
            {
              id: 3,
              severity: "high",
              status: "open",
              service_key: "svc-api",
              title: "New ingestion alert"
            }
          ],
          anomalies: [
            {
              id: 12,
              severity: "medium",
              service_key: "svc-api",
              metric_name: "memory_percent",
              score: 2.1
            }
          ]
        })
      );

    render(<App />);
    fireEvent.click(screen.getByRole("button", { name: "Load Dashboard" }));
    await screen.findByText("Token loaded");

    const openAlertsCard = screen.getByText("Open Alerts").closest("article");
    expect(within(openAlertsCard).getByText("0")).toBeInTheDocument();
    expect(screen.queryByText("New ingestion alert")).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Refresh now" }));
    await waitFor(() => expect(within(openAlertsCard).getByText("3")).toBeInTheDocument());

    expect(screen.getByText(/New ingestion alert/i)).toBeInTheDocument();
    expect(screen.getByText(/Last update:/)).toBeInTheDocument();
  });

  it("auto-refresh schedules polling with the selected refresh interval", async () => {
    const intervalSpy = vi.spyOn(window, "setInterval");

    render(<App />);
    fireEvent.click(screen.getByRole("button", { name: "Load Dashboard" }));
    await screen.findByText("Token loaded");

    expect(intervalSpy).toHaveBeenCalled();
    expect(intervalSpy.mock.calls.some((call) => call[1] === 15000)).toBe(true);

    intervalSpy.mockRestore();
  });

  it("clears the auto-refresh interval when auto-refresh is disabled", async () => {
    const intervalSpy = vi.spyOn(window, "setInterval");
    const clearSpy = vi.spyOn(window, "clearInterval");

    render(<App />);
    fireEvent.click(screen.getByRole("button", { name: "Load Dashboard" }));
    await screen.findByText("Token loaded");

    const checkbox = screen.getByRole("checkbox", { name: /Auto-refresh/i });
    fireEvent.click(checkbox);

    expect(clearSpy).toHaveBeenCalled();

    intervalSpy.mockRestore();
    clearSpy.mockRestore();
  });
});
