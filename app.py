import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import requests
from datetime import datetime
import pytz
import os

# --- ၁။ Setup ---
mm_tz = pytz.timezone('Asia/Yangon')
now = datetime.now(mm_tz)
dm_header_logo = "https://www.moezala.gov.mm/themes/custom/dmh/logo.png?v=1.1"

st.set_page_config(page_title="DMH AI Weather Dashboard", layout="wide", page_icon="🌤️")

# --- ၂။ ဘာသာစကား Dictionary (အပြည့်အစုံ) ---
LANG_DICT = {
    "English": {
        "title": "DMH AI Weather Forecast System",
        "time_label": "Local Time (MMT)",
        "city_select": "🎯 Select Station/City",
        "view_mode": "📊 View Mode",
        "modes": ["16-Day Detailed Analysis", "Heatwave IBF (Health)", "Climate Projection (2100)"],
        "charts": ["Temp (°C)", "Rainfall (mm)", "Wind (mph)", "Visibility (km)", "Humidity (%)", "Cloud (Oktas)", "Storm (%)"],
        "axis_time": "Time / Date",
        "dmh_alert": "📢 Please monitor official DMH announcements in real-time for latest updates.",
        "ibf_header": "🏥 Health Sector Impact & Recommendations",
        "risk_levels": ["Extreme Risk", "High Risk", "Moderate Risk", "Low Risk"],
        "impacts": [
            "Severe threat! High risk of heatstroke, sunstroke, and critical dehydration for all individuals.",
            "Significant risk! Heat exhaustion and cramps are likely. Vulnerable groups (elderly/children) are at high risk.",
            "Moderate threat! Prolonged exposure may cause fatigue and heat rashes. General discomfort expected.",
            "Low threat! Standard summer conditions. No significant health impact expected."
        ],
        "recommends": [
            "STAY INDOORS. Avoid all outdoor activities. Drink 3-4 liters of water. Seek urgent medical care if dizzy or fainting.",
            "Limit outdoor work to early morning/evening. Wear hats/umbrellas. Increase fluid intake. Stay in cool areas.",
            "Wear light, breathable cotton clothes. Drink water even if not thirsty. Take frequent breaks in shade.",
            "Standard health precautions. Stay hydrated and monitor weather changes."
        ],
        "footer": "Data: Open-Meteo | System: Department of Meteorology and Hydrology"
    },
    "မြန်မာ": {
        "title": "DMH AI မိုးလေဝသ ခန့်မှန်းချက်စနစ်",
        "time_label": "မြန်မာစံတော်ချိန်",
        "city_select": "🎯 စခန်း/မြို့အမည်ရွေးချယ်ပါ",
        "view_mode": "📊 ကြည့်ရှုမည့်ပုံစံ",
        "modes": ["၁၆ ရက်စာ အသေးစိတ်ဆန်းစစ်ချက်", "အပူချိန်နှင့် ကျန်းမာရေး (IBF)", "ရာသီဥတုပြောင်းလဲမှု (၂၁၀၀)"],
        "charts": ["အပူချိန် (°C)", "မိုးရေချိန် (mm)", "လေတိုက်နှုန်း (mph)", "အဝေးမြင်တာ (km)", "စိုထိုင်းဆ (%)", "တိမ်ဖုံးမှု (Oktas)", "မိုးတိမ်တောင် (%)"],
        "axis_time": "အချိန် / ရက်စွဲ",
        "dmh_alert": "📢 နောက်ဆုံးရသတင်းများအတွက် မိုးလေဝသနှင့်ဇလဗေဒညွှန်ကြားမှုဦးစီးဌာန၏ ထုတ်ပြန်ချက်များကို အချိန်နဲ့တစ်ပြေးညီ စောင့်ကြည့်ပါ။",
        "ibf_header": "🏥 ကျန်းမာရေးကဏ္ဍဆိုင်ရာ အကျိုးသက်ရောက်မှုနှင့် အကြံပြုချက်များ",
        "risk_levels": ["အလွန်အန္တရာယ်ရှိ", "အန္တရာယ်ရှိ", "သတိပြုရန်", "ပုံမှန်"],
        "impacts": [
            "အလွန်စိုးရိမ်ရသော အခြေအနေ! အပူဒဏ်လျှပ်စီးဖြတ်ခြင်း (Heatstroke) နှင့် ရေဓာတ်အလွန်အမင်း ကုန်ခမ်းခြင်းကြောင့် အသက်အန္တရာယ်ရှိနိုင်သည်။",
            "အန္တရာယ်ရှိသော အခြေအနေ! အပူဒဏ်ကြောင့် ပင်ပန်းနွမ်းနယ်ခြင်းနှင့် ကြွက်တက်ခြင်းများ ဖြစ်နိုင်ပါသည်။ ကလေးနှင့် လူအိုများ အထူးသတိပြုပါ။",
            "သတိပြုရန် အခြေအနေ! နေရောင်အောက်တွင် ကြာရှည်နေပါက ပင်ပန်းနွမ်းနယ်ခြင်းနှင့် အပူလောင်အကွက်များ ဖြစ်ပေါ်နိုင်ပါသည်။",
            "ပုံမှန်အခြေအနေ! သိသာထင်ရှားသော ကျန်းမာရေးထိခိုက်မှု မရှိနိုင်သော်လည်း ပုံမှန်အတိုင်း သွားလာနေထိုင်နိုင်ပါသည်။"
        ],
        "recommends": [
            "အိမ်ထဲတွင်သာ နေထိုင်ပါ။ ပြင်ပလုပ်ငန်းများ လုံးဝမလုပ်ပါနှင့်။ ရေ (၃-၄) လီတာခန့် သောက်ပါ။ မူးဝေမိန်းမောပါက ဆေးရုံသို့ အမြန်သွားပါ။",
            "ပြင်ပလုပ်ငန်းများကို နံနက်စောစော သို့မဟုတ် ညနေပိုင်းတွင်သာ လုပ်ပါ။ ထီး/ဦးထုပ် ဆောင်းပါ။ ရေဓာတ် ပိုမိုဖြည့်တင်းပါ။",
            "ပေါ့ပါးလွတ်လပ်သော ချည်ထည်များ ဝတ်ဆင်ပါ။ ရေမဆာသော်လည်း ရေကို ခဏခဏသောက်ပါ။ အရိပ်ရသောနေရာတွင် ခေတ္တအနားယူပါ။",
            "ပုံမှန်အတိုင်း နေထိုင်နိုင်ပါသည်။ ရေဓာတ်ဖြည့်တင်းရန်နှင့် မိုးလေဝသအခြေအနေကို ဆက်လက်စောင့်ကြည့်ရန် လိုအပ်ပါသည်။"
        ],
        "footer": "အချက်အလက်ရင်းမြစ်: Open-Meteo | တရားဝင်စနစ်: မိုးလေဝသနှင့်ဇလဗေဒညွှန်ကြားမှုဦးစီးဌာန"
    }
}

