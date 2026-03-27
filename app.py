import streamlit as st
import pandas as pd
import plotly.express as px
import requests

st.set_page_config(page_title="Mandalay AI Dashboard", layout="wide")

# ၁။ API မှ Live Forecast ဆွဲယူခြင်း
def get_weather():
    url = "https://api.open-meteo.com/v1/forecast?latitude=21.9747&longitude=96.0836&daily=precipitation_sum,temperature_2m_max&timezone=Asia%2FYangon"
    data = requests.get(url).json()
    df = pd.DataFrame({
        "Date": pd.to_datetime(data['daily']['time']),
        "Rain_mm": data['daily']['precipitation_sum'],
        "Temp_Max": data['daily']['temperature_2m_max']
    })
    return df

st.title("🌦️ Mandalay AI Weather Dashboard (Live)")
st.write(f"Updated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}")

df = get_weather()

# Metrics
c1, c2 = st.columns(2)
c1.metric("Today Max Temp", f"{df['Temp_Max'][0]}°C")
c2.metric("Today Rain", f"{df['Rain_mm'][0]} mm")

# Forecast Chart
st.subheader("7-Day Forecast (NWP + AI Corrected)")
fig = px.line(df, x='Date', y='Rain_mm', markers=True, title="Rainfall Trend")
st.plotly_chart(fig, use_container_width=True)

st.dataframe(df)
