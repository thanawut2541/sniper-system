"""
Private Sniper System V1.0 — Web App (Streamlit)
รันบน Browser / มือถือ ผ่าน Streamlit Cloud
"""

import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import sys
import os
from datetime import datetime

# ── Path setup so we can import core modules ──────────────────────
sys.path.insert(0, os.path.dirname(__file__))

from data.twelvedata_feed import TwelveDataFeed
from core.signal_engine import SignalEngine
from core.volume_profile import VolumeProfile
from core.risk_manager import RiskManager
from core.compounding import CompoundingCalculator

# ══════════════════════════════════════════════════════════════════
#  PAGE CONFIG
# ══════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="🎯 Private Sniper System",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── Custom CSS (Dark theme + mobile friendly) ─────────────────────
st.markdown("""
<style>
    /* Dark background */
    .stApp { background-color: #0d1117; color: #e6edf3; }
    .main .block-container { padding: 1rem 1rem 1rem 1rem; max-width: 100%; }

    /* Hide default streamlit elements */
    #MainMenu, footer, header { visibility: hidden; }

    /* Signal box */
    .signal-box {
        border-radius: 12px;
        padding: 16px 20px;
        text-align: center;
        font-weight: bold;
        font-size: 1.4rem;
        margin-bottom: 12px;
        border: 2px solid;
    }
    .signal-standby  { background: #ffc10722; border-color: #ffc107; color: #ffc107; }
    .signal-testing  { background: #ff910022; border-color: #ff9100; color: #ff9100; }
    .signal-buy      { background: #00e67622; border-color: #00e676; color: #00e676; }
    .signal-sell     { background: #00e67622; border-color: #00e676; color: #00e676; }
    .signal-locked   { background: #ff174422; border-color: #ff1744; color: #ff1744; }

    /* Win probability bar */
    .win-bar-wrap { background: #1c2333; border-radius: 8px; height: 28px; margin: 8px 0; }
    .win-bar-inner { border-radius: 8px; height: 28px; display: flex; align-items: center;
                     padding-left: 12px; font-weight: bold; font-size: 1rem; transition: width 0.5s; }

    /* Info cards */
    .info-card {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 10px;
        padding: 12px 16px;
        margin-bottom: 8px;
    }
    .info-label { color: #8b949e; font-size: 0.8rem; margin-bottom: 2px; }
    .info-value { color: #e6edf3; font-size: 1.1rem; font-weight: bold; }

    /* Price level rows */
    .price-row {
        display: flex; justify-content: space-between; align-items: center;
        padding: 6px 0; border-bottom: 1px solid #21262d;
        font-size: 0.9rem;
    }
    .price-label { color: #8b949e; }
    .price-value { font-weight: bold; font-family: monospace; }

    /* Header */
    .app-header {
        background: linear-gradient(135deg, #161b22, #1c2333);
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 12px 20px;
        margin-bottom: 16px;
        display: flex; align-items: center; justify-content: space-between;
    }
    .app-title { font-size: 1.3rem; font-weight: bold; color: #58a6ff; }
    .live-badge {
        background: #00e67622; border: 1px solid #00e676;
        border-radius: 20px; padding: 4px 12px;
        color: #00e676; font-size: 0.8rem; font-weight: bold;
    }

    /* Mobile-friendly buttons */
    .stButton > button {
        background: #21262d; color: #e6edf3; border: 1px solid #30363d;
        border-radius: 8px; padding: 8px 16px; width: 100%;
    }
    .stButton > button:hover { background: #30363d; border-color: #58a6ff; }

    /* Table */
    .comp-table { width: 100%; border-collapse: collapse; font-size: 0.82rem; }
    .comp-table th { background: #1c2333; color: #8b949e; padding: 6px 8px; text-align: right; }
    .comp-table th:first-child { text-align: center; }
    .comp-table td { padding: 5px 8px; border-bottom: 1px solid #21262d;
                     color: #e6edf3; text-align: right; }
    .comp-table td:first-child { text-align: center; color: #58a6ff; font-weight: bold; }
    .comp-table tr:hover td { background: #21262d; }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════
#  SESSION STATE INIT
# ══════════════════════════════════════════════════════════════════
@st.cache_resource
def get_engines():
    return {
        'feed':       TwelveDataFeed("EUR/USD", "7d1d88bd94fa4ba0bdabf73846f779bb"),
        'signal':     SignalEngine(),
        'vp':         VolumeProfile(),
        'risk':       RiskManager(),
        'compounding': CompoundingCalculator(),
    }

engines = get_engines()

if 'daily_losses' not in st.session_state:
    st.session_state.daily_losses = 0
if 'wins' not in st.session_state:
    st.session_state.wins = 0
if 'losses' not in st.session_state:
    st.session_state.losses = 0
if 'is_locked' not in st.session_state:
    st.session_state.is_locked = False


# ══════════════════════════════════════════════════════════════════
#  FETCH DATA
# ══════════════════════════════════════════════════════════════════
@st.cache_data(ttl=60)   # cache 60 seconds — avoids burning API credits
def load_candles():
    feed = TwelveDataFeed("EUR/USD", "7d1d88bd94fa4ba0bdabf73846f779bb")
    return feed.fetch_historical_data(120)

candles = load_candles()
recent  = candles[-24:] if len(candles) >= 24 else candles

# ── Signal & Volume ───────────────────────────────────────────────
vp_data     = engines['vp'].calculate_profile(recent)
vp_display  = engines['vp'].get_profile_for_display(recent)
vol_confirm = engines['vp'].check_volume_expansion(recent, recent[-1]['volume'] if recent else 0)

signal = engines['signal'].evaluate_signal(recent, recent[-1] if recent else {}, vol_confirm)
state  = signal.get('state', 'STANDBY')

entry_levels = {}
if 'EXECUTE' in state and signal.get('entry'):
    direction = 'BUY' if 'BUY' in state else 'SELL'
    entry_levels = engines['risk'].calculate_entry_levels(signal['entry'], direction)

# ── Win probability ───────────────────────────────────────────────
def calc_win_pct(candles, signal, vp_data):
    score, reasons = 0, []
    state = signal.get('state', 'STANDBY')

    if 'EXECUTE' in state:
        score += 40; reasons.append(('✓ แท่ง H1 ยืนยัน Breakout', '#00e676'))
    elif state == 'TESTING_ZONE':
        score += 15; reasons.append(('~ อยู่ใน Buffer Zone', '#ff9100'))
    else:
        reasons.append(('✗ ราคาอยู่ในกรอบ Daily', '#ff4444'))

    if len(candles) >= 5:
        vols = [c['volume'] for c in candles[-20:]]
        avg  = np.mean(vols[:-1]) or 1
        ratio = vols[-1] / avg
        if ratio >= 1.5:
            score += min(30, int((ratio - 1) * 20))
            reasons.append((f'✓ Volume {ratio:.1f}x เฉลี่ย', '#00e676'))
        else:
            reasons.append((f'✗ Volume ต่ำ ({ratio:.1f}x)', '#ff4444'))

    if vp_data and vp_data.get('poc_price'):
        poc   = vp_data['poc_price']
        entry = signal.get('entry') or candles[-1]['close']
        dh    = signal.get('daily_high', candles[-1]['close'])
        dl    = signal.get('daily_low',  candles[-1]['close'])
        rng   = (dh - dl) or 0.001
        d     = abs(entry - poc) / rng
        if d < 0.15:
            score += 20; reasons.append((f'✓ ใกล้ POC มาก ({poc:.5f})', '#00e676'))
        elif d < 0.35:
            score += 10; reasons.append(('~ ห่าง POC พอรับได้', '#ffc107'))
        else:
            reasons.append(('✗ ห่าง POC เยอะ', '#ff9100'))

    h = datetime.now().hour
    if 14 <= h < 23:
        score += 10; reasons.append(('✓ อยู่ในเวลาเทรด 14–23', '#00e676'))
    else:
        reasons.append(('✗ นอกเวลาเทรด', '#ff4444'))

    return min(score, 100), reasons

win_pct, reasons = calc_win_pct(candles, signal, vp_data)


# ══════════════════════════════════════════════════════════════════
#  HEADER
# ══════════════════════════════════════════════════════════════════
now_str = datetime.now().strftime('%d/%m/%Y  %H:%M:%S')
st.markdown(f"""
<div class="app-header">
    <div>
        <div class="app-title">🎯 PRIVATE SNIPER SYSTEM V1.0</div>
        <div style="color:#8b949e; font-size:0.8rem;">ระบบคัดกรองสัญญาณเทรดเบรคเอาท์ | {now_str}</div>
    </div>
    <div class="live-badge">🟢 LIVE: Twelve Data (EUR/USD)</div>
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════
#  LAYOUT: Chart (left) | Dashboard (right)
# ══════════════════════════════════════════════════════════════════
col_chart, col_dash = st.columns([3, 1.1])

# ─────────────────────────────────────────────────────────────────
#  CHART (Plotly candlestick)
# ─────────────────────────────────────────────────────────────────
with col_chart:
    if candles:
        display = candles[-48:]
        times  = [c['time']   for c in display]
        opens  = [c['open']   for c in display]
        highs  = [c['high']   for c in display]
        lows   = [c['low']    for c in display]
        closes = [c['close']  for c in display]
        vols   = [c['volume'] for c in display]
        colors = ['#00e676' if c >= o else '#ff1744' for o, c in zip(opens, closes)]

        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            row_heights=[0.82, 0.18],
            vertical_spacing=0.03
        )

        # Candlesticks
        fig.add_trace(go.Candlestick(
            x=times, open=opens, high=highs, low=lows, close=closes,
            name='EUR/USD H1',
            increasing_line_color='#00e676', increasing_fillcolor='#00e676',
            decreasing_line_color='#ff1744', decreasing_fillcolor='#ff1744',
            line_width=1
        ), row=1, col=1)

        # Volume bars
        fig.add_trace(go.Bar(
            x=times, y=vols,
            name='Volume', marker_color=colors, opacity=0.6, showlegend=False
        ), row=2, col=1)

        # Daily H/L lines
        dh = signal.get('daily_high')
        dl = signal.get('daily_low')
        bh = signal.get('buffer_high')
        bl = signal.get('buffer_low')

        if dh:
            fig.add_hline(y=dh, line_dash='dash', line_color='#ffc107',
                          line_width=1.2, row=1, col=1,
                          annotation_text=f'Daily H: {dh:.5f}',
                          annotation_font_color='#ffc107',
                          annotation_position='top left')
        if dl:
            fig.add_hline(y=dl, line_dash='dash', line_color='#ffc107',
                          line_width=1.2, row=1, col=1,
                          annotation_text=f'Daily L: {dl:.5f}',
                          annotation_font_color='#ffc107',
                          annotation_position='bottom left')

        # Buffer zones
        if dh and bh:
            fig.add_hrect(y0=dh, y1=bh, fillcolor='#ff9100', opacity=0.07,
                          line_width=0, row=1, col=1)
        if dl and bl:
            fig.add_hrect(y0=bl, y1=dl, fillcolor='#ff9100', opacity=0.07,
                          line_width=0, row=1, col=1)

        # POC line
        poc = vp_data.get('poc_price') if vp_data else None
        if poc:
            fig.add_hline(y=poc, line_dash='dot', line_color='#bc8cff',
                          line_width=1.3, row=1, col=1,
                          annotation_text=f'POC: {poc:.5f}',
                          annotation_font_color='#bc8cff',
                          annotation_position='top right')

        # Entry / SL / TP
        if 'EXECUTE' in state and entry_levels:
            for val, lbl, col in [
                (entry_levels.get('entry'), 'ENTRY', '#58a6ff'),
                (entry_levels.get('sl'),    'SL',    '#ff1744'),
                (entry_levels.get('tp'),    'TP',    '#00e676'),
            ]:
                if val:
                    fig.add_hline(y=val, line_color=col, line_width=1.6,
                                  row=1, col=1,
                                  annotation_text=f'{lbl}: {val:.5f}',
                                  annotation_font_color=col,
                                  annotation_position='right')

        # Chart styling
        fig.update_layout(
            height=520,
            paper_bgcolor='#0d1117',
            plot_bgcolor='#0d1117',
            font=dict(color='#8b949e', size=11),
            margin=dict(l=10, r=10, t=10, b=10),
            xaxis_rangeslider_visible=False,
            legend=dict(x=0, y=1, bgcolor='#0d1117'),
            xaxis2=dict(
                tickformat='%d/%m %H:%M',
                tickangle=-30
            ),
            yaxis=dict(
                gridcolor='#1c2333', gridwidth=0.7,
                showgrid=True, tickformat='.5f',
                side='right'
            ),
            yaxis2=dict(gridcolor='#1c2333', showgrid=True),
        )
        fig.update_xaxes(
            showgrid=True, gridcolor='#1c2333',
            zeroline=False, showline=False
        )

        st.plotly_chart(fig, use_container_width=True, config={
            'displayModeBar': False,
            'scrollZoom': True
        })

        # ── Win % bar ────────────────────────────────────────────
        win_col = '#00e676' if win_pct >= 65 else ('#ffc107' if win_pct >= 40 else '#ff1744')
        st.markdown(f"""
        <div style="margin: 4px 0 8px 0;">
            <div style="color:#8b949e; font-size:0.8rem; margin-bottom:4px;">
                โอกาสชนะ (Win Probability)
            </div>
            <div class="win-bar-wrap">
                <div class="win-bar-inner"
                     style="width:{win_pct}%; background:{win_col}22;
                             color:{win_col}; border-right: 3px solid {win_col};">
                    {win_pct}%
                </div>
            </div>
            <div style="display:flex; flex-wrap:wrap; gap:8px; margin-top:6px;">
        """, unsafe_allow_html=True)
        for rtxt, rcol in reasons:
            st.markdown(
                f'<span style="color:{rcol}; font-size:0.82rem;">{rtxt}</span>',
                unsafe_allow_html=True
            )
        st.markdown("</div></div>", unsafe_allow_html=True)

    else:
        st.warning("กำลังดึงข้อมูลกราฟ...")


