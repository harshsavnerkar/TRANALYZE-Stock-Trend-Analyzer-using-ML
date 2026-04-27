"""
app.py - Main Streamlit UI
TRANALYZE – Trend Analyze

Professional trading analysis dashboard for educational purposes.
Supports NSE, BSE, US Stocks, Forex, and Crypto markets.
"""

import streamlit as st
import pandas as pd
import json
import time
from datetime import datetime
import base64

import extra_streamlit_components as stx

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
from portfolio_logic import get_processed_portfolio, get_ai_advice, generate_portfolio_pdf
from market_advisor import get_market_pulse, get_news_sentiment, get_google_price

# Authentication
from auth import (
    login, signup, reset_password, generate_otp, verify_otp_logic,
    save_user_watchlist, load_user_watchlist, get_user_data
)

st.set_page_config(
    page_title="TRANALYZE – Trend Analyze",
    page_icon="logo.png",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Cookie Persistence Engine ───────────────────
cookie_manager = stx.CookieManager()

# ─────────────────────────────────────────────────
# Session state init
# ─────────────────────────────────────────────────

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if "active_module" not in st.session_state:
    st.session_state.active_module = "Hub"

if "logging_out" not in st.session_state:
    st.session_state.logging_out = False

# ── Master Logout Lock (Refesh-Proof) ──────────
if "action" in st.query_params and st.query_params["action"] == "logout":
    st.session_state.authenticated = False
    st.session_state.logging_out = True
    try:
        cookie_manager.delete("tranalyze_token")
    except:
        pass
    # Clear query params after processing to keep URL clean
    st.query_params.clear()

# ── Auto-Login from Cookies ────────────────────
if not st.session_state.authenticated and not st.session_state.logging_out:
    user_cookie = cookie_manager.get(cookie="tranalyze_token")
    if user_cookie:
        st.session_state.authenticated = True
        st.session_state.user = user_cookie
        st.session_state.watchlist = load_user_watchlist(user_cookie['localId'])
        st.rerun()

if "otp_sent" not in st.session_state:
    st.session_state.otp_sent = False
if "pending_user" not in st.session_state:
    st.session_state.pending_user = None

if "watchlist" not in st.session_state:
    st.session_state.watchlist = []

if "current_market" not in st.session_state:
    st.session_state.current_market = list(MARKET_CONFIG.keys())[0]

if "current_symbol" not in st.session_state:
    st.session_state.current_symbol = MARKET_CONFIG[st.session_state.current_market]["default"]

# ── Global Styling Engine (Locked to Premium Cyber) ──────────
primary_color = "#00f291" # Emerald Neon
secondary_color = "#00d2ff" 
bg_main = "radial-gradient(circle at 50% 0%, #1e293b 0%, #020617 100%)"
card_bg = "rgba(15, 23, 42, 0.65)"
sidebar_bg = "rgba(2, 6, 23, 0.9)"
text_main = "#f8fafc"
text_sub = "#94a3b8"
border_color = "rgba(255, 255, 255, 0.1)"
glass_blur = "15px"

# ─────────────────────────────────────────────────
# Custom CSS – Dynamic Variable Integration (Restored Best UI)
# ─────────────────────────────────────────────────

st.markdown(f"""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=Outfit:wght@300;400;600;700&display=swap');

  :root {{
    --primary: {primary_color};
    --secondary: {secondary_color};
    --text-main: {text_main};
    --text-sub: {text_sub};
    --card-bg: {card_bg};
    --border: {border_color};
    --glass-blur: {glass_blur};
  }}

  .stApp {{
    background: {bg_main} !important;
    color: var(--text-main) !important;
    font-family: 'Outfit', sans-serif !important;
  }}

  [data-testid="stHeader"] {{ background: transparent !important; }}

  /* ── Sidebar ────── */
  section[data-testid="stSidebar"] {{
    background: {sidebar_bg} !important;
    backdrop-filter: blur(var(--glass-blur));
    border-right: 1px solid var(--border);
  }}
  
  .section-title {{
     color: var(--primary) !important;
     font-size: 11px !important;
     letter-spacing: 0.15em !important;
     text-transform: uppercase !important;
     font-weight: 800 !important;
     margin: 20px 0 10px 0 !important;
  }}

  /* ── Hub Cards (Restored High-Visibility) ─────── */
  .hub-card {{
    background: var(--card-bg);
    backdrop-filter: blur(var(--glass-blur));
    border: 1px solid var(--border);
    border-radius: 28px;
    padding: 50px 40px;
    text-align: center;
    transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    position: relative;
    overflow: hidden;
    box-shadow: 0 10px 30px -15px rgba(0, 0, 0, 0.5);
  }}

  .hub-card:hover {{
    transform: translateY(-12px);
    border-color: var(--primary);
    box-shadow: 0 0 40px -10px var(--primary);
  }}

  /* ── Original Auth Styling ── */
  .auth-card {{
    background: var(--card-bg) !important;
    border: 1px solid var(--border) !important;
    border-radius: 32px !important;
    box-shadow: 0 40px 80px -20px rgba(0,0,0,0.8) !important;
    text-align: center !important;
    padding: 40px !important;
  }}

  .auth-title {{
    font-family: 'Syne', sans-serif !important;
    font-size: 42px !important;
    letter-spacing: -2px !important;
    text-align: center !important;
    color: var(--text-main) !important;
    margin-bottom: 5px !important;
  }}

  .hub-title {{
    font-family: 'Syne', sans-serif;
    font-size: 26px;
    font-weight: 800;
    color: var(--text-main);
    margin-bottom: 15px;
    letter-spacing: -0.5px;
  }}

  .hub-desc {{
    font-size: 15px;
    color: var(--text-sub);
    line-height: 1.6;
  }}

  /* ── Activation Badge (Restored) ── */
  .hub-card::after {{
    content: 'ACTIVATE MODULE';
    position: absolute;
    bottom: -30px;
    left: 0;
    right: 0;
    padding: 10px;
    font-size: 11px;
    font-weight: 800;
    letter-spacing: 0.25em;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent);
    transition: all 0.3s ease;
  }}

  .hub-card:hover::after {{
    bottom: 0;
  }}

  /* ── Interactive Buttons (Total Visibility Fix) ── */
  .stButton > button, .stDownloadButton > button, .stFormSubmitButton > button {{
    background: var(--card-bg) !important;
    color: var(--text-main) !important;
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
    font-weight: 700 !important;
    padding: 10px 24px !important;
    transition: all 0.3s ease !important;
    width: 100% !important;
    text-transform: uppercase !important;
    letter-spacing: 0.05em !important;
  }}

  .stButton > button:hover, .stDownloadButton > button:hover, .stFormSubmitButton > button:hover {{
    background: var(--primary) !important;
    color: #000000 !important;
    border-color: var(--primary) !important;
    box-shadow: 0 0 20px var(--primary) !important;
  }}

  /* Specific fix for the 'White Ghost' Download Button */
  .stDownloadButton > button {{
     background: rgba(255, 255, 255, 0.05) !important;
     color: var(--text-main) !important;
     border: 1px solid var(--primary) !important;
  }}

  /* ── Expander Styling (White-out Fix) ── */
  .stExpander {{
    background: var(--card-bg) !important;
    border: 1px solid var(--border) !important;
    border-radius: 16px !important;
    margin-bottom: 20px !important;
  }}

  .streamlit-expanderHeader {{
    background: transparent !important;
    color: var(--text-main) !important;
    font-weight: 700 !important;
    font-size: 16px !important;
    border-bottom: 1px solid var(--border) !important;
  }}

  .streamlit-expanderContent {{
    background: transparent !important;
    color: var(--text-main) !important;
  }}

  /* Key button override for Prediction */
  .pred-btn button {{
    background: linear-gradient(135deg, #00f291, #00d2ff) !important;
    color: #020617 !important;
    border: none !important;
    font-weight: 800 !important;
    font-family: 'Syne', sans-serif !important;
  }}

  /* Center the tabs and give them a box structure */
  .stTabs [data-baseweb="tab-list"] {{
    justify-content: center !important;
    gap: 15px !important;
    background: transparent !important;
    padding: 10px !important;
  }}

  .stTabs [data-baseweb="tab"] {{
    background: var(--card-bg) !important;
    border: 1px solid var(--border) !important;
    border-radius: 14px !important;
    padding: 12px 40px !important;
    color: var(--text-sub) !important;
    font-weight: 700 !important;
    transition: all 0.3s ease !important;
    font-size: 16px !important;
  }}

  /* Active Box Styling */
  .stTabs [aria-selected="true"] {{
    background: rgba(0, 242, 145, 0.1) !important;
    border-color: var(--primary) !important;
    color: var(--text-main) !important;
    box-shadow: 0 0 15px rgba(0, 242, 145, 0.2) !important;
    transform: translateY(-2px) !important;
  }}

  .auth-subtitle {{
    color: var(--text-sub) !important;
    font-size: 14px !important;
    font-weight: 500 !important;
    margin-bottom: 30px !important;
    letter-spacing: 0.05em !important;
  }}

  /* ── ML Prediction Card ── */
  .ml-card {{
    background: rgba(0, 242, 145, 0.05);
    border: 1px solid var(--primary);
    border-radius: 20px;
    padding: 30px;
    text-align: center;
    margin-bottom: 25px;
    box-shadow: 0 10px 30px -10px rgba(0, 242, 145, 0.1);
  }}
  .ml-price {{
    font-family: 'Syne', sans-serif;
    font-size: 48px;
    font-weight: 800;
    color: var(--primary);
    margin: 10px 0;
    display: block;
    text-shadow: 0 0 20px var(--primary);
  }}

  /* ── Market Pulse Index Banner ── */
  .pulse-grid {{
      display: flex;
      justify-content: space-between;
      gap: 20px;
      margin-bottom: 40px;
      margin-top: 20px;
  }}
  .pulse-card {{
      flex: 1;
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 24px;
      padding: 25px 20px;
      text-align: center;
      transition: all 0.3s ease;
      position: relative;
      overflow: hidden;
  }}
  .pulse-card:hover {{
      border-color: var(--primary);
      box-shadow: 0 0 25px rgba(0, 242, 145, 0.1);
  }}
  .index-name {{ font-size: 13px; font-weight: 700; color: #94a3b8; text-transform: uppercase; letter-spacing: 1.5px; opacity: 0.8; }}
  .index-price {{ font-size: 28px; font-weight: 800; color: #f8fafc; margin: 8px 0; letter-spacing: -1px; }}
  .pred-badge {{ 
      display: inline-block; 
      padding: 6px 14px; 
      border-radius: 30px; 
      font-size: 10px; 
      font-weight: 900; 
      text-transform: uppercase;
      margin-top: 10px;
      letter-spacing: 0.5px;
  }}
  .pred-green {{ background: rgba(0, 242, 145, 0.1); color: #00f291; border: 1px solid #00f291; }}
  .pred-red {{ background: rgba(255, 56, 96, 0.1); color: #ff3860; border: 1px solid #ff3860; }}
  .intensity-tag {{ font-size: 9px; color: #94a3b8; margin-top: 8px; font-weight: 600; opacity: 0.7; }}

  /* ── Nuclear Pulse Button Styling (Fixing the White-out) ── */
  .popover-green div[data-testid="stPopover"] > button {{
      background: #00f291 !important;
      color: #020617 !important;
      border: none !important;
      font-weight: 800 !important;
      text-transform: uppercase !important;
      box-shadow: 0 0 20px rgba(0, 242, 145, 0.5) !important;
  }}
  .popover-red div[data-testid="stPopover"] > button {{
      background: #ff3860 !important;
      color: #ffffff !important;
      border: none !important;
      font-weight: 800 !important;
      text-transform: uppercase !important;
      box-shadow: 0 0 20px rgba(255, 56, 96, 0.5) !important;
  }}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────
# ── AUTHENTICATION GATE ──────────────────────────
# ─────────────────────────────────────────────────

if not st.session_state.authenticated:
    # Use columns to center a small, slim login box in the middle of the wide page
    col_l, col_m, col_r = st.columns([1.2, 1, 1.2])
    
    with col_m:
        st.markdown('<div class="auth-card">', unsafe_allow_html=True)
        
        # Professional Centered Logo
        try:
            with open("logo.png", "rb") as f:
                encoded_logo = base64.b64encode(f.read()).decode("utf-8")
                st.markdown(f"""
<div style="display: flex; justify-content: center; align-items: center; margin-top: -10px; margin-bottom: 15px;">
    <img src="data:image/png;base64,{encoded_logo}" width="160" style="border-radius: 15px; box-shadow: 0 8px 32px rgba(0,0,0,0.4);">
</div>
""", unsafe_allow_html=True)
        except:
            pass

        st.markdown('<div class="auth-title">TRANALYZE</div>', unsafe_allow_html=True)
        
        if not st.session_state.otp_sent:
            st.markdown('<div class="auth-subtitle">Trend Analysis Intelligence Gate</div>', unsafe_allow_html=True)
            auth_tab1, auth_tab2 = st.tabs(["Login", "Sign Up"])
            
            with auth_tab1:
                email = st.text_input("Email", key="login_email")
                password = st.text_input("Password", type="password", key="login_pass")
                st.markdown("<div style='margin-top:10px;'></div>", unsafe_allow_html=True)
                if st.button("Login", use_container_width=True):
                    res = login(email, password)
                    if res["success"]:
                        st.session_state.authenticated = True
                        st.session_state.user = res["user"]
                        cookie_manager.set("tranalyze_token", res["user"])
                        st.session_state.watchlist = load_user_watchlist(res["user"]["localId"])
                        st.rerun()
                    else:
                        st.error(res["error"])

            with auth_tab2:
                su_name = st.text_input("Full Name")
                su_email = st.text_input("Email", key="su_email")
                su_pass = st.text_input("Password", type="password", key="su_pass")
                st.markdown("<div style='margin-top:10px;'></div>", unsafe_allow_html=True)
                if st.button("Generate OTP", use_container_width=True):
                    if su_email:
                        st.session_state.otp_sent = True
                        st.session_state.pending_user = {"email": su_email, "pass": su_pass, "phone": "", "name": su_name}
                        generate_otp(su_email, su_email)
                        st.success(f"Security code sent to {su_email}")
                        st.rerun()
                    else:
                        st.warning("Please enter a valid email address.")
                
        else:
            # OTP VERIFICATION STAGE
            st.markdown('<div class="auth-subtitle">Enter the code from your email</div>', unsafe_allow_html=True)
            otp_code = st.text_input("OTP Code", placeholder="XXXXXX")
            
            st.markdown("<div style='margin-top:10px;'></div>", unsafe_allow_html=True)
            if st.button("Verify & Signup", use_container_width=True):
                u = st.session_state.pending_user
                v_res = verify_otp_logic(u["email"], otp_code)
                
                if v_res["success"]:
                    res = signup(u["email"], u["pass"], u["phone"], u["name"])
                    if res["success"]:
                        st.session_state.authenticated = True
                        st.session_state.user = res["user"]
                        cookie_manager.set("tranalyze_token", res["user"])
                        st.session_state.watchlist = []
                        st.session_state.otp_sent = False
                        st.rerun()
                    else:
                        st.error(res["error"])
                else:
                    st.error(v_res["error"])
            
            if st.button("Back", use_container_width=True):
                st.session_state.otp_sent = False
                st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()



# ─────────────────────────────────────────────────
# Global Sidebar (Accessible Everywhere)
# ─────────────────────────────────────────────────

with st.sidebar:
    if st.session_state.authenticated:
        if st.button("🚪 Logout Session", use_container_width=True):
            st.session_state.logging_out = True
            try:
                cookie_manager.delete("tranalyze_token")
            except:
                pass
            st.session_state.authenticated = False
            st.session_state.user = None
            st.query_params["action"] = "logout"
            st.rerun()

# ─────────────────────────────────────────────────
# AUTHENTICATION GATE
# ─────────────────────────────────────────────────

if not st.session_state.authenticated:
    st.markdown(f"""
    <style>
      .auth-card {{
        background: rgba(10, 15, 28, 0.95) !important;
        border: 2px solid var(--primary) !important;
        border-radius: 32px !important;
        padding: 50px 40px !important;
        text-align: center !important;
        box-shadow: 0 40px 100px -20px rgba(0,0,0,1) !important;
        margin-top: 50px;
      }}
      .auth-card * {{
          color: #FFFFFF !important;
      }}
      .auth-card input, .auth-card select {{
          color: #020617 !important;
          font-weight: 700 !important;
      }}
      .auth-title {{
        font-family: 'Syne', sans-serif !important;
        font-size: 52px !important;
        color: #FFFFFF !important;
        letter-spacing: -3px !important;
        margin-bottom: 5px !important;
        font-weight: 800 !important;
        text-shadow: 0 4px 10px rgba(0,0,0,0.5) !important;
      }}
      .auth-subtitle {{
          color: #f8fafc !important;
          font-size: 16px !important;
          margin-bottom: 30px !important;
          text-align: center !important;
          font-weight: 600 !important;
          letter-spacing: 0.1em !important;
          text-transform: uppercase !important;
      }}
      /* Neon Emerald Label Override */
      .auth-card [data-testid="stWidgetLabel"] p {{
          color: var(--primary) !important;
          font-weight: 800 !important;
          font-size: 16px !important;
          margin-bottom: 8px !important;
          text-shadow: 0 0 10px rgba(0, 242, 145, 0.2) !important;
      }}
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div style="margin-top: 50px;"></div>', unsafe_allow_html=True)
    col_a1, col_a2, col_a3 = st.columns([1, 1.5, 1])
    with col_a2:
        st.markdown('<div class="auth-card">', unsafe_allow_html=True)
        st.markdown('<div class="auth-title">TRANALYZE</div>', unsafe_allow_html=True)
        
        tab_login, tab_signup = st.tabs(["Secure Login", "Join the Suite"])
        
        with tab_login:
            st.markdown('<div class="auth-subtitle">Access your professional trading desk</div>', unsafe_allow_html=True)
            email = st.text_input("Email Address", placeholder="trader@tranalyze.com", key="login_email")
            password = st.text_input("Security Password", type="password", placeholder="••••••••", key="login_pass")
            
            st.markdown("<div style='margin-top:20px;'></div>", unsafe_allow_html=True)
            if st.button("Authorize Access", use_container_width=True):
                res = login(email, password)
                if res["success"]:
                    st.session_state.authenticated = True
                    st.session_state.user = res["user"]
                    st.session_state.logging_out = False
                    cookie_manager.set("tranalyze_token", res["user"])
                    st.session_state.watchlist = load_user_watchlist(res["user"]['localId'])
                    st.rerun()
                else:
                    st.error(res["error"])
        
        with tab_signup:
            if not st.session_state.otp_sent:
                st.markdown('<div class="auth-subtitle">Begin your precision analysis journey</div>', unsafe_allow_html=True)
                su_name = st.text_input("Full Name", placeholder="John Doe")
                su_email = st.text_input("Email Address", placeholder="trader@tranalyze.com")
                su_pass = st.text_input("Choose Password", type="password", placeholder="••••••••")
                
                st.markdown("<div style='margin-top:20px;'></div>", unsafe_allow_html=True)
                if st.button("Generate OTP", use_container_width=True):
                    if su_email:
                        st.session_state.otp_sent = True
                        st.session_state.pending_user = {"email": su_email, "pass": su_pass, "phone": "", "name": su_name}
                        generate_otp(su_email, su_email)
                        st.success(f"Security code sent to {su_email}")
                        st.rerun()
                    else:
                        st.warning("Please enter a valid email address.")
                
            else:
                st.markdown('<div class="auth-subtitle">Enter the code from your email</div>', unsafe_allow_html=True)
                otp_code = st.text_input("OTP Code", placeholder="XXXXXX")
                if st.button("Verify & Signup", use_container_width=True):
                    u = st.session_state.pending_user
                    v_res = verify_otp_logic(u["email"], otp_code)
                    if v_res["success"]:
                        res = signup(u["email"], u["pass"], u["phone"], u["name"])
                        if res["success"]:
                            st.session_state.authenticated = True
                            st.session_state.user = res["user"]
                            st.session_state.logging_out = False
                            cookie_manager.set("tranalyze_token", res["user"])
                            st.rerun()
                        else: st.error(res["error"])
                    else: st.error(v_res["error"])
                
                if st.button("Back", use_container_width=True):
                    st.session_state.otp_sent = False
                    st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()


# ─────────────────────────────────────────────────
# ── MAIN APPLICATION ─────────────────────────────
# ─────────────────────────────────────────────────

if st.session_state.authenticated:
    
    # ── Sidebar Navigation Switcher ──────
    with st.sidebar:
        if st.session_state.active_module != "Hub":
            if st.button("🏠 Return to Central Hub", use_container_width=True):
                st.session_state.active_module = "Hub"
                st.rerun()
        st.markdown("---")

    # ── MODULE 1: CENTRAL HUB ────────────
    if st.session_state.active_module == "Hub":
        # ── Market Pulse HUD ─────────────────
        pulse = get_market_pulse()
        if pulse:
            # Custom HTML Pulse Grid
            st.markdown('<div class="pulse-grid">', unsafe_allow_html=True)
            p_cols = st.columns(len(pulse))
            for i, (name, data) in enumerate(pulse.items()):
                with p_cols[i]:
                    st.markdown(f'''
                        <div class="pulse-card" style="min-height: 240px;">
                            <div class="index-name">{name}</div>
                            <div class="index-price">{format_price(data['price'])}</div>
                            <div style="margin-top:10px; padding: 5px; background:rgba(0, 242, 145, 0.05); border-radius:8px; border:1px solid rgba(0, 242, 145, 0.1);">
                                <div style="font-size:10px; color:#94a3b8; font-weight:700; text-transform:uppercase; letter-spacing:0.05em;">🎯 Projected Open</div>
                                <div style="font-size:18px; color:#00f291; font-weight:800;">{format_price(data['projected_open'])}</div>
                            </div>
                            <div style="margin-top:15px; font-size:9px; color:#94a3b8; font-weight:600; opacity:0.7;">Institutional Intelligence Brief (Click)</div>
                        </div>
                    ''', unsafe_allow_html=True)
                    
                    # ── Interactive Global & Sector Intelligence ──
                    st.markdown(f'<div class="popover-{data["pred"].lower()}">', unsafe_allow_html=True)
                    with st.popover(f"{data['pred'].upper()} LIGHT", use_container_width=True):
                        st.markdown(f"### 🌐 {name} Tactical Brief")
                        
                        st.markdown("**🛡️ Intelligence Logic:**")
                        for r in data['reasons']:
                            st.write(f"- {r}")
                        
                        if data.get('headlines'):
                            st.divider()
                            st.markdown("**📰 Industry-Specific Audit:**")
                            for h in data['headlines']:
                                st.caption(f"• {h}")
                        
                        st.divider()
                        st.caption("Intelligence synthesized from Sector Trends, ATR Volatility, and Global Macro correlations.")
                    st.markdown('</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("""
        <div style="text-align:center; padding: 60px 0 30px 0;">
            <h1 style="font-family:'Syne', sans-serif; font-size:52px; font-weight:800; margin-bottom:10px; color: var(--text-main); letter-spacing: -2px;">Select Analysis Module</h1>
            <p style="color: var(--text-sub); font-size:18px; letter-spacing: 0.1em; font-weight: 500;">PRECISION INTELLIGENCE TRADING SUITE</p>
        </div>
        """, unsafe_allow_html=True)

        col_h1, col_h2 = st.columns(2)
        
        with col_h1:
            st.markdown("""
            <div class="hub-card card-pred">
                <span class="hub-icon">🎯</span>
                <div class="hub-title">Master Prediction</div>
                <div class="hub-desc">Deep neural trend analysis, technical indicators, and automated trade signal generation.</div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown('<div class="pred-btn">', unsafe_allow_html=True)
            if st.button("Activate Master Prediction", key="btn_pred", use_container_width=True):
                st.session_state.active_module = "Prediction"
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

            st.markdown("""
            <div class="hub-card card-fund" style="opacity:0.6;">
                <span class="hub-icon">📊</span>
                <div class="hub-title">Fundamental Data</div>
                <div class="hub-desc">Company health metrics, balance sheets, and intrinsic value estimations. (Upcoming)</div>
            </div>
            """, unsafe_allow_html=True)

        with col_h2:
            st.markdown("""
            <div class="hub-card card-port">
                <span class="hub-icon">💼</span>
                <div class="hub-title">Portfolio Tracker</div>
                <div class="hub-desc">Advanced asset management and AI-driven advisory for your holdings.</div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown('<div class="port-btn">', unsafe_allow_html=True)
            if st.button("Activate Portfolio Tracker", key="btn_port", use_container_width=True):
                st.session_state.active_module = "Portfolio"
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

            st.markdown("""
            <div class="hub-card card-news" style="opacity:0.6;">
                <span class="hub-icon">📰</span>
                <div class="hub-title">News Integration</div>
                <div class="hub-desc">Live global market sentiment and high-impact news delivery. (Upcoming)</div>
            </div>
            """, unsafe_allow_html=True)

    # ── MODULE 3: PORTFOLIO TRACKER ──────
    elif st.session_state.active_module == "Portfolio":
        st_autorefresh(interval=300000, key="portfolio_pulse")
        st.markdown('<div class="section-title">Portfolio Tracker & AI Advisor</div>', unsafe_allow_html=True)
        
        # ── 1. Add Position Form ─────────────
        with st.expander("➕ Add New Position to Ledger", expanded=False):
            with st.form("add_pos_form", clear_on_submit=True):
                p_col1, p_col2, p_col3 = st.columns(3)
                with p_col1:
                    p_mkt = st.selectbox("Market Type", list(MARKET_CONFIG.keys()))
                    # Dual Entry Logic
                    p_suggestions = get_all_symbols(p_mkt)
                    ps1, ps2 = st.columns([0.6, 0.4])
                    with ps1:
                        p_manual = st.text_input("Manual Symbol", help="Type any symbol e.g. TMCV, RELIANCE").upper()
                    with ps2:
                        p_suggested = st.selectbox("List", ["--"] + p_suggestions)
                    
                    p_sym = p_suggested if p_suggested != "--" else p_manual
                with p_col2:
                    p_entry = st.number_input("Entry Price", min_value=0.0, step=0.05, format="%.2f")
                    p_qty = st.number_input("Quantity", min_value=0.01, step=1.0)
                with p_col3:
                    p_side = st.selectbox("Position Side", ["Buy", "Sell"])
                    st.markdown("<div style='margin-top:28px;'></div>", unsafe_allow_html=True)
                    p_submit = st.form_submit_button("🚀 Add to Portfolio")
                
                if p_submit and p_sym:
                    new_pos = {
                        "symbol": p_sym,
                        "market": p_mkt,
                        "entry_price": p_entry,
                        "quantity": p_qty,
                        "side": p_side,
                        "status": "Active",
                        "added_at": str(datetime.now())
                    }
                    from auth import save_portfolio_position
                    if save_portfolio_position(st.session_state.user['localId'], new_pos):
                        st.success(f"Position for {p_sym} logged successfully!")
                        time.sleep(0.5)
                        st.rerun()

        # ── 2. Load and Process Data ─────────
        with st.spinner("Synchronizing Portfolio with Market Rates..."):
            active_pos, closed_pos = get_processed_portfolio(st.session_state.user['localId'])
        
        # Global Metrics Summary
        if active_pos:
            total_investment = sum([p['entry_price'] * p['quantity'] for p in active_pos])
            total_pnl = sum([p['pnl'] for p in active_pos])
            pnl_pct = (total_pnl / total_investment * 100) if total_investment > 0 else 0
            
            # Custom styled metrics for maximum visibility
            pnl_color = "#00f291" if total_pnl >= 0 else "#ff3860"
            st.markdown(f"""
            <div class="metric-container">
                <div class="metric-card">
                    <div class="m-label">Total Invested</div>
                    <div class="m-value">{format_price(total_investment)}</div>
                </div>
                <div class="metric-card" style="border-top: 3px solid {pnl_color}; border-bottom: 2px solid {pnl_color}44;">
                    <div class="m-label">Live Un-realized P&L</div>
                    <div class="m-value" style="color: {pnl_color};">{total_pnl:+.2f} ({pnl_pct:+.2f}%)</div>
                </div>
                <div class="metric-card">
                    <div class="m-label">Open Positions</div>
                    <div class="m-value">{len(active_pos)}</div>
                </div>
            </div>
            <style>
                .metric-container {{
                    display: flex;
                    justify-content: space-between;
                    gap: 20px;
                    margin-bottom: 30px;
                    flex-wrap: wrap;
                }}
                .metric-card {{
                    flex: 1;
                    min-width: 200px;
                    background: rgba(30, 41, 59, 0.4);
                    padding: 24px;
                    border-radius: 20px;
                    border: 1px solid rgba(255,255,255,0.05);
                    text-align: center;
                    box-shadow: 0 10px 25px rgba(0,0,0,0.3);
                    backdrop-filter: blur(10px);
                    transition: transform 0.3s ease;
                }}
                .metric-card:hover {{
                    transform: translateY(-5px);
                }}
                .m-label {{
                    color: #94a3b8;
                    font-size: 13px;
                    font-weight: 700;
                    letter-spacing: 0.15em;
                    text-transform: uppercase;
                    margin-bottom: 12px;
                }}
                .m-value {{
                    color: #ffffff;
                    font-family: 'Syne', sans-serif;
                    font-size: 30px;
                    font-weight: 800;
                }}
            </style>
            """, unsafe_allow_html=True)

            # ── PDF Report Export ──────
            st.markdown("<div style='margin-bottom:15px;'></div>", unsafe_allow_html=True)
            try:
                pdf_bytes = generate_portfolio_pdf(active_pos, closed_pos, "TRANALYZE")
                st.download_button(
                    label="📥 Download Executive Portfolio Report (PDF)",
                    data=bytes(pdf_bytes),
                    file_name=f"TRANALYZE_Report_{datetime.now().strftime('%Y%m%d')}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"PDF Engine Error: {str(e)}")

        # ── 3. Active Positions (A-Z) ────────
        st.markdown('<div class="section-title">Active Positions (A-Z Order)</div>', unsafe_allow_html=True)
        if not active_pos:
            st.info("No active positions found. Use the form above to add your first trade!")
        else:
            for p in active_pos:
                with st.container():
                    pnl_color = "#00f291" if p['pnl'] >= 0 else "#ff3860"
                    st.markdown(f"""
                    <div style="background:rgba(15, 23, 42, 0.6); padding:24px; border-radius:20px; border:1px solid rgba(255,255,255,0.05); margin-bottom:15px; border-left: 4px solid {pnl_color};">
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
                            <div>
                                <span style="font-family:Syne, sans-serif; font-size:22px; font-weight:800; color:#fff;">{p['symbol']}</span>
                                <span style="font-size:12px; color:#64748b; margin-left:12px; letter-spacing:0.1em;">{p['side'].upper()} · Qty: {p['quantity']}</span>
                            </div>
                            <div style="text-align:right;">
                                <div style="font-size:20px; font-weight:800; color:{pnl_color};">{p['pnl']:+.2f} ({p['pnl_pct']:+.2f}%)</div>
                                <div style="font-size:11px; color:#94a3b8;">Entry: {p['entry_price']} | Current: {p['current_price']}</div>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Recommendation and Close Action
                    adv_col, act_col = st.columns([0.75, 0.25])
                    with adv_col:
                        with st.expander("🧠 AI Advisor - Tactical Recommendation", expanded=False):
                            from portfolio_logic import get_ai_advice
                            advice = get_ai_advice(p['symbol'], p['market'], p['entry_price'], p['side'])
                            st.markdown(advice)
                    with act_col:
                        if st.button("Close Trade 🏁", key=f"close_{p['id']}", use_container_width=True):
                            from auth import update_portfolio_position
                            update_portfolio_position(st.session_state.user['localId'], p['id'], {
                                "status": "Closed",
                                "close_price": p['current_price'],
                                "closed_at": str(datetime.now()),
                                "realized_pnl": p['pnl']
                            })
                            st.success(f"Position for {p['symbol']} exited successfully!")
                            time.sleep(0.5)
                            st.rerun()

        # ── 4. Closed Trade History ──────────
        if closed_pos:
            st.markdown('<div class="section-title">Trade History (Realized Gains/Losses)</div>', unsafe_allow_html=True)
            hist_df = pd.DataFrame(closed_pos)
            hist_df = hist_df.sort_values(by="closed_at", ascending=False)
            
            # Formatted view
            for _, rp in hist_df.iterrows():
                r_pnl = float(rp['realized_pnl'])
                r_color = "#00f291" if r_pnl >= 0 else "#ff3860"
                st.markdown(f"""
                <div style="background:rgba(30, 41, 59, 0.2); padding:10px 20px; border-radius:12px; border:1px solid rgba(255,255,255,0.03); margin-bottom:8px; font-size:13px; display:flex; justify-content:space-between;">
                    <span><b>{rp['symbol']}</b> ({rp['side']}) | Closed at: {rp['close_price']} | Date: {str(rp['closed_at'])[:10]}</span>
                    <span style="color:{r_color}; font-weight:700;">{r_pnl:+.2f}</span>
                </div>
                """, unsafe_allow_html=True)

    # ── MODULE 2: MASTER PREDICTION (EXISTING DASHBOARD) ──
    elif st.session_state.active_module == "Prediction":
        
        # ── Watchlist Redirection Handler ────
        for i, item in enumerate(st.session_state.watchlist):
            if f"wl_btn_{i}" in st.session_state and st.session_state[f"wl_btn_{i}"]:
                st.session_state.current_market = item['market']
                st.session_state.current_symbol = item['symbol']
                st.rerun()

        # ── Sidebar Controls ─────────────────
        with st.sidebar:
            st.image("logo.png", use_container_width=True)
            st.markdown('<div style="text-align:center; font-size:9px; color:#64748b; letter-spacing:0.15em; margin-bottom:20px; font-weight:600;">TREND ANALYZE</div>', unsafe_allow_html=True)

            st.markdown('<div class="section-title">My Profile</div>', unsafe_allow_html=True)
            if "user" in st.session_state:
                u_info = get_user_data(st.session_state.user['localId'])
                u_name = u_info['name'] if u_info else "Trader"
                st.markdown(f'<div style="background:rgba(255,255,255,0.03); padding:12px; border-radius:10px; border:1px solid rgba(255,255,255,0.05); margin-bottom:10px;"><div style="font-size:14px; font-weight:700; color:#00f291;">{u_name}</div><div style="font-size:11px; color:#64748b;">UID: ...{st.session_state.user["localId"][-6:]}</div></div>', unsafe_allow_html=True)
                if st.button("🚪 Logout", use_container_width=True):
                    st.session_state.authenticated = False
                    st.rerun()

            st.markdown('<div class="section-title">Market & Symbol</div>', unsafe_allow_html=True)
            market_list = list(MARKET_CONFIG.keys())
            m_idx = market_list.index(st.session_state.current_market) if st.session_state.current_market in market_list else 0
            
            def on_market_change():
                st.session_state.current_market = st.session_state.m_selector
                st.session_state.current_symbol = MARKET_CONFIG[st.session_state.m_selector]["default"]

            market = st.selectbox("Market", market_list, index=m_idx, key="m_selector", on_change=on_market_change)
            cfg = MARKET_CONFIG[market]
            suggestions = get_all_symbols(market)

            # Manual Symbol Entry + Suggestion List
            col_s1, col_s2 = st.columns([0.65, 0.35])
            with col_s1:
                manual_ticker = st.text_input("Manual Symbol", value=st.session_state.current_symbol, help="Type any symbol e.g. RELIANCE, TMCV").upper()
            with col_s2:
                suggested_ticker = st.selectbox("List", ["--"] + suggestions, label_visibility="visible")
            
            # If a suggestion is picked, it overrides manual
            if suggested_ticker != "--":
                st.session_state.current_symbol = suggested_ticker
            else:
                st.session_state.current_symbol = manual_ticker

            selected_ticker = st.session_state.current_symbol

            st.markdown('<div class="section-title">Timeframe & Range</div>', unsafe_allow_html=True)
            tf_label = st.selectbox("Timeframe", list(TIMEFRAME_MAP.keys()), index=5)
            interval, _ = TIMEFRAME_MAP[tf_label]
            valid_ranges = get_valid_ranges(interval)
            r_label = st.selectbox("Range", valid_ranges, index=min(3, len(valid_ranges)-1))
            period = RANGE_MAP[r_label]

            st.markdown('<div class="section-title">Visuals & ML</div>', unsafe_allow_html=True)
            show_ma = st.checkbox("MAs", True)
            show_bb = st.checkbox("Bollinger", True)
            show_rsi = st.checkbox("RSI", True)
            show_macd = st.checkbox("MACD", True)
            run_ml = st.checkbox("Run ML Prediction", True)
            ml_model = st.selectbox("Model", ["Linear Regression", "Random Forest"])

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
            
            analyze_btn = st.button("🔍 ANALYZE", use_container_width=True)

            st.markdown('<div class="section-title">Watchlist</div>', unsafe_allow_html=True)
            col_a, col_c = st.columns(2)
            with col_a:
                if st.button("＋ Add", use_container_width=True):
                    entry = {"symbol": selected_ticker, "market": market}
                    if entry not in st.session_state.watchlist:
                        st.session_state.watchlist.append(entry)
                        save_user_watchlist(st.session_state.user['localId'], st.session_state.watchlist)
                        st.rerun()
            with col_c:
                if st.button("Clear", use_container_width=True):
                    st.session_state.watchlist = []
                    save_user_watchlist(st.session_state.user['localId'], st.session_state.watchlist)
                    st.rerun()

            # Clickable Watchlist Items with Delete option
            for i, item in enumerate(st.session_state.watchlist):
                label = f"📁 {item['symbol']} | {item['market']}"
                wl_col_nav, wl_col_del = st.columns([0.85, 0.15])
                
                with wl_col_nav:
                    if st.button(label, key=f"wl_btn_{i}", use_container_width=True):
                        st.session_state.current_market = item['market']
                        st.session_state.current_symbol = item['symbol']
                        st.rerun()
                
                with wl_col_del:
                    if st.button("🗑️", key=f"wl_del_{i}", use_container_width=True, help="Remove from watchlist"):
                        st.session_state.watchlist.pop(i)
                        save_user_watchlist(st.session_state.user['localId'], st.session_state.watchlist)
                        st.rerun()

        # ── Dashboard Header ─────────────────
        head_col1, head_col2 = st.columns([0.1, 0.9])
        with head_col1: st.image("logo.png", width=60)
        with head_col2:
            st.markdown('<div class="tranalyze-header"><span class="tranalyze-logo">TRANALYZE</span><span class="tranalyze-sub">Trend Analyze — Educational Trading Dashboard</span></div>', unsafe_allow_html=True)

        # ── Analysis Logic ───────────────────
        symbol = convert_symbol(selected_ticker, market)
        with st.spinner(f"Analyzing {symbol}..."):
            df_raw = fetch_data(symbol, interval, period)
            if not df_raw.empty:
                df = apply_all_indicators(df_raw, show_ma, show_rsi, show_macd, show_bb)
                patterns = detect_all_patterns(df)
                signal_res = generate_signal(df, patterns)
                ticker_info = fetch_ticker_info(symbol)
                metrics = get_summary_metrics(df)
                
                ml_result = {}
                if run_ml: ml_result = train_and_predict(df, ml_model)
                adv_analysis = get_expert_analysis(df, ml_result)

                # NEWS SENTIMENT INTEGRATION
                s_score, s_status, headlines = get_news_sentiment(symbol)
                s_color = "#00f291" if s_score > 0 else "#ff3860" if s_score < 0 else "#94a3b8"

                # Summary Header
                chg = metrics['pct_change']
                st.markdown(f'''
                    <div style="display:flex; align-items:center; gap:16px; margin-bottom:24px; padding: 20px; background: rgba(30, 41, 59, 0.4); border-radius: 16px; border: 1px solid rgba(255,255,255,0.05);">
                        <div style="flex-grow: 1;">
                            <div style="font-family:Syne,sans-serif; font-size:32px; font-weight:800; color:#fff; letter-spacing:-1px;">{ticker_info.get("name", symbol)}</div>
                            <div style="font-size:13px; color:#94a3b8; letter-spacing:0.05em;">{symbol} · {market}</div>
                        </div>
                        <div style="text-align: right;">
                            <div style="font-size:24px; font-weight:800; color:{'#00f291' if chg>=0 else '#ff3860'};">{format_price(metrics['current_price'])}</div>
                            <div style="font-size:12px; font-weight:700; color:{s_color}; background:rgba(255,255,255,0.03); padding:4px 10px; border-radius:30px; border:1px solid {s_color}; margin-top:5px; display:inline-block;">{s_status}</div>
                        </div>
                    </div>
                ''', unsafe_allow_html=True)
                # ── GOOGLE LIVE SYNC VERIFICATION ─────────────────
                g_col_text, g_col_act = st.columns([0.7, 0.3])
                with g_col_act:
                    if st.button("🌐 Verify Live Price (Google Finance)", use_container_width=True, help="Fetch absolute real-time price from Google Finance"):
                        with st.spinner("Polling Google Feed..."):
                            g_price = get_google_price(selected_ticker, market)
                            if g_price:
                                gap = g_price - metrics['current_price']
                                st.markdown(f'''
                                    <div style="background:rgba(66, 133, 244, 0.1); border:1px solid #4285f4; padding:12px; border-radius:12px; text-align:center; margin-bottom:10px;">
                                        <div style="font-size:10px; color:#4285f4; font-weight:800; text-transform:uppercase;">Google Verified Price</div>
                                        <div style="font-size:22px; font-weight:800; color:#fff;">{format_price(g_price)}</div>
                                        <div style="font-size:11px; color:#94a3b8;">Gap: {gap:+.2f} vs Yahoo</div>
                                    </div>
                                ''', unsafe_allow_html=True)
                            else:
                                st.warning("Google Sync temporarily restricted.")
                    
                    # External Portal Button
                    g_exch_link = "NSE" if market=="NSE" else "BOM" if market=="BSE" else "NASDAQ"
                    g_url_final = f"https://www.google.com/finance/quote/{selected_ticker.split('.')[0]}:{g_exch_link}"
                    st.markdown(f'<a href="{g_url_final}" target="_blank" style="text-decoration:none;"><button style="width:100%; padding:10px; background:rgba(66, 133, 244, 0.1); border:1px solid #4285f4; border-radius:12px; color:#4285f4; font-weight:800; cursor:pointer; text-transform:uppercase; font-size:10px; letter-spacing:0.1em;">View on G-Finance 🔗</button></a>', unsafe_allow_html=True)

                # Tabs
                t_chart, t_master, t_signal, t_ml, t_patterns, t_backtest, t_data = st.tabs(["📊 Chart", "🧠 Master", "🎯 Signal", "🤖 ML", "🕯️ Patterns", "⏱️ Backtest", "📋 Data"])

                with t_chart:
                    # Filter patterns based on the sidebar selection
                    filtered_patterns = {name: series for name, series in patterns.items() if name in selected_candles}
                    fig = build_chart(df, symbol, show_ma, show_bb, show_rsi, show_macd, filtered_patterns, adv_analysis)
                    st.plotly_chart(fig, use_container_width=True)

                with t_master:
                    st.markdown("### 🧠 Expert System Analysis")
                    st.markdown(adv_analysis["analysis"])
                    c_s, c_r = st.columns(2)
                    with c_s: 
                        st.write("**Support Levels**")
                        for x in adv_analysis["support"]:
                            st.write(f"₹{x:.2f}")
                    with c_r: 
                        st.write("**Resistance Levels**")
                        for x in adv_analysis["resistance"]:
                            st.write(f"₹{x:.2f}")
                    
                    st.divider()
                    st.markdown("### 📰 Market News Audit")
                    if headlines:
                        for h in headlines[:3]:
                            st.info(h)
                    else:
                        st.info("No recent high-impact headlines detected for this asset.")

                with t_signal:
                    st.markdown(f'### Prediction Signal: <span class="signal-badge signal-{signal_res["signal"]}">{signal_res["signal"]}</span>', unsafe_allow_html=True)
                    st.write(f"Confidence Score: {signal_res['score']}/5")
                    for r in signal_res["reasons"]: st.write(f"- {r}")

                with t_ml:
                    if run_ml and "error" not in ml_result:
                        st.markdown(f"""
                        <div class="ml-card">
                            <div class="ml-label">Predicted Next Close</div>
                            <div class="ml-price">{format_price(ml_result["predicted_price"])}</div>
                            <div style="font-size:12px; color:#64748b; font-weight:600;">Model: {ml_model}</div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        col_m1, col_m2 = st.columns(2)
                        with col_m1:
                            st.write(f"**Confidence Level:** {ml_result['confidence']}")
                        with col_m2:
                            st.write(f"**Model R² Score:** {ml_result['r2']:.4f}")
                    else: 
                        st.info("ML Prediction disabled or error occurred.")

                with t_patterns:
                    p_summary = get_pattern_summary(df)
                    if p_summary: st.dataframe(pd.DataFrame(p_summary), use_container_width=True)
                    else: st.info("No patterns detected in current range.")

                with t_backtest:
                    with st.spinner("Simulating MA Crossover..."):
                        # Use sidebar sliders if they exist, otherwise defaults
                        # (Sidebar actually has them if run_backtest is checked, but let's just use defaults to be safe manually since I simplified sidebar)
                        bt = run_ma_crossover_backtest(df_raw, fast_period=20, slow_period=50)
                        if "error" not in bt:
                            st.markdown(f"**Total P&L:** ₹{bt['total_pnl']:,.2f} ({bt['total_return_pct']:+.2f}%)")
                            st.write(f"Win Rate: {bt['win_rate_pct']:.1f}% | Capital: ₹{bt['initial_capital']:,.0f}")
                            
                            if not bt["portfolio_series"].empty:
                                import plotly.graph_objects as go
                                fig_ps = go.Figure(go.Scatter(x=bt["portfolio_series"].index, y=bt["portfolio_series"].values, line=dict(color="#00f291")))
                                fig_ps.update_layout(title="Equity Curve", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=250)
                                st.plotly_chart(fig_ps, use_container_width=True)
                        else:
                            st.warning(bt["error"])

                with t_data:
                    st.dataframe(df.sort_index(ascending=False).head(100), use_container_width=True)
                    st.download_button("Download CSV", df.to_csv(), f"{symbol}.csv")

            else:
                st.error("No data found for this symbol/range.")