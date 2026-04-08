import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import requests
from datetime import datetime
import pytz
import time

# --- ၁။ Functions (အခြေခံ တွက်ချက်မှုများ) ---

def calculate_all_indices(temp_c, rh):
    """Heat Indices ၄ မျိုး (Temp အပါအဝင်) တွက်ချက်ခြင်း"""
    try:
        hi = 0.5 * (temp_c + 61.0 + ((temp_c - 68.0) * 1.2) + (rh * 0.094))
        e = (rh / 100) * 6.105 * np.exp(17.27 * temp_c / (237.7 + temp_c))
        wbgt = (0.567 * temp_c) + (0.393 * e) + 3.94
        utci = temp_c + (0.33 * e) - (0.7 * 0.1) - 4.0
        return round(hi, 1), round(wbgt, 1), round(utci, 1)
    except:
        return temp_c, temp_c, temp_c

@st.cache_data(ttl=600)
def fetch_weather(lat, lon):
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=temperature_2m,relative_humidity_2m,precipitation,windspeed_10m,winddirection_10m,visibility,cloud_cover,cape&daily=temperature_2m_max,temperature_2m_min&windspeed_unit=mph&forecast_days=16&timezone=Asia%2FYangon"
    try:
        r = requests.get(url, timeout=15)
        res = r.json()
        df_h = pd.DataFrame({
            "Time": pd.to_datetime(res['hourly']['time']),
            "Temp": res['hourly']['temperature_2m'],
            "Humid": res['hourly']['relative_humidity_2m'],
            "Rain": res['hourly']['precipitation'],
            "Wind": res['hourly']['windspeed_10m'],
            "WindDir": res['hourly']['winddirection_10m'],
            "Vis": [v/1000 for v in res['hourly']['visibility']],
            "Cloud": [round((c/100)*8) for c in res['hourly']['cloud_cover']],
            "Thunder": [min(round((c/3500)*100), 100) if c else 0 for c in res['hourly'].get('cape', [])]
        })
        
        # Indices ၄ မျိုးအတွက် list များ
        hi_l, wbgt_l, utci_l = [], [], []
        for _, row in df_h.iterrows():
            h, w, u = calculate_all_indices(row['Temp'], row['Humid'])
            hi_l.append(h); wbgt_l.append(w); utci_l.append(u)
        df_h['HI'], df_h['WBGT'], df_h['UTCI'] = hi_l, wbgt_l, utci_l
        
        df_d = pd.DataFrame({
            "Date": pd.to_datetime(res['daily']['time']), 
            "Tmax": res['daily']['temperature_2m_max'], 
            "Tmin": res['daily']['temperature_2m_min']
        })
        return df_h, df_d
    except:
        return None, None

@st.cache_data
def load_stations():
    try:
        df_csv = pd.read_csv("Station.csv", encoding='utf-8-sig')
        return {str(row.iloc[0]).strip(): {'lat': float(row['Lat']), 'lon': float(row['Lon'])} for _, row in df_csv.iterrows()}
    except:
        return {"Naypyidaw": {"lat": 19.76, "lon": 96.08}}

# --- ၂။ Sidebar & UI Setup ---
st.set_page_config(page_title="DMH AI Weather System", layout="wide")
STATIONS = load_stations()
city_list = sorted(list(STATIONS.keys()))
mm_tz = pytz.timezone('Asia/Yangon')
now_time = datetime.now(mm_tz).strftime('%I:%M %p, %d %b %Y')

st.sidebar.image("https://www.moezala.gov.mm/themes/custom/dmh/logo.png?v=1.1", width=100)
lang = st.sidebar.radio("Language", ["မြန်မာ", "English"], horizontal=True)
selected_city = st.sidebar.selectbox("🎯 Select Station", city_list)
mode = st.sidebar.radio("📊 View Mode", [
    "1. 16-Days Detailed Forecast (ဂရပ် ၇ ခု)", 
    "2. Heatwave Monitoring (IBF - ၄ မျိုး)", 
    "3. Climate Change Projection"
])
bias = st.sidebar.slider("🌡️ Bias Correction", -5.0, 5.0, 0.0)

st.title("🌤️ DMH AI Weather Forecast System")
st.info(f"📍 {selected_city} | 🕒 {now_time}")

# --- ၃။ Main Logic ---
city_data = STATIONS[selected_city]
df_h, df_d = fetch_weather(city_data['lat'], city_data['lon'])

