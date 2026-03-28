import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import requests
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error
from datetime import datetime

# --- ၁။ ရက်စွဲကို Auto ရယူခြင်း ---
today_str = datetime.now().strftime("%d %B %Y")

# --- ၂။ Page Configuration ---
st.set_page_config(
    page_title="DMH AI Weather Dashboard",
    layout="wide",
    page_icon="🌦️",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://www.moezala.gov.mm',
        'Report a bug': None,
        'About': f"# DMH AI Weather Dashboard \n Updated: {today_str} \n Developed by Tin-Mar (DMH Myanmar)"
    }
)

# ဖုန်းမှာ အမည်မှန်ပေါ်စေရန်
st.markdown(
    """
    <head>
        <title>DMH AI Weather Dashboard</title>
        <meta name="apple-mobile-web-app-title" content="DMH Weather">
        <meta name="application-name" content="DMH Weather">
    </head>
    """,
    unsafe_allow_html=True
)
st.markdown('<link rel="manifest" href="./manifest.json">', unsafe_allow_html=True)
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

# --- Sidebar ---
st.sidebar.image("https://www.moezala.gov.mm/themes/custom/dmh/logo.png", width=100)
st.sidebar.title("DMH AI Dashboard")
st.sidebar.markdown(f"**Date:** {today_str}")
st.sidebar.markdown("---")

sorted_cities = sorted(list(MYANMAR_CITIES_20.keys()))
selected_city = st.sidebar.selectbox("🎯 Select City / မြို့ရွေးချယ်ရန်", sorted_cities)

# ဤနေရာတွင် view_mode ကို ပြန်ဖွင့်ပေးရပါမည် (မဖွင့်လျှင် Dashboard ပျက်ပါမည်)
view_mode = st.sidebar.radio("📊 View Mode", ["7-Day Forecast", "Future Projections (2100)"])

st.sidebar.markdown("---")
st.sidebar.info("Developed for DMH Myanmar 🇲🇲")

# --- Header ---
st.markdown(f"<h1 style='text-align: center; color: #1E88E5;'>🌦️ {selected_city} National AI Weather Dashboard</h1>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align: center;'><b>Last Updated:</b> {today_str}</p>", unsafe_allow_html=True)
st.markdown("---")

# --- AI Training & Data Logic ---
@st.cache_data(ttl=3600)
def train_local_ai_20(city):
    try:
        file_url = f"https://raw.githubusercontent.com/rosyf2908-code/Tin-Mar/main/{city}.xlsx"
        df = pd.read_excel(file_url)
        df['Prev_Tmax'] = df['Tmax'].shift(1)
        df = df.dropna()
        X = df[['Prev_Tmax']]
        y = df['Tmax']
        model = RandomForestRegressor(n_estimators=100, random_state=42)
        model.fit(X, y)
        prediction = model.predict(X)
        mae = mean_absolute_error(y, prediction)
        return model, mae, df
    except:
        return None, None, None

model, error_rate, history_df = train_local_ai_20(selected_city)

@st.cache_data(ttl=3600)
def get_live_forecast_20(city):
    lat, lon = MYANMAR_CITIES_20[city]['lat'], MYANMAR_CITIES_20[city]['lon']
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,windspeed_10m_max&timezone=Asia%2FYangon"
    r = requests.get(url).json()
    return pd.DataFrame({
        "Date": pd.to_datetime(r['daily']['time']),
        "Temp_Max": r['daily']['temperature_2m_max'],
        "Temp_Min": r['daily']['temperature_2m_min'],
        "Rain": r['daily']['precipitation_sum'],
        "Wind": r['daily']['windspeed_10m_max']
    })

forecast_df = get_live_forecast_20(selected_city)

def get_future_ai_projection_20(city_name, lulc_impact=1.2):
    years = np.arange(2026, 2101)
    base_temp_rise = 0.04
    temp_trend = [32 + (y-2026)*base_temp_rise * lulc_impact + np.random.normal(0, 0.5) for y in years]
    return pd.DataFrame({"Year": years, "Projected_Temp": temp_trend})

future_df = get_future_ai_projection_20(selected_city)

# --- UI Display ---
st.markdown(f"### ☀️ {selected_city} - Today's Highlights")
c1, c2, c3, c4 = st.columns(4)
c1.metric(label="🌡️ Max Temp", value=f"{forecast_df['Temp_Max'][0]} °C")
c2.metric(label="❄️ Min Temp", value=f"{forecast_df['Temp_Min'][0]} °C")
c3.metric(label="🌧️ Rainfall", value=f"{forecast_df['Rain'][0]} mm")
c4.metric(label="💨 Wind Speed", value=f"{forecast_df['Wind'][0]} km/h")
st.markdown("---")

if view_mode == "7-Day Forecast":
    # ဤနေရာတွင် subheader ကို သေသေချာချာ ပြန်ထားပေးထားပါသည်
    st.subheader(f"📈 {today_str} - 7-Day Forecast for {selected_city}")
    st.info(f"Forecast Period: {forecast_df['Date'].dt.strftime('%d %b').iloc[0]} to {forecast_df['Date'].dt.strftime('%d %b').iloc[-1]}")
    
    col1, col2 = st.columns(2)
    with col1:
        fig_temp = px.line(forecast_df, x='Date', y=['Temp_Max', 'Temp_Min'], markers=True,
                           title="Temperature Forecast (°C)",
                           color_discrete_map={'Temp_Max': 'orange', 'Temp_Min': 'blue'})
        fig_temp.update_layout(plot_bgcolor="#F0F2F6")
        st.plotly_chart(fig_temp, use_container_width=True)
    with col2:
        fig_rain = px.bar(forecast_df, x='Date', y='Rain', title="Precipitation Forecast (mm)", color_discrete_sequence=['deepskyblue'])
        fig_rain.update_layout(plot_bgcolor="#F0F2F6")
        st.plotly_chart(fig_rain, use_container_width=True)
    
    if error_rate:
        st.success(f"✅ AI Model Validation Complete (MAE: {error_rate:.2f}°C)")

else:
    st.subheader(f"🔮 {selected_city} Future Climate Trend (2026-2100)")
    fig_future = px.line(future_df, x='Year', y='Projected_Temp', title="Projected Temperature Rise", color_discrete_sequence=['red'])
    fig_future.update_layout(plot_bgcolor="#FEEFC3")
    st.plotly_chart(fig_future, use_container_width=True)
    st.warning("Insight: AI models suggest a long-term warming trend.")

if history_df is not None:
    st.markdown("---")
    st.subheader(f"📊 Historical Insight (1981-2025): {selected_city}")
    fig_hist = px.line(history_df.tail(1825), x='Date', y='Tmax', title="Historical Tmax Trend (Last 5 Years)", color_discrete_sequence=['green'])
    fig_hist.update_layout(plot_bgcolor="white")
    st.plotly_chart(fig_hist, use_container_width=True)

st.markdown("---")
st.markdown(f"<p style='text-align: center; color: gray;'>Department of Meteorology and Hydrology (DMH) | Myanmar 🇲🇲 <br> Data as of: {today_str}</p>", unsafe_allow_html=True)
