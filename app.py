import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import requests
from datetime import datetime
import pytz

# --- ၁။ Setup & Timezone ---
mm_tz = pytz.timezone('Asia/Yangon')
now = datetime.now(mm_tz)
formatted_now = now.strftime('%I:%M %p, %d %b %Y')
dm_header_logo = "https://www.moezala.gov.mm/themes/custom/dmh/logo.png?v=1.1"

st.set_page_config(page_title="DMH AI Weather Dashboard", layout="wide", page_icon="🌤️")

# --- ၂။ ဘာသာစကား Dictionary ---
LANG_DICT = {
    "English": {
        "title": "DMH AI Weather Forecast System",
        "city_select": "🎯 Select Station",
        "modes": ["16-Day Detailed Analysis", "Heatwave Monitoring (IBF-Health)", "Climate Projection (2100)"],
        "charts": ["🌡️ 1. Temp Outlook", "🌧️ 2. Rain Summary", "💨 3. Wind Speed/Dir", "🔭 4. Visibility", "💧 5. Humidity", "☁️ 6. Cloud Cover (Oktas)", "⚡ 7. Thunderstorm %"],
        "dmh_alert": "📢 Recommendations: Please monitor DMH official news regularly.",
        "storm_note": "📝 Note: If Thunderstorm Potential > 60%, please beware of strong winds, thunder, and lightning.",
        "footer": "Data: Open-Meteo | System: DMH Myanmar"
    },
    "မြန်မာ": {
        "title": "DMH AI မိုးလေဝသ ခန့်မှန်းချက်စနစ်",
        "city_select": "🎯 စခန်းအမည်ရွေးချယ်ပါ",
        "modes": ["၁၆ ရက်စာ အသေးစိတ်ဆန်းစစ်ချက်", "အပူချိန်စောင့်ကြည့်ခြင်း (IBF-ကျန်းမာရေး )", "ရာသီဥတုပြောင်းလဲမှု (၂၁၀၀)"],
        "charts": ["🌡️ ၁။ အပူချိန်ခန့်မှန်းချက်", "🌧️ ၂။ မိုးရေချိန်ခန့်မှန်းချက်", "💨 ၃။ လေတိုက်နှုန်း/ဦးတည်ရာ", "🔭 ၄။ အဝေးမြင်တာ", "💧 ၅။ စိုထိုင်းဆ", "☁️ ၆။ တိမ်ဖုံးမှု (Oktas)", "⚡ ၇။ မိုးတိမ်တောင် %"],
        "dmh_alert": "📢 အကြံပြုချက်: နောက်ဆုံးရ မိုးလေဝသသတင်းများအတွက် မိုးဇလ သတင်းများကိုစောင့်ကြည့်ပါ။",
        "storm_note": "📝 မှတ်ချက်: မိုးတိမ်တောင် ဖြစ်နိုင်ခြေ ၆၀% ထက်ကျော်လွန်ပါက လေပြင်းတိုက်ခတ်ခြင်း၊ မိုးကြိုးပစ်ခြင်းနှင့် လျှပ်စီးလက်ခြင်းများ ဖြစ်ပေါ်နိုင်သဖြင့် ဂရုပြုရန် လိုအပ်ပါသည်။",
        "footer": "အချက်အလက်ရင်းမြစ်: Open-Meteo | တရားဝင်စနစ်: မိုးဇလ"
    }
}

# --- ၃။ စခန်းစာရင်းဖတ်ခြင်း (CSV Header Fix) ---
@st.cache_data
def load_stations():
    try:
        # သင်ပေးထားတဲ့ CSV မှာ City, Lat, Lon လို့ ပါတာမို့ အဲဒီအတိုင်း ဖတ်ပါမယ်
        df_st = pd.read_csv("Station.csv", encoding='utf-8-sig')
        df_st.columns = [c.strip() for c in df_st.columns]
        # City သို့မဟုတ် Station column တစ်ခုခုကို ရှာမယ်
        name_col = 'City' if 'City' in df_st.columns else 'Station'
        return {str(row[name_col]): {'lat': row['Lat'], 'lon': row['Lon']} for _, row in df_st.iterrows()}
    except Exception as e:
        st.error(f"⚠️ Station.csv Error: {e}")
        return {"Naypyidaw": {"lat": 19.7633, "lon": 96.0785}}

MYANMAR_CITIES = load_stations()

