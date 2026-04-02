import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import requests
import os
from datetime import datetime
import pytz

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
        "risk_levels": ["အလွန်အန္တရာယ်ရှိ", "အန္တရာယ်ရှိ", "သတိပြုရန်", "ပုံမှန်"],
        "charts": [
            "🌡️ ၁။ အပူချိန်(ဒီဂရီဆဲလ်စီးယပ်)", 
            "🌧️ ၂။ မိုးရေချိန်(မီလီမီတာ)", 
            "💨 ၃။ လေတိုက်နှုန်း(mph)နှင့်လေတိုက်ရာအရပ်", 
            "🔭 ၄။ အဝေးမြင်တာ (km)", 
            "💧 ၅။ စိုထိုင်းဆ (%)", 
            "☁️ ၆။ တိမ်ဖုံးမှုပမာဏ (Oktas: 0-8)", 
            "⚡ ၇။ မိုးတိမ်တောင်နှင့် လျှပ်စီးလက်နိုင်ခြေ (%)"
        ],
         "impact_list": [
            "အလွန်စိုးရိမ်ရသော အခြေအနေ! အပူဒဏ်လျှပ်စီးဖြတ်ခြင်း (Heatstroke) နှင့် ရေဓာတ်ကုန်ခမ်းခြင်းကြောင့် အသက်အန္တရာယ်ရှိနိုင်သည်။", 
            "အန္တရာယ်ရှိသော အခြေအနေ! အပူဒဏ်ကြောင့် ပင်ပန်းနွမ်းနယ်ခြင်း ဖြစ်နိုင်ပါသည်။ ကလေးနှင့် လူအိုများ အထူးသတိပြုပါ။", 
            "သတိပြုရန် အခြေအနေ! နေရောင်အောက်တွင် ကြာရှည်နေပါက ပင်ပန်းနွမ်းနယ်ခြင်း ဖြစ်ပေါ်နိုင်ပါသည်။", 
            "ပုံမှန်အခြေအနေ! သိသာထင်ရှားသော ကျန်းမာရေးထိခိုက်မှု မရှိနိုင်ပါ။"
        ],
        "recom_list": [
            "အိမ်ထဲတွင်သာ နေပါ။ ရေ (၃-၄) လီတာ သောက်ပါ။ မူးဝေပါက ဆေးရုံသို့ အမြန်သွားပါ။ မိုးလေဝသ သတင်းများကို အချိန်ပြည့် စောင့်ကြည့်ပါ။", 
            "ပြင်ပလုပ်ငန်းများကို နံနက်/ညနေသာ လုပ်ပါ။ ထီး/ဦးထုပ် ဆောင်းပါ။ ရေဓာတ်ဖြည့်ပါ။ မိုးလေဝသ သတင်းများကို နားထောင်ပါ။", 
            "ပေါ့ပါးသော အဝတ်များ ဝတ်ပါ။ ရေခဏခဏသောက်ပါ။ အရိပ်တွင် နားပါ။ မိုးဇလခန့်မှန်းချက်များကို နားထောင်ပါ။", 
            "ပုံမှန်အတိုင်း နေနိုင်ပါသည်။ ရေဓာတ်ဖြည့်တင်းရန်နှင့် မိုးလေဝသ သတင်းများကို ဆက်လက်စောင့်ကြည့်ပါ။"
        ]
    },
    "English": {
        "title": "DMH AI Weather Forecast System",
        "station_label": "🎯 Select Station",
        "view_mode_label": "📊 View Mode",
        "modes": ["16-Day Analysis", "Heatwave Monitoring (IBF)", "Climate Change"],
        "dmh_alert": "📢 Tip: Follow DMH for updates.",
        "storm_note": "📝 Note: High storm risk warning.",
        "ibf_header": "🏥 Health Sector Impacts & Recommendations",
        "risk_levels": ["Extreme Danger", "Danger", "Caution", "Normal"],
        "charts": ["Temp", "Rain", "Wind", "Visibility", "Humidity", "Cloud", "Storm"],
        "impact_list": ["Extreme Heatstroke risk!", "Danger of fatigue!", "Caution needed!", "Normal conditions."],
        "recom_list": ["Stay indoors!", "Avoid peak sun.", "Wear light clothes.", "Stay hydrated."]
    }
}

