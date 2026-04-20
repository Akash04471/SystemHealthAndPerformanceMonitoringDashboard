import { fireEvent, render, screen, within } from "@testing-library/react";
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
});