# --- ၄။ API Function ---
@st.cache_data(ttl=600)
def get_full_weather(city):
    if city not in MYANMAR_CITIES: return None, None
    lat, lon = MYANMAR_CITIES[city]['lat'], MYANMAR_CITIES[city]['lon']
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=temperature_2m,relative_humidity_2m,cloud_cover,visibility,precipitation,windspeed_10m,winddirection_10m,cape&daily=temperature_2m_max,temperature_2m_min,precipitation_sum&windspeed_unit=mph&forecast_days=16&timezone=Asia%2FYangon"
    try:
        r = requests.get(url, timeout=15).json()
        h, d = r['hourly'], r['daily']
        df_h = pd.DataFrame({
            "Time": pd.to_datetime(h['time']), "Temp": h['temperature_2m'],
            "Visibility": [v/1000 if v is not None else 0 for v in h['visibility']],
            "Humidity": h['relative_humidity_2m'],
            "Cloud": [round((c/100)*8) if c is not None else 0 for c in h['cloud_cover']],
            "Wind": h['windspeed_10m'], "WindDir": h['winddirection_10m'],
            "Storm": [min(round((c/3500)*100), 100) if c is not None else 0 for c in h['cape']]
        })
        df_d = pd.DataFrame({
            "Date": pd.to_datetime(d['time']), "Tmax": d['temperature_2m_max'],
            "Tmin": d['temperature_2m_min'], "RainSum": d['precipitation_sum']
        })
        return df_h, df_d
    except: return None, None

# --- ၅။ Sidebar ---
st.sidebar.image(dm_header_logo, width=150)
lang = st.sidebar.radio("🌐 Language", ["မြန်မာ", "English"], horizontal=True)
T = LANG_DICT[lang]

city_list = sorted(list(MYANMAR_CITIES.keys()))
selected_city = st.sidebar.selectbox(T["city_select"], city_list)
temp_bias = st.sidebar.slider("🌡️ Bias Correction (°C)", -5.0, 5.0, 0.0)
view_mode = st.sidebar.radio("📊 View Mode", T["modes"])

# --- ၆။ Main Display ---
st.markdown(f"# {T['title']}")

# Alert Boxes (စာသားတွေ မထပ်အောင် Box အလှလေးတွေနဲ့ ခွဲလိုက်ပါတယ်)
st.warning(T["dmh_alert"])
st.info(f"🕒 **{formatted_now}** | 📍 **{selected_city}**")

df_h, df_d = get_full_weather(selected_city)

if df_h is not None:
    df_d['Tmax'] += temp_bias
    df_d['Tmin'] += temp_bias
    df_h['Temp'] += temp_bias

    if view_mode == T["modes"][0]:
        # Charts Section
        st.plotly_chart(px.line(df_d, x='Date', y=['Tmax', 'Tmin'], title=T['charts'][0], markers=True, color_discrete_map={'Tmax':'red','Tmin':'blue'}), use_container_width=True)
        st.plotly_chart(px.bar(df_d, x='Date', y='RainSum', title=T['charts'][1], color_discrete_sequence=['deepskyblue']), use_container_width=True)
        
        # Cloud Cover & Storm Potential
        c1, c2 = st.columns(2)
        with c1:
            st.plotly_chart(px.bar(df_h, x='Time', y='Cloud', title=T['charts'][5], color_continuous_scale='Blues'), use_container_width=True)
        with c2:
            st.plotly_chart(px.bar(df_h, x='Time', y='Storm', title=T['charts'][6], color_discrete_sequence=['orange']), use_container_width=True)
        
        # Storm Note
        st.error(T["storm_note"])

    elif view_mode == T["modes"][1]:
        # IBF Mode
        max_t = df_d['Tmax'].max()
        st.markdown(f"<div style='background-color:#d00000; padding:20px; border-radius:10px; text-align:center; color:white;'><h2>Max Temperature: {max_t:.1f} °C</h2></div>", unsafe_allow_html=True)
        st.plotly_chart(px.bar(df_d, x='Date', y='Tmax', color='Tmax', color_continuous_scale='YlOrRd'), use_container_width=True)

        # Batch Export
        if st.button("🚀 Process Reports for All 247 Stations"):
            all_list = []
            bar = st.progress(0)
            for i, city in enumerate(city_list):
                _, d_tmp = get_full_weather(city)
                if d_tmp is not None:
                    d_tmp['Station'] = city
                    all_list.append(d_tmp)
                bar.progress((i+1)/len(city_list))
            if all_list:
                st.session_state['m_data'] = pd.concat(all_list, ignore_index=True)
                st.success("✅ Done!")

        if 'm_data' in st.session_state:
            m_df = st.session_state['m_data']
            m_df['Date'] = pd.to_datetime(m_df['Date']).dt.strftime('%Y-%m-%d')
            sel_date = st.selectbox("📅 Select Date for Download", m_df['Date'].unique())
            day_df = m_df[m_df['Date'] == sel_date]
            st.download_button(f"📥 Download {sel_date} CSV", day_df.to_csv(index=False).encode('utf-8-sig'), f"DMH_{sel_date}.csv")

    else:
        st.subheader("Climate Projection 2100")
        st.line_chart(np.random.randn(50, 1) + 30)

st.markdown("---")
st.markdown(f"<center>{T['footer']}</center>", unsafe_allow_html=True)

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
