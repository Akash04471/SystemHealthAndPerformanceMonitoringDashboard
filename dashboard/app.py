from datetime import datetime
import os

import mysql.connector
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components


def _require_env(name: str) -> str:
        value = os.getenv(name)
        if not value:
                raise RuntimeError(f"Missing required environment variable: {name}")
        return value


def _db_config() -> dict:
        return {
                "host": os.getenv("DB_HOST", "127.0.0.1"),
                "user": _require_env("DB_USER"),
                "password": _require_env("DB_PASSWORD"),
                "database": os.getenv("DB_NAME", "system_monitoring"),
                "port": int(os.getenv("DB_PORT", "3306")),
        }

st.set_page_config(page_title="System Health Dashboard", layout="wide")

st.markdown(
        """
        <style>
            @import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@300;400;500&family=Syne:wght@600;700;800&family=Instrument+Sans:wght@400;500&display=swap');

            :root {
                --bg-base: #0D0F0F;
                --bg-surface: #141718;
                --bg-elevated: #1C2022;
                --border-subtle: #252C2E;
                --border-active: #3A4548;

                --accent-amber: #C8860A;
                --accent-ember: #E05C1A;
                --accent-steel: #4A8FA8;
                --accent-sage: #4A8C6A;
                --accent-stone: #8A9EA6;

                --text-primary: #E8EEF0;
                --text-secondary: #8A9EA6;
                --text-dim: #4A5C62;

                --glow-amber: rgba(200, 134, 10, 0.15);
                --glow-ember: rgba(224, 92, 26, 0.12);
            }

            #MainMenu {visibility: hidden;}
            header[data-testid="stHeader"] {background: transparent;}
            .stDeployButton {display: none;}

            .stApp {
                background: radial-gradient(circle at 25% 0%, #14191A 0%, var(--bg-base) 45%, #090B0B 100%);
                color: var(--text-primary);
            }

            .block-container {
                max-width: 1280px;
                padding-top: 0.7rem;
                padding-bottom: 1.5rem;
                                padding-left: 0.9rem;
                                padding-right: 0.9rem;
            }

            .cc-header {
                border: 1px solid var(--border-subtle);
                border-left: 0;
                border-right: 0;
                border-top: 0;
                margin-bottom: 16px;
                padding: 14px 0 16px 0;
                background-image: repeating-linear-gradient(
                    0deg,
                    transparent,
                    transparent 2px,
                    rgba(255,255,255,0.015) 2px,
                    rgba(255,255,255,0.015) 4px
                );
            }

            .cc-header-inner {
                display: flex;
                justify-content: space-between;
                align-items: center;
                gap: 16px;
            }

            .cc-title {
                font-family: 'Syne', sans-serif;
                font-weight: 800;
                font-size: 2.4rem;
                letter-spacing: -0.02em;
                color: var(--text-primary);
                line-height: 1;
            }

            .cc-subtitle {
                font-family: 'Instrument Sans', sans-serif;
                font-size: 0.85rem;
                letter-spacing: 0.1em;
                text-transform: uppercase;
                color: var(--text-secondary);
            }

            .cc-meta {
                text-align: right;
                font-family: 'DM Mono', monospace;
                color: var(--text-secondary);
                font-size: 0.78rem;
            }

            .cc-clock {
                font-family: 'DM Mono', monospace;
                color: var(--text-primary);
                font-size: 1rem;
            }

            .panel,
            .kpi-card,
            .section-card,
            .alert-feed {
                background: var(--bg-surface);
                border: 1px solid var(--border-subtle);
                border-radius: 4px;
                transition: all 0.2s ease;
                                width: 100%;
                                box-sizing: border-box;
            }

            .panel {
                                padding: 24px 28px;
            }

            .sidebar-panel {
                background: #0D0F0F;
                border-right: 1px solid rgba(200, 134, 10, 0.3);
                min-height: 100%;
            }

            .section-header {
                font-family: 'Syne', sans-serif;
                font-weight: 700;
                font-size: 0.9rem;
                text-transform: uppercase;
                letter-spacing: 0.08em;
                color: var(--text-primary);
                margin-bottom: 10px;
            }

            .subtle-meta {
                font-family: 'DM Mono', monospace;
                font-weight: 300;
                color: var(--text-dim);
                font-size: 0.72rem;
            }

            .kpi-wrap {
                display: grid;
                grid-template-columns: repeat(3, minmax(0, 1fr));
                gap: 16px;
                margin-bottom: 16px;
            }

            .kpi-card {
                padding: 16px 16px 10px 16px;
                position: relative;
                overflow: hidden;
                                min-height: 230px;
            }

                        .kpi-shell {
                                background: var(--bg-surface);
                                border: 1px solid var(--border-subtle);
                                border-radius: 4px;
                                padding: 10px;
                                transition: all 0.2s ease;
                        }

                        .kpi-shell:hover {
                                background: var(--bg-elevated);
                                border-color: var(--border-active);
                                box-shadow: 0 0 24px var(--glow-amber);
                        }

                        .card-shell {
                                background: var(--bg-surface);
                                border: 1px solid var(--border-subtle);
                                border-radius: 4px;
                                padding: 12px;
                        }

            .kpi-card:hover {
                background: var(--bg-elevated);
                border-color: var(--border-active);
                box-shadow: 0 0 24px var(--glow-amber);
            }

            .kpi-card::before {
                content: "";
                position: absolute;
                left: 0;
                top: 0;
                width: 100%;
                height: 1px;
                                background: var(--kpi-top, var(--accent-amber));
            }

            .kpi-label {
                font-family: 'Instrument Sans', sans-serif;
                font-size: 0.7rem;
                text-transform: uppercase;
                letter-spacing: 0.12em;
                color: var(--text-secondary);
            }

            .kpi-divider {
                border-right: 1px solid var(--border-subtle);
            }

            .status-badge {
                display: inline-flex;
                align-items: center;
                gap: 6px;
                border: 1px solid var(--border-subtle);
                border-radius: 999px;
                padding: 2px 8px;
                margin-top: 6px;
                font-family: 'Instrument Sans', sans-serif;
                font-size: 0.7rem;
                letter-spacing: 0.08em;
                text-transform: uppercase;
            }

            .status-dot {
                width: 8px;
                height: 8px;
                border-radius: 50%;
            }

            .status-nominal .status-dot { background: var(--accent-sage); }
            .status-warning .status-dot { background: var(--accent-amber); }
            .status-critical .status-dot { background: var(--accent-ember); box-shadow: 0 0 8px var(--glow-ember); }

            .alerts-header {
                display: flex;
                align-items: center;
                justify-content: space-between;
                margin-bottom: 8px;
            }

            .count-badge {
                background: var(--bg-elevated);
                color: var(--accent-amber);
                border: 1px solid var(--border-active);
                border-radius: 999px;
                font-family: 'DM Mono', monospace;
                font-size: 0.72rem;
                padding: 2px 8px;
            }

            .alert-feed {
                padding: 8px;
            }

            .alert-row {
                display: grid;
                                grid-template-columns: 18px minmax(90px, 140px) minmax(80px, 1fr) minmax(70px, 90px) minmax(100px, 110px);
                align-items: center;
                gap: 10px;
                border: 1px solid var(--border-subtle);
                border-left-width: 3px;
                border-radius: 4px;
                background: rgba(28, 32, 34, 0.35);
                padding: 8px 10px;
                margin-bottom: 8px;
                animation: slideInLeft 0.3s ease both;
                                overflow-wrap: anywhere;
            }

            .alert-dot {
                width: 9px;
                height: 9px;
                border-radius: 50%;
                margin-left: 3px;
            }

            .sev-critical { color: var(--accent-ember); border-left-color: var(--accent-ember); }
            .sev-warning { color: var(--accent-amber); border-left-color: var(--accent-amber); }
            .sev-ok { color: var(--accent-sage); border-left-color: var(--accent-sage); }

            .sev-critical .alert-dot {
                background: var(--accent-ember);
                animation: pulse 1.2s ease-in-out infinite;
            }

            .sev-warning .alert-dot { background: var(--accent-amber); }
            .sev-ok .alert-dot { background: var(--accent-sage); }

            .alert-time {
                font-family: 'DM Mono', monospace;
                font-size: 0.72rem;
                color: var(--text-secondary);
            }

            .alert-metric,
            .alert-value {
                font-family: 'DM Mono', monospace;
                font-size: 0.8rem;
            }

            .alert-badge {
                border: 1px solid currentColor;
                border-radius: 999px;
                padding: 2px 7px;
                font-family: 'Instrument Sans', sans-serif;
                font-size: 0.68rem;
                text-transform: uppercase;
                letter-spacing: 0.08em;
                width: fit-content;
            }

                        .stPlotlyChart,
                        .stDataFrame,
                        div[data-testid="stElementContainer"] {
                                width: 100%;
                        }

                        div[data-testid="stHorizontalBlock"] {
                                gap: 16px;
                                align-items: stretch;
                        }

                        div[data-testid="column"] > div {
                                min-width: 0;
                        }

            .nominal-state {
                border: 1px dashed var(--accent-sage);
                color: var(--accent-sage);
                border-radius: 4px;
                padding: 12px;
                text-align: center;
                font-family: 'DM Mono', monospace;
            }

            .main-section,
            .analytics-row {
                animation: fadeSlideUp 0.45s ease both;
            }

            .kpi-card:nth-child(1) { animation: fadeSlideUp 0.4s ease 0.1s both; }
            .kpi-card:nth-child(2) { animation: fadeSlideUp 0.4s ease 0.2s both; }
            .kpi-card:nth-child(3) { animation: fadeSlideUp 0.4s ease 0.3s both; }

            @keyframes fadeSlideUp {
                from { opacity: 0; transform: translateY(12px); }
                to { opacity: 1; transform: translateY(0); }
            }

            @keyframes slideInLeft {
                from { opacity: 0; transform: translateX(-10px); }
                to { opacity: 1; transform: translateX(0); }
            }

            @keyframes pulse {
                0%, 100% { opacity: 1; transform: scale(1); }
                50% { opacity: 0.4; transform: scale(1.4); }
            }

            .stSlider > div[data-baseweb="slider"] div {
                font-family: 'DM Mono', monospace !important;
            }

            .stSlider [role="slider"] {
                background: var(--accent-amber) !important;
            }

            .stCheckbox {
                padding: 4px 8px;
                border: 1px solid var(--border-subtle);
                border-radius: 999px;
                background: rgba(200, 134, 10, 0.05);
                margin-bottom: 8px;
            }

            .stCheckbox:has(input:checked) {
                border-color: var(--accent-amber);
                background: rgba(200, 134, 10, 0.12);
            }

            .stDataFrame {
                border: 1px solid var(--border-subtle);
                border-radius: 4px;
            }

                        @media (max-width: 1280px) {
                                .cc-title {
                                        font-size: 2rem;
                                }

                                .cc-header-inner {
                                        gap: 10px;
                                }

                                .panel {
                                        padding: 20px 20px;
                                }
                        }

                        @media (max-width: 1100px) {
                                .cc-header-inner {
                                        flex-direction: column;
                                        align-items: flex-start;
                                }

                                .cc-meta {
                                        text-align: left;
                                }

                                .kpi-card {
                                        min-height: 205px;
                                }

                                .alert-row {
                                        grid-template-columns: 14px 90px 1fr;
                                        row-gap: 6px;
                                }

                                .alert-row .alert-value,
                                .alert-row .alert-badge {
                                        grid-column: 2 / 4;
                                }
                        }

                        @media (max-width: 980px) {
                                div[data-testid="stHorizontalBlock"] {
                                        flex-direction: column;
                                        gap: 14px;
                                }

                                div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {
                                        width: 100% !important;
                                        flex: 1 1 100% !important;
                                }

                                .sidebar-panel {
                                        border-right: 0;
                                        border-bottom: 1px solid rgba(200, 134, 10, 0.3);
                                }

                                .cc-title {
                                        font-size: 1.6rem;
                                }

                                .kpi-label {
                                        font-size: 0.65rem;
                                }
                        }

                        @media (max-width: 720px) {
                                .block-container {
                                        padding-left: 0.55rem;
                                        padding-right: 0.55rem;
                                }

                                .panel,
                                .section-card,
                                .kpi-card,
                                .alert-feed {
                                        padding-left: 12px !important;
                                        padding-right: 12px !important;
                                }

                                .cc-subtitle {
                                        font-size: 0.72rem;
                                }

                                .alerts-header {
                                        gap: 8px;
                                }

                                .alert-time,
                                .alert-metric,
                                .alert-value,
                                .alert-badge {
                                        font-size: 0.7rem;
                                }
                        }
        </style>
        """,
        unsafe_allow_html=True,
)


