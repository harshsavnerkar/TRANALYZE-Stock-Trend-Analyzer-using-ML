import streamlit as st
import pandas as pd
from datetime import datetime
from utils import (
    MARKET_CONFIG, TIMEFRAME_MAP, RANGE_MAP,
    convert_symbol, get_valid_ranges, get_all_symbols,
    format_large_number, format_price, pct_change,
)
from data import fetch_data
from auth import (
    save_portfolio_position, load_user_portfolio, update_portfolio_position
)
from indicators import apply_all_indicators
from patterns import detect_all_patterns
from signals import generate_signal
from advanced_patterns import get_expert_analysis
from market_advisor import get_news_sentiment
from fpdf import FPDF

import re

def clean_for_pdf(text):
    """Removes emojis and non-standard characters for PDF compatibility."""
    if not text: return ""
    # Strip markdown and common emojis
    text = text.replace("### ", "").replace("**", "").replace("🚀", "").replace("⚠️", "").replace("⚖️", "").replace("🚨", "").replace("🛡️", "").replace("📊", "").replace("🕯️", "").replace("🏗️", "").replace("🧠", "")
    # Remove any remaining non-Latin1 characters
    return re.sub(r'[^\x00-\xff]', '', text)

def generate_portfolio_pdf(active, closed, user_name):
    """Generates a professional PDF report of the user portfolio."""
    pdf = FPDF()
    pdf.add_page()
    
    # Branding & Header
    pdf.set_font("Helvetica", 'B', 24)
    pdf.set_text_color(15, 23, 42) # Midnight Navy
    pdf.cell(0, 20, "TRANALYZE", ln=True, align='C')
    pdf.set_font("Helvetica", 'B', 16)
    pdf.cell(0, 10, "Executive Portfolio Report", ln=True, align='C')
    
    pdf.set_font("Helvetica", '', 10)
    pdf.set_text_color(100, 116, 139)
    pdf.cell(0, 10, f"Exported: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True, align='C')
    pdf.cell(0, 10, f"Investment Analyst: {clean_for_pdf(user_name)}", ln=True, align='C')
    pdf.ln(10)
    
    # ── Section 1: Portfolio Performance Summary ──
    pdf.set_font("Helvetica", 'B', 14)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 10, "1. Performance Summary", ln=True)
    pdf.set_font("Helvetica", '', 11)
    
    if active:
        total_inv = sum([p['entry_price'] * p['quantity'] for p in active])
        total_pnl = sum([p['pnl'] for p in active])
        pnl_pct = (total_pnl / total_inv * 100) if total_inv > 0 else 0
        
        pdf.cell(60, 10, f"Total Invested: {total_inv:,.2f}", border=1)
        pdf.cell(60, 10, f"Unrealized P&L: {total_pnl:,.2f}", border=1)
        pdf.cell(60, 10, f"Total Return: {pnl_pct:,.2f}%", border=1)
    else:
        pdf.cell(0, 10, "No active positions found.", ln=True)
    pdf.ln(20)
    
    # ── Section 2: Detailed Active Positions & AI Intelligence ──
    pdf.set_font("Helvetica", 'B', 14)
    pdf.cell(0, 10, "2. Active Positions & Tactical Intelligence", ln=True)
    pdf.ln(5)
    
    for p in active:
        # Mini Table for basic info
        pdf.set_font("Helvetica", 'B', 10)
        pdf.set_fill_color(241, 245, 249)
        pdf.cell(0, 10, f" ASSET: {p['symbol']} ({p['side'].upper()})", ln=True, fill=True, border=1)
        
        pdf.set_font("Helvetica", '', 9)
        pdf.cell(45, 8, f"Qty: {p['quantity']}", border=1)
        pdf.cell(45, 8, f"Entry: {p['entry_price']:,.2f}", border=1)
        pdf.cell(45, 8, f"Current: {p['current_price']:,.2f}", border=1)
        pdf.cell(55, 8, f"Unrealized P&L: {p['pnl']:,.2f} ({p['pnl_pct']:.2f}%)", border=1)
        pdf.ln(10)
        
        # AI ADVICE INJECTION
        pdf.set_font("Helvetica", 'B', 10)
        pdf.set_text_color(2, 132, 199) # Sky Blue
        pdf.cell(0, 8, "AI ADVISOR STRATEGIC VERDICT:", ln=True)
        
        pdf.set_font("Helvetica", '', 8)
        pdf.set_text_color(30, 41, 59)
        
        # Get advice and clean up for PDF
        raw_advice = get_ai_advice(p['symbol'], p['market'], p['entry_price'], p['side'])
        clean_advice = clean_for_pdf(raw_advice)
        
        # Write advice as a multi-cell block
        pdf.multi_cell(0, 5, clean_advice, border='L')
        pdf.ln(10)
    
    pdf.ln(5)
    
    # ── Section 3: Trade History (Closed) ──
    if closed:
        pdf.set_font("Helvetica", 'B', 14)
        pdf.cell(0, 10, "3. Realized Performance History", ln=True)
        pdf.set_font("Helvetica", 'B', 9)
        c_cols = ["Symbol", "Side", "Entry P.", "Exit P.", "Realized P&L", "Closed On"]
        c_widths = [35, 25, 30, 30, 35, 30]
        for i, c in enumerate(c_cols):
            pdf.cell(c_widths[i], 10, c, border=1, align='C')
        pdf.ln()
        
        pdf.set_font("Helvetica", '', 9)
        for cp in closed:
            pdf.cell(c_widths[0], 10, cp['symbol'], border=1, align='C')
            pdf.cell(c_widths[1], 10, cp['side'], border=1, align='C')
            pdf.cell(c_widths[2], 10, f"{cp['entry_price']:,.2f}", border=1, align='C')
            pdf.cell(c_widths[3], 10, f"{cp['close_price']:,.2f}", border=1, align='C')
            pdf.cell(c_widths[4], 10, f"{cp['realized_pnl']:,.2f}", border=1, align='C')
            pdf.cell(c_widths[5], 10, str(cp['closed_at'])[:10], border=1, align='C')
            pdf.ln()
            
    # Return as safe bytes for Streamlit
    return pdf.output()

