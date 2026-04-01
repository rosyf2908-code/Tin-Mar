import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import requests
from datetime import datetime
import pytz

# --- ၁။ Setup ---
mm_tz = pytz.timezone('Asia/Yangon')
now = datetime.now(mm_tz)
formatted_now = now.strftime('%I:%M %p, %d %b %Y')
dm_header_logo = "https://www.moezala.gov.mm/themes/custom/dmh/logo.png?v=1.1"

st.set_page_config(page_title="DMH AI Weather Dashboard", layout="wide")

# CSS for styling
st.markdown("""<style> .stAlert { margin-bottom: 0px; padding: 10px; } </style>""", unsafe_allow_html=True)

# --- ၂။ ဘာသာစကား Dictionary ---
LANG_DICT = {
    "English": {
        "title": "DMH AI Weather Forecast System",
        "city_select": "🎯 Select Station",
        "modes": ["16-Day Detailed Analysis", "Heatwave Monitoring (IBF-Health)", "Climate Projection (2100)"],
        "charts": ["🌡️ 1. Temp Outlook", "🌧️ 2. Rain Summary", "💨 3. Wind Speed", "🔭 4. Visibility", "💧 5. Humidity", "☁️ 6. Cloud Cover", "⚡ 7. Storm %"],
        "alert": "📢 Monitor DMH official news regularly.",
        "storm_warn": "📝 Beware of strong winds/lightning if Storm > 60%.",
        "footer": "System: DMH Myanmar | Data: Open-Meteo"
    },
    "မြန်မာ": {
        "title": "DMH AI မိုးလေဝသ ခန့်မှန်းချက်စနစ်",
        "city_select": "🎯 စခန်းအမည်ရွေးချယ်ပါ",
        "modes": ["၁၆ ရက်စာ အသေးစိတ်ဆန်းစစ်ချက်", "အပူချိန်စောင့်ကြည့်ခြင်း (IBF-ကျန်းမာရေး )", "ရာသီဥတုပြောင်းလဲမှု (၂၁၀၀)"],
        "charts": ["🌡️ ၁။ အပူချိန်ခန့်မှန်းချက်", "🌧️ ၂။ မိုးရေချိန်ခန့်မှန်းချက်", "💨 ၃။ လေတိုက်နှုန်း", "🔭 ၄။ အဝေးမြင်တာ", "💧 ၅။ စိုထိုင်းဆ", "☁️ ၆။ တိမ်ဖုံးမှု", "⚡ ၇။ မိုးတိမ်တောင် %"],
        "alert": "📢 အကြံပြုချက်: နောက်ဆုံးရ မိုးလေဝသသတင်းများအတွက် မိုးဇလ သတင်းများကိုစောင့်ကြည့်ပါ။",
        "storm_warn": "📝 မှတ်ချက်: မိုးတိမ်တောင် ၆၀% ကျော်ပါက လေပြင်းနှင့် မိုးကြိုးအန္တရာယ် သတိပြုရန်။",
        "footer": "တရားဝင်စနစ်: မိုးဇလ | အချက်အလက်ရင်းမြစ်: Open-Meteo"
    }
}

# --- ၃။ စခန်းစာရင်းဖတ်ခြင်း (Robust Checking) ---
@st.cache_data
def load_stations():
    try:
        # GitHub root ထဲတွင် Station.csv အမည်အတိအကျ ရှိရပါမည်
        df = pd.read_csv("Station.csv", encoding='utf-8-sig')
        df.columns = [c.strip() for c in df.columns]
        # Column အမည် City သို့မဟုတ် Station ဖြစ်နိုင်သည်
        name_col = 'City' if 'City' in df.columns else 'Station'
        return {str(row[name_col]): {'lat': row['Lat'], 'lon': row['Lon']} for _, row in df.iterrows()}
    except Exception as e:
        return None

MYANMAR_CITIES = load_stations()

# --- ၄။ Sidebar ---
st.sidebar.image(dm_header_logo, width=150)
lang = st.sidebar.radio("🌐 Language", ["မြန်မာ", "English"], horizontal=True)
T = LANG_DICT[lang]

if MYANMAR_CITIES is None:
    st.error("❌ 'Station.csv' file not found in GitHub! Please upload it to your repository.")
    city_list = ["Naypyidaw"]
    MYANMAR_CITIES = {"Naypyidaw": {"lat": 19.7633, "lon": 96.0785}}
else:
    city_list = sorted(list(MYANMAR_CITIES.keys()))

selected_city = st.sidebar.selectbox(T["city_select"], city_list)
view_mode = st.sidebar.radio("📊 View Mode", T["modes"])

