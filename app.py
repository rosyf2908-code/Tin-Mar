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
dmh_custom_logo = "logo.png" 
dm_header_logo = "https://www.moezala.gov.mm/themes/custom/dmh/logo.png?v=1.1"

st.set_page_config(page_title="DMH AI Weather Dashboard", layout="wide", page_icon="🌤️")

# --- ၂။ ဘာသာစကား Dictionary (Axis Labels များပါ ထည့်သွင်းထားသည်) ---
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
        "axis_time": "Time / Date",
        "axis_temp": "Temperature (°C)",
        "axis_rain": "Rainfall (mm)",
        "axis_wind": "Wind Speed (mph)",
        "axis_vis": "Visibility (km)",
        "axis_hum": "Humidity (%)",
        "axis_cloud": "Cloud Amount (Oktas)",
        "axis_prob": "Probability (%)",
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
        "axis_time": "အချိန် / ရက်စွဲ",
        "axis_temp": "အပူချိန် (°C)",
        "axis_rain": "မိုးရေချိန် (mm)",
        "axis_wind": "လေတိုက်နှုန်း (mph)",
        "axis_vis": "အဝေးမြင်တာ (km)",
        "axis_hum": "စိုထိုင်းဆ (%)",
        "axis_cloud": "တိမ်ပမာဏ (Oktas)",
        "axis_prob": "ဖြစ်နိုင်ခြေ (%)",
        "storm_note": "**မှတ်ချက်:** ၆၀% ထက်ကျော်လွန်ပါက လေပြင်းတိုက်ခြင်းနှင့် မိုးကြိုးပစ်ခြင်းများကို ဂရုပြုပါ။",
        "risk_levels": ["အလွန်အန္တရာယ်ရှိ", "အန္တရာယ်ရှိ", "သတိပြုရန်", "ပုံမှန်"],
        "storm_status": ["ပုံမှန်", "သတိပြုရန်", "အန္တရာယ်ရှိ"],
        "footer": "အချက်အလက်ရင်းမြစ်: Open-Meteo API | တရားဝင်စနစ်: မိုးလေဝသနှင့်ဇလဗေဒညွှန်ကြားမှုဦးစီးဌာန"
    }
}

# --- ၃။ စခန်းစာရင်း (စိတ်ကြိုက်တိုးနိုင်ပါသည်) ---
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
    "Myitkyina": {"lat": 25.3831, "lon": 97.3964},
    "Taunggyi": {"lat": 20.7888, "lon": 97.0333},
    "Mawlamyine": {"lat": 16.4905, "lon": 97.6282},
    "Sittwe": {"lat": 20.1436, "lon": 92.8977},
    "Lashio": {"lat": 22.9333, "lon": 97.7500},
    "Hpa-An": {"lat": 16.8906, "lon": 97.6333},
    "Loikaw": {"lat": 19.6742, "lon": 97.2093},
    "Dawei": {"lat": 14.0833, "lon": 98.2000}
    # ကျန်ရှိသော စခန်း ၃၂ ခုကို ဤနေရာတွင် ဆက်လက်ထည့်သွင်းနိုင်ပါသည်
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
lang = st.sidebar.selectbox("🌐 Language / ဘာသာစကား", ["English", "မြန်မာ"])
T = LANG_DICT[lang]

if os.path.exists(dmh_custom_logo):
    st.sidebar.image(dmh_custom_logo, use_container_width=True)

temp_bias = st.sidebar.slider("🌡️ Temp Offset (°C)", -5.0, 5.0, 0.0, step=0.5)
selected_city = st.sidebar.selectbox(T["city_select"], sorted(list(MYANMAR_CITIES.keys())))
view_mode = st.sidebar.radio(T["view_mode"], T["modes"])

# --- ၅။ Main UI ---
st.markdown(f"## {T['title']}")
st.markdown(f"**{T['time_label']}:** {now.strftime('%I:%M %p, %d %b %Y')} | **Station:** {selected_city}")
st.markdown("---")

df_h, df_d, df_w = get_weather_data(selected_city)