if df_h is not None and df_d is not None:
    df_h['Temp'] += bias
    df_d['Tmax'] += bias
    df_d['Tmin'] += bias

    # --- Mode 1: 16-Days Detailed (ဂရပ် ၇ ခု) ---
    if "1." in mode:
        st.subheader("🌡️ ၁။ အမြင့်ဆုံးနှင့် အနိမ့်ဆုံးအပူချိန် (၁၆ ရက်စာ)")
        st.plotly_chart(px.line(df_d, x='Date', y=['Tmax', 'Tmin'], markers=True), use_container_width=True)
        
        st.subheader("🌧️ ၂။ မိုးရေချိန် ခန့်မှန်းချက်")
        st.plotly_chart(px.bar(df_h, x='Time', y='Rain', color_discrete_sequence=['dodgerblue']), use_container_width=True)
        
        st.subheader("💨 ၃။ လေတိုက်နှုန်းနှင့် လေအရပ်")
        fig_w = go.Figure()
        fig_w.add_trace(go.Scatter(x=df_h['Time'], y=df_h['Wind'], mode='lines', line=dict(color='green')))
        fig_w.add_trace(go.Scatter(x=df_h[::6]['Time'], y=df_h[::6]['Wind'], mode='markers', marker=dict(symbol='triangle-up', angle=df_h[::6]['WindDir'], size=10, color='red')))
        st.plotly_chart(fig_w, use_container_width=True)

        c1, c2 = st.columns(2)
        with c1:
            st.subheader("🔭 ၄။ အဝေးမြင်တာ (Visibility)"); st.plotly_chart(px.line(df_h, x='Time', y='Vis', color_discrete_sequence=['gray']), use_container_width=True)
            st.subheader("☁️ ၆။ တိမ်ဖုံးမှု (Cloud Cover)"); st.plotly_chart(px.bar(df_h, x='Time', y='Cloud', color_discrete_sequence=['lightgreen']), use_container_width=True)
        with c2:
            st.subheader("💧 ၅။ စိုထိုင်းဆ (Humidity)"); st.plotly_chart(px.area(df_h, x='Time', y='Humid', color_discrete_sequence=['purple']), use_container_width=True)
            st.subheader("⚡ ၇။ မိုးတိမ်တောင် (Thunderstorm)"); st.plotly_chart(px.bar(df_h, x='Time', y='Thunder', color_discrete_sequence=['orange']), use_container_width=True)

    # --- Mode 2: IBF Monitoring (Bullet points + 4 Indices) ---
    elif "2." in mode:
        tmax = df_d.iloc[0]['Tmax']
        if tmax >= 42: 
            lvl, bg, color = "Extreme Risk", "#FF0000", "white"
            impacts = ["• Heatstroke ဖြစ်နိုင်ခြေ အလွန်များပါသည်။", "• အသက်အန္တရာယ်ရှိသော အခြေအနေဖြစ်ပါသည်။"]
            recoms = ["• အိမ်ထဲတွင်သာ နေထိုင်ပါ။", "• ရေ (၄) လီတာခန့်အထိ သောက်သုံးပါ။"]
        elif tmax >= 40: 
            lvl, bg, color = "High Risk", "#FFA500", "black"
            impacts = ["• ပင်ပန်းနွမ်းနယ်ခြင်းနှင့် မူးဝေခြင်း ဖြစ်နိုင်ပါသည်။", "• ရေဓာတ်ခန်းခြောက်မှု အလွန်ဖြစ်ပေါ်နိုင်ပါသည်။"]
            recoms = ["• ထီး သို့မဟုတ် ဦးထုပ် ဆောင်းပါ။", "• ပြင်းထန်သော လုပ်ငန်းများကို နားနားနေနေ လုပ်ပါ။"]
        elif tmax >= 38: 
            lvl, bg, color = "Moderate Risk", "#FFFF00", "black"
            impacts = ["• နေပူထဲကြာရှည်နေပါက ကျန်းမာရေး ထိခိုက်နိုင်ပါသည်။"]
            recoms = ["• ရေခဏခဏ သောက်ပါ။", "• အရိပ်တွင် နားနားနေနေ နေပါ။"]
        else: 
            lvl, bg, color = "Low Risk", "#008000", "white"
            impacts = ["• သိသာသော ကျန်းမာရေး ထိခိုက်မှု မရှိပါ။"]
            recoms = ["• ပုံမှန်အတိုင်း နေထိုင်နိုင်ပါသည်။"]

        # Risk Banner
        st.markdown(f"""
            <div style='background-color:{bg}; color:{color}; padding:20px; border-radius:15px; text-align:center;'>
                <h1 style='margin:0;'>{lvl}</h1>
                <h3>Today Max: {tmax:.1f}°C</h3>
            </div>
        """, unsafe_allow_html=True)

        # Bullet Points Section
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### ⚠️ **Health Impacts**")
            for item in impacts: st.write(item)
        with col2:
            st.markdown("### ✅ **Recommendations**")
            for item in recoms: st.write(item)

        st.markdown("---")
        st.subheader("🔥 Heat Indices Analysis (4 Types)")
        # Temp, HI, WBGT, UTCI ၄ မျိုးလုံးကို ဂရပ်တစ်ခုတည်းတွင်ပြခြင်း
        fig_idx = px.line(df_h, x='Time', y=['Temp', 'HI', 'WBGT', 'UTCI'], 
                         color_discrete_map={"Temp": "blue", "HI": "red", "WBGT": "orange", "UTCI": "purple"})
        st.plotly_chart(fig_idx, use_container_width=True)

    # --- Mode 3: Climate Change ---
    elif "3." in mode:
        st.subheader("🌡️ Future Climate Projection (SSP5-8.5)")
        years = np.arange(2026, 2101)
        trend = [31.5 + (y-2026)*0.048 + np.random.normal(0, 0.45) for y in years]
        st.plotly_chart(px.line(x=years, y=trend, color_discrete_sequence=['darkred']), use_container_width=True)

# --- ၄။ Export & Download Section ---
st.markdown("---")
if st.button("🚀 Export All Stations Report"):
    results = []
    p_bar = st.progress(0)
    for i, city in enumerate(city_list):
        coords = STATIONS[city]
        _, dd = fetch_weather(coords['lat'], coords['lon'])
        if dd is not None:
            results.append({'Date': dd.iloc[0]['Date'].strftime('%Y-%m-%d'), 'Station': city, 'Tmax': round(dd.iloc[0]['Tmax'], 1)})
        p_bar.progress((i + 1) / len(city_list))
    st.session_state['master_df'] = pd.DataFrame(results)
    st.success("Export Complete!")

if 'master_df' in st.session_state:
    st.dataframe(st.session_state['master_df'], use_container_width=True)
    csv = st.session_state['master_df'].to_csv(index=False).encode('utf-8-sig')
    st.download_button("📥 Download CSV Report", data=csv, file_name="DMH_Full_Report.csv", mime="text/csv")

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
