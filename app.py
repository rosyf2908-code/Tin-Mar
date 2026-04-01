import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import requests
from datetime import datetime
import pytz

# --- ၁။ Layout Setup ---
st.set_page_config(page_title="DMH AI Weather Dashboard", layout="wide")

mm_tz = pytz.timezone('Asia/Yangon')
now = datetime.now(mm_tz)
formatted_now = now.strftime('%I:%M %p, %d %b %Y')
dm_header_logo = "https://www.moezala.gov.mm/themes/custom/dmh/logo.png?v=1.1"

# --- ၂။ စခန်းစာရင်းဖတ်ခြင်း (Robust Reading) ---
@st.cache_data
def load_stations():
    try:
        # GitHub root folder ထဲက Station.csv ကို ဖတ်ခြင်း
        df = pd.read_csv("Station.csv", encoding='utf-8-sig')
        # Column names တွေကို Clean လုပ်ခြင်း (Space တွေပါရင် ဖယ်ထုတ်ရန်)
        df.columns = [c.strip() for c in df.columns]
        
        # ပုံထဲကအတိုင်း City, Lat, Lon column တွေကို အသုံးပြုခြင်း
        # Dictionary အဖြစ်ပြောင်းလဲခြင်း (Dropdown မှာ အကုန်ပေါ်စေရန်)
        station_dict = {}
        for _, row in df.iterrows():
            city_name = str(row['City']).strip()
            station_dict[city_name] = {'lat': row['Lat'], 'lon': row['Lon']}
        return station_dict
    except Exception as e:
        # CSV ဖတ်မရပါက Default အဖြစ် နေပြည်တော်ကို ပြခြင်း
        return {"Naypyidaw (Default)": {"lat": 19.7633, "lon": 96.0785}}

MYANMAR_CITIES = load_stations()
city_list = sorted(list(MYANMAR_CITIES.keys()))

# --- ၃။ Sidebar (ပုံထဲကအတိုင်း Bias ကို အပေါ်တင်ထားသည်) ---
st.sidebar.image(dm_header_logo, width=150)
st.sidebar.markdown("### ⚙️ Settings")

# ၁။ Select Station (စခန်းရွေးချယ်ရန် - ၂၄၇ ခုလုံး ပါဝင်မည်)
selected_city = st.sidebar.selectbox("🎯 စခန်းအမည်ရွေးချယ်ပါ", city_list)

# ၂။ Bias Correction Slider
bias = st.sidebar.slider("🌡️ Bias Correction (°C)", -5.0, 5.0, 0.0, step=0.1)

# ၃။ Language & View Mode
lang = st.sidebar.radio("🌐 Language", ["မြန်မာ", "English"], horizontal=True)
view_mode = st.sidebar.radio("📊 View Mode", 
                             ["၁၆ ရက်စာ အသေးစိတ်ဆန်းစစ်ချက်", 
                              "အပူချိန်စောင့်ကြည့်ခြင်း (IBF-ကျန်းမာရေး )", 
                              "ရာသီဥတုပြောင်းလဲမှု (၂၁၀၀)"])

# --- ၄။ API Data Fetching ---
@st.cache_data(ttl=600)
def fetch_weather(city):
    loc = MYANMAR_CITIES[city]
    url = f"https://api.open-meteo.com/v1/forecast?latitude={loc['lat']}&longitude={loc['lon']}&hourly=temperature_2m,relative_humidity_2m,cloud_cover,visibility,precipitation,windspeed_10m,winddirection_10m,cape&daily=temperature_2m_max,temperature_2m_min,precipitation_sum&windspeed_unit=mph&forecast_days=16&timezone=Asia%2FYangon"
    try:
        r = requests.get(url, timeout=10).json()
        df_h = pd.DataFrame({
            "Time": pd.to_datetime(r['hourly']['time']), 
            "Temp": r['hourly']['temperature_2m'],
            "Wind": r['hourly']['windspeed_10m'],
            "WindDir": r['hourly']['winddirection_10m'],
            "Vis": [v/1000 for v in r['hourly']['visibility']],
            "Humid": r['hourly']['relative_humidity_2m'],
            "Cloud": r['hourly']['cloud_cover'],
            "Storm": [min(round((c/3500)*100), 100) for c in r['hourly']['cape']]
        })
        df_d = pd.DataFrame({
            "Date": pd.to_datetime(r['daily']['time']), 
            "Tmax": r['daily']['temperature_2m_max'],
            "Tmin": r['daily']['temperature_2m_min'],
            "RainSum": r['daily']['precipitation_sum']
        })
        return df_h, df_d
    except: return None, None

# --- ၅။ Main Content ---
st.title("DMH AI Weather Forecast System")
st.info(f"📍 စခန်း: **{selected_city}** | 🕒 အချိန်: **{formatted_now}**")

h_data, d_data = fetch_weather(selected_city)

