import os
import sys
import requests
import numpy as np
from datetime import datetime, timedelta

# ── ตั้งค่า Telegram Bot ───────────────────────────────────────────
TELEGRAM_TOKEN = "8975079249:AAGzu-crMd4xg6MVainhiikaFeoWdaJHW3w"
CHAT_ID = "6314779533"

# เพื่อให้เรียกใช้ module ในโฟลเดอร์ core และ data ได้
sys.path.insert(0, os.path.dirname(__file__))

from data.twelvedata_feed import TwelveDataFeed
from core.signal_engine import SignalEngine
from core.volume_profile import VolumeProfile
from core.risk_manager import RiskManager

def send_telegram_message(text):
    """ส่งข้อความเข้า Telegram"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML"
    }
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Error sending Telegram message: {e}")

def get_thai_time():
    return datetime.utcnow() + timedelta(hours=7)

def main():
    print(f"[{get_thai_time()}] Running Sniper Bot Check...")
    
    # 1. โหลดข้อมูลแท่งเทียน
    feed = TwelveDataFeed("EUR/USD", "7d1d88bd94fa4ba0bdabf73846f779bb")
    candles = feed.fetch_historical_data(120)
    
    if not candles:
        print("No data fetched. Exiting.")
        return
        
    recent = candles[-24:] if len(candles) >= 24 else candles
    last_candle = recent[-1]
    
    # 2. โหลดเครื่องมือประมวลผล
    vp = VolumeProfile()
    signal_engine = SignalEngine()
    risk_manager = RiskManager()
    
    # คำนวณ
    vp_data = vp.calculate_profile(recent)
    vol_confirm = vp.check_volume_expansion(recent, last_candle['volume'])
    signal = signal_engine.evaluate_signal(recent, last_candle, vol_confirm)
    state = signal.get('state', 'STANDBY')
    
    # คำนวณโอกาสชนะ
    win_pct = 0
    if state != 'STANDBY':
        score = 0
        if 'EXECUTE' in state: score += 40
        elif state == 'TESTING_ZONE': score += 15
        
        vols = [c['volume'] for c in recent[-20:]]
        avg = np.mean(vols[:-1]) or 1
        if (vols[-1] / avg) >= 1.5:
            score += min(30, int(((vols[-1]/avg) - 1) * 20))
            
        if vp_data and vp_data.get('poc_price'):
            poc = vp_data['poc_price']
            entry = signal.get('entry') or last_candle['close']
            dh = signal.get('daily_high', last_candle['close'])
            dl = signal.get('daily_low', last_candle['close'])
            rng = (dh - dl) or 0.001
            d = abs(entry - poc) / rng
            if d < 0.15: score += 20
            elif d < 0.35: score += 10
            
        if 14 <= get_thai_time().hour < 23: score += 10
        win_pct = min(score, 100)

    # 3. เตรียมส่งข้อความถ้าไม่ใช่ STANDBY
    if state == 'STANDBY':
        print("Market is STANDBY. No notification sent.")
        return
        
    # ข้อความเริ่มต้น
    icon = "🚨" if "EXECUTE" in state else "⚠️"
    status_th = ""
    if "EXECUTE_BUY" in state: status_th = "เข้า BUY ทันที!"
    elif "EXECUTE_SELL" in state: status_th = "เข้า SELL ทันที!"
    elif "TESTING_ZONE" in state: status_th = "ราคาเข้าโซนเบรคเอาท์ (รอยืนยัน)"
    
    msg = f"{icon} <b>Private Sniper System V1.0</b> {icon}\n\n"
    msg += f"<b>คู่เงิน:</b> EUR/USD (H1)\n"
    msg += f"<b>สถานะ:</b> {status_th}\n"
    msg += f"<b>โอกาสชนะ:</b> {win_pct}%\n\n"
    
    msg += f"💵 <b>ราคาปัจจุบัน:</b> {last_candle['close']:.5f}\n"
    
    if "EXECUTE" in state and signal.get('entry'):
        direction = 'BUY' if 'BUY' in state else 'SELL'
        levels = risk_manager.calculate_entry_levels(signal['entry'], direction)
        
        msg += f"🎯 <b>จุดเข้า (ENTRY):</b> {levels['entry']:.5f}\n"
        msg += f"❌ <b>ตัดขาดทุน (SL):</b> {levels['sl']:.5f}\n"
        msg += f"✅ <b>ทำกำไร (TP):</b> {levels['tp']:.5f}\n"
    
    msg += f"\n⏰ <i>อัพเดต: {get_thai_time().strftime('%d/%m/%Y %H:%M:%S')}</i>"
    
    # ส่งข้อความ
    print("Sending Telegram Notification...")
    send_telegram_message(msg)
    print("Done!")

if __name__ == "__main__":
    main()
