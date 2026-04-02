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

st.markdown("""
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <meta name="apple-mobile-web-app-title" content="DMH AI">
""", unsafe_allow_html=True)

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
        "charts": ["🌡️ ၁။ အပူချိန်(ဒီဂရီဆဲလ်စီးယပ်)", "🌧️ ၂။ မိုးရေချိန်(မီလီမီတာ)", "💨 ၃။ လေတိုက်နှုန်း(mph)နှင့်လေတိုက်ရာအရပ်", "🔭 ၄။ အဝေးမြင်တာ (km)", "💧 ၅။ စိုထိုင်းဆ (%)", "☁️ ၆။ တိမ်ဖုံးမှုပမာဏ (Oktas: 0-8)", "⚡ ၇။ မိုးတိမ်တောင်နှင့် လျှပ်စီးလက်နိုင်ခြေ (%)"],
        "impact_list": ["အလွန်စိုးရိမ်ရသော အခြေအနေ! Heatstroke အသက်အန္တရာယ်ရှိနိုင်သည်။", "အန္တရာယ်ရှိသော အခြေအနေ! အပူဒဏ်ကြောင့် ပင်ပန်းနွမ်းနယ်နိုင်ပါသည်။", "သတိပြုရန် အခြေအနေ! ပင်ပန်းနွမ်းနယ်ခြင်း ဖြစ်နိုင်ပါသည်။", "ပုံမှန်အခြေအနေ!"],
        "recom_list": ["အိမ်ထဲတွင်သာ နေပါ။ ရေ (၃-၄) လီတာ သောက်ပါ။", "ပြင်ပလုပ်ငန်းများကို နံနက်/ညနေသာ လုပ်ပါ။", "ပေါ့ပါးသော အဝတ်များ ဝတ်ပါ။", "ပုံမှန်အတိုင်း နေနိုင်ပါသည်။"]
    },
    "English": {
        "title": "DMH AI Weather Forecast System",
        "station_label": "🎯 Select Station",
        "view_mode_label": "📊 View Mode",
        "modes": ["16-Day Detailed Analysis", "Heatwave Monitoring (IBF-Health)", "Climate Change (2100-SSP5-8.5)"],
        "dmh_alert": "📢 Tip: Follow DMH updates.",
        "storm_note": "📝 Note: Beware of thunderstorms if probability > 60%.",
        "ibf_header": "🏥 Health Sector Impacts & Recommendations",
        "risk_levels": ["Extreme Risk", "High Risk", "Moderate Risk", "Low Risk"],
        "charts": ["🌡️ 1. Temp", "🌧️ 2. Rain", "💨 3. Wind", "🔭 4. Vis", "💧 5. Humidity", "☁️ 6. Cloud", "⚡ 7. Storm"],
        "impact_list": ["Extreme danger!", "High danger!", "Caution!", "Normal."],
        "recom_list": ["Stay indoors.", "Limit outdoor work.", "Wear light clothes.", "Stay hydrated."]
    }
}

# --- ၃။ စခန်းစာရင်းဖတ်ခြင်း ---
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

# --- ၄။ Sidebar ---
st.sidebar.image(dm_header_logo, width=100)
lang = st.sidebar.radio("🌐 Language", ["မြန်မာ", "English"], horizontal=True)
T = LANG_DATA[lang]

bias = st.sidebar.slider("🌡️ Bias Correction (°C)", -5.0, 5.0, 0.0, step=0.1)
selected_city = st.sidebar.selectbox(T["station_label"], city_list)
view_mode = st.sidebar.radio(T["view_mode_label"], T["modes"])

# --- ၅။ Weather API Logic ---
@st.cache_data(ttl=600)
def fetch_weather(city):
    loc = MYANMAR_CITIES[city]
    url = f"https://api.open-meteo.com/v1/forecast?latitude={loc['lat']}&longitude={loc['lon']}&hourly=temperature_2m,relative_humidity_2m,cloud_cover,visibility,precipitation,windspeed_10m,winddirection_10m,cape&daily=temperature_2m_max,temperature_2m_min,precipitation_sum&windspeed_unit=mph&forecast_days=16&timezone=Asia%2FYangon"
    try:
        r = requests.get(url, timeout=15).json()
        df_h = pd.DataFrame({
            "Time": pd.to_datetime(r['hourly']['time']), "Temp": r['hourly']['temperature_2m'],
            "Wind": r['hourly']['windspeed_10m'], "WindDir": r['hourly']['winddirection_10m'],
            "Vis": [v/1000 for v in r['hourly']['visibility']], "Humid": r['hourly']['relative_humidity_2m'],
            "Cloud_Oktas": [round((c/100)*8) for c in r['hourly']['cloud_cover']],
            "Storm": [min(round((c/3500)*100), 100) if (c is not None and c >= 0) else 0 for c in r['hourly'].get('cape', [])],
            "precipitation": r['hourly']['precipitation']
        })
        df_d = pd.DataFrame({
            "Date": pd.to_datetime(r['daily']['time']), "Tmax": r['daily']['temperature_2m_max'],
            "Tmin": r['daily']['temperature_2m_min'], "Rain": r['daily']['precipitation_sum']
        })
        return df_h, df_d
    except: return None, None

# --- ၆။ Main Page Display ---
st.title(T["title"])
st.info(f"📍 {selected_city} | 🕒 {formatted_now}")
df_h, df_d = fetch_weather(selected_city)

