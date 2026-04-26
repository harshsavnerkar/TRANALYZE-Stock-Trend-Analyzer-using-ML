import pandas as pd
import numpy as np
from scipy.signal import find_peaks

def find_peaks_troughs(df):
    size = len(df)
    window = max(3, min(15, int(size * 0.035)))
    peaks, _ = find_peaks(df['High'].values, distance=window)
    troughs, _ = find_peaks(-df['Low'].values, distance=window)
    return peaks, troughs

def detect_support_resistance(df):
    peaks, troughs = find_peaks_troughs(df)
    res_lvls = df['High'].iloc[peaks].values
    sup_lvls = df['Low'].iloc[troughs].values
    def cluster(levels, pct=0.005): # Tightened for Forex/High Precision
        if not len(levels): return []
        lvls = sorted(levels)
        clusters = []; curr_cluster = [lvls[0]]
        for i in range(1, len(lvls)):
            if (lvls[i] - lvls[i-1])/lvls[i-1] < pct: curr_cluster.append(lvls[i])
            else: clusters.append(np.mean(curr_cluster)); curr_cluster = [lvls[i]]
        clusters.append(np.mean(curr_cluster))
        return clusters
    curr = df['Close'].iloc[-1]
    res_raw = cluster(res_lvls); sup_raw = cluster(sup_lvls)
    # Catch levels as close as 0.05% away
    res = sorted([r for r in res_raw if r > curr * 1.0005], key=lambda x: abs(x-curr))[:3]
    sup = sorted([s for s in sup_raw if s < curr * 0.9995], key=lambda x: abs(x-curr))[:3]
    return sorted(res), sorted(sup)

# ── A. REVERSAL PATTERNS ──────────────────────

def detect_double_bottom(df, tr):
    if len(tr) < 2: return None
    t1, t2 = tr[-2], tr[-1]
    v1, v2 = df['Low'].iloc[t1], df['Low'].iloc[t2]
    if abs(v1-v2)/min(v1,v2) < 0.04:
        return {"name": "Double Bottom", "type": "bullish", "points": [(df.index[t1],v1),(df.index[t2],v2)]}
    return None

def detect_double_top(df, pk):
    if len(pk) < 2: return None
    p1, p2 = pk[-2], pk[-1]
    v1, v2 = df['High'].iloc[p1], df['High'].iloc[p2]
    if abs(v1-v2)/min(v1,v2) < 0.04:
        return {"name": "Double Top", "type": "bearish", "points": [(df.index[p1],v1),(df.index[p2],v2)]}
    return None

def detect_triple_bottom(df, tr):
    if len(tr) < 3: return None
    t1, t2, t3 = tr[-3], tr[-2], tr[-1]
    v1, v2, v3 = df['Low'].iloc[t1], df['Low'].iloc[t2], df['Low'].iloc[t3]
    if abs(v1-v2)/v1 < 0.04 and abs(v2-v3)/v2 < 0.04:
        return {"name": "Triple Bottom", "type": "bullish", "points": [(df.index[t1],v1),(df.index[t2],v2),(df.index[t3],v3)]}
    return None

def detect_triple_top(df, pk):
    if len(pk) < 3: return None
    p1, p2, p3 = pk[-3], pk[-2], pk[-1]
    v1, v2, v3 = df['High'].iloc[p1], df['High'].iloc[p2], df['High'].iloc[p3]
    if abs(v1-v2)/v1 < 0.04 and abs(v2-v3)/v2 < 0.04:
        return {"name": "Triple Top", "type": "bearish", "points": [(df.index[p1],v1),(df.index[p2],v2),(df.index[p3],v3)]}
    return None

def detect_head_and_shoulders(df, pk):
    if len(pk) < 3: return None
    p1, p2, p3 = pk[-3:]
    v1, v2, v3 = df['High'].iloc[p1], df['High'].iloc[p2], df['High'].iloc[p3]
    if v2 > v1 * 1.02 and v2 > v3 * 1.02:
        return {"name": "Head and Shoulders", "type": "bearish", "points": [(df.index[p1],v1),(df.index[p2],v2),(df.index[p3],v3)]}
    return None

