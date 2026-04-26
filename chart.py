"""
chart.py - Interactive Plotly Chart Builder
TRANALYZE – Trend Analyze

Builds the main candlestick chart with overlaid indicators,
pattern markers, and optional sub-plots (RSI, MACD).
"""

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np


# ─────────────────────────────────────────────────
# Color palette (dark trading theme)
# ─────────────────────────────────────────────────

COLORS = {
    "bg":         "#0b0f15",
    "grid":       "rgba(30, 36, 48, 0.5)",
    "bull":       "#00f291",   # neon green
    "bear":       "#ff3860",   # vibrant red
    "ma20":       "#ffd600",
    "ma50":       "#00d2ff",
    "ma200":      "#ff9f43",
    "bb_upper":   "rgba(0, 210, 255, 0.5)",
    "bb_lower":   "rgba(0, 210, 255, 0.5)",
    "bb_fill":    "rgba(0, 210, 255, 0.05)",
    "rsi_line":   "#df9bff",
    "rsi_ob":     "rgba(255, 56, 96, 0.1)",
    "rsi_os":     "rgba(0, 242, 145, 0.1)",
    "macd_line":  "#40c4ff",
    "macd_signal":"#ff8f00",
    "macd_bull":  "#00f291",
    "macd_bear":  "#ff3860",
    "marker_bull":"#00f291",
    "marker_bear":"#ff3860",
    "marker_neut":"#ffd600",
    "text":       "#ffffff",
    "subtext":    "#9ca3af",
}

PATTERN_MARKER = {
    "Doji":              ("diamond",    COLORS["marker_neut"], "⬦ Doji"),
    "Hammer":            ("triangle-up", COLORS["marker_bull"], "▲ Hammer"),
    "Shooting Star":     ("triangle-down", COLORS["marker_bear"], "▼ Shoot★"),
    "Bullish Engulfing": ("star",       COLORS["marker_bull"], "★ Bull Eng"),
    "Bearish Engulfing": ("star",       COLORS["marker_bear"], "★ Bear Eng"),
}