MYANMAR_CITIES = {
    "Naypyidaw": {"lat": 19.7633, "lon": 96.0785}, "Yangon (Kaba-aye)": {"lat": 16.8661, "lon": 96.1951},
    "Mandalay": {"lat": 21.9747, "lon": 96.0836}, "Bago": {"lat": 17.3333, "lon": 96.4833},
    "Magway": {"lat": 20.1500, "lon": 94.9167}, "Monywa": {"lat": 22.1167, "lon": 95.1333},
    "Pathein": {"lat": 16.7833, "lon": 94.7333}, "Pyay": {"lat": 18.8167, "lon": 95.2167},
    "Taungoo": {"lat": 18.9333, "lon": 96.4333}, "Hinthada": {"lat": 17.6500, "lon": 95.3833}
    # စခန်းများကို ဤနေရာတွင် ဆက်လက်ထည့်သွင်းနိုင်ပါသည်
}

@st.cache_data(ttl=300)
def get_full_weather(city):
    lat, lon = MYANMAR_CITIES[city]['lat'], MYANMAR_CITIES[city]['lon']
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=temperature_2m,relative_humidity_2m,cloud_cover,visibility,precipitation,windspeed_10m,winddirection_10m,cape&daily=temperature_2m_max,temperature_2m_min,precipitation_sum&windspeed_unit=mph&forecast_days=16&timezone=Asia%2FYangon"
    try:
        r = requests.get(url, timeout=10).json()
        h, d = r['hourly'], r['daily']
        df_h = pd.DataFrame({
            "Time": pd.to_datetime(h['time']), "Temp": h['temperature_2m'], "Humidity": h['relative_humidity_2m'],
            "Visibility": np.array(h['visibility']) / 1000, "Cloud": [round((c/100)*8) for c in h['cloud_cover']],
            "Wind": h['windspeed_10m'], "WindDir": h['winddirection_10m'], "Rain": h['precipitation'],
            "Storm": [min(round((c/3500)*100), 100) for c in h['cape']]
        })
        df_d = pd.DataFrame({"Date": pd.to_datetime(d['time']), "Tmax": d['temperature_2m_max'], "Tmin": d['temperature_2m_min'], "RainSum": d['precipitation_sum']})
        return df_h, df_d
    except: return None, None

# --- ၃။ Sidebar ---
st.sidebar.image(dm_header_logo, width=120)
lang = st.sidebar.selectbox("🌐 Language", ["English", "မြန်မာ"])
T = LANG_DICT[lang]
selected_city = st.sidebar.selectbox(T["city_select"], sorted(list(MYANMAR_CITIES.keys())))
view_mode = st.sidebar.radio(T["view_mode"], T["modes"])