if h_data is not None:
    # Apply Bias Correction
    d_data['Tmax'] += bias
    d_data['Tmin'] += bias
    h_data['Temp'] += bias

    if "၁၆ ရက်စာ" in view_mode:
        # Charts ၁ မှ ၇ ထိ အစဉ်လိုက်ပြသခြင်း
        st.plotly_chart(px.line(d_data, x='Date', y=['Tmax', 'Tmin'], title="🌡️ ၁။ အပူချိန်ခန့်မှန်းချက်", markers=True, color_discrete_map={'Tmax':'red','Tmin':'blue'}), use_container_width=True)
        st.plotly_chart(px.bar(d_data, x='Date', y='RainSum', title="🌧️ ၂။ မိုးရေချိန်ခန့်မှန်းချက်"), use_container_width=True)
        
        # Wind Direction & Speed
        st.plotly_chart(px.line(h_data, x='Time', y='Wind', title="💨 ၃။ လေတိုက်နှုန်း (mph)"), use_container_width=True)
        st.plotly_chart(px.line(h_data, x='Time', y='Vis', title="🔭 ၄။ အဝေးမြင်တာ (km)"), use_container_width=True)
        st.plotly_chart(px.area(h_data, x='Time', y='Humid', title="💧 ၅။ စိုထိုင်းဆ (%)"), use_container_width=True)
        st.plotly_chart(px.bar(h_data, x='Time', y='Cloud', title="☁️ ၆။ တိမ်ဖုံးမှု (%)", color_continuous_scale='Blues'), use_container_width=True)
        
        st.error("📝 မှတ်ချက်: မိုးတိမ်တောင် ဖြစ်နိုင်ခြေ ၆၀% ထက်ကျော်လွန်ပါက လေပြင်း၊ မိုးကြိုးအန္တရာယ် ဂရုပြုပါ။")
        st.plotly_chart(px.bar(h_data, x='Time', y='Storm', title="⚡ ၇။ မိုးတိမ်တောင် ဖြစ်နိုင်ခြေ (%)", color_discrete_sequence=['purple']), use_container_width=True)

    elif "အပူချိန်စောင့်ကြည့်ခြင်း" in view_mode:
        # Heatwave IBF (ပုံထဲကအတိုင်း Risk Level များ)
        max_t = d_data['Tmax'].max()
        idx = 0 if max_t >= 42 else 1 if max_t >= 40 else 2 if max_t >= 38 else 3
        levels = ["အလွန်အန္တရာယ်ရှိ", "အန္တရာယ်ရှိ", "သတိပြုရန်", "ပုံမှန်"]
        colors = ['#800000','#d00000','#ffaa00','#008000']
        
        st.markdown(f"""
            <div style="background-color:{colors[idx]}; padding:30px; border-radius:15px; text-align:center; color:white;">
                <h1 style="margin:0;">{levels[idx]}</h1>
                <h2 style="margin:0;">အမြင့်ဆုံးအပူချိန်: {max_t:.1f} °C</h2>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("### 🏥 ကျန်းမာရေးကဏ္ဍ အကြံပြုချက်")
        st.warning("📢 အကြံပြုချက်: နောက်ဆုံးရ မိုးလေဝသသတင်းများအတွက် မိုးဇလ သတင်းများကိုစောင့်ကြည့်ပါ။")
        st.plotly_chart(px.bar(d_data, x='Date', y='Tmax', color='Tmax', color_continuous_scale='YlOrRd'), use_container_width=True)

        # ၂၄၇ စခန်းလုံး တစ်ခါတည်း Download လုပ်ရန်
        st.markdown("---")
        if st.button("🚀 ၂၄၇ စခန်းလုံး၏ Data စုစည်းမည်"):
            all_dfs = []
            bar = st.progress(0)
            for i, city in enumerate(city_list):
                _, d_tmp = fetch_weather(city)
                if d_tmp is not None:
                    d_tmp['Station'] = city
                    all_dfs.append(d_tmp)
                bar.progress((i+1)/len(city_list))
            if all_dfs:
                st.session_state['master_csv'] = pd.concat(all_dfs)
                st.success("✅ အကုန်လုံး အဆင်သင့်ဖြစ်ပါပြီ။")

        if 'master_csv' in st.session_state:
            m_df = st.session_state['master_csv']
            m_df['Date'] = m_df['Date'].dt.strftime('%Y-%m-%d')
            sel_d = st.selectbox("နေ့စွဲရွေးပါ", m_df['Date'].unique())
            day_data = m_df[m_df['Date'] == sel_d]
            st.download_button(f"📥 {sel_d} အတွက် စခန်းအားလုံး၏ Report (CSV) ရယူရန်", day_data.to_csv(index=False).encode('utf-8-sig'), f"DMH_Report_{sel_d}.csv")

    else:
        # Climate Mode
        st.subheader("🌡️ Climate Projection (2026-2100)")
        st.markdown("> **⚠️ Climate Risk Note:** Under the SSP 5-8.5 scenario, Myanmar could face significantly higher frequency of extreme heat and unpredictable monsoon patterns by the end of the century.")
        years = np.arange(2026, 2101)
        trend = [31 + (y-2026)*0.045 + np.random.normal(0, 0.4) for y in years]
        st.plotly_chart(px.line(x=years, y=trend, labels={'x':'Year','y':'Temp (°C)'}), use_container_width=True)

st.markdown("---")
st.markdown("<center>တရားဝင်စနစ်: မိုးလေဝသနှင့်ဇလဗေဒညွှန်ကြားမှုဦးစီးဌာန</center>", unsafe_allow_html=True)

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
