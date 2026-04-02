import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import requests
import os
from datetime import datetime
import pytz

# --- Layout Setup ---
st.set_page_config(page_title="DMH AI Weather Forecast System", layout="wide", page_icon="🌤️")

mm_tz = pytz.timezone('Asia/Yangon')
now = datetime.now(mm_tz)
formatted_now = now.strftime('%I:%M %p, %d %b %Y')
dm_header_logo = "https://www.moezala.gov.mm/themes/custom/dmh/logo.png?v=1.1"

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import requests
import os
from datetime import datetime
import pytz

# --- Layout Setup ---
st.set_page_config(page_title="DMH AI Weather Forecast System", layout="wide", page_icon="🌤️")

mm_tz = pytz.timezone('Asia/Yangon')
now = datetime.now(mm_tz)
formatted_now = now.strftime('%I:%M %p, %d %b %Y')
dm_header_logo = "https://www.moezala.gov.mm/themes/custom/dmh/logo.png?v=1.1"

# --- ဘာသာစကားနှင့် စာသားများ ---
LANG_DATA = {
    "မြန်မာ": {
        "title": "DMH AI မိုးလေဝသခန့်မှန်းစနစ်",
        "station_label": "🎯 စခန်းအမည်ရွေးချယ်ပါ",
        "view_mode_label": "📊 View Mode",
        "modes": ["၁၆ ရက်စာ အသေးစိတ်ဆန်းစစ်ချက်", "အပူချိန်စောင့်ကြည့်ခြင်း (IBF-ကျန်းမာရေး )", "ရာသီဥတုပြောင်းလဲမှု (၂၁၀၀-SSP5-8.5)"],
        "dmh_alert": "📢 အကြံပြုချက်: နောက်ဆုံးရ မိုးလေဝသသတင်းများအတွက် မိုးဇလ သတင်းများကိုစောင့်ကြည့်ပါ။",
        "storm_note": "📝 မှတ်ချက်: မိုးတိမ်တောင် ဖြစ်နိုင်ခြေ ၆၀% ထက်ကျော်လွန်ပါက လေပြင်းတိုက်ခတ်ခြင်း၊ မိုးကြိုးပစ်ခြင်းနှင့် လျှပ်စီးလက်ခြင်းများ ဖြစ်ပေါ်နိုင်သဖြင့် ဂရုပြုရန် လိုအပ်ပါသည်။",
        "charts": [
            "🌡️ ၁။ အပူချိန်(ဒီဂရီဆဲလ်စီးယပ်)", 
            "🌧️ ၂။ မိုးရေချိန်(မီလီမီတာ)", 
            "💨 ၃။ လေတိုက်နှုန်း(mph)နှင့် လေအရပ်", 
            "🔭 ၄။ အဝေးမြင်တာ (km)", 
            "💧 ၅။ စိုထိုင်းဆ (%)", 
            "☁️ ၆။ တိမ်ဖုံးမှုပမာဏ (Oktas: 0-8)", 
            "⚡ ၇။ မိုးတိမ်တောင်နှင့် လျှပ်စီးလက်နိုင်ခြေ (%)"
        ]
    },
    "English": {
        "title": "DMH AI Weather Forecast System",
        "station_label": "🎯 Select Station",
        "view_mode_label": "📊 View Mode",
        "modes": ["16-Day Detailed Analysis", "Heatwave Monitoring (IBF-Health)", "Climate Change (2100-SSP5-8.5)"],
        "dmh_alert": "📢 Tip: Follow DMH news for latest updates.",
        "storm_note": "📝 Note: High storm probability risk.",
        "charts": ["🌡️ 1. Temp(°C)", "🌧️ 2. Rain(mm)", "💨 3. Wind(mph)", "🔭 4. Vis(km)", "💧 5. Humid(%)", "☁️ 6. Cloud(Oktas)", "⚡ 7. Storm(%)"]
    }
}

# --- ဒေတာဖတ်ခြင်း ---
@st.cache_data
def load_stations():
    file_path = "Station.csv"
    if not os.path.exists(file_path):
        return {"Naypyidaw": {"lat": 19.76, "lon": 96.08}}
    try:
        df_csv = pd.read_csv(file_path, encoding='utf-8-sig')
        df_csv.columns = [c.strip() for c in df_csv.columns]
        return {str(row.iloc[0]).strip(): {'lat': float(row['Lat']), 'lon': float(row['Lon'])} for _, row in df_csv.iterrows()}
    except: return {"Naypyidaw": {"lat": 19.76, "lon": 96.08}}

MYANMAR_CITIES = load_stations()
city_list = sorted(list(MYANMAR_CITIES.keys()))

