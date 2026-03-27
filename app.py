import streamlit as st
import pandas as pd
import plotly.express as px
import requests

st.set_page_config(page_title="Myanmar AI Weather", layout="wide")

# DMH Logo နှင့် ခေါင်းစဉ်
st.title("🌦️ Myanmar AI Weather Dashboard")
st.markdown("Developed for Department of Meteorology and Hydrology")

# မြို့ရွေးချယ်ရန်
city_coords = {
    "Naypyidaw": [19.7633, 96.0785],
    "Yangon": [16.8661, 96.1951],
    "Mandalay": [21.9747, 96.0836]
}
selected = st.selectbox("🎯 မြို့ရွေးချယ်ရန် / Select City", list(city_coords.keys()))

# API မှ Live Data ဆွဲယူခြင်း
@st.cache_data(ttl=3600)
def get_weather(city):
    lat, lon = city_coords[city]
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=precipitation_sum,temperature_2m_max&timezone=Asia%2FYangon"
    r = requests.get(url).json()
    return pd.DataFrame({
        "Date": pd.to_datetime(r['daily']['time']),
        "Rainfall_mm": r['daily']['precipitation_sum'],
        "Temp_Max": r['daily']['temperature_2m_max']
    })

df = get_weather(selected)

# ရလဒ်ပြသခြင်း
st.success(f"**{selected}** မြို့အတွက် ရာသီဥတုခန့်မှန်းချက်များကို အောက်တွင် ကြည့်ရှုနိုင်ပါပြီ။")
st.plotly_chart(px.line(df, x='Date', y='Temp_Max', title="Temperature Trend (°C)"))
st.plotly_chart(px.bar(df, x='Date', y='Rainfall_mm', title="Precipitation Forecast (mm)"))