@st.cache_data(ttl=20)
def load_metrics() -> pd.DataFrame:
        conn = mysql.connector.connect(**_db_config())
        data = pd.read_sql("SELECT * FROM system_metrics", conn)
        conn.close()
        data["timestamp"] = pd.to_datetime(data["timestamp"])
        return data.sort_values("timestamp")


def metric_status(metric_name: str, value: float) -> tuple[str, str]:
        if metric_name == "cpu_percent":
                if value >= 90:
                        return "CRITICAL", "status-critical"
                if value >= 80:
                        return "WARNING", "status-warning"
        elif metric_name == "memory_percent":
                if value >= 95:
                        return "CRITICAL", "status-critical"
                if value >= 85:
                        return "WARNING", "status-warning"
        else:
                if value >= 90:
                        return "CRITICAL", "status-critical"
                if value >= 75:
                        return "WARNING", "status-warning"
        return "NOMINAL", "status-nominal"


@st.cache_data(ttl=20)
def build_sparkline(points: list[float], color: str) -> go.Figure:
        fig = go.Figure()
        fig.add_trace(
                go.Scatter(
                        y=points,
                        mode="lines",
                        line=dict(color=color, width=1.4),
                        fill="tozeroy",
                        fillcolor=rgba_from_hex(color, 0.14),
                        hoverinfo="skip",
                        showlegend=False,
                )
        )
        fig.update_layout(
                paper_bgcolor="#141718",
                plot_bgcolor="#141718",
                margin=dict(l=0, r=0, t=0, b=0),
                height=64,
        )
        fig.update_xaxes(visible=False)
        fig.update_yaxes(visible=False)
        return fig