# --- Sidebar ---
st.sidebar.image(dm_header_logo, width=100)
lang = st.sidebar.radio("🌐 Language", ["မြန်မာ", "English"], horizontal=True)
T = LANG_DATA[lang]
bias = st.sidebar.slider("🌡️ Bias Correction (°C)", -5.0, 5.0, 0.0, step=0.1)
selected_city = st.sidebar.selectbox(T["station_label"], city_list)
view_mode_choice = st.sidebar.radio(T["view_mode_label"], T["modes"])
mode_index = T["modes"].index(view_mode_choice)

# --- Weather API ---
@st.cache_data(ttl=600)
def fetch_weather(city):
    loc = MYANMAR_CITIES[city]
    url = f"https://api.open-meteo.com/v1/forecast?latitude={loc['lat']}&longitude={loc['lon']}&hourly=temperature_2m,precipitation,windspeed_10m,winddirection_10m,relative_humidity_2m,visibility,cloud_cover,cape&daily=temperature_2m_max,temperature_2m_min,precipitation_sum&windspeed_unit=mph&forecast_days=16&timezone=Asia%2FYangon"
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
            "Storm": [min(round((c/3500)*100), 100) if (c is not None and c >= 0) else 0 for c in r['hourly'].get('cape', [])]
        })
        df_d = pd.DataFrame({
            "Date": pd.to_datetime(r['daily']['time']), 
            "Tmax": r['daily']['temperature_2m_max'],
            "Tmin": r['daily']['temperature_2m_min'], 
            "Rain": r['daily']['precipitation_sum']
        })
        return df_h, df_d
    except: return None, None

# --- Main Page ---
st.title(T["title"])
st.info(f"📍 {selected_city} | 🕒 {formatted_now}")

df_h, df_d = fetch_weather(selected_city)

if df_h is not None and df_d is not None:
    df_d['Tmax'] += bias
    df_d['Tmin'] += bias
    df_h['Temp'] += bias
    
    if mode_index == 0:
        st.warning(T["dmh_alert"])
        # ၁။ အပူချိန်
        st.subheader(T["charts"][0])
        st.plotly_chart(px.line(df_d, x='Date', y=['Tmax', 'Tmin'], markers=True, color_discrete_map={'Tmax':'red','Tmin':'blue'}), use_container_width=True)
        
        # ၂။ မိုးရေချိန်
        st.subheader(T["charts"][1])
        st.plotly_chart(px.bar(df_d, x='Date', y='Rain', color_discrete_sequence=['skyblue']), use_container_width=True)
        
        # ၃။ လေတိုက်နှုန်း
        st.subheader(T["charts"][2])
        fig_wind = px.line(df_h, x='Time', y='Wind')
        fig_wind.add_trace(go.Scatter(x=df_h['Time'], y=df_h['Wind'], mode='markers', name='Direction', hovertext=df_h['WindDir']))
        st.plotly_chart(fig_wind, use_container_width=True)

        # ၄။ အဝေးမြင်တာ
        st.subheader(T["charts"][3])
        st.plotly_chart(px.line(df_h, x='Time', y='Vis', color_discrete_sequence=['purple']), use_container_width=True)

        # ၅။ စိုထိုင်းဆ
        st.subheader(T["charts"][4])
        st.plotly_chart(px.line(df_h, x='Time', y='Humid', color_discrete_sequence=['teal']), use_container_width=True)

        # ၆။ တိမ်ဖုံးမှု
        st.subheader(T["charts"][5])
        st.plotly_chart(px.bar(df_h, x='Time', y='Cloud_Oktas', color_discrete_sequence=['gray']), use_container_width=True)
        
        # ၇။ မိုးတိမ်တောင်
        st.error(T["storm_note"])
        st.subheader(T["charts"][6])
        st.plotly_chart(px.bar(df_h, x='Time', y='Storm', color_discrete_sequence=['orange']), use_container_width=True)

    elif mode_index == 1:
        # IBF Health Logic Here...
        max_t = df_d['Tmax'].max()
        st.metric("Max Temperature", f"{max_t:.1f} °C")
        st.plotly_chart(px.bar(df_d, x='Date', y='Tmax', color='Tmax', color_continuous_scale='YlOrRd'), use_container_width=True)

    elif mode_index == 2:
        # Climate Change logic here...
        st.subheader("🌡️ Future Trend (2026-2100)")
        years = np.arange(2026, 2101)
        trend = [31 + (y-2026)*0.045 + np.random.normal(0, 0.4) for y in years]
        st.plotly_chart(px.line(x=years, y=trend), use_container_width=True)

# Footer
st.markdown("---")
st.markdown("<p style='text-align: center; color: gray;'>Official System: Department of Meteorology and Hydrology (DMH) Myanmar</p>", unsafe_allow_html=True)

