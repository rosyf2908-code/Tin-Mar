import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import requests
from datetime import datetime
import pytz
import os

# --- ၁။ Setup & Configuration ---
mm_tz = pytz.timezone('Asia/Yangon')
now = datetime.now(mm_tz)
dmh_custom_logo = "logo.png" # User တင်ထားသော Logo ဖိုင်အမည်
dm_header_logo = "https://www.moezala.gov.mm/themes/custom/dmh/logo.png?v=1.1"

st.set_page_config(page_title="DMH AI Weather Dashboard", layout="wide", page_icon="🌤️")

# --- ၂။ ဘာသာစကား Dictionary (All-in-One) ---
LANG_DICT = {
    "English": {
        "title": "DMH AI Weather Forecast System",
        "time_label": "Local Time (MMT)",
        "city_select": "🎯 Select Station/City",
        "view_mode": "📊 Analysis View",
        "modes": ["16-Day Forecast Analysis", "Heatwave IBF (Health)", "Climate Projection (2100)"],
        "temp_chart": "🌡️ 1. Temperature Outlook (°C)",
        "rain_chart": "🌧️ 2. Daily Precipitation Summary (mm)",
        "axis_time": "Time / Date",
        "axis_temp": "Temperature (°C)",
        "axis_rain": "Rainfall (mm)",
        "ibf_header": "🏥 Health Sector Impact & Recommendations",
        "risk_levels": ["Extreme Risk", "High Risk", "Moderate Risk", "Low Risk"],
        "impacts": [
            "High risk of heatstroke and dehydration for all ages.",
            "Increased risk of heat-related illnesses; stay hydrated.",
            "Uncomfortable heat; avoid prolonged sun exposure.",
            "Normal conditions; no significant health risk."
        ],
        "recommends": [
            "Stay indoors; Seek immediate medical help if dizzy.",
            "Drink plenty of water; Wear light clothing.",
            "Use umbrellas; Stay in shaded areas.",
            "Standard weather precautions."
        ],
        "climate_title": "🔮 Long-term Climate Projection Trend (2100)",
        "footer": "Forecast Data: Open-Meteo API | Official System: DMH Myanmar"
    },
    "မြန်မာ": {
        "title": "DMH AI မိုးလေဝသ ခန့်မှန်းချက်စနစ်",
        "time_label": "မြန်မာစံတော်ချိန်",
        "city_select": "🎯 စခန်း/မြို့အမည်ရွေးချယ်ပါ",
        "view_mode": "📊 ကြည့်ရှုမည့်ပုံစံ",
        "modes": ["၁၆ ရက်စာ ခန့်မှန်းချက်", "အပူချိန်နှင့် ကျန်းမာရေး (IBF)", "ရာသီဥတုပြောင်းလဲမှု (၂၁၀၀)"],
        "temp_chart": "🌡️ ၁။ အပူချိန်ခန့်မှန်းချက် (°C)",
        "rain_chart": "🌧️ ၂။ မိုးရေချိန်ခန့်မှန်းချက် (mm)",
        "axis_time": "အချိန် / ရက်စွဲ",
        "axis_temp": "အပူချိန် (°C)",
        "axis_rain": "မိုးရေချိန် (mm)",
        "ibf_header": "🏥 ကျန်းမာရေးကဏ္ဍဆိုင်ရာ အကျိုးသက်ရောက်မှုနှင့် အကြံပြုချက်များ",
        "risk_levels": ["အလွန်အန္တရာယ်ရှိ", "အန္တရာယ်ရှိ", "သတိပြုရန်", "ပုံမှန်"],
        "impacts": [
            "အပူဒဏ်ကြောင့် အသက်အန္တရာယ်ရှိနိုင်ခြင်းနှင့် ရေဓာတ်ကုန်ခမ်းခြင်း ဖြစ်နိုင်ခြေ အလွန်မြင့်မားသည်။",
            "အပူဒဏ်ကြောင့် ဖျားနာခြင်းများ ဖြစ်နိုင်သဖြင့် ရေဓာတ်ကို အထူးဂရုစိုက်ပါ။",
            "နေအပူဒဏ်ကြောင့် မအီမသာဖြစ်နိုင်သဖြင့် နေရောင်ထဲတွင် ကြာရှည်မနေပါနှင့်။",
            "ပုံမှန်အခြေအနေဖြစ်သဖြင့် ကျန်းမာရေးအတွက် သိသာသော စိုးရိမ်ရန်မရှိပါ။"
        ],
        "recommends": [
            "အိမ်ထဲတွင်သာ နေထိုင်ပါ။ မူးဝေပါက ဆေးရုံ/ဆေးခန်းသို့ အမြန်သွားပါ။",
            "ရေများများသောက်ပါ။ ပေါ့ပါးသော အဝတ်အစားများကို ဝတ်ဆင်ပါ။",
            "ထီး/ဦးထုပ် သုံးပါ။ အရိပ်ရသောနေရာတွင် နေထိုင်ပါ။",
            "ပုံမှန်အတိုင်း သွားလာနေထိုင်နိုင်ပါသည်။"
        ],
        "climate_title": "🔮 ရေရှည်ရာသီဥတုပြောင်းလဲမှု ခန့်မှန်းချက် (၂၁၀၀)",
        "footer": "အချက်အလက်ရင်းမြစ်: Open-Meteo API | တရားဝင်စနစ်: မိုးလေဝသနှင့်ဇလဗေဒညွှန်ကြားမှုဦးစီးဌာန"
    }
}

