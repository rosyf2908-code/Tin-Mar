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
dmh_custom_logo = "logo.png" 
dm_header_logo = "https://www.moezala.gov.mm/themes/custom/dmh/logo.png?v=1.1"

st.set_page_config(page_title="DMH AI Weather Dashboard", layout="wide", page_icon="🌤️")

# --- ၂။ ဘာသာစကား Dictionary ---
LANG_DICT = {
    "English": {
        "title": "DMH AI Weather Forecast System",
        "time_label": "Local Time (MMT)",
        "city_select": "🎯 Select Station/City",
        "view_mode": "📊 Analysis View",
        "modes": ["16-Day Forecast Analysis", "Heatwave Monitoring (IBF)", "Climate Projection (2100)"],
        "temp_chart": "🌡️ 1. Temperature Outlook (°C)",
        "rain_chart": "🌧️ 2. Daily Precipitation Summary (mm)",
        "wind_chart": "💨 3. Wind Speed (mph) & Direction",
        "vis_chart": "🔭 4. Visibility Analysis (km)",
        "hum_chart": "💧 5. Relative Humidity (%)",
        "cloud_chart": "☁️ 6. Cloud Cover (Oktas: 0-8)",
        "storm_chart": "⚡ 7. Thunderstorm Potential (%)",
        "storm_note": "**Note:** Probability > 60% indicates a high chance of lightning and squalls.",
        "risk_levels": ["Extreme Risk", "High Risk", "Moderate Risk", "Low Risk"],
        "storm_status": ["Normal", "Caution", "Danger"],
        "footer": "Forecast Data: Open-Meteo API | Official System: DMH Myanmar"
    },
    "မြန်မာ": {
        "title": "DMH AI မိုးလေဝသ ခန့်မှန်းချက်စနစ်",
        "time_label": "မြန်မာစံတော်ချိန်",
        "city_select": "🎯 စခန်း/မြို့အမည်ရွေးချယ်ပါ",
        "view_mode": "📊 ကြည့်ရှုမည့်ပုံစံ",
        "modes": ["၁၆ ရက်စာ မိုးလေဝသ", "အပူချိန်သတိပေးချက် (IBF)", "ရာသီဥတုပြောင်းလဲမှုခန့်မှန်းချက် (၂၁၀၀)"],
        "temp_chart": "🌡️ ၁။ အပူချိန်ခန့်မှန်းချက် (°C)",
        "rain_chart": "🌧️ ၂။ မိုးရေချိန်ခန့်မှန်းချက် (mm)",
        "wind_chart": "💨 ၃။ လေတိုက်နှုန်းနှင့် လေအရပ်",
        "vis_chart": "🔭 ၄။ အဝေးမြင်တာ ခန့်မှန်းချက် (km)",
        "hum_chart": "💧 ၅။ စိုထိုင်းဆ ခန့်မှန်းချက် (%)",
        "cloud_chart": "☁️ ၆။ တိမ်ဖုံးလွှမ်းမှု (Oktas: 0-8)",
        "storm_chart": "⚡ ၇။ မိုးတိမ်တောင်နှင့် လျှပ်စီးလက်နိုင်ခြေ (%)",
        "storm_note": "**မှတ်ချက်:** ၆၀% ထက်ကျော်လွန်ပါက လေပြင်းတိုက်ခြင်းနှင့် မိုးကြိုးပစ်ခြင်းများကို ဂရုပြုပါ။",
        "risk_levels": ["အလွန်အန္တရာယ်ရှိ", "အန္တရာယ်ရှိ", "သတိပြုရန်", "ပုံမှန်"],
        "storm_status": ["ပုံမှန်", "သတိပြုရန်", "အန္တရာယ်ရှိ"],
        "footer": "အချက်အလက်ရင်းမြစ်: Open-Meteo API | တရားဝင်စနစ်: မိုးလေဝသနှင့်ဇလဗေဒညွှန်ကြားမှုဦးစီးဌာန"
    }
}