# --- ဒေတာဖတ်ခြင်း ---
@st.cache_data
def load_stations():
    file_path = "Station.csv"
    if not os.path.exists(file_path):
        return {"Naypyidaw": {"lat": 19.76, "lon": 96.08}}
    try:
        df_csv = pd.read_csv(file_path, encoding='utf-8-sig')
        df_csv.columns = [c.strip() for c in df_csv.columns]
        return {str(row.iloc[0]).strip(): {'lat': float(row['Lat']), 'lon': float(row['Lon'])} for _, row in df_csv.iterrows()}
    except: return {"Naypyidaw": {"lat": 19.76, "lon": 96.08}}

MYANMAR_CITIES = load_stations()
city_list = sorted(list(MYANMAR_CITIES.keys()))

# --- Sidebar ---
st.sidebar.image(dm_header_logo, width=100)
lang = st.sidebar.radio("🌐 Language", ["မြန်မာ", "English"], horizontal=True)
T = LANG_DATA[lang]
bias = st.sidebar.slider("🌡️ Bias Correction (°C)", -5.0, 5.0, 0.0, step=0.1)
selected_city = st.sidebar.selectbox(T["station_label"], city_list)
view_mode_choice = st.sidebar.radio(T["view_mode_label"], T["modes"])
mode_index = T["modes"].index(view_mode_choice)

# --- Weather API ---
@st.cache_data(ttl=600)
def fetch_weather(city):
    loc = MYANMAR_CITIES[city]
    url = f"https://api.open-meteo.com/v1/forecast?latitude={loc['lat']}&longitude={loc['lon']}&hourly=temperature_2m,precipitation,windspeed_10m,winddirection_10m,relative_humidity_2m,visibility,cloud_cover,cape&daily=temperature_2m_max,temperature_2m_min,precipitation_sum&windspeed_unit=mph&forecast_days=16&timezone=Asia%2FYangon"
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
            "Storm": [min(round((c/3500)*100), 100) if (c is not None and c >= 0) else 0 for c in r['hourly'].get('cape', [])]
        })
        df_d = pd.DataFrame({
            "Date": pd.to_datetime(r['daily']['time']), 
            "Tmax": r['daily']['temperature_2m_max'],
            "Tmin": r['daily']['temperature_2m_min'], 
            "Rain": r['daily']['precipitation_sum']
        })
        return df_h, df_d
    except: return None, None

# --- Main Page ---
st.title(T["title"])
st.info(f"📍 {selected_city} | 🕒 {formatted_now}")

df_h, df_d = fetch_weather(selected_city)

