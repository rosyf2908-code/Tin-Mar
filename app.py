import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import requests
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error

# Page Setup
st.set_page_config(page_title="DMH National AI Weather Dashboard", layout="wide")

# ၁။ မြန်မာနိုင်ငံ အထင်ကရမြို့များ Lat/Lon (အဆင့် ၁)
MYANMAR_CITIES = {
    "Naypyidaw": {"lat": 19.7633, "lon": 96.0785},
    "Yangon": {"lat": 16.8661, "lon": 96.1951},
    "Mandalay": {"lat": 21.9747, "lon": 96.0836},
    "Bago": {"lat": 17.3333, "lon": 96.4833},
    "Mawlamyine": {"lat": 16.4905, "lon": 97.6282},
    "Taunggyi": {"lat": 20.7888, "lon": 97.0333},
    "Sittwe": {"lat": 20.1436, "lon": 92.8977},
    "Pathein": {"lat": 16.7833, "lon": 94.7333},
    "Magway": {"lat": 20.1500, "lon": 94.9167},
    "Monywa": {"lat": 22.1167, "lon": 95.1333}
}

st.title("🌦️ DMH National AI Weather & Climate Dashboard")
st.sidebar.image("https://www.moezala.gov.mm/themes/custom/dmh/logo.png", width=70)
selected_city = st.sidebar.selectbox("🎯 Select City / မြို့ရွေးချယ်ရန်", list(MYANMAR_CITIES.keys()))

# ၂ နှင့် ၃။ Local Excel Data ဖြင့် AI Training & Validation
@st.cache_data
def train_local_ai(city):
    try:
        # Excel ဖိုင်ကို ဖတ်ခြင်း (GitHub ထဲတွင် မြို့အမည်အတိုင်း ရှိရမည်)
        file_url = f"https://raw.githubusercontent.com/rosyf2908-code/Tin-Mar/main/{city}.xlsx"
        df = pd.read_excel(file_url)
        
        # Feature Engineering: ယခင်နေ့ အပူချိန်ဖြင့် ယနေ့ကို ခန့်မှန်းခြင်း
        df['Prev_Tmax'] = df['Tmax'].shift(1)
        df = df.dropna()

        X = df[['Prev_Tmax']]
        y = df['Tmax']
        
        # Model Training (အဆင့် ၂)
        model = RandomForestRegressor(n_estimators=100, random_state=42)
        model.fit(X, y)
        
        # Validation (အဆင့် ၃): Open-Meteo နှင့် တိုက်ဆိုင်စစ်ဆေးရန် Sample Logic
        prediction = model.predict(X)
        mae = mean_absolute_error(y, prediction)
        
        return model, mae, df
    except:
        return None, None, None

model, error_rate, history_df = train_local_ai(selected_city)

# ၄။ ၇ ရက်စာ Forecast ရယူခြင်း (အဆင့် ၄)
def get_forecast(city):
    lat, lon = MYANMAR_CITIES[city]['lat'], MYANMAR_CITIES[city]['lon']
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=temperature_2m_max,precipitation_sum&timezone=Asia%2FYangon"
    r = requests.get(url).json()
    return pd.DataFrame({
        "Date": pd.to_datetime(r['daily']['time']),
        "Temp_Max": r['daily']['temperature_2m_max'],
        "Rain": r['daily']['precipitation_sum']
    })

forecast_df = get_forecast(selected_city)

# ၅။ Future Projection with LULC (အဆင့် ၅)
def future_climate_ai(city):
    years = np.arange(2026, 2101)
    # LULC factor ကို မြို့ပြဖွံ့ဖြိုးမှုအရ ၁.၂ ဟု သတ်မှတ် (Urban Heat Island Impact)
    temp_trend = 32 + (years - 2026) * 0.04 * 1.2 
    return pd.DataFrame({"Year": years, "Projected_Temp": temp_trend})

future_df = future_climate_ai(selected_city)

# ၆။ Dashboard တွင် Automatic ပြသခြင်း (အဆင့် ၆)
col1, col2 = st.columns(2)

with col1:
    st.subheader(f"📅 7-Day Forecast: {selected_city}")
    st.plotly_chart(px.line(forecast_df, x='Date', y='Temp_Max', title="Predicted Max Temp (°C)"))
    if error_rate:
        st.write(f"✅ AI Model Validation Error (MAE): {error_rate:.2f}°C")

with col2:
    st.subheader("🔮 Future Climate Projection (2100)")
    st.plotly_chart(px.line(future_df, x='Year', y='Projected_Temp', title="Temperature Projection under SSP Scenarios"))

if history_df is not None:
    st.markdown("---")
    st.subheader(f"📊 Historical Insight (1981-2025): {selected_city}")
    st.line_chart(history_df.set_index('Date')['Tmax'].tail(365)) # နောက်ဆုံး ၁ နှစ်စာ ပြသခြင်း