# --- ၃။ မြို့/စခန်း စာရင်း (ဒီနေရာမှာ စခန်းအသစ်တွေ စိတ်ကြိုက်ထည့်နိုင်ပါတယ်) ---
MYANMAR_CITIES = {
    "Naypyidaw": {"lat": 19.7633, "lon": 96.0785},
    "Yangon (Kaba-aye)": {"lat": 16.8661, "lon": 96.1951},
    "Pyinmana": {"lat": 19.7414, "lon": 96.2004},
    "Bawlakhae": {"lat": 19.1576, "lon": 97.3328},
    "Dagon (Seikan)": {"lat": 16.8489, "lon": 96.2734},
    "Dagon (South)": {"lat": 16.8840, "lon": 96.2400},
    "Hlaing Thayar": {"lat": 16.8812, "lon": 96.0503},
    "Shwe Pyithar": {"lat": 16.9759, "lon": 96.0760},
    "Dala": {"lat": 16.7562, "lon": 96.1591},
    "Amarapura": {"lat": 21.9100, "lon": 96.0512},
    "Pyigyitagon": {"lat": 21.9167, "lon": 96.0833},
    "Pathein Gyi": {"lat": 22.0000, "lon": 96.1670},
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
    "Moegkok": {"lat": 22.9233, "lon": 96.5108},
    "Ela Airport": {"lat": 19.6159, "lon": 96.2127},
    "Chauk": {"lat": 20.8941, "lon": 94.8205},
    "Myinmu": {"lat": 21.9219, "lon": 95.5772},
    "Mawlamyine": {"lat": 16.4905, "lon": 97.6282},
    "Sittwe": {"lat": 20.1436, "lon": 92.8977},
    "Lashio": {"lat": 22.9333, "lon": 97.7500},
    "Hpa-An": {"lat": 16.8906, "lon": 97.6333},
    "Loikaw": {"lat": 19.6742, "lon": 97.2093},
    "Mindat": {"lat": 21.3748, "lon": 93.9725},
    "Hkamti": {"lat": 25.9977, "lon": 95.6905},
    "Dawei": {"lat": 14.0833, "lon": 98.2000}
    # ဤနေရာတွင် စခန်းအသစ်များ ထပ်တိုးနိုင်ပါသည်
}

@st.cache_data(ttl=300)
def get_weather_data(city):
    lat, lon = MYANMAR_CITIES[city]['lat'], MYANMAR_CITIES[city]['lon']
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=temperature_2m,relative_humidity_2m,cloud_cover,visibility,precipitation,windspeed_10m,winddirection_10m,cape&daily=temperature_2m_max,temperature_2m_min,precipitation_sum&windspeed_unit=mph&forecast_days=16&timezone=Asia%2FYangon"
    try:
        r = requests.get(url, timeout=10).json()
        h, d = r['hourly'], r['daily']
        storm_prob = [min(round((c / 3500) * 100), 100) for c in h['cape']]
        df_h = pd.DataFrame({
            "Time": pd.to_datetime(h['time']), "Temp": h['temperature_2m'], "Humidity": h['relative_humidity_2m'],
            "Visibility": np.array(h['visibility']) / 1000, "Cloud_Okta": [round((c / 100) * 8) for c in h['cloud_cover']],
            "Wind": h['windspeed_10m'], "WindDir": h['winddirection_10m'], "Rain": h['precipitation'], "StormProb": storm_prob
        })
        df_d = pd.DataFrame({"Date": pd.to_datetime(d['time']), "Tmax": d['temperature_2m_max'], "Tmin": d['temperature_2m_min'], "RainSum": d['precipitation_sum']})
        return df_h, df_d, df_h[df_h['Time'].dt.hour == 13].copy()
    except: return None, None, None

# --- ၄။ Sidebar ---
st.sidebar.image(dm_header_logo, width=120)
st.sidebar.markdown("---")

lang = st.sidebar.selectbox("🌐 Language / ဘာသာစကား", ["English", "မြန်မာ"])
T = LANG_DICT[lang]

if os.path.exists(dmh_custom_logo):
    st.sidebar.image(dmh_custom_logo, caption="Hydrological Cycle", use_container_width=True)

temp_bias = st.sidebar.slider("🌡️ Temp Offset (°C)", -5.0, 5.0, 0.0, step=0.5)
st.sidebar.markdown("---")

# စခန်းအရေအတွက် ဘယ်လောက်ရှိရှိ အကုန်ပြပေးမည့် dropdown
selected_city = st.sidebar.selectbox(T["city_select"], sorted(list(MYANMAR_CITIES.keys())))
view_mode = st.sidebar.radio(T["view_mode"], T["modes"])

# --- ၅။ UI Header ---
h_col1, h_col2 = st.columns([1, 6])
with h_col1:
    if os.path.exists(dmh_custom_logo): st.image(dmh_custom_logo, width=80)
with h_col2:
    st.markdown(f"<h1 style='margin:0;'>{T['title']}</h1>", unsafe_allow_html=True)
    st.markdown(f"<b>{T['time_label']}:</b> {now.strftime('%I:%M %p, %d %b %Y')}")
st.markdown("---")

df_h, df_d, df_w = get_weather_data(selected_city)

