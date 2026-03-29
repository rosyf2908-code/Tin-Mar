import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import requests
from datetime import datetime

# --- ၁။ အချိန်နှင့် ရက်စွဲ ---
now = datetime.now()
current_hour = now.hour

# --- ၂။ Page Configuration ---
st.set_page_config(page_title="DMH AI Weather Dashboard", layout="wide")

# မြို့ကြီး (၂၀) စာရင်း (သြဒီနိတ်များ)
MYANMAR_CITIES_20 = {
    "Naypyidaw": {"lat": 19.7633, "lon": 96.0785}, "Yangon": {"lat": 16.8661, "lon": 96.1951},
    "Mandalay": {"lat": 21.9747, "lon": 96.0836}, "Bago": {"lat": 17.3333, "lon": 96.4833},
    "Magway": {"lat": 20.1500, "lon": 94.9167}, "Monywa": {"lat": 22.1167, "lon": 95.1333},
    "Pathein": {"lat": 16.7833, "lon": 94.7333}, "Pyay": {"lat": 18.8167, "lon": 95.2167},
    "Taungoo": {"lat": 18.9333, "lon": 96.4333}, "Hinthada": {"lat": 17.6500, "lon": 95.3833},
    "Myitkyina": {"lat": 25.3831, "lon": 97.3964}, "Taunggyi": {"lat": 20.7888, "lon": 97.0333},
    "Mawlamyine": {"lat": 16.4905, "lon": 97.6282}, "Sittwe": {"lat": 20.1436, "lon": 92.8977},
    "Lashio": {"lat": 22.9333, "lon": 97.7500}, "Hpa-An": {"lat": 16.8906, "lon": 97.6333},
    "Loikaw": {"lat": 19.6742, "lon": 97.2093}, "Mindat": {"lat": 21.3748, "lon": 93.9725},
    "Hkamti": {"lat": 25.9977, "lon": 95.6905}, "Dawei": {"lat": 14.0833, "lon": 98.2000}
}

@st.cache_data(ttl=300)
def get_detailed_weather(city):
    lat, lon = MYANMAR_CITIES_20[city]['lat'], MYANMAR_CITIES_20[city]['lon']
    # forecast_days=16 (Maximum available for free)
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=windspeed_10m,winddirection_10m&windspeed_unit=mph&forecast_days=16&timezone=Asia%2FYangon"
    try:
        r = requests.get(url, timeout=10).json()
        h = r['hourly']
        df = pd.DataFrame({
            "Time": pd.to_datetime(h['time']),
            "WindSpeed": h['windspeed_10m'],
            "WindDir": h['winddirection_10m']
        })
        # နေ့စဉ် ပျမ်းမျှမဟုတ်ဘဲ နေ့လည် ၁ နာရီအချိန် (Peak hour) ဒေတာကို နမူနာယူ၍ ဂရပ်ဆွဲပါမည်
        df_daily_sample = df[df['Time'].dt.hour == 13].copy()
        return df_daily_sample
    except: return None

# --- Sidebar ---
st.sidebar.image("https://www.moezala.gov.mm/themes/custom/dmh/logo.png", width=80)
selected_city = st.sidebar.selectbox("🎯 Select City", sorted(list(MYANMAR_CITIES_20.keys())))

# --- Main UI ---
st.title(f"💨 {selected_city} Wind Direction Analysis")
df = get_detailed_weather(selected_city)

if df is not None:
    # Wind Graph with Dynamic Arrows
    fig = go.Figure()

    # ၁။ Wind Speed Line
    fig.add_trace(go.Scatter(
        x=df['Time'], y=df['WindSpeed'],
        mode='lines+markers',
        name='Wind Speed (mph)',
        line=dict(color='teal', width=2)
    ))

    # ၂။ Dynamic Arrows (မြှားခေါင်းများကို ဒီဂရီအလိုက် လှည့်ခြင်း)
    fig.add_trace(go.Scatter(
        x=df['Time'], y=df['WindSpeed'] + 1,
        mode='markers',
        name='Wind Direction',
        marker=dict(
            symbol='arrow',
            size=18,
            angle=df['WindDir'], # ၃၆၀ ဒီဂရီ အတိအကျ လှည့်မည်
            color='orangered',
            line=dict(width=1, color='black')
        ),
        text=df['WindDir'].apply(lambda x: f"Dir: {x}°"),
        hoverinfo='text'
    ))

    fig.update_layout(height=500, xaxis_title="Date", yaxis_title="Speed (mph)")
    st.plotly_chart(fig, use_container_width=True)
    st.info("💡 မြှားခေါင်းလေးများသည် နေ့စဉ် နေ့လည် (၁) နာရီအချိန်ရှိ လေတိုက်ရာအရပ်ကို ညွှန်ပြနေခြင်းဖြစ်ပါသည်။")

else:
    st.error("Data Connection Error. Please refresh.")

st.markdown("---")
st.caption("Data Source: Open-Meteo API (16-Day Forecast Limit for Free Tier)")
