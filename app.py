import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px  # သေချာအောင် ပြန်စစ်ပါ
import requests
from datetime import datetime

# --- ၁။ ရက်စွဲကို Auto ရယူခြင်း ---
today_str = datetime.now().strftime("%d %B %Y")

# --- ၂။ Page Configuration ---
st.set_page_config(
    page_title="DMH AI Weather Dashboard",
    layout="wide",
    page_icon="🌦️",
    initial_sidebar_state="expanded"
)

# ဖုန်းမှာ အမည်မှန်ပေါ်စေရန် Metadata (Title ကို ခေတ္တဖယ်ထားပါသည်)
st.markdown(
    """
    <head>
        <meta name="apple-mobile-web-app-title" content="DMH Weather">
        <meta name="application-name" content="DMH Weather">
    </head>
    """,
    unsafe_allow_html=True
)

# --- မြန်မာနိုင်ငံ မြို့ကြီး (၂၀) စာရင်း ---
MYANMAR_CITIES_20 = {
    "Naypyidaw": {"lat": 19.7633, "lon": 96.0785},
    "Yangon": {"lat": 16.8661, "lon": 96.1951},
    "Mandalay": {"lat": 21.9747, "lon": 96.0836},
    "Bago": {"lat": 17.3333, "lon": 96.4833},
    "Magway": {"lat": 20.1500, "lon": 94.9167},
    "Monywa": {"lat": 22.1167, "lon": 95.1333},
    "Pathein": {"lat": 16.7833, "lon": 94.7333},
    "Pyay": {"lat": 18.8167, "lon": 95.2167},
    "Taungoo": {"lat": 18.9333, "lon": 96.4333},
    "Hinthada": {"lat": 17.6500, "lon": 95.3833},
    "Myitkyina": {"lat": 25.3831, "lon": 97.3964},
    "Taunggyi": {"lat": 20.7888, "lon": 97.0333},
    "Mawlamyine": {"lat": 16.4905, "lon": 97.6282},
    "Sittwe": {"lat": 20.1436, "lon": 92.8977},
    "Lashio": {"lat": 22.9333, "lon": 97.7500},
    "Hpa-An": {"lat": 16.8906, "lon": 97.6333},
    "Loikaw": {"lat": 19.6742, "lon": 97.2093},
    "Mindat": {"lat": 21.3748, "lon": 93.9725},
    "Hkamti": {"lat": 25.9977, "lon": 95.6905},
    "Dawei": {"lat": 14.0833, "lon": 98.2000}
}

# --- Functions ---
@st.cache_data(ttl=3600)
def get_live_forecast_20(city):
    if city not in MYANMAR_CITIES_20:
        return pd.DataFrame()
    lat, lon = MYANMAR_CITIES_20[city]['lat'], MYANMAR_CITIES_20[city]['lon']
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,windspeed_10m_max&timezone=Asia%2FYangon"
    try:
        r = requests.get(url).json()
        return pd.DataFrame({
            "Date": pd.to_datetime(r['daily']['time']),
            "Temp_Max": r['daily']['temperature_2m_max'],
            "Temp_Min": r['daily']['temperature_2m_min'],
            "Rain": r['daily']['precipitation_sum'],
            "Wind": r['daily']['windspeed_10m_max']
        })
    except:
        return pd.DataFrame()

def get_future_ai_projection_20(city_name):
    years = np.arange(2026, 2101)
    temp_trend = [32 + (y-2026)*0.04 + np.random.normal(0, 0.5) for y in years]
    return pd.DataFrame({"Year": years, "Projected_Temp": temp_trend})

# --- Sidebar ---
st.sidebar.image("https://www.moezala.gov.mm/themes/custom/dmh/logo.png", width=100)
st.sidebar.title("DMH AI Dashboard")
st.sidebar.markdown(f"**Date:** {today_str}")

sorted_cities = sorted(list(MYANMAR_CITIES_20.keys()))
selected_city = st.sidebar.selectbox("🎯 Select City", sorted_cities)
view_mode = st.sidebar.radio("📊 View Mode", ["7-Day Forecast", "Future Projections (2100)"])

# --- Main Logic ---
st.markdown(f"<h1 style='text-align: center; color: #1E88E5;'>🌦️ {selected_city} Weather Dashboard</h1>", unsafe_allow_html=True)

forecast_df = get_live_forecast_20(selected_city)

if not forecast_df.empty:
    st.markdown(f"### ☀️ {selected_city} - Today's Highlights")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🌡️ Max Temp", f"{forecast_df['Temp_Max'][0]} °C")
    c2.metric("❄️ Min Temp", f"{forecast_df['Temp_Min'][0]} °C")
    c3.metric("🌧️ Rainfall", f"{forecast_df['Rain'][0]} mm")
    c4.metric("💨 Wind Speed", f"{forecast_df['Wind'][0]} km/h")

    if view_mode == "7-Day Forecast":
        st.subheader(f"📈 7-Day Forecast for {selected_city}")
        col1, col2 = st.columns(2)
        with col1:
            fig_temp = px.line(forecast_df, x='Date', y=['Temp_Max', 'Temp_Min'], 
                              markers=True, title="Temperature Forecast (°C)",
                              labels={'value': 'Temp (°C)', 'variable': 'Type'})
            st.plotly_chart(fig_temp, use_container_width=True)
        with col2:
            fig_rain = px.bar(forecast_df, x='Date', y='Rain', 
                             title="Precipitation Forecast (mm)",
                             labels={'Rain': 'Rain (mm)'})
            st.plotly_chart(fig_rain, use_container_width=True)
    else:
        st.subheader(f"🔮 Future Trend (2026-2100)")
        future_df = get_future_ai_projection_20(selected_city)
        fig_future = px.line(future_df, x='Year', y='Projected_Temp', 
                            title="Projected Temperature Rise",
                            labels={'Projected_Temp': 'Temp (°C)'})
        st.plotly_chart(fig_future, use_container_width=True)
else:
    st.error("Data could not be fetched. Please check your connection.")

st.markdown("---")
st.markdown(f"<p style='text-align: center; color: gray;'>Department of Meteorology and Hydrology (DMH) | Myanmar 🇲🇲</p>", unsafe_allow_html=True)