if df_h is not None:
    df_d['Tmax'] += bias
    df_d['Tmin'] += bias
    df_h['Temp'] += bias
    st.warning(T["dmh_alert"])

    if view_mode == T["modes"][0]:
        st.plotly_chart(px.line(df_d, x='Date', y=['Tmax', 'Tmin'], title=T["charts"][0], markers=True, color_discrete_map={'Tmax':'red','Tmin':'blue'}), use_container_width=True)
        st.plotly_chart(px.bar(df_d, x='Date', y='Rain', title=T["charts"][1]), use_container_width=True)
        st.plotly_chart(px.line(df_h, x='Time', y='Vis', title=T["charts"][3]), use_container_width=True)
        st.error(T["storm_note"])
        st.plotly_chart(px.bar(df_h, x='Time', y='Storm', title=T["charts"][6], color_discrete_sequence=['#e67e22']), use_container_width=True)

    elif view_mode == T["modes"][1]:
        max_t = df_d['Tmax'].max()
        idx = 0 if max_t >= 42 else 1 if max_t >= 40 else 2 if max_t >= 38 else 3
        colors = ['#800000','#d00000','#ffaa00','#008000']
        st.markdown(f"<div style='background-color:{colors[idx]}; padding:35px; border-radius:15px; text-align:center;'><h1 style='color:white;'>{T['risk_levels'][idx]}: {max_t:.1f} °C</h1></div>", unsafe_allow_html=True)
        st.subheader(T['ibf_header'])
        st.error(f"⚠️ **Impact:** {T['impact_list'][idx]}")
        st.success(f"💡 **Recommendations:** {T['recom_list'][idx]}")
        fig_ibf = px.bar(df_d, x='Date', y='Tmax', color='Tmax', color_continuous_scale='YlOrRd')
        st.plotly_chart(fig_ibf, use_container_width=True)

    elif view_mode == T["modes"][2]:
        st.subheader("🌡️ Climate Projection (2026-2100)")
        years = np.arange(2026, 2101)
        trend = [31 + (y-2026)*0.045 + np.random.normal(0, 0.4) for y in years]
        st.plotly_chart(px.line(x=years, y=trend, labels={'y':'Temp (°C)', 'x':'Year'}), use_container_width=True)
        st.warning("⚠️ **Climate Risk Note:** High risk of extreme heat in SSP 5-8.5 scenario.")

# --- ၇။ Global Export Section ---
st.markdown("---")
if st.button("🚀 Export All Stations Data"):
    all_data = []
    p_bar = st.progress(0)
    status_text = st.empty()
    for i, c in enumerate(city_list):
        status_text.text(f"⏳ Processing: {c}...")
        dh, dd = fetch_weather(c)
        if dh is not None:
            for d in dd['Date']:
                t930 = d + pd.Timedelta(hours=9, minutes=30)
                y930 = t930 - pd.Timedelta(days=1)
                rain = dh.loc[(dh['Time'] > y930) & (dh['Time'] <= t930), 'precipitation'].sum()
                all_data.append({
                    'Date': d.strftime('%Y-%m-%d'), 'Station': c,
                    'Max_Temp_C': round(dd.loc[dd['Date']==d, 'Tmax'].values[0] + bias, 1),
                    'Min_Temp_C': round(dd.loc[dd['Date']==d, 'Tmin'].values[0] + bias, 1),
                    'Rainfall_24h_mm': round(rain, 2)
                })
        p_bar.progress((i + 1) / len(city_list))
    st.session_state['master_df'] = pd.DataFrame(all_data)
    status_text.success("✅ Done!")

if 'master_df' in st.session_state:
    m_df = st.session_state['master_df']
    unique_dates = sorted(m_df['Date'].unique())
    sel_date = st.selectbox("📅 Report ထုတ်လိုသည့် နေ့စွဲကို ရွေးပါ", unique_dates)
    final_df = m_df[m_df['Date'] == sel_date].sort_values(by='Station')
    
    st.write(f"### {sel_date} ရက်နေ့အတွက် ခန့်မှန်းချက် အနှစ်ချုပ် (Bias +{bias}°C ပေါင်းပြီး)")
    st.dataframe(final_df[['Station', 'Max_Temp_C', 'Min_Temp_C', 'Rainfall_24h_mm']], use_container_width=True)
    
    csv = final_df.to_csv(index=False).encode('utf-8-sig')
    st.download_button(
        label=f"📥 Download {sel_date} Report (CSV)",
        data=csv,
        file_name=f"DMH_Report_{sel_date}.csv",
        mime='text/csv'
    )

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
st.markdown(f"""
<div style='text-align: center; font-size: 0.85em; color: #666; line-height: 1.6;'>
    <p><b>Forecast Data Source (16-Day):</b> Open-Meteo API (ECMWF, GFS, ICON, JMA models).</p>
    <p><b>Rainfall Cycle:</b> 24-hour total from 09:30 AM (Yesterday) to 09:30 AM (Today).</p>
    <p><b>Heatwave Analysis:</b> Impact-Based Forecasting (IBF) thresholds and WMO criteria.</p>
    <p style='margin-top: 10px; font-weight: bold;'>Official System: Department of Meteorology and Hydrology (DMH) Myanmar</p>
</div>
""", unsafe_allow_html=True)