def rgba_from_hex(hex_color: str, alpha: float) -> str:
        h = hex_color.lstrip("#")
        return f"rgba({int(h[0:2], 16)}, {int(h[2:4], 16)}, {int(h[4:6], 16)}, {alpha})"


@st.cache_data(ttl=20)
def build_main_chart(data: pd.DataFrame, metric_cols: tuple[str, ...]) -> tuple[go.Figure, pd.DataFrame]:
        fig = go.Figure()
        colors = {
                "cpu_percent": "#C8860A",
                "memory_percent": "#4A8FA8",
                "disk_percent": "#4A8C6A",
        }

        for col in metric_cols:
                fig.add_trace(
                        go.Scatter(
                                x=data["timestamp"],
                                y=data[col],
                                mode="lines",
                                name=col.replace("_percent", "").upper(),
                                line=dict(color=colors[col], width=1.5, dash="solid"),
                                fill="tozeroy",
                                fillcolor=rgba_from_hex(colors[col], 0.06),
                                hovertemplate="<b>%{x}</b><br>%{y:.1f}%<extra></extra>",
                        )
                )

        if "cpu_percent" in metric_cols:
                fig.add_hline(
                        y=80,
                        line=dict(color="#E05C1A", width=1.2, dash="dash"),
                        annotation_text="THRESHOLD",
                        annotation_position="top right",
                        annotation_font_color="#E05C1A",
                )
        if "memory_percent" in metric_cols:
                fig.add_hline(
                        y=90,
                        line=dict(color="#4A8FA8", width=1.2, dash="dash"),
                )

        anomaly_df = pd.DataFrame(columns=["timestamp", "cpu_percent", "sigma"])
        if "cpu_percent" in metric_cols and len(data) > 3:
                mean_cpu = data["cpu_percent"].mean()
                std_cpu = data["cpu_percent"].std(ddof=0)
                if std_cpu > 0:
                        anomaly_mask = data["cpu_percent"] > (mean_cpu + 2 * std_cpu)
                        anomaly_df = data.loc[anomaly_mask, ["timestamp", "cpu_percent"]].copy()
                        anomaly_df["sigma"] = (anomaly_df["cpu_percent"] - mean_cpu) / std_cpu

                        if not anomaly_df.empty:
                                fig.add_trace(
                                        go.Scatter(
                                                x=anomaly_df["timestamp"],
                                                y=anomaly_df["cpu_percent"],
                                                mode="markers",
                                                marker=dict(color="#E05C1A", size=6),
                                                name="ANOMALY",
                                                hovertemplate="ANOMALY DETECTED - +%{customdata:.2f}σ above baseline<extra></extra>",
                                                customdata=anomaly_df["sigma"],
                                        )
                                )

                                for x_value in anomaly_df["timestamp"]:
                                        fig.add_vline(
                                                x=x_value,
                                                line_width=1,
                                                line_dash="dash",
                                                line_color=rgba_from_hex("#E05C1A", 0.6),
                                        )

        fig.update_layout(
                title="SYSTEM RESOURCE TELEMETRY",
                paper_bgcolor="#141718",
                plot_bgcolor="#141718",
                font_family="DM Mono",
                font_color="#8A9EA6",
                margin=dict(l=16, r=16, t=36, b=36),
                hoverlabel=dict(bgcolor="#1C2022", bordercolor="#3A4548", font_color="#E8EEF0"),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        )
        fig.update_xaxes(
                gridcolor="#252C2E",
                gridwidth=0.5,
                zeroline=False,
                rangeslider=dict(visible=True),
                showline=True,
                linecolor="#252C2E",
                tickfont=dict(family="DM Mono", size=11, color="#8A9EA6"),
        )
        fig.update_yaxes(
                title="Usage (%)",
                gridcolor="#252C2E",
                gridwidth=0.5,
                zeroline=False,
                showline=True,
                linecolor="#252C2E",
                tickfont=dict(family="DM Mono", size=11, color="#8A9EA6"),
                title_font=dict(family="DM Mono", size=11, color="#8A9EA6"),
        )
        return fig, anomaly_df


