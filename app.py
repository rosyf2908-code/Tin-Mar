import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import requests
from datetime import datetime

# --- ၁။ ရက်စွဲနှင့် အချိန်ကို ရယူခြင်း ---
now = datetime.now()
today_str = now.strftime("%d %B %Y")
current_hour = now.hour

# --- ၂။ Page Configuration ---
st.set_page_config(
    page_title="DMH AI Weather Dashboard",
    layout="wide",
    page_icon="🌦️"
)

# ဖုန်း Icon အတွက် Metadata
st.markdown("""<head><meta name="apple-mobile-web-app-title" content="DMH Weather"><meta name="application-name" content="DMH Weather"></head>""", unsafe_allow_html=True)

# မြန်မာနိုင်ငံ မြို့ကြီး (၂၀)
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

# လေတိုက်ရာအရပ်ကို စာသားပြောင်းပေးသော Function
def get_wind_dir(deg):
    dirs = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']
    return dirs[int((deg + 11.25) / 22.5) % 16]

@st.cache_data(ttl=600) # ၁၀ မိနစ်တစ်ခါ update စစ်မည်
def get_weather_data(city):
    lat, lon = MYANMAR_CITIES_20[city]['lat'], MYANMAR_CITIES_20[city]['lon']
    # Hourly နှင့် Daily ဒေတာများ ရယူခြင်း
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=temperature_2m,precipitation,windspeed_10m,winddirection_10m&daily=temperature_2m_max,temperature_2m_min,precipitation_sum&timezone=Asia%2FYangon"
    try:
        r = requests.get(url).json()
        h = r['hourly']
        d = r['daily']
        # အချိန်အလိုက် DataFrame
        df_h = pd.DataFrame({
            "Time": pd.to_datetime(h['time']), "Temp": h['temperature_2m'],
            "Rain": h['precipitation'], "Wind": h['windspeed_10m'], "WindDir": h['winddirection_10m']
        })
        # ရက်အလိုက် DataFrame
        df_d = pd.DataFrame({"Date": pd.to_datetime(d['time']), "Tmax": d['temperature_2m_max'], "Tmin": d['temperature_2m_min'], "RainSum": d['precipitation_sum']})
        return df_h, df_d
    except: return None, None

# --- Sidebar ---
st.sidebar.image("https://www.moezala.gov.mm/themes/custom/dmh/logo.png", width=80)
selected_city = st.sidebar.selectbox("🎯 Select City", sorted(list(MYANMAR_CITIES_20.keys())))
view_mode = st.sidebar.radio("📊 Mode", ["Hourly & 7-Day", "Future Projection"])

# --- UI Display ---
st.markdown(f"<h1 style='text-align: center; color: #1E88E5;'>🌦️ {selected_city} Weather Dashboard</h1>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align: center;'><b>Current Local Time:</b> {now.strftime('%I:%M %p, %d %b %Y')}</p>", unsafe_allow_html=True)

df_h, df_d = get_weather_data(selected_city)

if df_h is not None:
    # လက်ရှိအချိန်နှင့် အနီးစပ်ဆုံး row ကိုယူခြင်း
    curr_data = df_h.iloc[current_hour]
    
    st.markdown(f"### 📍 Current Highlights (Hourly Update)")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🌡️ Temp", f"{curr_data['Temp']} °C")
    c2.metric("🌧️ Precipitation", f"{curr_data['Rain']} mm")
    c3.metric("💨 Wind Speed", f"{curr_data['Wind']} km/h")
    c4.metric("🧭 Wind Direction", f"{get_wind_dir(curr_data['WindDir'])} ({curr_data['WindDir']}°)")
    st.markdown("---")

    if view_mode == "Hourly & 7-Day":
        # ၁။ အပူချိန် Graph (Hourly Trend for Today)
        st.subheader(f"📈 Today's Hourly Temperature Trend")
        today_h = df_h.head(24)
        fig1 = px.line(today_h, x='Time', y='Temp', markers=True, title="Hourly Temperature")
        fig1.update_layout(height=400, plot_bgcolor="#f9f9f9")
        st.plotly_chart(fig1, use_container_width=True)

        # ၂။ ၇ ရက်စာ ခန့်မှန်းချက် (Daily)
        st.subheader(f"📅 7-Day Forecast (Summary)")
        fig2 = px.bar(df_d, x='Date', y=['Tmax', 'Tmin'], barmode='group', title="7-Day Temp Outlook")
        fig2.update_layout(height=400)
        st.plotly_chart(fig2, use_container_width=True)
else:
    st.error("Connection Error. Please refresh.")

st.markdown("---")
st.markdown(f"<p style='text-align: center; color: gray;'>DMH Myanmar | Data updated every hour</p>", unsafe_allow_html=True)