# ─────────────────────────────────────────────────────────────────
#  DASHBOARD (right column)
# ─────────────────────────────────────────────────────────────────
with col_dash:

    # ── Signal Status ────────────────────────────────────────────
    state_cfg = {
        'STANDBY':      ('รอสัญญาณ (STANDBY)',   'signal-standby',  '⏸'),
        'TESTING_ZONE': ('โซนทดสอบ (TESTING)',   'signal-testing',  '⚠️'),
        'EXECUTE_BUY':  ('เข้า BUY ทันที!',      'signal-buy',      '🟢'),
        'EXECUTE_SELL': ('เข้า SELL ทันที!',     'signal-sell',     '🔴'),
        'LOCKED':       ('ระบบล็อค (LOCKED)',     'signal-locked',   '🔒'),
    }
    slabel, scls, sicon = state_cfg.get(state, ('รอสัญญาณ', 'signal-standby', '⏸'))
    msg = signal.get('message', '')

    st.markdown(f"""
    <div class="signal-box {scls}">
        {sicon} {slabel}
    </div>
    <div style="color:#8b949e; font-size:0.8rem; margin:-4px 0 12px 0;
                text-align:center;">{msg}</div>
    """, unsafe_allow_html=True)

    # ── Entry Levels ─────────────────────────────────────────────
    st.markdown("#### 📊 ระดับราคา")
    for lbl, val, col in [
        ('Daily High (กรอบบน)', signal.get('daily_high'), '#ffc107'),
        ('Daily Low (กรอบล่าง)', signal.get('daily_low'), '#ffc107'),
        ('Buffer High', signal.get('buffer_high'), '#ff9100'),
        ('Buffer Low',  signal.get('buffer_low'),  '#ff9100'),
        ('จุดเข้า (ENTRY)', entry_levels.get('entry'), '#58a6ff'),
        ('ตัดขาดทุน (SL)',  entry_levels.get('sl'),    '#ff1744'),
        ('ทำกำไร (TP)',     entry_levels.get('tp'),    '#00e676'),
    ]:
        v_str = f"{val:.5f}" if val else "—"
        st.markdown(f"""
        <div class="price-row">
            <span class="price-label">{lbl}</span>
            <span class="price-value" style="color:{col};">{v_str}</span>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Account & Risk ───────────────────────────────────────────
    st.markdown("#### 💰 บัญชีและความเสี่ยง")
    balance_cents = 1000.0
    lot_info = engines['compounding'].get_current_lot_size(balance_cents)

    lock_str = "🔒 ล็อคการเทรด" if st.session_state.is_locked else "🟢 ทำงานปกติ"
    lock_col = "#ff1744" if st.session_state.is_locked else "#00e676"

    items = [
        ("ยอดเงิน (Cents)", f"{balance_cents:.0f} ¢", "#e6edf3"),
        ("ยอดเงิน (USD)", f"${lot_info['balance_usd']:.2f}", "#e6edf3"),
        ("ขนาด Lot", f"{lot_info['lot_size']:.2f}", "#58a6ff"),
        ("ความเสี่ยง/ไม้", f"{lot_info['risk_per_trade_cents']:.0f} ¢", "#ff9100"),
        ("แพ้สะสมวันนี้", f"{st.session_state.daily_losses}/2", "#ff1744"),
        ("สถานะระบบ", lock_str, lock_col),
        ("สถิติ ชนะ/แพ้", f"{st.session_state.wins}W / {st.session_state.losses}L", "#00e676"),
    ]
    for lbl, val, col in items:
        st.markdown(f"""
        <div class="price-row">
            <span class="price-label">{lbl}</span>
            <span class="price-value" style="color:{col};">{val}</span>
        </div>
        """, unsafe_allow_html=True)

    # ── Quick action buttons ─────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        if st.button("✅ บันทึก Win"):
            st.session_state.wins += 1
            st.rerun()
    with c2:
        if st.button("❌ บันทึก Loss"):
            st.session_state.losses += 1
            st.session_state.daily_losses += 1
            if st.session_state.daily_losses >= 2:
                st.session_state.is_locked = True
            st.rerun()
    if st.button("🔄 รีเซ็ตรายวัน", use_container_width=True):
        st.session_state.daily_losses = 0
        st.session_state.is_locked = False
        st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Compounding Table ─────────────────────────────────────────
    st.markdown("#### 📈 ตารางทบต้น 12 เดือน")
    proj = engines['compounding'].generate_projection(12)
    rows = ""
    for m in proj:
        rows += f"""<tr>
            <td>{m['month']}</td>
            <td>{m['starting_balance_cents']:.0f}</td>
            <td>{m['lot_size']:.2f}</td>
            <td>{m['estimated_profit_cents']:.0f}</td>
            <td>{m['ending_balance_cents']:.0f}</td>
            <td>${m['ending_balance_usd']:.1f}</td>
        </tr>"""
    st.markdown(f"""
    <table class="comp-table">
        <tr>
            <th>ด.</th><th>ทุน ¢</th><th>Lot</th>
            <th>กำไร ¢</th><th>จบ ¢</th><th>USD</th>
        </tr>
        {rows}
    </table>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════
#  AUTO REFRESH every 60 seconds
# ══════════════════════════════════════════════════════════════════
import time
st.markdown("---")
cols = st.columns([4, 1])
with cols[0]:
    next_refresh = 60
    st.caption(f"⏱ อัพเดตอัตโนมัติทุก 60 วินาที | เวลา: {datetime.now().strftime('%H:%M:%S')}")
with cols[1]:
    if st.button("🔄 รีเฟรช"):
        st.cache_data.clear()
        st.rerun()

# Auto-rerun every 60 seconds
time.sleep(60)
st.cache_data.clear()
st.rerun()