@st.cache_data(ttl=20)
def build_memory_gauge(memory_value: float) -> go.Figure:
        fig = go.Figure(
                go.Indicator(
                        mode="gauge+number",
                        value=float(memory_value),
                        number={"suffix": "%", "font": {"family": "DM Mono", "size": 34, "color": "#E8EEF0"}},
                        title={"text": "MEM", "font": {"family": "DM Mono", "size": 14, "color": "#8A9EA6"}},
                        gauge={
                                "axis": {"range": [0, 100], "tickwidth": 0, "tickcolor": "#8A9EA6"},
                                "bar": {"color": "#141718", "thickness": 0.35},
                                "bgcolor": "#141718",
                                "borderwidth": 1,
                                "bordercolor": "#252C2E",
                                "steps": [
                                        {"range": [0, 70], "color": "#4A8C6A"},
                                        {"range": [70, 90], "color": "#C8860A"},
                                        {"range": [90, 100], "color": "#E05C1A"},
                                ],
                        },
                )
        )
        fig.update_layout(
                paper_bgcolor="#141718",
                plot_bgcolor="#141718",
                margin=dict(l=18, r=18, t=28, b=24),
                height=280,
                font_family="DM Mono",
        )
        return fig


def render_countup_value(dom_id: str, end_value: float, text_color: str) -> None:
        components.html(
                f"""
                <div style="font-family:'DM Mono',monospace;font-weight:500;font-size:3rem;color:{text_color};font-variant-numeric:tabular-nums;line-height:1.05;transition:color 0.3s ease;">
                        <span id="{dom_id}">0.00</span><span style="font-size:1.4rem;color:#8A9EA6;">%</span>
                </div>
                <script>
                    function animateValue(id, start, end, duration) {{
                        let startTime = null;
                        const element = document.getElementById(id);
                        function step(timestamp) {{
                            if (!startTime) startTime = timestamp;
                            const progress = Math.min((timestamp - startTime) / duration, 1);
                            element.textContent = (progress * (end - start) + start).toFixed(2);
                            if (progress < 1) window.requestAnimationFrame(step);
                        }}
                        window.requestAnimationFrame(step);
                    }}
                    animateValue('{dom_id}', 0, {end_value:.4f}, 900);
                </script>
                """,
                height=72,
        )


