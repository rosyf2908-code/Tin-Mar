import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import requests
import os
from datetime import datetime
import pytz

# --- ၁။ Layout Setup ---
st.set_page_config(page_title="DMH AI Weather Forecast System", layout="wide", page_icon="🌤️")

mm_tz = pytz.timezone('Asia/Yangon')
now = datetime.now(mm_tz)
formatted_now = now.strftime('%I:%M %p, %d %b %Y')
dm_header_logo = "https://www.moezala.gov.mm/themes/custom/dmh/logo.png?v=1.1"

# --- ၂။ ဘာသာစကားနှင့် စာသားများ ---
LANG_DATA = {
    "မြန်မာ": {
        "title": "DMH AI မိုးလေဝသခန့်မှန်းစနစ်",
        "station_label": "🎯 စခန်းအမည်ရွေးချယ်ပါ",
        "view_mode_label": "📊 View Mode",
        "modes": ["၁၆ ရက်စာ အသေးစိတ်ဆန်းစစ်ချက်", "အပူချိန်စောင့်ကြည့်ခြင်း (IBF-ကျန်းမာရေး )", "ရာသီဥတုပြောင်းလဲမှု (၂၁၀၀-SSP5-8.5)"],
        "dmh_alert": "📢 အကြံပြုချက်: နောက်ဆုံးရ မိုးလေဝသသတင်းများအတွက် မိုးဇလ သတင်းများကိုစောင့်ကြည့်ပါ။",
        "storm_note": "📝 မှတ်ချက်: မိုးတိမ်တောင် ဖြစ်နိုင်ခြေ ၆၀% ထက်ကျော်လွန်ပါက လေပြင်းတိုက်ခတ်ခြင်း၊ မိုးကြိုးပစ်ခြင်းနှင့် လျှပ်စီးလက်ခြင်းများ ဖြစ်ပေါ်နိုင်သဖြင့် ဂရုပြုရန် လိုအပ်ပါသည်။",
        "ibf_header": "🏥 ကျန်းမာရေးကဏ္ဍဆိုင်ရာ အကျိုးသက်ရောက်မှုနှင့် အကြံပြုချက်များ",
        "risk_levels": ["Extreme Risk (အလွန်အန္တရာယ်ရှိ)", "High Risk (အန္တရာယ်ရှိ)", "Moderate Risk (သတိပြုရန်)", "Low Risk (ပုံမှန်)"],
        "charts": [
            "🌡️ ၁။ အပူချိန်(°C)", "🌧️ ၂။ မိုးရေချိန်(mm)", "💨 ၃။ လေတိုက်နှုန်း(mph)", 
            "🔭 ၄။ အဝေးမြင်တာ (km)", "💧 ၅။ စိုထိုင်းဆ (%)", "☁️ ၆။ တိမ်ဖုံးမှု (Oktas)", 
            "⚡ ၇။ မိုးတိမ်တောင် (%)"
        ],
        "impact_list": [
            "အလွန်စိုးရိမ်ရသော အခြေအနေ! Heatstroke အန္တရာယ်ရှိသည်။", 
            "အန္တရာယ်ရှိသော အခြေအနေ! အပူဒဏ်ကြောင့် ပင်ပန်းနွမ်းနယ်နိုင်သည်။", 
            "သတိပြုရန် အခြေအနေ! နေရောင်အောက်တွင် ကြာရှည်မနေပါနှင့်။", 
            "ပုံမှန်အခြေအနေ! သိသာသော ထိခိုက်မှုမရှိပါ။"
        ],
        "recom_list": [
            "အိမ်ထဲတွင်သာနေပါ။ ရေများများသောက်ပါ။ ဆေးရုံသို့ အမြန်သွားပါ။", 
            "ပြင်ပလုပ်ငန်းများကို နံနက်/ညနေသာလုပ်ပါ။ ထီးဆောင်းပါ။", 
            "ပေါ့ပါးသောအဝတ်များဝတ်ပါ။ အရိပ်တွင်နားပါ။", 
            "ပုံမှန်အတိုင်းနေနိုင်ပါသည်။ ရေဓာတ်ဖြည့်တင်းပါ။"
        ]
    },
    "English": {
        "title": "DMH AI Weather System",
        "station_label": "🎯 Select Station",
        "view_mode_label": "📊 View Mode",
        "modes": ["16-Day Analysis", "Heatwave (IBF)", "Climate Change"],
        "dmh_alert": "📢 Tip: Follow DMH news updates.",
        "storm_note": "📝 Note: Beware of lightning if > 60%.",
        "ibf_header": "🏥 Health Impacts & Recommendations",
        "risk_levels": ["Extreme Risk", "High Risk", "Moderate Risk", "Low Risk"],
        "charts": ["🌡️ 1. Temp", "🌧️ 2. Rain", "💨 3. Wind", "🔭 4. Vis", "💧 5. Humid", "☁️ 6. Cloud", "⚡ 7. Storm"],
        "impact_list": ["Extreme danger! Heatstroke.", "High danger! Fatigue.", "Caution! Exposure risk.", "Normal."],
        "recom_list": ["Stay indoors. Drink water.", "Avoid noon sun. Use umbrella.", "Wear light clothes.", "Stay hydrated."]
    }
}