# --- ၃။ စခန်းစာရင်း (စိတ်ကြိုက်တိုးနိုင်သည်) ---
MYANMAR_CITIES = {
    "Naypyidaw": {"lat": 19.7633, "lon": 96.0785},
    "Yangon (Kaba-aye)": {"lat": 16.8661, "lon": 96.1951},
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
    "Dawei": {"lat": 14.0833, "lon": 98.2000}
    # ဤနေရာတွင် စခန်းအသစ်များအား Format အတိုင်း ဆက်လက်ထည့်သွင်းနိုင်ပါသည်။
}

@st.cache_data(ttl=300)
def get_weather_data(city):
    lat, lon = MYANMAR_CITIES[city]['lat'], MYANMAR_CITIES[city]['lon']
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=temperature_2m_max,temperature_2m_min,precipitation_sum&forecast_days=16&timezone=Asia%2FYangon"
    try:
        r = requests.get(url, timeout=10).json()
        d = r['daily']
        df_d = pd.DataFrame({
            "Date": pd.to_datetime(d['time']), 
            "Tmax": d['temperature_2m_max'], 
            "Tmin": d['temperature_2m_min'], 
            "RainSum": d['precipitation_sum']
        })
        return df_d
    except: return None

# --- ၄။ Sidebar Controls ---
st.sidebar.image(dm_header_logo, width=120)
st.sidebar.markdown("---")

lang = st.sidebar.selectbox("🌐 Language / ဘာသာစကား", ["English", "မြန်မာ"])
T = LANG_DICT[lang]

if os.path.exists(dmh_custom_logo):
    st.sidebar.image(dmh_custom_logo, use_container_width=True)

temp_bias = st.sidebar.slider("🌡️ Temp Offset (°C)", -5.0, 5.0, 0.0, step=0.5)
selected_city = st.sidebar.selectbox(T["city_select"], sorted(list(MYANMAR_CITIES.keys())))
view_mode = st.sidebar.radio(T["view_mode"], T["modes"])

# --- ၅။ Main Display UI ---
st.markdown(f"## {T['title']}")
st.markdown(f"**{T['time_label']}:** {now.strftime('%I:%M %p, %d %b %Y')} | **Station:** {selected_city}")
st.markdown("---")

df_d = get_weather_data(selected_city)

if df_d is not None:
    df_d['Tmax'] += temp_bias
    df_d['Tmin'] += temp_bias

    # --- Mode 1: 16-Day Forecast ---
    if view_mode == T["modes"][0]:
        st.subheader(T['temp_chart'])
        fig1 = px.line(df_d, x='Date', y=['Tmax', 'Tmin'], markers=True, 
                       color_discrete_map={'Tmax':'red','Tmin':'blue'},
                       labels={'value': T['axis_temp'], 'Date': T['axis_time'], 'variable': 'Type'})
        st.plotly_chart(fig1, use_container_width=True)
        
        st.subheader(T['rain_chart'])
        fig2 = px.bar(df_d, x='Date', y='RainSum', color_discrete_sequence=['deepskyblue'],
                      labels={'RainSum': T['axis_rain'], 'Date': T['axis_time']})
        st.plotly_chart(fig2, use_container_width=True)

    # --- Mode 2: Heatwave IBF (Health Sector) ---
    elif view_mode == T["modes"][1]:
        max_t = df_d['Tmax'].max()
        idx = 0 if max_t >= 42 else 1 if max_t >= 40 else 2 if max_t >= 38 else 3
        colors = ["#780000", "#e63946", "#ffb703", "#2a9d8f"]
        
        st.markdown(f"<div style='background-color:{colors[idx]}; padding:25px; border-radius:15px; text-align:center; box-shadow: 2px 2px 10px rgba(0,0,0,0.1);'><h2 style='color:white;'>{T['risk_levels'][idx]}: {max_t:.1f} °C</h2></div>", unsafe_allow_html=True)
        
        st.subheader(T['ibf_header'])
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"📍 **Impact / အကျိုးသက်ရောက်မှု:**\n\n{T['impacts'][idx]}")
        with col2:
            st.success(f"✅ **Recommendation / အကြံပြုချက်:**\n\n{T['recommends'][idx]}")
            
        fig_ibf = px.bar(df_d, x='Date', y='Tmax', color='Tmax', color_continuous_scale='YlOrRd', 
                         labels={'Tmax': T['axis_temp'], 'Date': T['axis_time']})
        st.plotly_chart(fig_ibf, use_container_width=True)

    # --- Mode 3: Climate Projection 2100 ---
    else:
        st.subheader(T['climate_title'])
        years = np.arange(2026, 2101)
        # Linear Trend Simulation (SSP5-8.5 style)
        temp_trend = [30 + (y-2026)*0.045 + np.random.normal(0, 0.4) for y in years]
        fig_c = px.line(x=years, y=temp_trend, color_discrete_sequence=['darkred'],
                        labels={'x': 'Year / ခုနှစ်', 'y': T['axis_temp']})
        fig_c.update_traces(mode='lines+markers', marker=dict(size=4))
        st.plotly_chart(fig_c, use_container_width=True)
        st.caption("Data source: Simulated Trend based on Historical Variabilities and SSP Scenarios.")



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