df = load_metrics()
if df.empty:
        st.warning("No metrics available yet.")
        st.stop()

left_col, right_col = st.columns([1, 3], gap="medium")

with left_col:
        st.markdown('<div class="panel sidebar-panel">', unsafe_allow_html=True)
        st.markdown('<div class="section-header">Filter Panel</div>', unsafe_allow_html=True)
        records = st.slider("Number of recent records", 20, 500, 120, 10)
        auto_refresh = st.toggle("AUTO REFRESH")
        refresh_interval = st.selectbox("Interval", ["30s"], index=0)

        st.markdown('<div class="section-header" style="margin-top:16px;">Metric Channels</div>', unsafe_allow_html=True)
        show_cpu = st.checkbox("CPU", value=True)
        show_memory = st.checkbox("Memory", value=True)
        show_disk = st.checkbox("Disk", value=True)

        st.markdown(
                f'<div class="subtle-meta" style="margin-top:14px;">LAST REFRESHED  {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</div>',
                unsafe_allow_html=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)

if auto_refresh and refresh_interval == "30s":
        components.html(
                """
                <script>
                    setTimeout(function () {
                        window.parent.location.reload();
                    }, 30000);
                </script>
                """,
                height=0,
        )

df = df.tail(records).copy()

selected_metrics: list[str] = []
if show_cpu:
        selected_metrics.append("cpu_percent")