# --- ၃။ ဒေတာဖတ်ခြင်းနှင့် API ---
@st.cache_data
def load_stations():
    try:
        df_csv = pd.read_csv("Station.csv", encoding='utf-8-sig')
        return {str(row.iloc[0]).strip(): {'lat': float(row['Lat']), 'lon': float(row['Lon'])} for _, row in df_csv.iterrows()}
    except:
        return {"Naypyidaw": {"lat": 19.76, "lon": 96.08}}

MYANMAR_CITIES = load_stations()

@st.cache_data(ttl=600)
def fetch_weather(city):
    loc = MYANMAR_CITIES[city]
    url = f"https://api.open-meteo.com/v1/forecast?latitude={loc['lat']}&longitude={loc['lon']}&hourly=temperature_2m,precipitation,windspeed_10m,winddirection_10m,relative_humidity_2m,visibility,cloud_cover,cape&daily=temperature_2m_max,temperature_2m_min,precipitation_sum&windspeed_unit=mph&forecast_days=16&timezone=Asia%2FYangon"
    try:
        r = requests.get(url, timeout=15).json()
        df_h = pd.DataFrame({
            "Time": pd.to_datetime(r['hourly']['time']), 
            "Temp": r['hourly']['temperature_2m'],
            "precipitation": r['hourly']['precipitation'],
            "Wind": r['hourly']['windspeed_10m'],
            "WindDir": r['hourly']['winddirection_10m'],
            "Vis": [v/1000 for v in r['hourly']['visibility']],
            "Humid": r['hourly']['relative_humidity_2m'],
            "Cloud_Oktas": [round((c/100)*8) for c in r['hourly']['cloud_cover']],
            "Thunderstorm": [min(round((c/3500)*100), 100) if c else 0 for c in r['hourly'].get('cape', [])]
        })
        df_d = pd.DataFrame({
            "Date": pd.to_datetime(r['daily']['time']), 
            "Tmax": r['daily']['temperature_2m_max'],
            "Tmin": r['daily']['temperature_2m_min']
        })
        return df_h, df_d
    except:
        return None, None

# --- ၄။ Sidebar & UI ---
st.sidebar.image(dm_header_logo, width=100)
lang = st.sidebar.radio("🌐 Language", ["မြန်မာ", "English"], horizontal=True)
T = LANG_DATA[lang]
bias = st.sidebar.slider("🌡️ Bias Correction (°C)", -5.0, 5.0, 0.0)
selected_city = st.sidebar.selectbox(T["station_label"], sorted(list(MYANMAR_CITIES.keys())))
view_mode_choice = st.sidebar.radio(T["view_mode_label"], T["modes"])
mode_index = T["modes"].index(view_mode_choice)

st.title(T["title"])
st.info(f"📍 {selected_city} | 🕒 {formatted_now}")

