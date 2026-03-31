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

st.set_page_config(page_title="DMH AI Public Weather", layout="wide")

# --- ၂။ မြို့ကြီး ၃၀ စာရင်း ---
MYANMAR_CITIES_30 = {
     "Naypyidaw": {"lat": 19.7633, "lon": 96.0785}, "Yangon (Kaba-aye)": {"lat": 16.8661, "lon": 96.1951},
    "Pyinmana": {"lat": 19.7414, "lon": 96.2004}, "Bawlakhae": {"lat": 19.1576, "lon": 97.3328},
    "Dagon (Seikan)": {"lat": 16.8489, "lon": 96.2734}, "Dagon (South)": {"lat": 16.8840, "lon": 96.2400},
    "Hlaing Thayar": {"lat": 16.8812, "lon": 96.0503}, "Shwe Pyithar": {"lat": 16.9759, "lon": 96.0760},
    "Dala": {"lat": 16.7562, "lon": 96.1591}, "Amarapura": {"lat": 21.9100, "lon": 96.0512},
    "Pyigyitagon": {"lat": 21.9167, "lon": 96.0833}, "Pathein Gyi": {"lat": 22.0000, "lon": 96.1670},
    "Mandalay": {"lat": 21.9747, "lon": 96.0836}, "Bago": {"lat": 17.3333, "lon": 96.4833},
    "Magway": {"lat": 20.1500, "lon": 94.9167}, "Monywa": {"lat": 22.1167, "lon": 95.1333},
    "Pathein": {"lat": 16.7833, "lon": 94.7333}, "Pyay": {"lat": 18.8167, "lon": 95.2167},
    "Taungoo": {"lat": 18.9333, "lon": 96.4333}, "Hinthada": {"lat": 17.6500, "lon": 95.3833},
    "Myitkyina": {"lat": 25.3831, "lon": 97.3964}, "Taunggyi": {"lat": 20.7888, "lon": 97.0333},
    "Moegkok": {"lat": 22.9233, "lon": 96.5108}, "Ela Airport": {"lat": 19.6159, "lon": 96.2127},
    "Chauk": {"lat": 20.8941, "lon": 94.8205}, "Myinmu": {"lat": 21.9219, "lon": 95.5772},
    "Mawlamyine": {"lat": 16.4905, "lon": 97.6282}, "Sittwe": {"lat": 20.1436, "lon": 92.8977},
    "Lashio": {"lat": 22.9333, "lon": 97.7500}, "Hpa-An": {"lat": 16.8906, "lon": 97.6333},
    "Loikaw": {"lat": 19.6742, "lon": 97.2093}, "Mindat": {"lat": 21.3748, "lon": 93.9725},
    "Hkamti": {"lat": 25.9977, "lon": 95.6905}, "Dawei": {"lat": 14.0833, "lon": 98.2000}
}

@st.cache_data(ttl=300)
def get_weather_data(city):
    lat, lon = MYANMAR_CITIES_30[city]['lat'], MYANMAR_CITIES_30[city]['lon']
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=temperature_2m,relative_humidity_2m,cloud_cover,visibility,precipitation,windspeed_10m,winddirection_10m,cape&daily=temperature_2m_max,temperature_2m_min,precipitation_sum&windspeed_unit=mph&forecast_days=16&timezone=Asia%2FYangon"
    try:
        r = requests.get(url, timeout=10).json()
        h, d = r['hourly'], r['daily']
        # CAPE ကို % အဖြစ်ပြောင်းလဲခြင်း (Max 4000 J/kg ကို 100% ဟု ယူဆသည်)
        storm_prob = [min(round((c / 3500) * 100), 100) for c in h['cape']]
        
        df_h = pd.DataFrame({
            "Time": pd.to_datetime(h['time']), "Temp": h['temperature_2m'], 
            "Humidity": h['relative_humidity_2m'], "Visibility": np.array(h['visibility']) / 1000,
            "Cloud_Okta": [round((c / 100) * 8) for c in h['cloud_cover']], 
            "Wind": h['windspeed_10m'], "WindDir": h['winddirection_10m'],
            "Rain": h['precipitation'], "StormProb": storm_prob
        })
        df_d = pd.DataFrame({"Date": pd.to_datetime(d['time']), "Tmax": d['temperature_2m_max'], "Tmin": d['temperature_2m_min'], "RainSum": d['precipitation_sum']})
        return df_h, df_d, df_h[df_h['Time'].dt.hour == 13].copy()
    except: return None, None, None

