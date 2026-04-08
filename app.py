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

# --- ၂။ Functions (Error ကင်းစေရန် အပေါ်ဆုံးတွင် ထားရမည်) ---

def calculate_all_indices(temp_c, rh):
    """Heat Indices များတွက်ချက်ခြင်း"""
    # Heat Index
    hi = 0.5 * (temp_c + 61.0 + ((temp_c - 68.0) * 1.2) + (rh * 0.094))
    # Simplified WBGT
    e = (rh / 100) * 6.105 * np.exp(17.27 * temp_c / (237.7 + temp_c))
    wbgt = (0.567 * temp_c) + (0.393 * e) + 3.94
    # UTCI
    utci = temp_c + (0.33 * e) - (0.7 * 0.1) - 4.0
    return round(hi, 1), round(wbgt, 1), round(utci, 1)

@st.cache_data(ttl=600)
def fetch_weather(city):
    if city not in MYANMAR_CITIES: return None, None
    loc = MYANMAR_CITIES[city]
    # Hourly data ထဲတွင် visibility ပါအောင် ထည့်သွင်းထားသည်
    url = f"https://api.open-meteo.com/v1/forecast?latitude={loc['lat']}&longitude={loc['lon']}&hourly=temperature_2m,relative_humidity_2m,precipitation,windspeed_10m,winddirection_10m,visibility,cloud_cover,cape&daily=temperature_2m_max,temperature_2m_min&windspeed_unit=mph&forecast_days=16&timezone=Asia%2FYangon"
    
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        res = r.json()
        
        df_h = pd.DataFrame({
            "Time": pd.to_datetime(res['hourly']['time']),
            "Temp": res['hourly']['temperature_2m'],
            "Humid": res['hourly']['relative_humidity_2m'],
            "Rain": res['hourly']['precipitation'],
            "Wind": res['hourly']['windspeed_10m'],
            "WindDir": res['hourly']['winddirection_10m'],
            "Vis": [v/1000 for v in res['hourly']['visibility']], # m to km
            "Cloud_Oktas": [round((c/100)*8) for c in res['hourly']['cloud_cover']],
            "Thunderstorm": [min(round((c/3500)*100), 100) if c else 0 for c in res['hourly'].get('cape', [])]
        })
        
        # Heat Indices တွက်ချက်ခြင်း
        df_h['HI'], df_h['WBGT'], df_h['UTCI'] = zip(*df_h.apply(lambda x: calculate_all_indices(x['Temp'], x['Humid']), axis=1))
        
        df_d = pd.DataFrame({
            "Date": pd.to_datetime(res['daily']['time']), 
            "Tmax": res['daily']['temperature_2m_max'], 
            "Tmin": res['daily']['temperature_2m_min']
        })
        return df_h, df_d
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return None, None

@st.cache_data
def load_stations():
    try:
        df_csv = pd.read_csv("Station.csv", encoding='utf-8-sig')
        return {str(row.iloc[0]).strip(): {'lat': float(row['Lat']), 'lon': float(row['Lon'])} for _, row in df_csv.iterrows()}
    except:
        return {"Naypyidaw": {"lat": 19.76, "lon": 96.08}, "Amarapura": {"lat": 21.90, "lon": 96.05}}

# --- ၃။ Constants & Initialization ---
MYANMAR_CITIES = load_stations()
city_list = sorted(list(MYANMAR_CITIES.keys()))
mm_tz = pytz.timezone('Asia/Yangon')
now = datetime.now(mm_tz)
formatted_now = now.strftime('%I:%M %p, %d %b %Y')
dm_header_logo = "https://www.moezala.gov.mm/themes/custom/dmh/logo.png?v=1.1"