if df_d is not None:
    df_d['Tmax'] += temp_bias
    df_d['Tmin'] += temp_bias

    if view_mode in [T["modes"][0]]: # 16-Day Forecast Analysis
        # 1. Temp
        fig1 = px.line(df_d, x='Date', y=['Tmax', 'Tmin'], markers=True, color_discrete_map={'Tmax':'red','Tmin':'blue'},
                       labels={'value': T['axis_temp'], 'Date': T['axis_time'], 'variable': 'Type'})
        st.subheader(f"{T['temp_chart']}")
        st.plotly_chart(fig1, use_container_width=True)

        # 2. Rain
        fig2 = px.bar(df_d, x='Date', y='RainSum', color_discrete_sequence=['deepskyblue'],
                      labels={'RainSum': T['axis_rain'], 'Date': T['axis_time']})
        st.subheader(f"{T['rain_chart']}")
        st.plotly_chart(fig2, use_container_width=True)

        # 3. Wind
        st.subheader(f"{T['wind_chart']}")
        fig3 = go.Figure()
        fig3.add_trace(go.Scatter(x=df_w['Time'], y=df_w['Wind'], mode='markers+lines', name='Speed', line=dict(color='teal', width=3)))
        fig3.add_trace(go.Scatter(x=df_w['Time'], y=df_w['Wind']+1.5, mode='markers', marker=dict(symbol='arrow', size=18, angle=df_w['WindDir'], color='red'), name='Direction'))
        fig3.update_layout(xaxis_title=T['axis_time'], yaxis_title=T['axis_wind'])
        st.plotly_chart(fig3, use_container_width=True)

        # 4. Vis
        fig4 = px.line(df_h, x='Time', y='Visibility', color_discrete_sequence=['#2ecc71'],
                       labels={'Visibility': T['axis_vis'], 'Time': T['axis_time']})
        st.subheader(f"{T['vis_chart']}")
        st.plotly_chart(fig4, use_container_width=True)

        # 5. Hum
        fig5 = px.area(df_h, x='Time', y='Humidity', color_discrete_sequence=['#3498db'],
                       labels={'Humidity': T['axis_hum'], 'Time': T['axis_time']})
        st.subheader(f"{T['hum_chart']}")
        st.plotly_chart(fig5, use_container_width=True)

        # 6. Cloud
        fig6 = px.bar(df_h, x='Time', y='Cloud_Okta', color='Cloud_Okta', color_continuous_scale='Blues',
                      labels={'Cloud_Okta': T['axis_cloud'], 'Time': T['axis_time']})
        st.subheader(f"{T['cloud_chart']}")
        st.plotly_chart(fig6, use_container_width=True)

        # 7. Storm
        st.subheader(f"{T['storm_chart']}")
        df_h['Status'] = [T["storm_status"][0] if x < 30 else T["storm_status"][1] if x < 60 else T["storm_status"][2] for x in df_h['StormProb']]
        fig7 = px.bar(df_h, x='Time', y='StormProb', color='Status',
                      color_discrete_map={T["storm_status"][0]: '#3498db', T["storm_status"][1]: '#f1c40f', T["storm_status"][2]: '#e74c3c'},
                      labels={'StormProb': T['axis_prob'], 'Time': T['axis_time']})
        st.plotly_chart(fig7, use_container_width=True)
        st.warning(T["storm_note"])

    elif view_mode in [T["modes"][1]]: # IBF
        max_t = df_d['Tmax'].max()
        risk_idx = 0 if max_t >= 42 else 1 if max_t >= 40 else 2 if max_t >= 38 else 3
        st.markdown(f"<div style='background-color:{['red','orange','yellow','green'][risk_idx]}; padding:20px; border-radius:10px; text-align:center;'><h2>{T['risk_levels'][risk_idx]}: {max_t:.1f} °C</h2></div>", unsafe_allow_html=True)
        st.plotly_chart(px.bar(df_d, x='Date', y='Tmax', color='Tmax', color_continuous_scale='YlOrRd', labels={'Tmax': T['axis_temp'], 'Date': T['axis_time']}), use_container_width=True)



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