def detect_inverse_h_s(df, tr):
    if len(tr) < 3: return None
    t1, t2, t3 = tr[-3:]
    v1, v2, v3 = df['Low'].iloc[t1], df['Low'].iloc[t2], df['Low'].iloc[t3]
    if v2 < v1 * 0.98 and v2 < v3 * 0.98:
        return {"name": "Inverse Head and Shoulders", "type": "bullish", "points": [(df.index[t1],v1),(df.index[t2],v2),(df.index[t3],v3)]}
    return None

def detect_cup_handle(df, tr):
    if len(tr) < 5: return None
    v = df['Low'].iloc[tr[-5:]].values
    if v[2] < v[0] and v[2] < v[-1]:
        return {"name": "Cup and Handle", "type": "bullish", "points": [(df.index[i],df['Low'].iloc[i]) for i in tr[-5:]]}
    return None

# ── B. CONTINUATION PATTERNS ──────────────────

def detect_flags(df):
    if len(df) < 15: return None
    pole = (df['Close'].iloc[-5] - df['Close'].iloc[-12]) / df['Close'].iloc[-12]
    if pole > 0.05: return {"name": "Bullish Flag", "type": "bullish", "points": []}
    if pole < -0.05: return {"name": "Bearish Flag", "type": "bearish", "points": []}
    return None

def detect_triangles(df, pk, tr):
    if len(pk) < 2 or len(tr) < 2: return None
    p1, p2 = pk[-2], pk[-1]; t1, t2 = tr[-2], tr[-1]
    # Ascending
    if abs(df['High'].iloc[p1]-df['High'].iloc[p2])/df['High'].iloc[p1] < 0.02 and df['Low'].iloc[t2] > df['Low'].iloc[t1]:
        return {"name": "Ascending Triangle", "type": "bullish", "points": []}
    # Descending
    if abs(df['Low'].iloc[t1]-df['Low'].iloc[t2])/df['Low'].iloc[t1] < 0.02 and df['High'].iloc[p2] < df['High'].iloc[p1]:
        return {"name": "Descending Triangle", "type": "bearish", "points": []}
    return None

def detect_wedges(df, pk, tr):
    if len(pk) < 2 or len(tr) < 2: return None
    if df['High'].iloc[pk[-1]] > df['High'].iloc[pk[-2]] and df['Low'].iloc[tr[-1]] > df['Low'].iloc[tr[-2]]:
        return {"name": "Rising Wedge", "type": "bearish", "points": []}
    if df['High'].iloc[pk[-1]] < df['High'].iloc[pk[-2]] and df['Low'].iloc[tr[-1]] < df['Low'].iloc[tr[-2]]:
        return {"name": "Falling Wedge", "type": "bullish", "points": []}
    return None

# ── C. ADVANCED ───────────────────────────────

def detect_diamond(df, pk):
    if len(pk) < 4: return None
    v = df['High'].iloc[pk[-4:]].values
    if v[1] > v[0] and v[2] < v[1]: return {"name": "Diamond Top", "type": "bearish", "points": []}
    return None

# ── MASTER EXPERT LOGIC ──────────────────────

def get_expert_analysis(df, ml_result):
    pk, tr = find_peaks_troughs(df)
    found = []
    
    # Run all detections
    checks = [
        detect_double_top(df, pk), detect_double_bottom(df, tr),
        detect_triple_top(df, pk), detect_triple_bottom(df, tr),
        detect_head_and_shoulders(df, pk), detect_inverse_h_s(df, tr),
        detect_cup_handle(df, tr), detect_flags(df),
        detect_triangles(df, pk, tr), detect_wedges(df, pk, tr),
        detect_diamond(df, pk)
    ]
    for c in checks:
        if c: found.append(c)

    res, sup = detect_support_resistance(df)
    ml_pred = ml_result.get('predicted_price', 0)
    curr = df['Close'].iloc[-1]
    ml_trend = "BULLISH" if ml_pred > curr else "BEARISH"
    
    return {
        "patterns": found, # ALL found patterns
        "support": sup, "resistance": res,
        "analysis": f"Detected {len(found)} structural patterns." if found else "No grand patterns.",
        "congruence": "HIGH" if found and found[-1]['type'].upper() == ml_trend else "Mixed"
    }