def get_processed_portfolio(uid):
    """Fetch, Calculate P&L, and Sort Portfolio categories."""
    raw_data = load_user_portfolio(uid)
    active = []
    closed = []
    
    for pos_id, data in raw_data.items():
        if data.get("status") == "Closed":
            closed.append({**data, "id": pos_id})
        else:
            # Fetch current price
            try:
                # CONVERT SYMBOL FOR LIVE FETCH
                live_sym = convert_symbol(data['symbol'], data['market'])
                # Use a small range to get latest price
                # USE 1M INTERVAL FOR MAXIMUM ACCURACY (LATEST AVAILABLE FEED)
                df = fetch_data(live_sym, "1m", "1d")
                if not df.empty:
                    current_price = df['Close'].iloc[-1]
                    entry_price = data['entry_price']
                    qty = data['quantity']
                    side = data.get("side", "Buy")
                    
                    if side == "Buy":
                        unrealized_pnl = (current_price - entry_price) * qty
                    else: # Sell/Short
                        unrealized_pnl = (entry_price - current_price) * qty
                    
                    pnl_pct = (unrealized_pnl / (entry_price * qty)) * 100
                    
                    active.append({
                        **data, 
                        "id": pos_id, 
                        "current_price": current_price,
                        "pnl": unrealized_pnl,
                        "pnl_pct": pnl_pct
                    })
                else:
                    active.append({**data, "id": pos_id, "current_price": 0, "pnl": 0, "pnl_pct": 0})
            except:
                active.append({**data, "id": pos_id, "current_price": 0, "pnl": 0, "pnl_pct": 0})
                
    # Sort active A-Z by symbol
    active.sort(key=lambda x: x['symbol'])
    return active, closed