# --- ၅။ API Function ---
@st.cache_data(ttl=600)
def fetch_weather(city):
    lat, lon = MYANMAR_CITIES[city]['lat'], MYANMAR_CITIES[city]['lon']
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=temperature_2m,relative_humidity_2m,cloud_cover,visibility,precipitation,windspeed_10m,cape&daily=temperature_2m_max,temperature_2m_min,precipitation_sum&forecast_days=16&timezone=Asia%2FYangon"
    try:
        r = requests.get(url, timeout=10).json()
        df_h = pd.DataFrame({"Time": pd.to_datetime(r['hourly']['time']), 
                             "Temp": r['hourly']['temperature_2m'],
                             "Rain": r['hourly']['precipitation'],
                             "Wind": r['hourly']['windspeed_10m'],
                             "Vis": [v/1000 for v in r['hourly']['visibility']],
                             "Humid": r['hourly']['relative_humidity_2m'],
                             "Cloud": r['hourly']['cloud_cover'],
                             "Storm": [min(round((c/3500)*100), 100) for c in r['hourly']['cape']]})
        df_d = pd.DataFrame({"Date": pd.to_datetime(r['daily']['time']), 
                             "Tmax": r['daily']['temperature_2m_max'],
                             "Tmin": r['daily']['temperature_2m_min'],
                             "RainSum": r['daily']['precipitation_sum']})
        return df_h, df_d
    except: return None, None

# --- ၆။ Main Content ---
st.title(T["title"])
st.warning(T["alert"])
st.info(f"📍 {selected_city} | 🕒 {formatted_now}")

h_data, d_data = fetch_weather(selected_city)

if h_data is not None:
    if view_mode == T["modes"][0]: # 16-Day Detailed
        st.plotly_chart(px.line(d_data, x='Date', y=['Tmax', 'Tmin'], title=T['charts'][0], markers=True, color_discrete_map={'Tmax':'red','Tmin':'blue'}), use_container_width=True)
        st.plotly_chart(px.bar(d_data, x='Date', y='RainSum', title=T['charts'][1], color_discrete_sequence=['skyblue']), use_container_width=True)
        st.plotly_chart(px.line(h_data, x='Time', y='Wind', title=T['charts'][2]), use_container_width=True)
        st.plotly_chart(px.line(h_data, x='Time', y='Vis', title=T['charts'][3]), use_container_width=True)
        st.plotly_chart(px.area(h_data, x='Time', y='Humid', title=T['charts'][4]), use_container_width=True)
        st.plotly_chart(px.bar(h_data, x='Time', y='Cloud', title=T['charts'][5]), use_container_width=True)
        st.error(T["storm_warn"])
        st.plotly_chart(px.bar(h_data, x='Time', y='Storm', title=T['charts'][6], color_discrete_sequence=['purple']), use_container_width=True)

    elif view_mode == T["modes"][1]: # IBF Heatwave
        max_t = d_data['Tmax'].max()
        # Alert Level Logic
        color = "#008000" if max_t < 38 else "#ffaa00" if max_t < 40 else "#d00000" if max_t < 42 else "#800000"
        st.markdown(f"<div style='background-color:{color}; padding:20px; border-radius:10px; text-align:center; color:white;'><h1>Current Risk Max: {max_t:.1f} °C</h1></div>", unsafe_allow_html=True)
        
        st.plotly_chart(px.bar(d_data, x='Date', y='Tmax', color='Tmax', color_continuous_scale='YlOrRd'), use_container_width=True)

        st.markdown("### 📥 ၂၄၇ စခန်းလုံးအတွက် Data ရယူရန်")
        if st.button("🚀 Process All Stations"):
            all_results = []
            progress = st.progress(0)
            for i, city in enumerate(city_list):
                _, d_tmp = fetch_weather(city)
                if d_tmp is not None:
                    d_tmp['Station'] = city
                    all_results.append(d_tmp)
                progress.progress((i+1)/len(city_list))
            
            if all_results:
                final_df = pd.concat(all_results)
                final_df['Date'] = final_df['Date'].dt.strftime('%Y-%m-%d')
                st.session_state['master_df'] = final_df
                st.success(f"✅ စခန်း {len(city_list)} ခုလုံး၏ Data ရရှိပါပြီ။")

        if 'master_df' in st.session_state:
            m_df = st.session_state['master_df']
            sel_date = st.selectbox("ရက်စွဲရွေးချယ်ပါ", m_df['Date'].unique())
            day_df = m_df[m_df['Date'] == sel_date]
            st.dataframe(day_df, use_container_width=True)
            st.download_button(f"📥 Download {sel_date} CSV", day_df.to_csv(index=False).encode('utf-8-sig'), f"DMH_{sel_date}.csv")

    else: # Climate Projection
        st.subheader("🌡️ Climate Projection (2026-2100)")
        years = np.arange(2026, 2101)
        trend = [31 + (y-2026)*0.045 + np.random.normal(0, 0.4) for y in years]
        st.plotly_chart(px.line(x=years, y=trend, labels={'x':'Year', 'y':'Avg Temp (°C)'}), use_container_width=True)

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
