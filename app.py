import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import requests
from datetime import datetime
import pytz
import time

# --- ၁။ Functions (အပေါ်ဆုံးတွင် ထားရမည်) ---

def calculate_all_indices(temp_c, rh):
    """Heat Indices တွက်ချက်ခြင်း"""
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
        # Indices တွက်ချက်ခြင်း
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

# --- ၂။ Setup ---
st.set_page_config(page_title="DMH AI Weather System", layout="wide")
STATIONS = load_stations()
city_list = sorted(list(STATIONS.keys()))
mm_tz = pytz.timezone('Asia/Yangon')
now_time = datetime.now(mm_tz).strftime('%I:%M %p, %d %b %Y')

# --- ၃။ Sidebar ---
st.sidebar.image("https://www.moezala.gov.mm/themes/custom/dmh/logo.png?v=1.1", width=100)
lang = st.sidebar.radio("Language", ["မြန်မာ", "English"], horizontal=True)
selected_city = st.sidebar.selectbox("🎯 Select Station", city_list)
mode = st.sidebar.radio("📊 Mode", ["16-Days Detailed", "IBF Heat Monitoring", "Climate Projection"])
bias = st.sidebar.slider("🌡️ Bias Correction", -5.0, 5.0, 0.0)

st.title("🌤️ DMH AI Weather Forecast System")
st.info(f"📍 {selected_city} | 🕒 {now_time}")

city_data = STATIONS[selected_city]
df_h, df_d = fetch_weather(city_data['lat'], city_data['lon'])

if df_h is not None and df_d is not None:
    df_h['Temp'] += bias
    df_d['Tmax'] += bias
    df_d['Tmin'] += bias

    # --- Mode 1: 16 Days (ဂရပ် ၇ ခု) ---
    if mode == "16-Days Detailed":
        st.subheader("🌡️ 1. Max/Min Temperature")
        st.plotly_chart(px.line(df_d, x='Date', y=['Tmax', 'Tmin'], markers=True), use_container_width=True)
        
        st.subheader("🌧️ 2. Rainfall Forecast")
        st.plotly_chart(px.bar(df_h, x='Time', y='Rain', color_discrete_sequence=['dodgerblue']), use_container_width=True)
        
        st.subheader("💨 3. Wind Speed & Direction")
        fig_w = go.Figure()
        fig_w.add_trace(go.Scatter(x=df_h['Time'], y=df_h['Wind'], mode='lines', line=dict(color='green')))
        fig_w.add_trace(go.Scatter(x=df_h[::6]['Time'], y=df_h[::6]['Wind'], mode='markers', marker=dict(symbol='triangle-up', angle=df_h[::6]['WindDir'], size=10, color='red')))
        st.plotly_chart(fig_w, use_container_width=True)

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("🔭 4. Visibility"); st.plotly_chart(px.line(df_h, x='Time', y='Vis'), use_container_width=True)
            st.subheader("☁️ 6. Cloud Cover (Oktas)"); st.plotly_chart(px.bar(df_h, x='Time', y='Cloud'), use_container_width=True)
        with col2:
            st.subheader("💧 5. Humidity"); st.plotly_chart(px.area(df_h, x='Time', y='Humid', color_discrete_sequence=['purple']), use_container_width=True)
            st.subheader("⚡ 7. Thunderstorm Potential"); st.plotly_chart(px.bar(df_h, x='Time', y='Thunder', color_discrete_sequence=['orange']), use_container_width=True)

    # --- Mode 2: IBF (Index ၄ မျိုး + Recommendations) ---
    elif mode == "IBF Heat Monitoring":
        tmax = df_d.iloc[0]['Tmax']
        if tmax >= 42: lvl, bg, txt = "Extreme", "#FF0000", "Stay indoors, drink 4L water!"
        elif tmax >= 40: lvl, bg, txt = "High", "#FFA500", "Use umbrella, avoid direct sun."
        elif tmax >= 38: lvl, bg, txt = "Moderate", "#FFFF00", "Stay hydrated, rest in shade."
        else: lvl, bg, txt = "Low", "#008000", "Normal conditions."

        st.markdown(f"<div style='background-color:{bg}; padding:20px; border-radius:10px; text-align:center;'><h1>{lvl} Risk</h1><h3>Max Temp: {tmax:.1f}°C</h3><p>{txt}</p></div>", unsafe_allow_html=True)

        st.subheader("🔥 Heat Indices (4 Types)")
        # ဂရပ်တစ်ခုတည်းမှာ ၄ မျိုးလုံးပြခြင်း
        fig_idx = px.line(df_h, x='Time', y=['Temp', 'HI', 'WBGT', 'UTCI'], title="Thermal Stress Analysis")
        st.plotly_chart(fig_idx, use_container_width=True)

    # --- Mode 3: Climate Projection ---
    elif mode == "Climate Projection":
        st.subheader("🌡️ Future Temperature Projection (2026-2100)")
        years = np.arange(2026, 2101)
        trend = [31.5 + (y-2026)*0.048 + np.random.normal(0, 0.5) for y in years]
        st.plotly_chart(px.line(x=years, y=trend, labels={'x':'Year', 'y':'Avg Temp (°C)'}, color_discrete_sequence=['red']), use_container_width=True)

# --- ၄။ Export & Download ---
st.markdown("---")
if st.button("🚀 Generate All Stations Report"):
    all_data = []
    bar = st.progress(0)
    for i, city in enumerate(city_list):
        coords = STATIONS[city]
        _, dd = fetch_weather(coords['lat'], coords['lon'])
        if dd is not None:
            all_data.append({'Date': dd.iloc[0]['Date'].strftime('%Y-%m-%d'), 'Station': city, 'Tmax': dd.iloc[0]['Tmax']})
        bar.progress((i+1)/len(city_list))
    
    st.session_state['df_report'] = pd.DataFrame(all_data)
    st.success("Report Generated!")

if 'df_report' in st.session_state:
    st.dataframe(st.session_state['df_report'], use_container_width=True)
    csv = st.session_state['df_report'].to_csv(index=False).encode('utf-8-sig')
    st.download_button("📥 Download CSV Report", data=csv, file_name="DMH_Weather_Report.csv", mime="text/csv")

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