# --- ၃။ ဒေတာဖတ်ခြင်း ---
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

# --- ၄။ Sidebar ---
st.sidebar.image(dm_header_logo, width=100)
lang = st.sidebar.radio("🌐 Language", ["မြန်မာ", "English"], horizontal=True, key="lang_radio")
T = LANG_DATA[lang]
bias = st.sidebar.slider("🌡️ Bias Correction (°C)", -5.0, 5.0, 0.0, step=0.1)
selected_city = st.sidebar.selectbox(T["station_label"], city_list, key="city_select")
view_mode_choice = st.sidebar.radio(T["view_mode_label"], T["modes"], key="view_mode_radio")
mode_index = T["modes"].index(view_mode_choice)

# --- ၅။ Weather API ---
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

# --- ၆။ Main Page Display ---
st.title(T["title"])
st.info(f"📍 {selected_city} | 🕒 {formatted_now}")

df_h, df_d = fetch_weather(selected_city)

if df_h is not None and df_d is not None:
    df_d['Tmax'] += bias
    df_d['Tmin'] += bias
    df_h['Temp'] += bias
    
    # --- Mode 0: ၁၆ ရက်စာ ဂရပ်အားလုံး (၁ မှ ၇ ထိ) ---
    if mode_index == 0:
        st.warning(T["dmh_alert"])
        # 1. Temp
        st.subheader(T["charts"][0])
        st.plotly_chart(px.line(df_d, x='Date', y=['Tmax', 'Tmin'], markers=True, color_discrete_map={'Tmax':'red','Tmin':'blue'}), use_container_width=True)
        # 2. Rain
        st.subheader(T["charts"][1])
        st.plotly_chart(px.bar(df_d, x='Date', y='Rain', color_discrete_sequence=['skyblue']), use_container_width=True)
        # 3. Wind
        fig_wind = go.Figure()
        fig_wind.add_trace(go.Scatter(x=df_h['Time'], y=df_h['Wind'], mode='lines', name='Wind Speed', line=dict(color='blue', width=1)))
        df_arrow = df_h.iloc[::6, :] 
        fig_wind.add_trace(go.Scatter(
            x=df_arrow['Time'], y=df_arrow['Wind'], mode='markers',
            marker=dict(symbol='arrow', size=15, angle=df_arrow['WindDir'], color='darkgreen', line=dict(width=1, color='white')),
            name='Wind Direction'
        ))
        fig_wind.update_layout(title=T["charts"][2], yaxis_title="mph")
        st.plotly_chart(fig_wind, use_container_width=True)

        # 4. Visibility
        st.subheader(T["charts"][3])
        st.plotly_chart(px.line(df_h, x='Time', y='Vis', color_discrete_sequence=['gray']), use_container_width=True)
        # 5. Humidity
        st.subheader(T["charts"][4])
        st.plotly_chart(px.line(df_h, x='Time', y='Humid', color_discrete_sequence=['blue']), use_container_width=True)
        # 6. Cloud
        st.subheader(T["charts"][5])
        st.plotly_chart(px.bar(df_h, x='Time', y='Cloud_Oktas', color_discrete_sequence=['lightblue']), use_container_width=True)
        # 7. Storm
        st.subheader(T["charts"][6])
        st.error(T["storm_note"])
        st.plotly_chart(px.bar(df_h, x='Time', y='Storm', title=T["charts"][6], color_discrete_sequence=['#e67e22']), use_container_width=True)

    # --- Mode 1: IBF Health Risk Level ---
    elif mode_index == 1:
        st.subheader(T["ibf_header"])
        today_max = df_d.iloc[0]['Tmax']
        
        # Risk Logic
        if today_max >= 40: lvl, color, bg = 0, "white", "#FF0000" # အနီ
        elif today_max >= 37: lvl, color, bg = 1, "black", "#FFA500" # လိမ္မော်
        elif today_max >= 34: lvl, color, bg = 2, "black", "#FFFF00" # အဝါ
        else: lvl, color, bg = 3, "white", "#008000" # အစိမ်း

        # Risk Indicator UI
        st.markdown(f"""
            <div style='background-color:{bg}; color:{color}; padding:25px; border-radius:15px; text-align:center; border: 2px solid #333;'>
                <h1 style='margin:0;'>{T['risk_levels'][lvl]}</h1>
                <p style='font-size:1.2em; margin-top:10px;'>ယနေ့ခန့်မှန်းအမြင့်ဆုံးအပူချိန်: <b>{today_max:.1f} °C</b></p>
            </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            st.info(f"### ⚠️ အကျိုးသက်ရောက်မှု (Impact)\n{T['impact_list'][lvl]}")
        with col2:
            st.success(f"### ✅ အကြံပြုချက် (Action)\n{T['recom_list'][lvl]}")
        
        st.plotly_chart(px.bar(df_d, x='Date', y='Tmax', color='Tmax', color_continuous_scale='YlOrRd', title="Temperature Forecast Trend"), use_container_width=True)

    # --- Mode 2: Climate Change ---
    elif mode_index == 2:
        st.subheader("🌡️ Future Climate Projection (SSP5-8.5)")
        years = np.arange(2026, 2101)
        trend = [31 + (y-2026)*0.045 + np.random.normal(0, 0.4) for y in years]
        st.plotly_chart(px.line(x=years, y=trend, labels={'x':'Year', 'y':'Temp (°C)'}), use_container_width=True)

# --- ၇။ Export & Footer (အရင်အတိုင်း) ---
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
    st.download_button(label="📥 Download Report (CSV)", data=final_df.to_csv(index=False).encode('utf-8-sig'), file_name=f"DMH_{sel_date}.csv", mime='text/csv')

    # Data Description Box
    st.markdown("""
    <div style='background-color: #f8f9fa; padding: 20px; border-radius: 10px; border-left: 5px solid #007bff; margin-top:20px;'>
        <h4 style='color: #007bff; margin-top: 0;'>📝 ဇယားတွင် ပါဝင်သည့် ဒေတာများရှင်းလင်းချက်</h4>
        <ul style='list-style-type: none; padding-left: 0; line-height: 1.8;'>
            <li><b>၁။ အမြင့်ဆုံးအပူချိန်:</b> နေ့တစ်နေ့၏ ဖြစ်ပေါ်နိုင်သော အမြင့်ဆုံးအပူချိန် (Max Temp)</li>
            <li><b>၂။ အနိမ့်ဆုံးအပူချိန်:</b> နေ့တစ်နေ့၏ ဖြစ်ပေါ်နိုင်သော အနိမ့်ဆုံးအပူချိန် (Min Temp)</li>
            <li><b>၃။ မိုးရေချိန် (၂၄ နာရီ):</b> ၂၄ နာရီအတွင်း ရွာသွန်းသော စုစုပေါင်းမိုးရေချိန်</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown(f"""
<div style='text-align: center; font-size: 0.85em; color: #666; line-height: 1.6;'>
    <p><b>Forecast Data Source:</b> Open-Meteo API | <b>Rainfall Cycle:</b> 09:30 AM to 09:30 AM</p>
    <p><b>Heatwave Analysis:</b> IBF Thresholds & WMO Criteria</p>
    <p style='margin-top: 10px; font-weight: bold;'>Official System: Department of Meteorology and Hydrology (DMH) Myanmar</p>
</div>
""", unsafe_allow_html=True)