def get_ai_advice(symbol, market, entry_price, side):
    """
    Core AI Advisor Engine.
    Provides Deep Tactical Reports with Basis, SL, and Targets.
    """
    try:
        # CONVERT SYMBOL FOR LIVE FETCH
        live_sym = convert_symbol(symbol, market)
        # Use daily data for tactical advice
        df_raw = fetch_data(live_sym, "1d", "1mo")
        if df_raw.empty: return "Insufficient data for tactical advice."
        
        df = apply_all_indicators(df_raw, True, True, True, True)
        patterns = detect_all_patterns(df)
        sig = generate_signal(df, patterns)
        # ── NEWS SENTIMENT INTEGRATION ─────────────────
        s_score, s_status, headlines = get_news_sentiment(live_sym)
        news_bias = f"**{s_status}** ({'Bullish' if s_score > 0 else 'Bearish' if s_score < 0 else 'Neutral'})"
        headline_str = "\n".join([f"- {h}" for h in headlines[:3]]) if headlines else "No recent high-impact headlines detected."

        adv = get_expert_analysis(df, {}) # Get support/resistance
        
        current_price = df['Close'].iloc[-1]
        trend = sig['signal'] # BUY, SELL, HOLD

        # High-Conviction Sentiment Overrides
        if s_score <= -2 and trend == "BUY":
            trend = "HOLD (Sentiment Alert 🚨)"
        elif s_score >= 2 and trend == "SELL":
            trend = "HOLD (Improving News 💡)"

        reasons = sig.get('reasons', [])
        
        # Calculate dynamic SL/Target based on Support/Resistance + entry awareness
        s_levels = sorted(adv.get("support", []))
        r_levels = sorted(adv.get("resistance", []))
        
        # Basis of Levels formatting for display
        s_text = ", ".join([f"₹{x:.2f}" for x in s_levels[:3]]) if s_levels else "N/A"
        r_text = ", ".join([f"₹{x:.2f}" for x in r_levels[:3]]) if r_levels else "N/A"

        if side == "Buy":
            # Logic: Targets must be > entry_price for profit. SL must be < entry_price.
            targets = [r for r in r_levels if r > entry_price]
            if not targets: targets = [entry_price * 1.05, entry_price * 1.10, entry_price * 1.20]
            elif len(targets) < 3: targets += [targets[-1] * 1.05, targets[-1] * 1.10]
            
            sls = [s for s in s_levels if s < entry_price]
            if not sls: sls = [entry_price * 0.98, entry_price * 0.95, entry_price * 0.90]
            elif len(sls) < 3: sls = [sls[0] * 0.98, sls[0] * 0.95] + sls
            sls = sorted(sls, reverse=True) # Nearest SL first
            
            t_small, t_mod, t_risk = sorted(targets)[:3]
            sl_safe, sl_mod, sl_deep = sls[:3]
            basis_levels = "Structural Support and Fibonacci Pivots"
        else: # Sell/Short
            targets = [s for s in s_levels if s < entry_price]
            if not targets: targets = [entry_price * 0.95, entry_price * 0.90, entry_price * 0.80]
            elif len(targets) < 3: targets = targets + [targets[-1]*0.95, targets[-1]*0.90]
            targets = sorted(targets, reverse=True) # Nearest Target first
            
            sls = [r for r in r_levels if r > entry_price]
            if not sls: sls = [entry_price * 1.02, entry_price * 1.05, entry_price * 1.10]
            elif len(sls) < 3: sls += [sls[-1] * 1.05, sls[-1] * 1.10]
            
            t_small, t_mod, t_risk = targets[:3]
            sl_safe, sl_mod, sl_deep = sorted(sls)[:3]
            basis_levels = "Upper Supply Resistance and ATR Volatility"

        # Pattern Summary
        detected_pats = [name for name, val in patterns.items() if val.iloc[-1] != 0]
        pat_str = ", ".join(detected_pats) if detected_pats else "No major candlestick patterns detected in the current candle."

        # Formatting the detailed report
        header = f"### AI Strategic Verdict: {trend}"
        basis_section = "**📊 Technical Basis:**\n" + "\n".join([f"- {r}" for r in reasons])
        
        deep_reasoning = ""
        if side == "Buy":
            if trend == "BUY":
                deep_reasoning = f"The price is currently showing bullish momentum with support at {s_text}. The oscillators and moving averages suggest a trend continuation above your entry of {entry_price}. **REASON FOR BUY/HOLD:** Indicators suggest demand is outpacing supply."
            elif trend == "SELL":
                deep_reasoning = f"The trend has broken below key levels. With resistance now forming at {r_text}, the probability of further downside is high. **REASON FOR EXIT:** Technical breakdown detected relative to entry."
            else:
                deep_reasoning = f"Price is trapped in a narrow range. Neither buyers nor sellers have control. **REASON FOR NEUTRAL:** Low volatility/sideways trend."
        else: # Short
             if trend == "SELL":
                deep_reasoning = f"Bearish trend is stable. Resistance at {r_text} is holding firm. **REASON FOR HOLD SHORT:** Downward pressure remains dominant."
             else:
                deep_reasoning = f"Trend reversal detected. Price is bouncing off support at {s_text}. **REASON FOR EXIT SHORT:** Bullish strength emerging."

        report = f"""
{header}

**📰 Market Sentiment Pulse:**
- **Sentiment Bias:** {news_bias}
- **Latest Headlines:**
{headline_str}

{deep_reasoning}

---
**🕯️ Pattern Audit:**
{pat_str}

---
{basis_section}

---
**🏗️ Structural Geometry:**
- **Linear Support Zone:** {s_text}
- **Linear Resistance Zone:** {r_text}

---
🛡️ **Strategic Guardrails (Multi-Tier):**
*Basis of levels: {basis_levels}*

**Profit Targets (Take Profit):**
1. **Conservative (Small):** ₹{t_small:.2f}
2. **Structural (Moderate):** ₹{t_mod:.2f}
3. **High-Yield (Risky):** ₹{t_risk:.2f}

**Stop-Loss Levels (Risk Control):**
1. **Tight (Safe):** ₹{sl_safe:.2f}
2. **Structural (Moderate):** ₹{sl_mod:.2f}
3. **Deep Caveat (Risky):** ₹{sl_deep:.2f}
"""
        return report
    except Exception as e:
        return f"AI Advisor unavailable: {str(e)}"