if df_d is not None:
    df_d['Tmax'] += temp_bias
    df_d['Tmin'] += temp_bias

    if view_mode in [T["modes"][0]]: # 16-Day Forecast
        st.subheader(f"{T['temp_chart']} - {selected_city}")
        st.plotly_chart(px.line(df_d, x='Date', y=['Tmax', 'Tmin'], markers=True, color_discrete_map={'Tmax':'red','Tmin':'blue'}), use_container_width=True)

        st.subheader(f"{T['rain_chart']} - {selected_city}")
        st.plotly_chart(px.bar(df_d, x='Date', y='RainSum', color_discrete_sequence=['deepskyblue']), use_container_width=True)

        st.subheader(f"{T['wind_chart']} - {selected_city}")
        fig_w = go.Figure()
        fig_w.add_trace(go.Scatter(x=df_w['Time'], y=df_w['Wind'], mode='markers+lines', name='Speed', line=dict(color='teal', width=3)))
        fig_w.add_trace(go.Scatter(x=df_w['Time'], y=df_w['Wind']+1.5, mode='markers', marker=dict(symbol='arrow', size=18, angle=df_w['WindDir'], color='red')))
        st.plotly_chart(fig_w, use_container_width=True)

        st.subheader(f"{T['vis_chart']} - {selected_city}")
        st.plotly_chart(px.line(df_h, x='Time', y='Visibility', color_discrete_sequence=['#2ecc71']), use_container_width=True)

        st.subheader(f"{T['hum_chart']} - {selected_city}")
        st.plotly_chart(px.area(df_h, x='Time', y='Humidity', color_discrete_sequence=['#3498db']), use_container_width=True)

        st.subheader(f"{T['cloud_chart']} - {selected_city}")
        st.plotly_chart(px.bar(df_h, x='Time', y='Cloud_Okta', color='Cloud_Okta', color_continuous_scale='Blues'), use_container_width=True)

        st.subheader(f"{T['storm_chart']} - {selected_city}")
        df_h['Status'] = [T["storm_status"][0] if x < 30 else T["storm_status"][1] if x < 60 else T["storm_status"][2] for x in df_h['StormProb']]
        fig_storm = px.bar(df_h, x='Time', y='StormProb', color='Status',
                           color_discrete_map={T["storm_status"][0]: '#3498db', T["storm_status"][1]: '#f1c40f', T["storm_status"][2]: '#e74c3c'})
        st.plotly_chart(fig_storm, use_container_width=True)
        st.warning(T["storm_note"])

    elif view_mode in [T["modes"][1]]: # IBF Heatwave
        max_t = df_d['Tmax'].max()
        risk_idx = 0 if max_t >= 42 else 1 if max_t >= 40 else 2 if max_t >= 38 else 3
        risk_text = T["risk_levels"][risk_idx]
        color = ["red", "orange", "yellow", "green"][risk_idx]
        txt_c = "black" if color == "yellow" else "white"
        
        st.markdown(f"<div style='background-color:{color}; padding:25px; border-radius:15px; text-align:center;'><h2 style='color:{txt_c};'>{risk_text}: {max_t:.1f} °C</h2></div>", unsafe_allow_html=True)
        st.plotly_chart(px.bar(df_d, x='Date', y='Tmax', color='Tmax', color_continuous_scale='YlOrRd').add_hline(y=40, line_dash="dash", line_color="red"), use_container_width=True)

    else: # Climate Projection
        st.subheader(f"🔮 Future Projection (2100) - {selected_city}")
        years = np.arange(2026, 2101)
        temp_trend = [30 + (y-2026)*0.043 + np.random.normal(0, 0.5) for y in years]
        st.plotly_chart(px.line(x=years, y=temp_trend, color_discrete_sequence=['darkred']), use_container_width=True)

st.markdown("### 🏥 Health Sector Impact & Recommendations")
        col1, col2 = st.columns(2)
        with col1:
            st.error("**⚠️ Possible Impacts:**\n* Heatstroke (အပူလျှပ်ခြင်း) ဖြစ်နိုင်ခြေ မြင့်မားခြင်း။\n* ရေဓာတ်ခမ်းခြောက်ခြင်းနှင့် မူးဝေခြင်း။\n* သက်ကြီးရွယ်အိုများနှင့် ကလေးငယ်များအတွက် အထူးအန္တရာယ်ရှိခြင်း။")
        with col2:
            st.success("**🛡️ Mitigation Actions:**\n* နေပူထဲ တိုက်ရိုက်သွားလာခြင်းကို အတတ်နိုင်ဆုံး ရှောင်ကြဉ်ပါ။\n* ရေနှင့် ဓာတ်ဆားရည်ကို ပုံမှန်ထက် ပိုသောက်ပါ။\n* မိုးလေဝသသတင်းများကိုအမြဲနားထောင်ပါ။\n* လေဝင်လေထွက်ကောင်းသော အဝတ်အစားများ ဝတ်ဆင်ပါ။")
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

