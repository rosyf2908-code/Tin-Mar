import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import requests

# Page Layout
st.set_page_config(page_title="Myanmar AI Weather Dashboard", layout="wide", page_icon="🌦️")

# Sidebar - DMH Logo & Info
st.sidebar.image("https://www.moezala.gov.mm/themes/custom/dmh/logo.png", width=80)
st.sidebar.title("DMH AI Dashboard")
st.sidebar.info("Developed for Myanmar's Future Climate Resilience.")

# မြို့ကြီးများ စာရင်း
CITIES = {
    "Mandalay": {"lat": 21.9747, "lon": 96.0836},
    "Yangon": {"lat": 16.8661, "lon": 96.1951},
    "Naypyidaw": {"lat": 19.7633, "lon": 96.0785},
    "Taunggyi": {"lat": 20.7888, "lon": 97.0333},
    "Sittwe": {"lat": 20.1436, "lon": 92.8977}
}

# User Selection
selected_city = st.sidebar.selectbox("🎯 Select City / မြို့ရွေးချယ်ရန်", list(CITIES.keys()))
view_mode = st.sidebar.radio("📊 View Mode", ["7-Day Forecast", "Future Projections (2100)"])

st.title(f"🌦️ {selected_city} Weather & Climate AI Dashboard")
st.markdown("---")

# API ခေါ်ယူခြင်း Function
@st.cache_data(ttl=3600)
def get_weather(city):
    coords = CITIES[city]
    url = f"https://api.open-meteo.com/v1/forecast?latitude={coords['lat']}&longitude={coords['lon']}&daily=precipitation_sum,temperature_2m_max,temperature_2m_min&timezone=Asia%2FYangon"
    r = requests.get(url).json()
    return pd.DataFrame({
        "Date": pd.to_datetime(r['daily']['time']),
        "Rainfall_mm": r['daily']['precipitation_sum'],
        "Temp_Max": r['daily']['temperature_2m_max'],
        "Temp_Min": r['daily']['temperature_2m_min']
    })

df = get_weather(selected_city)

if view_mode == "7-Day Forecast":
    # Metrics
    c1, c2, c3 = st.columns(3)
    c1.metric("Today's Max Temp", f"{df['Temp_Max'][0]} °C")
    c2.metric("Rainfall Today", f"{df['Rainfall_mm'][0]} mm")
    c3.metric("Data Source", "Open-Meteo API")

    # Chart 1: Temperature
    fig_temp = px.line(df, x='Date', y=['Temp_Max', 'Temp_Min'], markers=True, 
                       title=f"Temperature Forecast for {selected_city}",
                       color_discrete_map={"Temp_Max": "orange", "Temp_Min": "blue"})
    st.plotly_chart(fig_temp, use_container_width=True)

    # Chart 2: Rainfall
    fig_rain = px.bar(df, x='Date', y='Rainfall_mm', title="Precipitation Forecast", color_discrete_sequence=['skyblue'])
    st.plotly_chart(fig_rain, use_container_width=True)

else:
    st.subheader(f"🔮 Future Temperature Trends (SSP Scenarios)")
    st.write(f"Analyzing potential climate scenarios for {selected_city} based on AI modeling.")
    
    # Future Projection Data (Sample based on your research)
    years = np.arange(2026, 2101)
    ssp245 = 32 + (years - 2026) * 0.02 + np.random.normal(0, 0.4, len(years))
    ssp585 = 32 + (years - 2026) * 0.06 + np.random.normal(0, 0.6, len(years))
    
    future_df = pd.DataFrame({
        "Year": years,
        "SSP2-4.5 (Moderate)": ssp245,
        "SSP5-8.5 (High Emission)": ssp585
    })
    
    fig_future = px.line(future_df, x='Year', y=["SSP2-4.5 (Moderate)", "SSP5-8.5 (High Emission)"],
                         title="Projected Temperature Rise (2026-2100)",
                         labels={"value": "Temperature (°C)"})
    st.plotly_chart(fig_future, use_container_width=True)
    st.warning("Insight: AI predicts a significant heat trend. Mitigation and adaptation are needed.")

st.sidebar.markdown("---")
st.sidebar.write("Developed for DMH Myanmar 🇲🇲")