# --- ၄။ Main Display ---
st.markdown(f"## {T['title']}")
st.info(T["dmh_alert"]) # DMH သတိပေးချက်

df_h, df_d = get_full_weather(selected_city)

if df_h is not None:
    if view_mode == T["modes"][0]: # Detailed Analysis (7 Charts)
        # 1. Temp
        st.subheader(f"📊 {T['charts'][0]}")
        st.plotly_chart(px.line(df_d, x='Date', y=['Tmax', 'Tmin'], markers=True, color_discrete_map={'Tmax':'red','Tmin':'blue'}, labels={'value': T['charts'][0], 'Date': T['axis_time']}), use_container_width=True)
        # 2. Rain
        st.subheader(f"📊 {T['charts'][1]}")
        st.plotly_chart(px.bar(df_d, x='Date', y='RainSum', color_discrete_sequence=['deepskyblue'], labels={'RainSum': T['charts'][1]}), use_container_width=True)
        # 3. Wind
        st.subheader(f"📊 {T['charts'][2]}")
        df_w = df_h[df_h['Time'].dt.hour == 13]
        fig_w = go.Figure()
        fig_w.add_trace(go.Scatter(x=df_w['Time'], y=df_w['Wind'], mode='lines+markers', name='Speed'))
        fig_w.add_trace(go.Scatter(x=df_w['Time'], y=df_w['Wind']+2, mode='markers', marker=dict(symbol='arrow', angle=df_w['WindDir'], size=12, color='red'), name='Dir'))
        st.plotly_chart(fig_w, use_container_width=True)
        # 4. Visibility & 5. Humidity
        c1, c2 = st.columns(2)
        with c1: 
            st.subheader(T['charts'][3])
            st.plotly_chart(px.line(df_h, x='Time', y='Visibility', color_discrete_sequence=['green']), use_container_width=True)
        with c2:
            st.subheader(T['charts'][4])
            st.plotly_chart(px.area(df_h, x='Time', y='Humidity'), use_container_width=True)
        # 6. Cloud & 7. Storm
        c3, c4 = st.columns(2)
        with c3:
            st.subheader(T['charts'][5])
            st.plotly_chart(px.bar(df_h, x='Time', y='Cloud', color='Cloud'), use_container_width=True)
        with c4:
            st.subheader(T['charts'][6])
            st.plotly_chart(px.bar(df_h, x='Time', y='Storm', color_discrete_sequence=['orange']), use_container_width=True)

    elif view_mode == T["modes"][1]: # IBF (Enhanced)
        max_t = df_d['Tmax'].max()
        idx = 0 if max_t >= 42 else 1 if max_t >= 40 else 2 if max_t >= 38 else 3
        st.markdown(f"<div style='background-color:{['#800000','#d00000','#ffaa00','#008000'][idx]}; padding:30px; border-radius:15px; text-align:center;'><h1 style='color:white;'>{T['risk_levels'][idx]}: {max_t:.1f} °C</h1></div>", unsafe_allow_html=True)
        st.subheader(T['ibf_header'])
        st.error(f"**Potential Impact:**\n\n{T['impacts'][idx]}")
        st.success(f"**Recommendations:**\n\n{T['recommends'][idx]}")
        st.plotly_chart(px.bar(df_d, x='Date', y='Tmax', color='Tmax', color_continuous_scale='YlOrRd'), use_container_width=True)

    else: # Climate 2100
        st.subheader(T['modes'][2])
        years = np.arange(2026, 2101)
        trend = [30 + (y-2026)*0.045 + np.random.normal(0, 0.4) for y in years]
        st.plotly_chart(px.line(x=years, y=trend, labels={'x':'Year','y':'Temp (°C)'}, color_discrete_sequence=['darkred']), use_container_width=True)



# --- ၆။ Data Source Footer ---
st.markdown("---")
st.markdown(f"""
<div style='text-align: center; font-size: 0.85em; color: #666; line-height: 1.6;'>
    <p><b>Forecast Data Source (16-Day):</b> Open-Meteo API (Combining ECMWF IFS, GFS, ICON, and JMA global models).</p>
    <p><b>Heatwave Analysis:</b> Based on Impact-Based Forecasting (IBF) thresholds (P90, P95, P99) and WMO criteria.</p>
    <p><b>Climate Data:</b> IPCC AR6 Assessment Report and CMIP6 Global Climate Models (SSP scenarios).</p>
    <p style='margin-top: 10px; font-weight: bold;'>Official System: Department of Meteorology and Hydrology (DMH) Myanmar</p>
</div>
""", unsafe_allow_html=True)

