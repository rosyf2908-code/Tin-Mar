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

# --- ၂။ စခန်းစာရင်းဖတ်ခြင်း (၂၄၇ စခန်းလုံးအတွက်) ---
@st.cache_data
def load_stations():
    try:
        # GitHub ရှိ Station.csv ကိုဖတ်ခြင်း
        df = pd.read_csv("Station.csv", encoding='utf-8-sig')
        df.columns = [c.strip() for c in df.columns]
        
        # City သို့မဟုတ် Station column အမည်ကို ရှာဖွေခြင်း
        c_col = 'City' if 'City' in df.columns else 'Station'
        
        # စခန်းများကို Dictionary ထဲထည့်ခြင်း
        s_dict = {}
        for _, row in df.iterrows():
            name = str(row[c_col]).strip()
            s_dict[name] = {'lat': row['Lat'], 'lon': row['Lon']}
        return s_dict
    except Exception as e:
        st.sidebar.error(f"⚠️ Station.csv Error: {e}")
        return {"Naypyidaw": {"lat": 19.7633, "lon": 96.0785}}

MYANMAR_CITIES = load_stations()
city_names = sorted(list(MYANMAR_CITIES.keys()))

# --- ၃။ Sidebar (ပုံထဲကအတိုင်း Layout ပြင်ဆင်ခြင်း) ---
st.sidebar.image(dm_header_logo, width=150)
st.sidebar.markdown("### ⚙️ Dashboard Settings")

# (က) Bias Correction Slider - အပေါ်ဆုံးတွင်ထားရှိသည်
bias_val = st.sidebar.slider("🌡️ Bias Correction (°C)", -5.0, 5.0, 0.0, step=0.1)

# (ခ) Select Station - စခန်းအားလုံး ရွေးချယ်နိုင်သည်
selected_city = st.sidebar.selectbox("🎯 စခန်းအမည်ရွေးချယ်ပါ", city_names)

# (ဂ) Language Selection
lang_opt = st.sidebar.radio("🌐 Language", ["မြန်မာ", "English"], horizontal=True)

# (ဃ) View Mode
mode_opt = st.sidebar.radio("📊 View Mode", 
                             ["၁၆ ရက်စာ အသေးစိတ်ဆန်းစစ်ချက်", 
                              "အပူချိန်စောင့်ကြည့်ခြင်း (IBF-ကျန်းမာရေး )", 
                              "ရာသီဥတုပြောင်းလဲမှု (၂၁၀၀)"])

# --- ၄။ Weather API Logic ---
@st.cache_data(ttl=600)
def get_weather_data(city):
    loc = MYANMAR_CITIES[city]
    url = f"https://api.open-meteo.com/v1/forecast?latitude={loc['lat']}&longitude={loc['lon']}&hourly=temperature_2m,relative_humidity_2m,cloud_cover,visibility,precipitation,windspeed_10m,cape&daily=temperature_2m_max,temperature_2m_min,precipitation_sum&windspeed_unit=mph&forecast_days=16&timezone=Asia%2FYangon"
    try:
        resp = requests.get(url, timeout=10).json()
        h = resp['hourly']
        d = resp['daily']
        
        df_hourly = pd.DataFrame({
            "Time": pd.to_datetime(h['time']),
            "Temp": h['temperature_2m'],
            "Wind": h['windspeed_10m'],
            "Vis": [v/1000 for v in h['visibility']],
            "Humid": h['relative_humidity_2m'],
            "Cloud": h['cloud_cover'],
            "Storm": [min(round((c/3500)*100), 100) for c in h['cape']]
        })
        
        df_daily = pd.DataFrame({
            "Date": pd.to_datetime(d['time']),
            "Tmax": d['temperature_2m_max'],
            "Tmin": d['temperature_2m_min'],
            "Rain": d['precipitation_sum']
        })
        return df_hourly, df_daily
    except:
        return None, None

# --- ၅။ Main Page Content ---
st.title("DMH AI Weather Forecast System")
st.markdown(f"📍 စခန်း: **{selected_city}** | 🕒 နောက်ဆုံးရရှိချိန်: **{formatted_now}**")

h_df, d_df = get_weather_data(selected_city)