def build_chart(
    df: pd.DataFrame,
    symbol: str,
    show_ma: bool    = True,
    show_bb: bool    = True,
    show_rsi: bool   = True,
    show_macd: bool  = True,
    patterns: dict   = None,
    advanced_patterns: dict = None,
) -> go.Figure:
    """
    Build the full interactive trading chart.

    Args:
        df:        OHLCV DataFrame with indicator columns
        symbol:    ticker symbol (for title)
        show_ma:   overlay MA lines
        show_bb:   overlay Bollinger Bands
        show_rsi:  add RSI sub-plot
        show_macd: add MACD sub-plot
        patterns:  dict of {pattern_name: bool Series}

    Returns:
        Plotly Figure object
    """
    # Determine subplot rows
    rows  = 1
    rsi_row = macd_row = None
    specs = [[{"type": "candlestick"}]]

    if show_rsi:
        rows += 1
        rsi_row = rows
        specs.append([{"type": "scatter"}])
    if show_macd:
        rows += 1
        macd_row = rows
        specs.append([{"type": "scatter"}])

    row_heights = _get_row_heights(rows)

    fig = make_subplots(
        rows=rows, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=row_heights,
        specs=specs,
    )

    # ── 1. Candlestick ───────────────────────────
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df["Open"], high=df["High"],
        low=df["Low"],  close=df["Close"],
        name="OHLC",
        increasing_line_color=COLORS["bull"],
        decreasing_line_color=COLORS["bear"],
        increasing_fillcolor=COLORS["bull"],
        decreasing_fillcolor=COLORS["bear"],
        line=dict(width=1),
    ), row=1, col=1)

    # ── 2. Bollinger Bands ───────────────────────
    if show_bb and "BB_Upper" in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index, y=df["BB_Upper"],
            name="BB Upper",
            line=dict(color=COLORS["bb_upper"], width=1, dash="dot"),
            showlegend=True,
        ), row=1, col=1)
        fig.add_trace(go.Scatter(
            x=df.index, y=df["BB_Lower"],
            name="BB Lower",
            line=dict(color=COLORS["bb_lower"], width=1, dash="dot"),
            fill="tonexty",
            fillcolor=COLORS["bb_fill"],
            showlegend=True,
        ), row=1, col=1)

    # ── 3. Moving Averages ───────────────────────
    if show_ma:
        ma_cfg = [("MA_20", "MA 20", COLORS["ma20"]),
                  ("MA_50", "MA 50", COLORS["ma50"]),
                  ("MA_200","MA 200", COLORS["ma200"])]
        for col, label, color in ma_cfg:
            if col in df.columns:
                fig.add_trace(go.Scatter(
                    x=df.index, y=df[col],
                    name=label,
                    line=dict(color=color, width=1.5),
                ), row=1, col=1)

    # ── 4. Pattern Markers ───────────────────────
    if patterns:
        for name, series in patterns.items():
            hits = series[series].index
            if hits.empty:
                continue
            cfg = PATTERN_MARKER.get(name, ("circle", "#FFFFFF", name))
            symbol_shape, color, label = cfg

            # Position markers above high or below low
            is_bearish = "Bear" in name or "Shooting" in name
            y_vals = df.loc[hits, "High"] * 1.005 if not is_bearish else df.loc[hits, "Low"] * 0.995

            fig.add_trace(go.Scatter(
                x=hits,
                y=y_vals,
                mode="markers+text",
                marker=dict(symbol=symbol_shape, size=12, color=color,
                            line=dict(width=1, color="#000")),
                text=[label] * len(hits),
                textposition="top center" if not is_bearish else "bottom center",
                textfont=dict(size=9, color=color),
                name=name,
                showlegend=True,
            ), row=1, col=1)

    # ── 5. Advanced Patterns & S/R ───────────────
    if advanced_patterns:
        # Support / Resistance Lines
        for sup in advanced_patterns.get("support", []):
            fig.add_hline(y=sup, row=1, col=1, 
                          line=dict(color=COLORS["bull"], width=1.5, dash="dash"),
                          annotation_text=f"Support ₹{sup:.2f}", 
                          annotation_position="bottom right")
        
        for res in advanced_patterns.get("resistance", []):
            fig.add_hline(y=res, row=1, col=1, 
                          line=dict(color=COLORS["bear"], width=1.5, dash="dash"),
                          annotation_text=f"Resistance ₹{res:.2f}", 
                          annotation_position="top right")

        # Shapes drawing logic removed per user request
    # ── 6. RSI Sub-plot ──────────────────────────
    if show_rsi and rsi_row and "RSI" in df.columns:
        rsi = df["RSI"].dropna()

        # Overbought / oversold shading
        fig.add_hrect(y0=65, y1=100, row=rsi_row, col=1,
                      fillcolor=COLORS["rsi_ob"], line_width=0)
        fig.add_hrect(y0=0, y1=35, row=rsi_row, col=1,
                      fillcolor=COLORS["rsi_os"], line_width=0)

        fig.add_trace(go.Scatter(
            x=rsi.index, y=rsi,
            name="RSI",
            line=dict(color=COLORS["rsi_line"], width=1.5),
        ), row=rsi_row, col=1)

        # Reference lines
        for level, dash in [(65, "dash"), (35, "dash"), (50, "dot")]:
            fig.add_hline(y=level, row=rsi_row, col=1,
                          line=dict(color=COLORS["subtext"], width=0.8, dash=dash))

        fig.update_yaxes(title_text="RSI", row=rsi_row, col=1,
                         range=[0, 100], tickfont=dict(size=10))

    # ── 6. MACD Sub-plot ─────────────────────────
    if show_macd and macd_row and "MACD" in df.columns:
        macd_df = df[["MACD", "MACD_Signal", "MACD_Hist"]].dropna()

        # Histogram bars colored by direction
        hist_colors = [COLORS["macd_bull"] if v >= 0 else COLORS["macd_bear"]
                       for v in macd_df["MACD_Hist"]]

        fig.add_trace(go.Bar(
            x=macd_df.index,
            y=macd_df["MACD_Hist"],
            name="MACD Hist",
            marker_color=hist_colors,
            opacity=0.7,
        ), row=macd_row, col=1)

        fig.add_trace(go.Scatter(
            x=macd_df.index, y=macd_df["MACD"],
            name="MACD",
            line=dict(color=COLORS["macd_line"], width=1.5),
        ), row=macd_row, col=1)

        fig.add_trace(go.Scatter(
            x=macd_df.index, y=macd_df["MACD_Signal"],
            name="Signal",
            line=dict(color=COLORS["macd_signal"], width=1.5, dash="dot"),
        ), row=macd_row, col=1)

        fig.add_hline(y=0, row=macd_row, col=1,
                      line=dict(color=COLORS["subtext"], width=0.8))
        fig.update_yaxes(title_text="MACD", row=macd_row, col=1,
                         tickfont=dict(size=10))

    # ── 7. Global Layout ─────────────────────────
    fig.update_layout(
        title=dict(
            text=f"<b>{symbol}</b>",
            font=dict(size=20, color=COLORS["text"]),
            x=0.01,
        ),
        paper_bgcolor=COLORS["bg"],
        plot_bgcolor=COLORS["bg"],
        font=dict(color=COLORS["text"], family="monospace"),
        legend=dict(
            bgcolor="rgba(13,17,23,0.85)",
            bordercolor=COLORS["grid"],
            borderwidth=1,
            font=dict(size=11),
            orientation="h",
            yanchor="bottom",
            y=1.01,
            xanchor="left",
            x=0,
        ),
        margin=dict(l=10, r=10, t=60, b=10),
        height=700 if rows == 1 else (800 if rows == 2 else 900),
        xaxis_rangeslider_visible=False,
        hovermode="x unified",
    )

    # Grid styling for all axes
    for i in range(1, rows + 1):
        fig.update_xaxes(
            row=i, col=1,
            gridcolor=COLORS["grid"],
            zerolinecolor=COLORS["grid"],
            showgrid=True,
            tickfont=dict(size=10),
            # Remove gaps for non-trading times
            rangebreaks=[
                dict(bounds=["sat", "mon"]), # hide weekends
                # dict(bounds=[16, 9.5], pattern="hour"), # hide non-trading hours (US)
            ]
        )
        fig.update_yaxes(
            row=i, col=1,
            gridcolor=COLORS["grid"],
            zerolinecolor=COLORS["grid"],
            showgrid=True,
            tickfont=dict(size=10),
            side="right",
        )

    return fig