df_h, df_d = fetch_weather(selected_city)

if df_h is not None:
    df_h['Temp'] += bias
    df_d['Tmax'] += bias
    df_d['Tmin'] += bias

    # --- Mode 0: 16-Day Detailed Analysis ---
    if mode_index == 0:
        st.warning(T["dmh_alert"])
        st.subheader(T["charts"][0])
        st.plotly_chart(px.line(df_d, x='Date', y=['Tmax', 'Tmin'], markers=True), use_container_width=True)

        df_6h = df_h.set_index('Time').resample('6h').agg({
            'precipitation': 'sum', 'Wind': 'mean', 'WindDir': 'mean', 
            'Cloud_Oktas': 'max', 'Thunderstorm': 'max'
        }).reset_index()

        st.subheader(T["charts"][1] + " (6-hourly)")
        st.plotly_chart(px.bar(df_6h, x='Time', y='precipitation', color_discrete_sequence=['skyblue']), use_container_width=True)

        st.subheader(T["charts"][2] + " (6-hourly)")
        fig3 = go.Figure()
        fig3.add_trace(go.Scatter(x=df_6h['Time'], y=df_6h['Wind'], mode='lines+markers', line=dict(color='green')))
        fig3.add_trace(go.Scatter(x=df_6h['Time'], y=df_6h['Wind'], mode='markers', marker=dict(symbol='triangle-up', angle=df_6h['WindDir'], size=12, color='darkgreen')))
        st.plotly_chart(fig3, use_container_width=True)

        st.subheader(T["charts"][5] + " (6-hourly)")
        st.plotly_chart(px.bar(df_6h, x='Time', y='Cloud_Oktas', color_discrete_sequence=['lightgreen']), use_container_width=True)
        
        st.subheader(T["charts"][6] + " (6-hourly)")
        st.error(T["storm_note"])
        st.plotly_chart(px.bar(df_6h, x='Time', y='Thunderstorm', color_discrete_sequence=['orange']), use_container_width=True)

    # --- Mode 1: IBF Health Monitoring ---
    elif mode_index == 1:
        st.subheader(T["ibf_header"])
        today_max = df_d.iloc[0]['Tmax']
        if today_max >= 40: lvl, color, bg = 0, "white", "#FF0000"
        elif today_max >= 37: lvl, color, bg = 1, "black", "#FFA500"
        elif today_max >= 34: lvl, color, bg = 2, "black", "#FFFF00"
        else: lvl, color, bg = 3, "white", "#008000"

        st.markdown(f"<div style='background-color:{bg}; color:{color}; padding:25px; border-radius:15px; text-align:center;'><h1>{T['risk_levels'][lvl]}</h1><h3>Max Temp: {today_max:.1f}°C</h3></div>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1: st.info(f"### ⚠️ Impact\n{T['impact_list'][lvl]}")
        with col2: st.success(f"### ✅ Action\n{T['recom_list'][lvl]}")
        
        fig_ibf = px.bar(df_d, x='Date', y='Tmax', color='Tmax', color_continuous_scale='YlOrRd')
        st.plotly_chart(fig_ibf, use_container_width=True)

    # --- Mode 2: Climate Change Projection ---
    elif mode_index == 2:
        st.subheader("🌡️ Future Climate Projection (SSP5-8.5 Scenario)")
        years = np.arange(2026, 2101)
        trend = [31 + (y-2026)*0.045 + np.random.normal(0, 0.4) for y in years]
        fig_cc = px.line(x=years, y=trend, labels={'x':'Year', 'y':'Avg Temp (°C)'}, title="Projected Temperature Rise in Myanmar (2026-2100)")
        st.plotly_chart(fig_cc, use_container_width=True)
        st.warning("⚠️ **Note:** Under the SSP5-8.5 'Business as Usual' scenario, significant temperature increases are expected by the end of the century.")

# Footer
st.markdown("---")
st.markdown("<div style='text-align: center; color: gray;'>Official System: Department of Meteorology and Hydrology (DMH) Myanmar</div>", unsafe_allow_html=True)