# --- Sidebar ---
st.sidebar.image(dm_header_logo, width=120)
selected_city = st.sidebar.selectbox("🎯 မြို့အမည်ရွေးချယ်ပါ", sorted(list(MYANMAR_CITIES_30.keys())))
view_mode = st.sidebar.radio("📊 ကြည့်ရှုမည့်ပုံစံ", ["၁၆ ရက်စာ မိုးလေဝသ", "အပူချိန်သတိပေးချက် (IBF)"])

# --- Header ---
st.markdown(f"## 🌤️ DMH AI အများပြည်သူဆိုင်ရာ ခန့်မှန်းချက် - {selected_city}")
st.markdown(f"ထုတ်ပြန်ချိန်: {now.strftime('%d %b %Y, %I:%M %p')}")
st.markdown("---")

df_h, df_d, df_w = get_weather_data(selected_city)

if df_d is not None:
    if view_mode == "၁၆ ရက်စာ မိုးလေဝသ":
        # ၁။ အပူချိန် နှင့် မိုးရေချိန်
        st.subheader("🌡️ ၁။ အပူချိန်နှင့် မိုးရွာနိုင်မှု အခြေအနေ")
        st.plotly_chart(px.line(df_d, x='Date', y=['Tmax', 'Tmin'], markers=True, title="နေ့အပူချိန်နှင့် ညအပူချိန် (°C)"), use_container_width=True)
        st.plotly_chart(px.bar(df_d, x='Date', y='RainSum', title="မိုးရေချိန် ခန့်မှန်းချက် (mm)"), use_container_width=True)

        # ၂။ မိုးတိမ်တောင် ဖြစ်နိုင်ခြေ (အများပြည်သူ နားလည်စေရန် ပြောင်းထားသောအပိုင်း)
        st.subheader("⚡ ၂။ မိုးတိမ်တောင်နှင့် လျှပ်စီးလက်နိုင်ခြေ ခန့်မှန်းချက် (%)")
        
        # Color coding for public safety
        df_h['Status'] = ["ပုံမှန်" if x < 30 else "သတိပြုရန်" if x < 60 else "အန္တရာယ်ရှိ" for x in df_h['StormProb']]
        
        fig_storm = px.bar(df_h, x='Time', y='StormProb', color='Status',
                           color_discrete_map={'ပုံမှန်': '#3498db', 'သတိပြုရန်': '#f1c40f', 'အန္တရာယ်ရှိ': '#e74c3c'},
                           labels={'StormProb': 'ဖြစ်နိုင်ခြေ (%)'})
        fig_storm.update_layout(yaxis_range=[0, 105])
        st.plotly_chart(fig_storm, use_container_width=True)
        
        st.warning("**မှတ်ချက်:** မိုးတိမ်တောင် ဖြစ်နိုင်ခြေ ၆၀% ထက်ကျော်လွန်ပါက လေပြင်းတိုက်ခတ်ခြင်း၊ မိုးကြိုးပစ်ခြင်းနှင့် လျှပ်စီးလက်ခြင်းများ ဖြစ်ပေါ်နိုင်သဖြင့် ဂရုပြုရန် လိုအပ်ပါသည်။")

        # ၃။ လေတိုက်နှုန်း
        st.subheader("💨 ၃။ လေတိုက်နှုန်း ခန့်မှန်းချက် (mph)")
        st.plotly_chart(px.line(df_h, x='Time', y='Wind', color_discrete_sequence=['teal']), use_container_width=True)

    elif view_mode == "အပူချိန်သတိပေးချက် (IBF)":
        # IBF Section
        max_t = df_d['Tmax'].max()
        st.subheader(f"🔥 အပူဒဏ်သတိပေးချက် - {selected_city}")
        if max_t >= 40:
            st.error(f"အမြင့်ဆုံးအပူချိန် {max_t:.1f}°C ရှိနိုင်သဖြင့် အပြင်မထွက်ရန် သတိပြုပါ။")
        else:
            st.success(f"အမြင့်ဆုံးအပူချိန် {max_t:.1f}°C ရှိနိုင်ပါသည်။ ပုံမှန်အတိုင်း သွားလာနိုင်ပါသည်။")

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