LANG_DATA = {
    "မြန်မာ": {
        "title": "DMH AI မိုးလေဝသခန့်မှန်းစနစ်",
        "station_label": "🎯 စခန်းအမည်ရွေးချယ်ပါ",
        "view_mode_label": "📊 View Mode",
        "modes": ["၁၆ ရက်စာ အသေးစိတ်ဆန်းစစ်ချက်", "အပူချိန်စောင့်ကြည့်ခြင်း (IBF-ကျန်းမာရေး )", "ရာသီဥတုပြောင်းလဲမှု (၂၁၀၀-SSP5-8.5)"],
        "dmh_alert": "📢 အကြံပြုချက်: နောက်ဆုံးရ မိုးလေဝသသတင်းများကို မိုးဇလတွင် စောင့်ကြည့်ပါ။",
        "storm_note": "📝 မှတ်ချက်: မိုးတိမ်တောင် ဖြစ်နိုင်ခြေ ၆၀% ထက်ကျော်လွန်ပါက လေပြင်း၊ မိုးကြိုးနှင့် လျှပ်စီးများ သတိပြုရန်။",
        "ibf_header": "🏥 ကျန်းမာရေးကဏ္ဍဆိုင်ရာ အကျိုးသက်ရောက်မှုနှင့် အကြံပြုချက်များ",
        "risk_levels": ["Extreme Risk", "High Risk", "Moderate Risk", "Low Risk"],
        "charts": ["🌡️ ၁။ အပူချိန်", "🌧️ ၂။ မိုးရေချိန် (၆ နာရီ)", "💨 ၃။ လေတိုက်နှုန်း", "🔭 ၄။ အဝေးမြင်တာ (km)", "💧 ၅။ စိုထိုင်းဆ (%)", "☁️ ၆။ တိမ်ဖုံးမှု", "⚡ ၇။ မိုးတိမ်တောင် (%)"],
        "impact_list": ["Extreme danger! Heatstroke possible.", "High danger! Fatigue possible.", "Caution! Sun exposure fatigue.", "Normal conditions."],
        "recom_list": ["အိမ်ထဲတွင်သာနေပါ။ ရေများများသောက်ပါ။", "ပြင်ပလုပ်ငန်းများကို နံနက်/ညနေသာလုပ်ပါ။", "ပေါ့ပါးသောအဝတ်များဝတ်ပါ။", "ပုံမှန်အတိုင်းနေနိုင်ပါသည်။"]
    },
    "English": {
        "title": "DMH AI Weather Forecast System",
        "station_label": "🎯 Select Station",
        "view_mode_label": "📊 View Mode",
        "modes": ["16-Days Forecast", "Heatwave Monitoring (IBF)", "Climate Change Projection"],
        "dmh_alert": "📢 Tip: Follow DMH news for latest updates.",
        "storm_note": "📝 Note: Beware of lightning if probability > 60%.",
        "ibf_header": "🏥 Health Impacts & Recommendations",
        "risk_levels": ["Extreme Risk", "High Risk", "Moderate Risk", "Low Risk"],
        "charts": ["🌡️ 1. Temp", "🌧️ 2. Rain", "💨 3. Wind", "🔭 4. Vis", "💧 5. Humid", "☁️ 6. Cloud", "⚡ 7. Storm"],
        "impact_list": ["Extreme danger!", "High danger!", "Caution!", "Normal."],
        "recom_list": ["Stay indoors.", "Work morning/evening.", "Wear light clothes.", "Stay hydrated."]
    }
}

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

        # Resampling 6h (Rain column အမည်သေချာစေရန် ပြင်ဆင်ထားသည်)
        df_6h = df_h.set_index('Time').resample('6H').agg({
            'Rain': 'sum', 'Wind': 'mean', 'WindDir': 'mean', 
            'Cloud_Oktas': 'max', 'Thunderstorm': 'max'
        }).reset_index()

        # Rainfall
        st.subheader(T["charts"][1])
        st.plotly_chart(px.bar(df_6h, x='Time', y='Rain', color_discrete_sequence=['green']), use_container_width=True)

        # Wind
        st.subheader(T["charts"][2])
        fig_wind = go.Figure()
        fig_wind.add_trace(go.Scatter(x=df_6h['Time'], y=df_6h['Wind'], mode='lines+markers', line=dict(color='darkgreen')))
        fig_wind.add_trace(go.Scatter(x=df_6h['Time'], y=df_6h['Wind'], mode='markers', marker=dict(symbol='triangle-up', angle=df_6h['WindDir'], size=12, color='red')))
        st.plotly_chart(fig_wind, use_container_width=True)

        # Visibility & Humidity
        c_vis, c_hum = st.columns(2)
        with c_vis:
            st.subheader(T["charts"][3])
            st.plotly_chart(px.line(df_h, x='Time', y='Vis', color_discrete_sequence=['gray']), use_container_width=True)
        with c_hum:
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
        idx_choice = st.radio("🌡️ Select Index", ["အမြင့်ဆုံးအပူချိန်", "Heat Index", "WBGT", "UTCI"], horizontal=True)
        
        t_now = df_h.iloc[0]
        if idx_choice == "အမြင့်ဆုံးအပူချိန်": val, th = df_d.iloc[0]['Tmax'], [42, 40, 38]
        elif idx_choice == "Heat Index": val, th = t_now['HI'], [41, 38, 35]
        elif idx_choice == "WBGT": val, th = t_now['WBGT'], [32, 30, 28]
        else: val, th = t_now['UTCI'], [38, 32, 26]

        if val >= th[0]: lvl, color, bg = 0, "white", "#FF0000"
        elif val >= th[1]: lvl, color, bg = 1, "black", "#FFA500"
        elif val >= th[2]: lvl, color, bg = 2, "black", "#FFFF00"
        else: lvl, color, bg = 3, "white", "#008000"

        st.markdown(f"""
            <div style='background-color:{bg}; color:{color}; padding:25px; border-radius:15px; text-align:center; border: 2px solid #333;'>
                <h1 style='margin:0;'>{T['risk_levels'][lvl]}</h1>
                <p style='font-size:1.5em; margin-top:10px;'>{idx_choice}: <b>{val:.1f} °C</b></p>
            </div>
            """, unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        with c1: st.info(f"### ⚠️ Impact\n{T['impact_list'][lvl]}")
        with c2: st.success(f"### ✅ Action\n{T['recom_list'][lvl]}")

# --- ၅။ Export Section ---
st.markdown("---")
if st.button("🚀 Export All Stations Report"):
    all_data = []
    p_bar = st.progress(0)
    for i, city in enumerate(city_list):
        dh, dd = fetch_weather(city)
        if dh is not None:
            latest = dd.iloc[0]
            all_data.append({'Date': latest['Date'].strftime('%Y-%m-%d'), 'Station': city, 'Tmax': latest['Tmax'] + bias})
        time.sleep(1.2) # API Throttle (429 Error ကာကွယ်ရန်)
        p_bar.progress((i + 1) / len(city_list))
    st.session_state['master_df'] = pd.DataFrame(all_data)
    st.success("Export Complete!")

if 'master_df' in st.session_state:
    m_df = st.session_state['master_df']
    sel_date = st.selectbox("📅 နေ့စွဲရွေးချယ်ပါ", sorted(m_df['Date'].unique(), reverse=True))
    final_df = m_df[m_df['Date'] == sel_date].sort_values(by='Station')
    st.dataframe(final_df, use_container_width=True)
    st.download_button("📥 Download CSV", final_df.to_csv(index=False).encode('utf-8-sig'), f"DMH_{sel_date}.csv", "text/csv")

    # Data Description Box
    st.markdown("""
    <div style='background-color: #f8f9fa; padding: 20px; border-radius: 10px; border-left: 5px solid #007bff; margin-top:20px;'>
        <h4 style='color: #007bff; margin-top: 0;'>📝 ဇယားတွင် ပါဝင်သည့် ဒေတာများရှင်းလင်းချက်</h4>
        <ul style='list-style-type: none; padding-left: 0; line-height: 1.8;'>
            <li><b>၁။ အမြင့်ဆုံးအပူချိန်:</b> နေ့တစ်နေ့၏ ဖြစ်ပေါ်နိုင်သော အမြင့်ဆုံးအပူချိန် (Max Temp)</li>
            <li><b>၂။ အနိမ့်ဆုံးအပူချိန်:</b> နေ့တစ်နေ့၏ ဖြစ်ပေါ်နိုင်သော အနိမ့်ဆုံးအပူချိန် (Min Temp)</li>
            <li><b>၃။ မိုးရေချိန် (၂၄ နာရီ):</b> ယခင်နေ့ နံနက် ၀၉:၃၀ နာရီမှ ယနေ့နံနက် ၀၉:၃၀ နာရီအထိ ၂၄ နာရီအတွင်း ရွာသွန်းသော စုစုပေါင်းမိုးရေချိန်</li>
        </ul>
        <p style='font-size: 0.85em; color: #666; font-style: italic; margin-top: 10px;'>
            *မှတ်ချက်။ ။ အထက်ပါဒေတာများသည် DMH ၏ စံသတ်မှတ်ချက်များနှင့်အညီ တွက်ချက်ဖော်ပြထားခြင်း ဖြစ်ပါသည်။
         </p>
         </div>
         """, unsafe_allow_html=True)

# Footer Section
st.markdown("---")
st.markdown(f"""
<div style='text-align: center; font-size: 0.85em; color: #666; line-height: 1.6;'>
    <p><b>Forecast Data Source (16-Day):</b> Open-Meteo API (ECMWF, GFS, ICON, JMA models).</p>
    <p><b>Rainfall Cycle:</b> 24-hour total from 09:30 AM (Yesterday) to 09:30 AM (Today).</p>
    <p><b>Heatwave Analysis:</b> Based on Impact-Based Forecasting (IBF) thresholds (P90, P95, P99) and WMO criteria.</p>
    <p><b>Climate Data:</b> IPCC AR6 Assessment Report and CMIP6 Global Climate Models (SSP scenarios).</p>
    <p style='margin-top: 10px; font-weight: bold;'>Official System: Department of Meteorology and Hydrology (DMH) Myanmar</p>
</div>
""", unsafe_allow_html=True)
st.markdown("<br><div style='text-align: center; color: gray;'>Official System: Department of Meteorology and Hydrology (DMH) Myanmar</div>", unsafe_allow_html=True)