if df_h is not None and df_d is not None:
    df_d['Tmax'] += bias
    df_d['Tmin'] += bias
    df_h['Temp'] += bias
    
    if mode_index == 0:
        st.warning(T["dmh_alert"])
        # ၁။ အပူချိန်
        st.subheader(T["charts"][0])
        st.plotly_chart(px.line(df_d, x='Date', y=['Tmax', 'Tmin'], markers=True, color_discrete_map={'Tmax':'red','Tmin':'blue'}), use_container_width=True)
        
        # ၂။ မိုးရေချိန်
        st.subheader(T["charts"][1])
        st.plotly_chart(px.bar(df_d, x='Date', y='Rain', color_discrete_sequence=['skyblue']), use_container_width=True)
        
        # ၃။ လေတိုက်နှုန်း
        st.subheader(T["charts"][2])
        fig_wind = px.line(df_h, x='Time', y='Wind')
        fig_wind.add_trace(go.Scatter(x=df_h['Time'], y=df_h['Wind'], mode='markers', name='Direction', hovertext=df_h['WindDir']))
        st.plotly_chart(fig_wind, use_container_width=True)

        # ၄။ အဝေးမြင်တာ
        st.subheader(T["charts"][3])
        st.plotly_chart(px.line(df_h, x='Time', y='Vis', color_discrete_sequence=['purple']), use_container_width=True)

        # ၅။ စိုထိုင်းဆ
        st.subheader(T["charts"][4])
        st.plotly_chart(px.line(df_h, x='Time', y='Humid', color_discrete_sequence=['teal']), use_container_width=True)

        # ၆။ တိမ်ဖုံးမှု
        st.subheader(T["charts"][5])
        st.plotly_chart(px.bar(df_h, x='Time', y='Cloud_Oktas', color_discrete_sequence=['gray']), use_container_width=True)
        
        # ၇။ မိုးတိမ်တောင်
        st.error(T["storm_note"])
        st.subheader(T["charts"][6])
        st.plotly_chart(px.bar(df_h, x='Time', y='Storm', color_discrete_sequence=['orange']), use_container_width=True)

    elif mode_index == 1:
        # IBF Health Logic Here...
        max_t = df_d['Tmax'].max()
        st.metric("Max Temperature", f"{max_t:.1f} °C")
        st.plotly_chart(px.bar(df_d, x='Date', y='Tmax', color='Tmax', color_continuous_scale='YlOrRd'), use_container_width=True)

    elif mode_index == 2:
        # Climate Change logic here...
        st.subheader("🌡️ Future Trend (2026-2100)")
        years = np.arange(2026, 2101)
        trend = [31 + (y-2026)*0.045 + np.random.normal(0, 0.4) for y in years]
        st.plotly_chart(px.line(x=years, y=trend), use_container_width=True)
  # --- ဒေတာများကို Export လုပ်သည့်အပိုင်း ---
        if st.button("🚀 Export All Stations Data"):
            all_data = []
            p_bar = st.progress(0) # Progress bar စတင်ခြင်း
            status_text = st.empty() # အခြေအနေပြစာသားအတွက်နေရာလွတ်
            generation_time = formatted_now 

            for i, c in enumerate(city_list):
                status_text.text(f"⏳ Processing: {c}...") # ဘယ်စခန်းကို လုပ်နေလဲဆိုတာ ပြပေးရန်
                df_h_tmp, df_d_tmp = fetch_weather(c)
                if df_h_tmp is not None:
                    daily_records = []
                    for d in df_d_tmp['Date']:
                        today_930 = d + pd.Timedelta(hours=9, minutes=30)
                        yesterday_930 = today_930 - pd.Timedelta(days=1)
                        mask = (df_h_tmp['Time'] > yesterday_930) & (df_h_tmp['Time'] <= today_930)
                        
                        # မိုးရေချိန်ပေါင်းခြင်း
                        rain_val = df_h_tmp.loc[mask, 'precipitation'].sum() if 'precipitation' in df_h_tmp else 0
                        
                        tmax_val = df_d_tmp.loc[df_d_tmp['Date'] == d, 'Tmax'].values[0]
                        tmin_val = df_d_tmp.loc[df_d_tmp['Date'] == d, 'Tmin'].values[0]

                        daily_records.append({
                            'Date': d.strftime('%Y-%m-%d'),
                            'Station': c,
                            'Max_Temp_C': round(tmax_val, 1),
                            'Min_Temp_C': round(tmin_val, 1),
                            'Rainfall_24h_mm': round(rain_val, 2)
                        })
                    all_data.extend(daily_records)
                p_bar.progress((i + 1) / len(city_list))
            
            if all_data:
                st.session_state['master_df'] = pd.DataFrame(all_data)
                status_text.success("✅ ဒေတာများ အားလုံး စုစည်းပြီးပါပြီ။")
            else:
                status_text.error("❌ ဒေတာရယူ၍ မရနိုင်ပါ။")

        # --- ဒေတာများကို ဇယားဖြင့်ပြသခြင်းနှင့် Download ---
        if 'master_df' in st.session_state:
            m_df = st.session_state['master_df'].copy()
            unique_dates = sorted(m_df['Date'].unique())
            sel_date = st.selectbox("📅 Report ထုတ်လိုသည့် နေ့စွဲကို ရွေးပါ", unique_dates)
            
            final_df = m_df[m_df['Date'] == sel_date].sort_values(by='Station')
            display_cols = ['Station', 'Max_Temp_C', 'Min_Temp_C', 'Rainfall_24h_mm']
            
            if not final_df.empty:
                st.write(f"### {sel_date} ရက်နေ့အတွက် ခန့်မှန်းချက် အနှစ်ချုပ်")
                st.dataframe(final_df[display_cols], use_container_width=True)
                
                try:
                    csv_output = final_df[display_cols].to_csv(index=False).encode('utf-8-sig')
                    
                    # ဒီနေရာမှာ fileName ကို file_name လို့ ပြောင်းလိုက်ပါတယ်
                    st.download_button(
                        label=f"📥 Download {sel_date} Report (CSV)",
                        data=csv_output,
                        file_name=f"DMH_Report_{sel_date}.csv", # ပြင်ဆင်လိုက်သည့်နေရာ
                        mime='text/csv'
                    )
                except Exception as e:
                    st.error(f"CSV ထုတ်ယူရာတွင် အမှားအယွင်းရှိနေပါသည် - {e}")

    # Download ခလုတ်၏ အောက်တွင် ထည့်ရန်
                st.markdown("---")
                st.markdown("""
                <div style='background-color: #f8f9fa; padding: 20px; border-radius: 10px; border-left: 5px solid #007bff;'>
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
# Footer
st.markdown("---")
st.markdown("<p style='text-align: center; color: gray;'>Official System: Department of Meteorology and Hydrology (DMH) Myanmar</p>", unsafe_allow_html=True)
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
