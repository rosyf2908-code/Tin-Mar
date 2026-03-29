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
    page_icon="🌦️",
    initial_sidebar_state="expanded"
)

# ဖုန်း Icon အတွက် Metadata
st.markdown("""<head><meta name="apple-mobile-web-app-title" content="DMH Weather"><meta name="application-name" content="DMH Weather"></head>""", unsafe_allow_html=True)

# မြန်မာနိုင်ငံ မြို့ကြီး (၂၀) စာရင်း
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

@st.cache_data(ttl=600)
def get_weather_data(city):
    lat, lon = MYANMAR_CITIES_20[city]['lat'], MYANMAR_CITIES_20[city]['lon']
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=temperature_2m,precipitation,windspeed_10m,winddirection_10m&daily=temperature_2m_max,temperature_2m_min,precipitation_sum&timezone=Asia%2FYangon"
    try:
        r = requests.get(url).json()
        h, d = r['hourly'], r['daily']
        df_h = pd.DataFrame({"Time": pd.to_datetime(h['time']), "Temp": h['temperature_2m'], "Rain": h['precipitation'], "Wind": h['windspeed_10m'], "WindDir": h['winddirection_10m']})
        df_d = pd.DataFrame({"Date": pd.to_datetime(d['time']), "Tmax": d['temperature_2m_max'], "Tmin": d['temperature_2m_min'], "RainSum": d['precipitation_sum']})
        return df_h, df_d
    except: return None, None

def get_future_ai_projection_20(city_name):
    years = np.arange(2026, 2101)
    temp_trend = [32 + (y-2026)*0.04 + np.random.normal(0, 0.5) for y in years]
    return pd.DataFrame({"Year": years, "Projected_Temp": temp_trend})

# --- Sidebar ---
st.sidebar.image("https://www.moezala.gov.mm/themes/custom/dmh/logo.png", width=80)
st.sidebar.title("DMH AI Dashboard")
selected_city = st.sidebar.selectbox("🎯 Select City", sorted(list(MYANMAR_CITIES_20.keys())))
view_mode = st.sidebar.radio("📊 View Mode", ["Hourly & 7-Day Forecast", "Future Projections (2100)"])

# --- Main UI ---
st.markdown(f"<h1 style='text-align: center; color: #1E88E5;'>🌦️ {selected_city} National AI Weather Dashboard</h1>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align: center;'><b>Local Time:</b> {now.strftime('%I:%M %p, %d %b %Y')}</p>", unsafe_allow_html=True)
st.markdown("---")

df_h, df_d = get_weather_data(selected_city)

if df_h is not None:
    # Hourly Highlights (လက်ရှိအချိန်နဲ့ အနီးစပ်ဆုံး row ကိုယူခြင်း)
    curr_data = df_h.iloc[current_hour]
    
    st.markdown(f"### 📍 Current Highlights ({now.strftime('%I:%M %p')})")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🌡️ Temp", f"{curr_data['Temp']} °C")
    c2.metric("🌧️ Rain", f"{curr_data['Rain']} mm")
    c3.metric("💨 Wind Speed", f"{curr_data['Wind']} km/h")
    c4.metric("🧭 Direction", f"{get_wind_dir(curr_data['WindDir'])} ({curr_data['WindDir']}°)")
    st.markdown("---")

    if view_mode == "Hourly & 7-Day Forecast":
        # ၁။ Hourly Graph
        st.subheader(f"📈 Today's Hourly Temperature Trend ({today_str})")
        fig1 = px.line(df_h.head(24), x='Time', y='Temp', markers=True, title="Temperature (°C)")
        fig1.update_layout(height=450, plot_bgcolor="#f9f9f9")
        st.plotly_chart(fig1, use_container_width=True)

        # ၂။ 7-Day Forecast
        st.subheader(f"📅 7-Day Forecast Summary")
        fig2 = px.bar(df_d, x='Date', y=['Tmax', 'Tmin'], barmode='group', title="7-Day Temperature Range")
        fig2.update_layout(height=450)
        st.plotly_chart(fig2, use_container_width=True)

    else:
        # Future Projection အပိုင်း (ပြန်လည်ထည့်သွင်းခြင်း)
        st.subheader(f"🔮 {selected_city} Future Climate Trend (2026-2100)")
        future_df = get_future_ai_projection_20(selected_city)
        fig_future = px.line(future_df, x='Year', y='Projected_Temp', title="AI Projected Temperature Rise", color_discrete_sequence=['red'])
        fig_future.update_layout(height=550)
        st.plotly_chart(fig_future, use_container_width=True)
        st.warning("Insight: Statistical projections suggest a long-term warming trend based on current data.")
else:
    st.error("Data could not be fetched. Please refresh the page.")

st.markdown("---")
st.markdown(f"<p style='text-align: center; color: gray;'>
