import streamlit as st
import pandas as pd
import numpy as np
import requests
import os
from datetime import datetime
import pytz

# --- ၁။ Layout Setup ---
st.set_page_config(page_title="DMH AI Weather Forecast System", layout="wide", page_icon="🌤️")

# Mobile Web App Meta
st.markdown("""
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <meta name="apple-mobile-web-app-title" content="DMH AI">
""", unsafe_allow_html=True)

mm_tz = pytz.timezone('Asia/Yangon')
now = datetime.now(mm_tz)
formatted_now = now.strftime('%I:%M %p, %d %b %Y')
dm_header_logo = "https://www.moezala.gov.mm/themes/custom/dmh/logo.png?v=1.1"

# --- ၂။ စခန်းစာရင်းဖတ်ခြင်း ---
@st.cache_data
def load_stations():
    file_path = "Station.csv"
    if not os.path.exists(file_path):
        return {"Naypyidaw": {"lat": 19.76, "lon": 96.08}}
    try:
        df = pd.read_csv(file_path, encoding='utf-8-sig')
        df.columns = [c.strip() for c in df.columns]
        s_dict = {}
        for _, row in df.iterrows():
            s_dict[str(row.iloc[0]).strip()] = {'lat': float(row['Lat']), 'lon': float(row['Lon'])}
        return s_dict
    except: return {"Naypyidaw": {"lat": 19.76, "lon": 96.08}}

MYANMAR_CITIES = load_stations()
city_list = sorted(list(MYANMAR_CITIES.keys()))

# --- ၃။ Sidebar ---
st.sidebar.image(dm_header_logo, width=100)
bias = st.sidebar.slider("🌡️ Bias Correction (°C)", -5.0, 5.0, 2.0, step=0.1)

# --- ၄။ Weather API Logic ---
@st.cache_data(ttl=600)
def fetch_weather(city):
    loc = MYANMAR_CITIES[city]
    url = f"https://api.open-meteo.com/v1/forecast?latitude={loc['lat']}&longitude={loc['lon']}&hourly=precipitation&daily=temperature_2m_max,temperature_2m_min&forecast_days=16&timezone=Asia%2FYangon"
    try:
        r = requests.get(url, timeout=15).json()
        df_h = pd.DataFrame({
            "Time": pd.to_datetime(r['hourly']['time']),
            "precipitation": r['hourly']['precipitation']
        })
        df_d = pd.DataFrame({
            "Date": pd.to_datetime(r['daily']['time']),
            "Tmax": r['daily']['temperature_2m_max'],
            "Tmin": r['daily']['temperature_2m_min']
        })
        return df_h, df_d
    except: return None, None

# --- ၅။ Main Display ---
st.title("🌤️ DMH AI Data Download System")
st.info(f"🕒 Current Time: {formatted_now}")

st.markdown("---")

# --- ၆။ Export Button Section ---
if st.button("🚀 Export All Stations Data"):
    all_data = []
    p_bar = st.progress(0)
    status_text = st.empty()
    
    for i, c in enumerate(city_list):
        status_text.text(f"⏳ Processing: {c}...")
        dh, dd = fetch_weather(c)
        if dh is not None:
            for d in dd['Date']:
                # ၂၄ နာရီ မိုးရေချိန်တွက်ချက်မှု (၀၉:၃၀ မှ ၀၉:၃၀)
                t930 = d + pd.Timedelta(hours=9, minutes=30)
                y930 = t930 - pd.Timedelta(days=1)
                rain = dh.loc[(dh['Time'] > y930) & (dh['Time'] <= t930), 'precipitation'].sum()
                
                all_data.append({
                    'Date': d.strftime('%Y-%m-%d'),
                    'Station': c,
                    'Max_Temp_C': round(dd.loc[dd['Date']==d, 'Tmax'].values[0] + bias, 1),
                    'Min_Temp_C': round(dd.loc[dd['Date']==d, 'Tmin'].values[0] + bias, 1),
                    'Rainfall_24h_mm': round(rain, 2)
                })
        p_bar.progress((i + 1) / len(city_list))
    
    st.session_state['master_df'] = pd.DataFrame(all_data)
    status_text.success("✅ Data Processing Complete!")

# --- ၇။ Display & Download Section ---
if 'master_df' in st.session_state:
    m_df = st.session_state['master_df']
    unique_dates = sorted(m_df['Date'].unique())
    
    sel_date = st.selectbox("📅 Select Date for Report", unique_dates)
    
    if sel_date:
        final_df = m_df[m_df['Date'] == sel_date].sort_values(by='Station')
        
        st.write(f"### {sel_date} ရက်နေ့အတွက် ခန့်မှန်းချက် အနှစ်ချုပ် (Bias +{bias}°C ပေါင်းပြီး)")
        
        # ဇယားကိုပြသခြင်း
        st.dataframe(final_df[['Station', 'Max_Temp_C', 'Min_Temp_C', 'Rainfall_24h_mm']], use_container_width=True)
        
        # ဒေါင်းလော့ခလုတ်
        csv = final_df.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label=f"📥 Download {sel_date} Report (CSV)",
            data=csv,
            file_name=f"DMH_Report_{sel_date}.csv",
            mime='text/csv'
        )

        # 📝 ရှင်းလင်းချက် Box
        st.markdown(f"""
        <div style='background-color: #f0f7ff; padding: 20px; border-radius: 10px; border-left: 5px solid #007bff; margin-top: 15px;'>
            <h4 style='color: #007bff; margin-top: 0;'>📝 ဇယားတွင် ပါဝင်သည့် ဒေတာများရှင်းလင်းချက်</h4>
            <ul style='list-style-type: none; padding-left: 0; line-height: 1.8;'>
                <li><b>၁။ အမြင့်ဆုံးအပူချိန်:</b> နေ့တစ်နေ့၏ ဖြစ်ပေါ်နိုင်သော အမြင့်ဆုံးအပူချိန် (Bias {bias}°C ပေါင်းပြီး)</li>
                <li><b>၂။ အနိမ့်ဆုံးအပူချိန်:</b> နေ့တစ်နေ့၏ ဖြစ်ပေါ်နိုင်သော အနိမ့်ဆုံးအပူချိန် (Bias {bias}°C ပေါင်းပြီး)</li>
                <li><b>၃။ မိုးရေချိန် (၂၄ နာရီ):</b> ယခင်နေ့ ၀၉:၃၀ နာရီမှ ယနေ့နံနက် ၀၉:၃၀ နာရီအထိ ၂၄ နာရီအတွင်း ရွာသွန်းသော စုစုပေါင်းမိုးရေချိန်</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

# Footer Section
st.markdown("---")
st.markdown("<div style='text-align: center; color: #666;'>Official System: Department of Meteorology and Hydrology (DMH) Myanmar</div>", unsafe_allow_html=True)

# Footer Section
st.markdown("---")
st.markdown(f"""
<div style='text-align: center; font-size: 0.85em; color: #666; line-height: 1.6;'>
    <p><b>Forecast Data Source (16-Day):</b> Open-Meteo API (ECMWF, GFS, ICON, JMA models).</p>
    <p><b>Rainfall Cycle:</b> 24-hour total from 09:30 AM (Yesterday) to 09:30 AM (Today).</p>
    <p><b>Heatwave Analysis:</b> Impact-Based Forecasting (IBF) thresholds and WMO criteria.</p>
    <p style='margin-top: 10px; font-weight: bold;'>Official System: Department of Meteorology and Hydrology (DMH) Myanmar</p>
</div>
""", unsafe_allow_html=True)