if show_memory:
        selected_metrics.append("memory_percent")
if show_disk:
        selected_metrics.append("disk_percent")

if not selected_metrics:
        selected_metrics = ["cpu_percent", "memory_percent", "disk_percent"]

cpu_avg = float(df["cpu_percent"].mean())
mem_avg = float(df["memory_percent"].mean())
disk_avg = float(df["disk_percent"].mean())

cpu_status, cpu_status_cls = metric_status("cpu_percent", cpu_avg)
mem_status, mem_status_cls = metric_status("memory_percent", mem_avg)
disk_status, disk_status_cls = metric_status("disk_percent", disk_avg)

uptime = df["timestamp"].max() - df["timestamp"].min()
uptime_label = f"UPTIME WINDOW {str(uptime).split('.')[0]}"

with right_col:
        st.markdown(
                f"""
                <div class="cc-header">
                    <div class="cc-header-inner">
                        <div>
                            <div class="cc-title">⌁ SYSTEM HEALTH</div>
                            <div class="cc-subtitle">PERFORMANCE MONITOR</div>
                        </div>
                        <div class="cc-meta">
                            <div id="live-clock" class="cc-clock">--:--:--</div>
                            <div>{uptime_label}</div>
                        </div>
                    </div>
                </div>
                <script>
                    function updateClock() {{
                        const e = document.getElementById('live-clock');
                        if (!e) return;
                        const now = new Date();
                        e.innerText = now.toLocaleTimeString();
                    }}
                    updateClock();
                    setInterval(updateClock, 1000);
                </script>
                """,
                unsafe_allow_html=True,
        )

        st.markdown('<div class="main-section">', unsafe_allow_html=True)
        kpi_cols = st.columns(3, gap="medium")

        with kpi_cols[0]:
                st.markdown('<div class="kpi-shell">', unsafe_allow_html=True)
                st.markdown('<div class="kpi-card kpi-divider" style="--kpi-top:#C8860A;"><div class="kpi-label">CPU UTILIZATION</div></div>', unsafe_allow_html=True)
                render_countup_value("cpu-kpi", cpu_avg, "#E8EEF0" if cpu_avg < 80 else "#E05C1A")
                st.plotly_chart(build_sparkline(df["cpu_percent"].tail(20).tolist(), "#C8860A"), use_container_width=True, config={"displayModeBar": False})
                st.markdown(
                        f'<div class="status-badge {cpu_status_cls}"><span class="status-dot"></span>{cpu_status}</div>',
                        unsafe_allow_html=True,
                )
                st.markdown("</div>", unsafe_allow_html=True)

        with kpi_cols[1]:
                st.markdown('<div class="kpi-shell">', unsafe_allow_html=True)
                st.markdown('<div class="kpi-card kpi-divider" style="--kpi-top:#4A8FA8;"><div class="kpi-label">MEMORY UTILIZATION</div></div>', unsafe_allow_html=True)
                render_countup_value("mem-kpi", mem_avg, "#E8EEF0" if mem_avg < 90 else "#E05C1A")
                st.plotly_chart(build_sparkline(df["memory_percent"].tail(20).tolist(), "#4A8FA8"), use_container_width=True, config={"displayModeBar": False})
                st.markdown(
                        f'<div class="status-badge {mem_status_cls}"><span class="status-dot"></span>{mem_status}</div>',
                        unsafe_allow_html=True,
                )
                st.markdown("</div>", unsafe_allow_html=True)

        with kpi_cols[2]:
                st.markdown('<div class="kpi-shell">', unsafe_allow_html=True)
                st.markdown('<div class="kpi-card" style="--kpi-top:#4A8C6A;"><div class="kpi-label">DISK UTILIZATION</div></div>', unsafe_allow_html=True)
                render_countup_value("disk-kpi", disk_avg, "#E8EEF0" if disk_avg < 75 else "#E05C1A")
                st.plotly_chart(build_sparkline(df["disk_percent"].tail(20).tolist(), "#4A8C6A"), use_container_width=True, config={"displayModeBar": False})
                st.markdown(
                        f'<div class="status-badge {disk_status_cls}"><span class="status-dot"></span>{disk_status}</div>',
                        unsafe_allow_html=True,
                )
                st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

        fig_main, anomaly_df = build_main_chart(df, tuple(selected_metrics))
        st.plotly_chart(fig_main, use_container_width=True)

        alert_entries = []
        for _, row in df.tail(200).iterrows():
                checks = [
                        ("CPU", float(row["cpu_percent"]), 80, 90),
                        ("MEM", float(row["memory_percent"]), 85, 95),
                        ("DISK", float(row["disk_percent"]), 70, 90),
                ]
                for name, value, warn, crit in checks:
                        if value >= crit:
                                alert_entries.append(("CRITICAL", row["timestamp"], name, value, f">= {crit}%"))
                        elif value >= warn:
                                alert_entries.append(("WARNING", row["timestamp"], name, value, f">= {warn}%"))

        alert_count = len(alert_entries)
        st.markdown(
                f"""
                <div class="alerts-header">
                    <div class="section-header" style="margin-bottom:0;">Alerts</div>
                    <div class="count-badge">{alert_count}</div>
                </div>
                """,
                unsafe_allow_html=True,
        )

        if alert_entries:
                st.markdown('<div class="alert-feed">', unsafe_allow_html=True)
                recent_alerts = alert_entries[-12:]
                for i, (sev, ts, metric_name, val, cond) in enumerate(recent_alerts):
                        sev_cls = "sev-critical" if sev == "CRITICAL" else "sev-warning"
                        delay = i * 0.05
                        st.markdown(
                                f"""
                                <div class="alert-row {sev_cls}" style="animation-delay:{delay:.2f}s;">
                                    <span class="alert-dot"></span>
                                    <span class="alert-time">{pd.to_datetime(ts).strftime('%H:%M:%S')}</span>
                                    <span class="alert-metric">{metric_name}_PERCENT</span>
                                    <span class="alert-value">{val:.1f}%</span>
                                    <span class="alert-badge">{sev} {cond}</span>
                                </div>
                                """,
                                unsafe_allow_html=True,
                        )
                st.markdown("</div>", unsafe_allow_html=True)
        else:
                st.markdown('<div class="nominal-state">✓ ALL SYSTEMS NOMINAL</div>', unsafe_allow_html=True)

        st.markdown('<div class="analytics-row" style="margin-top:16px;">', unsafe_allow_html=True)
        a_col, b_col, c_col = st.columns(3, gap="medium")

        with a_col:
                st.markdown('<div class="card-shell"><div class="section-header">Utilization Gauge</div>', unsafe_allow_html=True)
                st.plotly_chart(build_memory_gauge(mem_avg), use_container_width=True, config={"displayModeBar": False})
                st.markdown("</div>", unsafe_allow_html=True)

        with b_col:
                st.markdown('<div class="card-shell"><div class="section-header">Rolling Statistics</div>', unsafe_allow_html=True)
                stats_df = df[["cpu_percent", "memory_percent", "disk_percent"]].describe().round(2)

                def style_stats(frame: pd.DataFrame):
                        styled = frame.style
                        styled = styled.set_properties(**{"background-color": "#141718", "color": "#E8EEF0", "border-color": "#252C2E"})
                        if "max" in frame.index:
                                styled = styled.apply(lambda x: ["background-color: rgba(200,134,10,0.18); color: #E8EEF0;"] * len(x) if x.name == "max" else [""] * len(x), axis=1)
                        if "min" in frame.index:
                                styled = styled.apply(lambda x: ["background-color: rgba(74,140,106,0.18); color: #E8EEF0;"] * len(x) if x.name == "min" else [""] * len(x), axis=1)
                        return styled

                st.dataframe(style_stats(stats_df), use_container_width=True, height=280)
                st.markdown("</div>", unsafe_allow_html=True)

        with c_col:
                st.markdown('<div class="card-shell"><div class="section-header">Anomaly Marker</div>', unsafe_allow_html=True)
                if anomaly_df.empty:
                        st.markdown('<div class="nominal-state">✓ NO CPU ANOMALIES ABOVE +2σ</div>', unsafe_allow_html=True)
                else:
                        preview = anomaly_df.tail(6).copy()
                        preview["timestamp"] = preview["timestamp"].dt.strftime("%H:%M:%S")
                        preview["message"] = preview["sigma"].apply(lambda x: f"ANOMALY DETECTED - +{x:.2f}σ")
                        st.dataframe(
                                preview[["timestamp", "cpu_percent", "message"]].rename(
                                        columns={"timestamp": "TIME", "cpu_percent": "CPU %", "message": "EVENT"}
                                ),
                                use_container_width=True,
                                height=280,
                        )
                st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)