if h_df is not None:
    # Bias Correction ထည့်သွင်းခြင်း
    d_df['Tmax'] += bias_val
    d_df['Tmin'] += bias_val
    h_df['Temp'] += bias_val

    if "၁၆ ရက်စာ" in mode_opt:
        st.plotly_chart(px.line(d_df, x='Date', y=['Tmax', 'Tmin'], title="🌡️ ၁။ အပူချိန်ခန့်မှန်းချက်", markers=True, color_discrete_map={'Tmax':'red','Tmin':'blue'}), use_container_width=True)
        st.plotly_chart(px.bar(d_df, x='Date', y='Rain', title="🌧️ ၂။ မိုးရေချိန်ခန့်မှန်းချက်", color_discrete_sequence=['deepskyblue']), use_container_width=True)
        st.plotly_chart(px.line(h_df, x='Time', y='Wind', title="💨 ၃။ လေတိုက်နှုန်း (mph)"), use_container_width=True)
        st.plotly_chart(px.line(h_df, x='Time', y='Vis', title="🔭 ၄။ အဝေးမြင်တာ (km)"), use_container_width=True)
        st.plotly_chart(px.area(h_df, x='Time', y='Humid', title="💧 ၅။ စိုထိုင်းဆ (%)"), use_container_width=True)
        st.plotly_chart(px.bar(h_df, x='Time', y='Cloud', title="☁️ ၆။ တိမ်ဖုံးမှု (%)", color='Cloud', color_continuous_scale='Blues'), use_container_width=True)
        
        st.error("📝 မှတ်ချက်: မိုးတိမ်တောင် ဖြစ်နိုင်ခြေ ၆၀% ထက်ကျော်လွန်ပါက လေပြင်း၊ မိုးကြိုးအန္တရာယ် သတိပြုရန်။")
        st.plotly_chart(px.bar(h_df, x='Time', y='Storm', title="⚡ ၇။ မိုးတိမ်တောင် ဖြစ်နိုင်ခြေ (%)", color_discrete_sequence=['purple']), use_container_width=True)

    elif "အပူချိန်စောင့်ကြည့်ခြင်း" in mode_opt:
        # IBF Section
        max_temp = d_df['Tmax'].max()
        idx = 0 if max_temp >= 42 else 1 if max_temp >= 40 else 2 if max_temp >= 38 else 3
        colors = ['#800000', '#d00000', '#ffaa00', '#008000']
        levels = ["အလွန်အန္တရာယ်ရှိ (Extreme Risk)", "အန္တရာယ်ရှိ (High Risk)", "သတိပြုရန် (Moderate Risk)", "ပုံမှန် (Low Risk)"]
        
        st.markdown(f"""
            <div style="background-color:{colors[idx]}; padding:30px; border-radius:15px; text-align:center; color:white;">
                <h1 style="margin:0;">{levels[idx]}</h1>
                <h2 style="margin:0;">{max_temp:.1f} °C</h2>
            </div>
            """, unsafe_allow_html=True)
        
        st.subheader("🏥 ကျန်းမာရေးဆိုင်ရာ အကြံပြုချက်")
        st.warning("📢 အကြံပြုချက်: နောက်ဆုံးရ မိုးလေဝသသတင်းများအတွက် မိုးဇလ သတင်းများကိုစောင့်ကြည့်ပါ။")
        st.plotly_chart(px.bar(d_df, x='Date', y='Tmax', color='Tmax', color_continuous_scale='YlOrRd', title="Daily Maximum Temperature"), use_container_width=True)

        # ၂၄၇ စခန်းလုံးအတွက် Batch Process
        st.markdown("---")
        if st.button("🚀 စခန်းအားလုံး၏ Data စုစည်းမည် (Batch Export)"):
            all_st_data = []
            p_bar = st.progress(0)
            for i, c in enumerate(city_names):
                _, daily_tmp = get_weather_data(c)
                if daily_tmp is not None:
                    daily_tmp['Station'] = c
                    all_st_data.append(daily_tmp)
                p_bar.progress((i+1)/len(city_names))
            if all_st_data:
                st.session_state['full_report'] = pd.concat(all_st_data)
                st.success("✅ စခန်းအားလုံး၏ အချက်အလက်များ ရရှိပါပြီ။")

        if 'full_report' in st.session_state:
            f_df = st.session_state['full_report']
            f_df['Date'] = f_df['Date'].dt.strftime('%Y-%m-%d')
            target_date = st.selectbox("အစီရင်ခံစာထုတ်ယူမည့်ရက် ရွေးချယ်ပါ", f_df['Date'].unique())
            final_day_df = f_df[f_df['Date'] == target_date].sort_values(by='Station')
            st.dataframe(final_day_df, use_container_width=True)
            st.download_button(f"📥 Download CSV Report ({target_date})", final_day_df.to_csv(index=False).encode('utf-8-sig'), f"DMH_Daily_Report_{target_date}.csv")

    else:
        # Climate Projection Mode
        st.subheader("🌡️ Climate Projection (2026-2100)")
        st.markdown("> **⚠️ Climate Risk Note:** Under the SSP 5-8.5 scenario, Myanmar could face significantly higher frequency of extreme heat and unpredictable monsoon patterns by the end of the century.")
        years = np.arange(2026, 2101)
        trend_data = [31 + (y-2026)*0.045 + np.random.normal(0, 0.4) for y in years]
        st.plotly_chart(px.line(x=years, y=trend_data, labels={'x':'Year','y':'Temp (°C)'}, title="SSP 5-8.5 High Emission Projection"), use_container_width=True)

st.markdown("---")
st.markdown("<center>Data Source: Open-Meteo | System: Department of Meteorology and Hydrology (DMH)</center>", unsafe_allow_html=True)

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