def _get_row_heights(rows: int) -> list:
    if rows == 1:
        return [1.0]
    if rows == 2:
        return [0.65, 0.35]
def build_clean_analysis_chart(df: pd.DataFrame, symbol: str, advanced_patterns: dict) -> go.Figure:
    """Build a clean line chart specifically for pattern visualization (no RSI/MACD)."""
    fig = go.Figure()

    # 1. Main Line Chart (Clean and simple)
    fig.add_trace(go.Scatter(
        x=df.index, y=df["Close"],
        name="Price",
        line=dict(color=COLORS["bull"], width=2),
        fill='tozeroy',
        fillcolor='rgba(0, 242, 145, 0.05)' # subtle glow
    ))

    # Patterns drawing logic removed per user request

    fig.update_layout(
        title=f"<b>Pattern Recognition: {symbol}</b>",
        paper_bgcolor=COLORS["bg"],
        plot_bgcolor=COLORS["bg"],
        font=dict(color=COLORS["text"]),
        height=500,
        margin=dict(l=10, r=10, t=50, b=10),
        xaxis=dict(showgrid=False, rangebreaks=[dict(bounds=["sat", "mon"])]),
        yaxis=dict(showgrid=True, gridcolor=COLORS["grid"], side="right"),
        showlegend=True
    )
    
    return fig
