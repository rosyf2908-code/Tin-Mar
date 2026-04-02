import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import requests
from datetime import datetime
import pytz
import time

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
        "impact_list": ["Extreme danger!", "High danger!", "Caution!", "Normal."],
        "recom_list": ["Stay indoors.", "Avoid sun.", "Drink water.", "Normal."]
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
city_list = sorted(list(MYANMAR_CITIES.keys())) # Export အတွက် ဒီ Variable က အရေးကြီးပါတယ်

@st.cache_data(ttl=600)
def fetch_weather(city):
    if city not in MYANMAR_CITIES: return None, None
    loc = MYANMAR_CITIES[city]
    url = f"https://api.open-meteo.com/v1/forecast?latitude={loc['lat']}&longitude={loc['lon']}&hourly=temperature_2m,precipitation,windspeed_10m,winddirection_10m,relative_humidity_2m,visibility,cloud_cover,cape&daily=temperature_2m_max,temperature_2m_min,precipitation_sum&windspeed_unit=mph&forecast_days=16&timezone=Asia%2FYangon"
    
    for _ in range(3): # API Timeout ဖြစ်ရင် ၃ ကြိမ်အထိ ထပ်ကျိုးစားမယ်
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
            time.sleep(1)
    return None, None

# --- ၄။ Sidebar & UI ---
st.sidebar.image(dm_header_logo, width=100)
lang = st.sidebar.radio("🌐 Language", ["မြန်မာ", "English"], horizontal=True)
T = LANG_DATA[lang]
bias = st.sidebar.slider("🌡️ Bias Correction (°C)", -5.0, 5.0, 0.0)
selected_city = st.sidebar.selectbox(T["station_label"], city_list)
view_mode_choice = st.sidebar.radio(T["view_mode_label"], T["modes"])
mode_index = T["modes"].index(view_mode_choice)

st.title(T["title"])
st.info(f"📍 {selected_city} | 🕒 {formatted_now}")

df_h, df_d = fetch_weather(selected_city)

if df_h is not None:
    df_h['Temp'] += bias
    df_d['Tmax'] += bias
    df_d['Tmin'] += bias

    if mode_index == 0:
        st.warning(T["dmh_alert"])
        # Temp Chart
        st.subheader(T["charts"][0])
        st.plotly_chart(px.line(df_d, x='Date', y=['Tmax', 'Tmin'], markers=True), use_container_width=True)

        # Resampling 6h
        df_6h = df_h.set_index('Time').resample('6h').agg({
            'precipitation': 'sum', 'Wind': 'mean', 'WindDir': 'mean', 
            'Cloud_Oktas': 'max', 'Thunderstorm': 'max'
        }).reset_index()

        # Rainfall
        st.subheader(T["charts"][1])
        st.plotly_chart(px.bar(df_6h, x='Time', y='precipitation', color_discrete_sequence=['skyblue']), use_container_width=True)

        # Wind
        st.subheader(T["charts"][2])
        fig_wind = go.Figure()
        fig_wind.add_trace(go.Scatter(x=df_6h['Time'], y=df_6h['Wind'], mode='lines+markers', line=dict(color='green')))
        fig_wind.add_trace(go.Scatter(x=df_6h['Time'], y=df_6h['Wind'], mode='markers', marker=dict(symbol='triangle-up', angle=df_6h['WindDir'], size=12, color='darkgreen')))
        st.plotly_chart(fig_wind, use_container_width=True)

        # Visibility & Humidity
        c1, c2 = st.columns(2)
        with c1:
            st.subheader(T["charts"][3])
            st.plotly_chart(px.line(df_h, x='Time', y='Vis', color_discrete_sequence=['gray']), use_container_width=True)
        with c2:
            st.subheader(T["charts"][4])
            st.plotly_chart(px.area(df_h, x='Time', y='Humid', color_discrete_sequence=['purple']), use_container_width=True)

        # Cloud & Storm
        st.subheader(T["charts"][5])
        st.plotly_chart(px.bar(df_6h, x='Time', y='Cloud_Oktas', color_discrete_sequence=['lightgreen']), use_container_width=True)
        
        st.subheader(T["charts"][6])
        st.error(T["storm_note"])
        st.plotly_chart(px.bar(df_6h, x='Time', y='Thunderstorm', color_discrete_sequence=['orange']), use_container_width=True)

    elif mode_index == 1:
        st.subheader(T["ibf_header"])
        today_max = df_d.iloc[0]['Tmax']
        lvl = 0 if today_max >= 40 else 1 if today_max >= 37 else 2 if today_max >= 34 else 3
        bg = ["#FF0000", "#FFA500", "#FFFF00", "#008000"][lvl]
        color = "white" if lvl in [0, 3] else "black"
        st.markdown(f"<div style='background-color:{bg}; color:{color}; padding:25px; border-radius:15px; text-align:center;'><h1>{T['risk_levels'][lvl]}</h1><h3>Max Temp: {today_max:.1f}°C</h3></div>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1: st.info(f"### ⚠️ Impact\n{T['impact_list'][lvl]}")
        with col2: st.success(f"### ✅ Action\n{T['recom_list'][lvl]}")
        st.plotly_chart(px.bar(df_d, x='Date', y='Tmax', color='Tmax', color_continuous_scale='YlOrRd'), use_container_width=True)

    elif mode_index == 2:
        st.subheader("🌡️ Future Climate Projection (SSP5-8.5)")
        years = np.arange(2026, 2101)
        trend = [31 + (y-2026)*0.045 + np.random.normal(0, 0.4) for y in years]
        st.plotly_chart(px.line(x=years, y=trend, labels={'x':'Year', 'y':'Temp (°C)'}), use_container_width=True)
        st.warning("⚠️ **Note:** Under the SSP5-8.5 scenario, significant warming is expected by 2100.")

# --- ၅။ Export Report ---
st.markdown("---")
if st.button("🚀 Export All Stations Report"):
    all_data = []
    p_bar = st.progress(0)
    for i, city in enumerate(city_list):
        dh, dd = fetch_weather(city)
        if dh is not None:
            for d in dd['Date']:
                t_930 = d + pd.Timedelta(hours=9, minutes=30)
                y_930 = t_930 - pd.Timedelta(days=1)
                rain_24h = dh.loc[(dh['Time'] > y_930) & (dh['Time'] <= t_930), 'precipitation'].sum()
                all_data.append({
                    'Date': d.strftime('%Y-%m-%d'), 'Station': city,
                    'Max_Temp_C': round(dd.loc[dd['Date'] == d, 'Tmax'].values[0] + bias, 1),
                    'Min_Temp_C': round(dd.loc[dd['Date'] == d, 'Tmin'].values[0] + bias, 1),
                    'Rainfall_24h_mm': round(rain_24h, 2)
                })
        p_bar.progress((i + 1) / len(city_list))
    st.session_state['master_df'] = pd.DataFrame(all_data)

if 'master_df' in st.session_state:
    m_df = st.session_state['master_df']
    sel_date = st.selectbox("📅 နေ့စွဲရွေးချယ်ပါ", sorted(m_df['Date'].unique(), reverse=True))
    final_df = m_df[m_df['Date'] == sel_date].sort_values(by='Station')
    st.dataframe(final_df, use_container_width=True)
    st.download_button("📥 Download Report (CSV)", final_df.to_csv(index=False).encode('utf-8-sig'), f"DMH_{sel_date}.csv", "text/csv")

st.markdown("<br><div style='text-align: center; color: gray;'>Official System: Department of Meteorology and Hydrology (DMH) Myanmar</div>", unsafe_allow_html=True)
