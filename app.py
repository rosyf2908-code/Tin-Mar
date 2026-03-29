import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import requests
from datetime import datetime

# --- ၁။ အချိန်နှင့် ရက်စွဲ ---
now = datetime.now()
today_str = now.strftime("%d %B %Y")
current_hour = now.hour

# --- ၂။ Page Configuration ---
st.set_page_config(page_title="DMH AI Weather Dashboard", layout="wide", page_icon="🌦️")

# မြို့ကြီး (၂၀) စာရင်း
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
def get_weather_data(city):
    lat, lon = MYANMAR_CITIES_20[city]['lat'], MYANMAR_CITIES_20[city]['lon']
    # ၁၆ ရက်စာ (Free API ၏ အများဆုံး)
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=temperature_2m,precipitation,windspeed_10m,winddirection_10m&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,windspeed_10m_max,winddirection_10m_dominant&windspeed_unit=mph&forecast_days=16&timezone=Asia%2FYangon"
    try:
        r = requests.get(url).json()
        h, d = r['hourly'], r['daily']
        df_h = pd.DataFrame({"Time": pd.to_datetime(h['time']), "Temp": h['temperature_2m'], "Rain": h['precipitation'], "Wind": h['windspeed_10m'], "WindDir": h['winddirection_10m']})
        df_d = pd.DataFrame({"Date": pd.to_datetime(d['time']), "Tmax": d['temperature_2m_max'], "Tmin": d['temperature_2m_min'], "RainSum": d['precipitation_sum'], "WindMax": d['windspeed_10m_max'], "WindDirDom": d['winddirection_10m_dominant']})
        return df_h, df_d
    except: return None, None

# --- Sidebar & UI ---
st.sidebar.image("https://www.moezala.gov.mm/themes/custom/dmh/logo.png", width=80)
selected_city = st.sidebar.selectbox("🎯 Select City", sorted(list(MYANMAR_CITIES_20.keys())))
df_h, df_d = get_weather_data(selected_city)

if df_h is not None:
    st.markdown(f"<h1 style='text-align: center;'>🌦️ {selected_city} Weather & Wind Analysis</h1>", unsafe_allow_html=True)
    st.markdown("---")

    # --- Wind Analysis Graph (Line + Arrow Markers) ---
    st.subheader("💨 Wind Speed (mph) & Direction (Arrows)")
    
    fig_wind = go.Figure()

    # ၁။ Wind Speed Line (အစိမ်းရောင်လိုင်း)
    fig_wind.add_trace(go.Scatter(
        x=df_d['Date'], y=df_d['WindMax'],
        mode='lines+markers',
        name='Wind Speed',
        line=dict(color='green', width=3),
        marker=dict(size=8)
    ))

    # ၂။ Wind Direction Arrows (၃၆၀ ဒီဂရီ မြှားခေါင်းများ)
    # Plotly တွင် 'arrow' သင်္ကေတကို သုံးပြီး angle ကို WindDir အတိုင်း လှည့်ပါမည်
    fig_wind.add_trace(go.Scatter(
        x=df_d['Date'], y=df_d['WindMax'] + 2, # လိုင်းပေါ်မှာ မြင်သာအောင် အပေါ်နည်းနည်းတင်ထားခြင်း
        mode='markers',
        name='Direction',
        marker=dict(
            symbol='arrow',
            size=15,
            angle=df_d['WindDirDom'], # မြှားကို ဒီဂရီအတိုင်းလှည့်ခြင်း
            color='darkred',
            line=dict(width=2, color='black')
        ),
        text=df_d['WindDirDom'].apply(lambda x: f"{x}°"),
        hoverinfo='text'
    ))

    fig_wind.update_layout(
        height=500,
        xaxis_title="Date",
        yaxis_title="Wind Speed (mph)",
        plot_bgcolor="#f9f9f9",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    st.plotly_chart(fig_wind, use_container_width=True)
    st.caption("မြှားခေါင်းလေးများသည် လေတိုက်ရာအရပ် (Direction) ကို ညွှန်ပြနေခြင်းဖြစ်ပါသည်။")

    # --- အခြား Graph များ (Temperature & Rain) ---
    st.markdown("---")
    st.subheader("🌡️ Temperature & 🌧️ Rain Forecast")
    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(px.line(df_d, x='Date', y=['Tmax', 'Tmin'], title="Temperature Outlook").update_layout(height=400))
    with c2:
        st.plotly_chart(px.bar(df_d, x='Date', y='RainSum', title="Precipitation Sum (mm)").update_layout(height=400))

else:
    st.error("Data Fetching Error.")

# Footer
st.markdown("---")
st.markdown("<p style='text-align: center; color: gray;'>Source: Open-Meteo API | MMT Timezone</p>", unsafe_allow_html=True)
