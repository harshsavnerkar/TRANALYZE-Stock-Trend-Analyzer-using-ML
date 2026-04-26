"""
app.py - Main Streamlit UI
TRANALYZE – Trend Analyze

Professional trading analysis dashboard for educational purposes.
Supports NSE, BSE, US Stocks, Forex, and Crypto markets.
"""

import streamlit as st
import pandas as pd
import json
from datetime import datetime

# ── Module imports ──────────────────────────────
from utils import (
    MARKET_CONFIG, TIMEFRAME_MAP, RANGE_MAP,
    convert_symbol, get_valid_ranges, get_all_symbols,
    format_large_number, format_price, pct_change,
)
from data import fetch_data, fetch_ticker_info, get_summary_metrics
from indicators import apply_all_indicators
from patterns import detect_all_patterns, get_pattern_summary
from signals import generate_signal
from model import train_and_predict
from chart import build_chart, build_clean_analysis_chart
from advanced_patterns import get_expert_analysis
from backtest import run_ma_crossover_backtest
from streamlit_autorefresh import st_autorefresh


# ─────────────────────────────────────────────────
# Page config
# ─────────────────────────────────────────────────

st.set_page_config(
    page_title="TRANALYZE – Trend Analyze",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────
# Custom CSS – dark trading terminal aesthetic
# ─────────────────────────────────────────────────

st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=Outfit:wght@300;400;600;700&display=swap');

  /* ── Global ───────────────────── */
  html, body, [class*="css"] {
    background-color: #0b0f15 !important;
    color: #cbd5e1 !important;
    font-family: 'Outfit', sans-serif !important;
  }

  /* ── Sidebar Glassmorphism ────── */
  section[data-testid="stSidebar"] {
    background: rgba(15, 23, 42, 0.95) !important;
    backdrop-filter: blur(10px);
    border-right: 1px solid rgba(255, 255, 255, 0.05);
  }
  section[data-testid="stSidebar"] .stSelectbox label,
  section[data-testid="stSidebar"] .stTextInput label,
  section[data-testid="stSidebar"] .stSlider label,
  section[data-testid="stSidebar"] .stCheckbox label {
    color: #94a3b8 !important;
    font-size: 11px !important;
    font-weight: 600;
    letter-spacing: 0.05em;
    text-transform: uppercase;
  }

  /* ── Header ───────────────────── */
  .tranalyze-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 10px 0 20px 0;
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    margin-bottom: 24px;
  }
  .tranalyze-logo {
    font-family: 'Syne', sans-serif;
    font-size: 32px;
    font-weight: 800;
    background: linear-gradient(135deg, #00f291 0%, #00d2ff 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    letter-spacing: -1px;
  }

  /* ── Card Overhaul ────────────── */
  div[data-testid="stMetric"] {
    background: rgba(30, 41, 59, 0.4) !important;
    border: 1px solid rgba(255, 255, 255, 0.03) !important;
    border-radius: 12px !important;
    padding: 16px !important;
    transition: transform 0.2s ease, background 0.2s ease;
  }
  div[data-testid="stMetric"]:hover {
    transform: translateY(-2px);
    background: rgba(30, 41, 59, 0.6) !important;
    border-color: rgba(0, 242, 145, 0.2) !important;
  }

  /* ── Signal Badge ─────────────── */
  .signal-badge {
    display: inline-block;
    padding: 8px 24px;
    border-radius: 8px;
    font-size: 20px;
    font-weight: 700;
    letter-spacing: 0.1em;
    box-shadow: 0 4px 12px rgba(0,0,0,0.2);
  }
  .signal-BUY  { background: rgba(0, 242, 145, 0.1); color: #00f291; border: 1px solid #00f291; }
  .signal-SELL { background: rgba(255, 56, 96, 0.1); color: #ff3860; border: 1px solid #ff3860; }
  .signal-HOLD { background: rgba(255, 214, 0, 0.1); color: #ffd600; border: 1px solid #ffd600; }

  /* ── Section Title ────────────── */
  .section-title {
    font-family: 'Syne', sans-serif;
    font-size: 13px;
    font-weight: 700;
    color: #64748b;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    padding: 16px 0 8px 0;
    margin-top: 10px;
  }

  /* ── Pattern Chips ────────────── */
  .pattern-chip {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 11px;
    font-weight: 600;
    margin: 4px;
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
  }
  .chip-bullish { color: #00f291; border-color: rgba(0, 242, 145, 0.3); }
  .chip-bearish { color: #ff3860; border-color: rgba(255, 56, 96, 0.3); }
  .chip-neutral { color: #ffd600; border-color: rgba(255, 214, 0, 0.3); }

  /* ── Buttons ──────────────────── */
  .stButton > button {
    background: linear-gradient(135deg, #00f291, #00d2ff) !important;
    color: #0d1117 !important;
    font-weight: 700 !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 10px !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 4px 15px rgba(0, 242, 145, 0.2) !important;
  }
  .stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 20px rgba(0, 242, 145, 0.3) !important;
    opacity: 0.95 !important;
  }

  /* ── Scrollbar ────────────────── */
  ::-webkit-scrollbar { width: 6px; height: 6px; }
  ::-webkit-scrollbar-track { background: transparent; }
  ::-webkit-scrollbar-thumb { background: rgba(255, 255, 255, 0.1); border-radius: 10px; }
  ::-webkit-scrollbar-thumb:hover { background: rgba(255, 255, 255, 0.2); }

  /* ── Other Tweaks ─────────────── */
  .stTabs [data-baseweb="tab-list"] { background-color: transparent !important; }
  .stTabs [data-baseweb="tab"] {
    color: #94a3b8;
    font-weight: 600;
    border-bottom-width: 2px;
  }
  .stTabs [aria-selected="true"] { color: #00f291 !important; border-bottom-color: #00f291 !important; }
  .stDataFrame { border: 1px solid rgba(255, 255, 255, 0.05) !important; border-radius: 12px !important; }
  .stAlert { background: rgba(30, 41, 59, 0.4) !important; border: 1px solid rgba(255, 255, 255, 0.05) !important; border-radius: 12px !important; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────
# Session state init
# ─────────────────────────────────────────────────

if "watchlist" not in st.session_state:
    st.session_state.watchlist = []


# ─────────────────────────────────────────────────
# Sidebar – Controls
# ─────────────────────────────────────────────────

with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding: 12px 0 20px 0;">
      <span style="font-family:'Syne',sans-serif; font-size:20px; font-weight:800;
                   background:linear-gradient(135deg,#00f291,#00d2ff);
                   letter-spacing: -0.02em;
                   -webkit-background-clip:text; -webkit-text-fill-color:transparent;">
        TRANALYZE
      </span>
      <div style="font-size:9px; color:#64748b; letter-spacing:0.15em; margin-top:-2px; font-weight:600;">
        TREND ANALYZE
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="section-title">Market & Symbol</div>', unsafe_allow_html=True)

    # Callback to reset everything when market changes
    def on_market_change():
        new_market = st.session_state.market_selector
        new_cfg = MARKET_CONFIG[new_market]
        new_sugs = get_all_symbols(new_market)
        st.session_state.current_symbol = new_cfg["default"]
        st.session_state.ticker_history = new_sugs[:20]

    market = st.selectbox(
        "Select Market",
        list(MARKET_CONFIG.keys()),
        label_visibility="collapsed",
        key="market_selector",
        on_change=on_market_change
    )

    cfg = MARKET_CONFIG[market]
    suggestions = get_all_symbols(market)

    # 1. Initialize History and Ticker State (if first run)
    if "ticker_history" not in st.session_state:
        st.session_state.ticker_history = suggestions[:20] 
    if "current_symbol" not in st.session_state:
        st.session_state.current_symbol = cfg["default"]

    # 2. THE HYBRID SEARCH
    st.markdown('<div class="section-title">Search Symbol</div>', unsafe_allow_html=True)
    
    # Combined options list
    search_options = [st.session_state.current_symbol] + [s for s in st.session_state.ticker_history if s != st.session_state.current_symbol]
    
    # Dropdown Selection
    # Note: We use an on_change for instant response
    def on_dropdown_change():
        st.session_state.current_symbol = st.session_state.hybrid_search_box

    selected_ticker = st.selectbox(
        "Select or type...",
        options=search_options,
        index=0,
        label_visibility="collapsed",
        key="hybrid_search_box",
        on_change=on_dropdown_change
    )

    # 3. Manual Entry Overrider
    # We use a button or Enter key for manual entry
    manual_entry = st.text_input(
        "Type new ticker (e.g. TMCV):",
        placeholder="Type here and hit Enter...",
        key="manual_input_entry"
    )

    if manual_entry:
        new_ticker = manual_entry.strip().upper()
        if new_ticker != st.session_state.current_symbol:
            if new_ticker not in st.session_state.ticker_history:
                st.session_state.ticker_history.insert(0, new_ticker)
            st.session_state.current_symbol = new_ticker
            st.rerun()

    raw_symbol = st.session_state.current_symbol
    st.caption(f"Target: **{raw_symbol}** | Ready for Analysis")

    st.markdown('<div class="section-title">Continuous Updates</div>', unsafe_allow_html=True)
    auto_refresh_on = st.toggle("Enable Auto-Refresh", value=False)
    if auto_refresh_on:
        refresh_interval = st.slider("Interval (sec)", 10, 300, 60)
        st_autorefresh(interval=refresh_interval * 1000, key="datarefresh")

    st.markdown('<div class="section-title">Timeframe & Range</div>', unsafe_allow_html=True)

    timeframe_label = st.selectbox(
        "Timeframe",
        list(TIMEFRAME_MAP.keys()),
        index=5,  # Default: 1 Day
        label_visibility="visible",
    )
    interval, _ = TIMEFRAME_MAP[timeframe_label]

    valid_ranges = get_valid_ranges(interval)
    range_label = st.selectbox(
        "Range",
        valid_ranges,
        index=min(3, len(valid_ranges) - 1),
    )
    period = RANGE_MAP[range_label]

    st.markdown('<div class="section-title">Indicators</div>', unsafe_allow_html=True)

    show_ma   = st.checkbox("Moving Averages (MA20/50/200)", value=True)
    show_bb   = st.checkbox("Bollinger Bands", value=True)
    show_rsi  = st.checkbox("RSI (14)", value=True)
    show_macd = st.checkbox("MACD (12/26/9)", value=True)

    st.markdown('<div class="section-title">ML Model</div>', unsafe_allow_html=True)

    ml_model = st.selectbox("Model", ["Linear Regression", "Random Forest"])
    run_ml   = st.checkbox("Run Price Prediction", value=True)

    st.markdown('<div class="section-title">Candlestick Highlights</div>', unsafe_allow_html=True)
    available_candles = [
        "Doji", "Hammer", "Hanging Man", "Shooting Star", "Inverted Hammer",
        "Bullish Engulfing", "Bearish Engulfing", "Morning Star", "Evening Star",
        "Three White Soldiers", "Three Black Crows", "Piercing Pattern", 
        "Dark Cloud Cover", "Spinning Top", "Marubozu"
    ]
    selected_candles = st.multiselect(
        "Highlight patterns:",
        options=available_candles,
        default=["Hammer", "Shooting Star"],
        label_visibility="collapsed"
    )

    st.markdown('<div class="section-title">Backtesting</div>', unsafe_allow_html=True)
    run_backtest = st.checkbox("Run MA Crossover Backtest", value=False)
    if run_backtest:
        bt_fast = st.slider("Fast MA Period", 5, 50, 20)
        bt_slow = st.slider("Slow MA Period", 20, 200, 50)

    analyze_btn = st.button("🔍  ANALYZE", use_container_width=True)

    # ── Watchlist ─────────────────────────────────
    st.markdown('<div class="section-title">Watchlist</div>', unsafe_allow_html=True)

    symbol_display = convert_symbol(raw_symbol, market)
    col_add, col_clr = st.columns(2)
    with col_add:
        if st.button("＋ Add"):
            entry = f"{symbol_display} ({market})"
            if entry not in st.session_state.watchlist:
                st.session_state.watchlist.append(entry)
    with col_clr:
        if st.button("Clear"):
            st.session_state.watchlist = []

    for item in st.session_state.watchlist:
        st.markdown(f"• `{item}`")

    st.markdown("---")
    st.markdown(
        '<div style="font-size:10px; color:#444c56; text-align:center;">'
        'For educational purposes only.<br>Not financial advice.'
        '</div>',
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────
# Header
# ─────────────────────────────────────────────────

st.markdown("""
<div class="tranalyze-header">
  <span class="tranalyze-logo">TRANALYZE</span>
  <span class="tranalyze-sub">Trend Analyze — Educational Trading Dashboard</span>
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────
# Main Analysis
# ─────────────────────────────────────────────────

if analyze_btn or True:   # auto-load on first render
    symbol = convert_symbol(raw_symbol, market)

    with st.spinner(f"Fetching data for **{symbol}** …"):
        df_raw = fetch_data(symbol, interval, period)

    if df_raw.empty:
        st.error(
            f"⚠️ No data returned for **{symbol}**. "
            "Check the symbol and try a different timeframe / range combination."
        )
        st.stop()

    # ── Apply indicators ──────────────────────────
    df = apply_all_indicators(
        df_raw,
        show_ma=show_ma,
        show_rsi=show_rsi,
        show_macd=show_macd,
        show_bb=show_bb,
    )

    # ── Detect patterns ───────────────────────────
    patterns = detect_all_patterns(df)

    # ── Generate signal ───────────────────────────
    signal_result = generate_signal(df, patterns)

    # ── ML Prediction (Pre-calculating for Master Analysis) ──
    ml_result = {}
    if run_ml:
        ml_result = train_and_predict(df, model_type=ml_model)

    # ── Advanced Trend Analysis ──
    adv_analysis = get_expert_analysis(df, ml_result)

    # ── Summary metrics ───────────────────────────
    metrics = get_summary_metrics(df)
    ticker_info = fetch_ticker_info(symbol)

    # ── Symbol name header ────────────────────────
    name = ticker_info.get("name", symbol)
    currency = ticker_info.get("currency", "")
    chg = metrics.get("pct_change", 0)
    chg_class = "positive" if chg >= 0 else "negative"
    chg_arrow = "▲" if chg >= 0 else "▼"

    st.markdown(
        f'<div style="display:flex; align-items:center; gap:16px; margin-bottom:24px; padding: 10px; background: rgba(30, 41, 59, 0.2); border-radius: 12px; border: 1px solid rgba(255,255,255,0.03);">'
        f'  <div style="flex-grow: 1;">'
        f'    <div style="font-family:Syne,sans-serif; font-size:28px; font-weight:800; color:#fff; line-height: 1.2;">{name}</div>'
        f'    <div style="font-size:12px; color:#94a3b8; font-weight:600; text-transform: uppercase; letter-spacing: 0.05em;">{symbol} · {market} · {currency}</div>'
        f'  </div>'
        f'  <div style="text-align: right; background: rgba(0,0,0,0.2); padding: 8px 16px; border-radius: 8px;">'
        f'    <div style="font-size:10px; color:#94a3b8; text-transform: uppercase; font-weight:700;">Price Change</div>'
        f'    <div class="{chg_class}" style="font-size:20px; font-weight:800;">{chg_arrow} {abs(chg):.2f}%</div>'
        f'  </div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # Injecting the positive/negative/neutral colors for the header spans if not already in CSS
    st.markdown("""
    <style>
    .positive { color: #00f291 !important; }
    .negative { color: #ff3860 !important; }
    .neutral  { color: #ffd600 !important; }
    </style>
    """, unsafe_allow_html=True)

    # ── Metric row ────────────────────────────────
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    price     = metrics.get("current_price", 0)
    prev_c    = metrics.get("prev_close", 0)
    period_hi = metrics.get("period_high", 0)
    period_lo = metrics.get("period_low", 0)
    volume    = metrics.get("volume", 0)
    open_p    = metrics.get("open", 0)

    with c1:
        st.metric("Price", f"{format_price(price)}", f"{chg:+.2f}%")
    with c2:
        st.metric("Open", format_price(open_p))
    with c3:
        st.metric("Prev Close", format_price(prev_c))
    with c4:
        st.metric("Period High", format_price(period_hi))
    with c5:
        st.metric("Period Low", format_price(period_lo))
    with c6:
        st.metric("Volume", format_large_number(volume))

    st.markdown("---")

    # ═══════════════════════════════════════════
    # Tabs
    # ═══════════════════════════════════════════
    tab_chart, tab_master, tab_signal, tab_ml, tab_patterns, tab_backtest, tab_data = st.tabs([
        "📊 Chart",
        "🧠 Master Analysis",
        "🎯 Signal",
        "🤖 ML Predict",
        "🕯️ Patterns",
        "⏱️ Backtest",
        "📋 Raw Data",
    ])

    # ── Filter patterns based on selection ──
    filtered_patterns = {name: series for name, series in patterns.items() if name in selected_candles}

    # ─────────────────────────────────────────────
    # TAB 1 – Chart
    # ─────────────────────────────────────────────
    with tab_chart:
        fig = build_chart(
            df, symbol,
            show_ma=show_ma,
            show_bb=show_bb,
            show_rsi=show_rsi,
            show_macd=show_macd,
            patterns=filtered_patterns,
            advanced_patterns=adv_analysis,
        )
        st.plotly_chart(fig, use_container_width=True, config={'scrollZoom': True, 'displayModeBar': True})

        # Info strip
        n_candles = len(df)
        date_from = df.index[0].strftime("%d %b %Y") if hasattr(df.index[0], "strftime") else str(df.index[0])
        date_to   = df.index[-1].strftime("%d %b %Y") if hasattr(df.index[-1], "strftime") else str(df.index[-1])
        st.caption(
            f"Showing **{n_candles} candles** · "
            f"{date_from} → {date_to} · "
            f"Timeframe: {timeframe_label} · Range: {range_label}"
        )

    # ─────────────────────────────────────────────
    # TAB 1.5 – Master Analysis
    # ─────────────────────────────────────────────
    with tab_master:
        st.markdown('<div class="section-title">🧠 Master Neural-Trend Analysis</div>', unsafe_allow_html=True)
        
        # Display ALL detected structural patterns
        if adv_analysis["patterns"]:
            st.markdown(f"### 🔍 Detected Patterns ({len(adv_analysis['patterns'])})")
            for p in adv_analysis["patterns"]:
                color = "#00f291" if p["type"] == "bullish" else "#ff3860" if p["type"] == "bearish" else "#ffd600"
                st.markdown(f"""
                <div style="background: rgba(255,255,255,0.05); padding: 15px; border-left: 5px solid {color}; border-radius: 5px; margin-bottom: 10px;">
                    <span style="color: {color}; font-weight: bold; font-size: 1.2rem;">{p['name']}</span><br>
                    <span style="color: #9ca3af;">Type: {p['type'].capitalize()} Sentiment</span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("ℹ️ No complex structural patterns (Double Tops, Triangles, etc.) detected in the current view.")

        st.divider()
        col_m1, col_m2 = st.columns([2, 1])
        
        with col_m1:
            st.markdown(adv_analysis["analysis"])
            
            if adv_analysis["congruence"] == "HIGH":
                st.success("✅ Technical patterns and ML predictions are in sync. Higher probability signal.")
            elif adv_analysis["congruence"] == "CONFLICT":
                st.warning("⚠️ Indicators are providing conflicting signals. High-risk environment.")
        
        with col_m2:
            st.markdown("""
            <div style="background:rgba(0,210,255,0.05); padding:15px; border-radius:10px; border:1px solid rgba(0,210,255,0.1);">
                <div style="font-weight:700; color:#00d2ff; margin-bottom:5px;">Detected Levels</div>
                <div style="font-size:12px; color:#9ca3af;">
                    Automated support and resistance zones based on historical local extrema.
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            c_sup, c_res = st.columns(2)
            with c_sup:
                st.write("**Support**")
                for s in adv_analysis["support"]:
                    st.write(f"₹{s:.2f}")
            with c_res:
                st.write("**Resistance**")
                for r in adv_analysis["resistance"]:
                    st.write(f"₹{r:.2f}")

    # ─────────────────────────────────────────────
    # TAB 2 – Signal
    # ─────────────────────────────────────────────
    with tab_signal:
        sig    = signal_result["signal"]
        score  = signal_result["score"]
        reasons = signal_result["reasons"]
        sub    = signal_result["sub"]

        col_sig, col_score = st.columns([1, 2])

        with col_sig:
            st.markdown(
                f'<div style="padding:24px 0;">'
                f'  <div class="metric-label">Recommendation</div>'
                f'  <div style="margin-top:10px;">'
                f'    <span class="signal-badge signal-{sig}">{sig}</span>'
                f'  </div>'
                f'  <div style="margin-top:8px; font-size:13px; color:#8b949e;">'
                f'    Score: {score:+d} / 5'
                f'  </div>'
                f'</div>',
                unsafe_allow_html=True,
            )

        with col_score:
            st.markdown('<div class="section-title">Signal Breakdown</div>', unsafe_allow_html=True)
            for k, v in sub.items():
                bar_color = "#00c853" if v > 0 else "#ff1744" if v < 0 else "#444c56"
                direction = "▲ Bullish" if v > 0 else "▼ Bearish" if v < 0 else "— Neutral"
                st.markdown(
                    f'<div style="display:flex; justify-content:space-between; '
                    f'padding:6px 0; border-bottom:1px solid #1e2430;">'
                    f'  <span style="color:#8b949e;">{k}</span>'
                    f'  <span style="color:{bar_color}; font-weight:700;">{direction} ({v:+d})</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

        st.markdown('<div class="section-title" style="margin-top:20px;">Analysis Reasons</div>', unsafe_allow_html=True)
        if reasons:
            for r in reasons:
                icon = "🟢" if "bullish" in r.lower() or "oversold" in r.lower() else \
                       "🔴" if "bearish" in r.lower() or "overbought" in r.lower() else "🟡"
                st.markdown(f"{icon}  {r}")
        else:
            st.info("Not enough indicator data to generate detailed reasons.")

        st.markdown("""
        <div style="margin-top:24px; padding:12px; background:#161b22; border:1px solid #1e2430;
                    border-radius:8px; font-size:11px; color:#8b949e;">
          ⚠️ <strong>Disclaimer:</strong> Signals are generated algorithmically for
          educational purposes only. They are NOT financial advice. Always do your own
          research before making any investment decisions.
        </div>
        """, unsafe_allow_html=True)

    # ─────────────────────────────────────────────
    # TAB 3 – ML Prediction
    # ─────────────────────────────────────────────
    with tab_ml:
        if run_ml:
            with st.spinner("Training ML model …"):
                ml_result = train_and_predict(df, model_type=ml_model)

            if "error" in ml_result:
                st.warning(ml_result["error"])
            else:
                pred_price  = ml_result["predicted_price"]
                mae         = ml_result["mae"]
                r2          = ml_result["r2"]
                confidence  = ml_result["confidence"]
                conf_color  = "#00c853" if confidence == "High" else \
                              "#FFF176" if confidence == "Medium" else "#ff1744"

                direction   = "▲" if pred_price > price else "▼"
                diff_pct    = pct_change(pred_price, price)

                col_ml1, col_ml2, col_ml3 = st.columns(3)
                with col_ml1:
                    st.metric("Predicted Next Close", format_price(pred_price),
                              f"{direction} {diff_pct:+.2f}%")
                with col_ml2:
                    st.metric("Model MAE", format_price(mae, 4))
                with col_ml3:
                    st.metric("R² Score", f"{r2:.4f}")

                st.markdown(
                    f'<div style="margin:16px 0; padding:12px 18px; background:#161b22; '
                    f'border:1px solid #1e2430; border-radius:8px;">'
                    f'  Model: <strong>{ml_model}</strong> &nbsp;|&nbsp; '
                    f'  Confidence: <span style="color:{conf_color}; font-weight:700;">{confidence}</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

                # Feature importance (Random Forest only)
                if ml_result.get("feature_importance"):
                    st.markdown('<div class="section-title">Feature Importance</div>', unsafe_allow_html=True)
                    fi = ml_result["feature_importance"]
                    fi_df = pd.DataFrame(
                        {"Feature": list(fi.keys()), "Importance (%)": list(fi.values())}
                    ).sort_values("Importance (%)", ascending=False)
                    st.dataframe(fi_df, use_container_width=True, hide_index=True)

                st.markdown("""
                <div style="margin-top:16px; font-size:11px; color:#8b949e;">
                  ⚠️ ML predictions are estimates based on historical patterns.
                  They are NOT reliable indicators of future price movements.
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Enable 'Run Price Prediction' in the sidebar to see ML results.")

    # ─────────────────────────────────────────────
    # TAB 4 – Candlestick Patterns
    # ─────────────────────────────────────────────
    with tab_patterns:
        pattern_events = get_pattern_summary(df)

        # Summary chips
        st.markdown('<div class="section-title">Active Patterns (Last 30 Candles)</div>', unsafe_allow_html=True)

        if pattern_events:
            chip_html = ""
            for ev in pattern_events[:10]:
                css_class = (
                    "chip-bullish" if ev["sentiment"] == "Bullish"
                    else "chip-bearish" if ev["sentiment"] == "Bearish"
                    else "chip-neutral"
                )
                date_str = ev["date"].strftime("%d %b") if hasattr(ev["date"], "strftime") else str(ev["date"])
                chip_html += (
                    f'<span class="pattern-chip {css_class}">'
                    f'{ev["pattern"]} · {date_str}'
                    f'</span> '
                )
            st.markdown(chip_html, unsafe_allow_html=True)

            # Detailed table
            st.markdown('<div class="section-title" style="margin-top:16px;">Pattern Log</div>', unsafe_allow_html=True)
            events_df = pd.DataFrame(pattern_events)
            events_df["date"] = events_df["date"].astype(str)
            events_df["close"] = events_df["close"].round(2)
            st.dataframe(events_df.rename(columns={
                "date": "Date", "pattern": "Pattern",
                "sentiment": "Sentiment", "close": "Close Price"
            }), use_container_width=True, hide_index=True)
        else:
            st.info("No notable candlestick patterns detected in the last 30 candles.")

        # Pattern legend
        st.markdown('<div class="section-title" style="margin-top:20px;">Pattern Guide</div>', unsafe_allow_html=True)
        guide = {
            "Doji":              ("Neutral",  "Open ≈ Close; signals indecision and potential reversal"),
            "Hammer":            ("Bullish",  "Small body + long lower shadow; bullish reversal after downtrend"),
            "Shooting Star":     ("Bearish",  "Small body + long upper shadow; bearish reversal after uptrend"),
            "Bullish Engulfing": ("Bullish",  "Large green candle engulfs previous red candle"),
            "Bearish Engulfing": ("Bearish",  "Large red candle engulfs previous green candle"),
        }
        for pname, (sent, desc) in guide.items():
            color = "#00c853" if sent == "Bullish" else "#ff1744" if sent == "Bearish" else "#FFF176"
            st.markdown(
                f'<div style="padding:8px 0; border-bottom:1px solid #1e2430;">'
                f'  <span style="color:{color}; font-weight:700;">{pname}</span>'
                f'  <span style="color:#8b949e; font-size:12px;"> · {sent}</span><br>'
                f'  <span style="font-size:12px; color:#6e7681;">{desc}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )

    # ─────────────────────────────────────────────
    # TAB 5 – Backtest
    # ─────────────────────────────────────────────
    with tab_backtest:
        if run_backtest:
            with st.spinner("Running backtest …"):
                bt = run_ma_crossover_backtest(
                    df_raw,
                    fast_period=bt_fast,
                    slow_period=bt_slow,
                )

            if "error" in bt:
                st.warning(bt["error"])
            else:
                total_ret = bt["total_return_pct"]
                ret_color = "#00c853" if total_ret >= 0 else "#ff1744"

                st.markdown(
                    f'<div style="padding:12px; background:#161b22; border:1px solid #1e2430; '
                    f'border-radius:8px; margin-bottom:16px;">'
                    f'  Strategy: <strong>MA{bt_fast} × MA{bt_slow} Crossover</strong> &nbsp;·&nbsp; '
                    f'  Capital: ₹{bt["initial_capital"]:,.0f}'
                    f'</div>',
                    unsafe_allow_html=True,
                )

                col_b1, col_b2, col_b3, col_b4 = st.columns(4)
                with col_b1:
                    st.metric("Final Value",    f"₹{bt['final_value']:,.2f}")
                with col_b2:
                    st.metric("Total P&L",      f"₹{bt['total_pnl']:,.2f}",
                              f"{total_ret:+.2f}%")
                with col_b3:
                    st.metric("Win Rate",       f"{bt['win_rate_pct']:.1f}%")
                with col_b4:
                    st.metric("Max Drawdown",   f"{bt['max_drawdown_pct']:.2f}%")

                # Portfolio equity curve
                if not bt["portfolio_series"].empty:
                    import plotly.graph_objects as go
                    ps = bt["portfolio_series"]
                    fig_bt = go.Figure()
                    fig_bt.add_trace(go.Scatter(
                        x=ps.index, y=ps.values,
                        fill="tozeroy",
                        fillcolor="rgba(0,200,83,0.08)",
                        line=dict(color="#00c853", width=1.5),
                        name="Portfolio Value",
                    ))
                    fig_bt.update_layout(
                        title="Portfolio Equity Curve",
                        paper_bgcolor="#0d1117",
                        plot_bgcolor="#0d1117",
                        font=dict(color="#e6edf3"),
                        height=300,
                        margin=dict(l=10, r=10, t=40, b=10),
                        xaxis=dict(gridcolor="#1e2430"),
                        yaxis=dict(gridcolor="#1e2430", side="right"),
                    )
                    st.plotly_chart(fig_bt, use_container_width=True)

                # Trade log
                if not bt["trades"].empty:
                    st.markdown('<div class="section-title">Trade Log</div>', unsafe_allow_html=True)
                    tdf = bt["trades"].copy()
                    tdf["Date"] = tdf["Date"].astype(str)
                    st.dataframe(tdf.rename(columns={
                        "Date": "Date", "Action": "Action",
                        "Price": "Price", "Shares": "Units", "PnL": "P&L"
                    }), use_container_width=True, hide_index=True)
        else:
            st.info("Enable 'Run MA Crossover Backtest' in the sidebar and click Analyze.")

    # ─────────────────────────────────────────────
    # TAB 6 – Raw Data
    # ─────────────────────────────────────────────
    with tab_data:
        st.markdown('<div class="section-title">OHLCV + Indicators</div>', unsafe_allow_html=True)

        display_df = df.copy()
        display_df.index = display_df.index.astype(str)

        # Round floats for display
        float_cols = display_df.select_dtypes(include="float").columns
        display_df[float_cols] = display_df[float_cols].round(4)

        st.dataframe(display_df.tail(200), use_container_width=True)

        csv_data = df.to_csv()
        st.download_button(
            label="⬇  Download CSV",
            data=csv_data,
            file_name=f"{symbol}_{interval}_{period}.csv",
            mime="text/csv",
        )

        st.caption(f"Showing last 200 of {len(df)} rows. Download for full dataset.")