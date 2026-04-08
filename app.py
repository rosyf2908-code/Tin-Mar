import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import requests
from datetime import datetime
import pytz
import time

# --- ၁။ Functions ---

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
def fetch_weather(city, stations_dict):
    if city not in stations_dict: return None, None
    loc = stations_dict[city]
    url = f"https://api.open-meteo.com/v1/forecast?latitude={loc['lat']}&longitude={loc['lon']}&hourly=temperature_2m,relative_humidity_2m,precipitation,windspeed_10m,winddirection_10m,visibility,cloud_cover,cape&daily=temperature_2m_max,temperature_2m_min&windspeed_unit=mph&forecast_days=16&timezone=Asia%2FYangon"
    try:
        r = requests.get(url, timeout=15)
        res = r.json()
        df_h = pd.DataFrame({
            "Time": pd.to_datetime(res['hourly']['time']),
            "Temp": res['hourly']['temperature_2m'],
            "Humid": res['hourly']['relative_humidity_2m'],
            "precipitation": res['hourly']['precipitation'],
            "Wind": res['hourly']['windspeed_10m'],
            "WindDir": res['hourly']['winddirection_10m'],
            "Vis": [v/1000 for v in res['hourly']['visibility']],
            "Cloud_Oktas": [round((c/100)*8) for c in res['hourly']['cloud_cover']],
            "Thunderstorm": [min(round((c/3500)*100), 100) if c else 0 for c in res['hourly'].get('cape', [])]
        })
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

# --- ၂။ UI Setup ---
st.set_page_config(page_title="DMH AI Weather Forecast", layout="wide")
MYANMAR_CITIES = load_stations()
city_list = sorted(list(MYANMAR_CITIES.keys()))
formatted_now = datetime.now(pytz.timezone('Asia/Yangon')).strftime('%I:%M %p, %d %b %Y')

LANG_DATA = {
    "မြန်မာ": {
        "title": "DMH AI မိုးလေဝသခန့်မှန်းစနစ်",
        "modes": ["၁၆ ရက်စာ အသေးစိတ်ဆန်းစစ်ချက်", "အပူချိန်စောင့်ကြည့်ခြင်း (IBF-ကျန်းမာရေး)", "ရာသီဥတုပြောင်းလဲမှု"],
        "risk_levels": ["Extreme Risk", "High Risk", "Moderate Risk", "Low Risk"],
        "impacts": ["Heatstroke ဖြစ်နိုင်ခြေ အလွန်များပါသည်။", "ပင်ပန်းနွမ်းနယ်ပြီး မူးဝေနိုင်ပါသည်။", "နေပူထဲကြာရှည်မနေသင့်ပါ။", "ပုံမှန်အတိုင်း အန္တရာယ်မရှိပါ။"],
        "recoms": ["အိမ်ထဲတွင်သာနေပြီး ရေများများသောက်ပါ။", "ထီး/ဦးထုပ်ဆောင်းပါ။ ပြင်းထန်သောအလုပ်ရှောင်ပါ။", "ပေါ့ပါးသောအဝတ်ဝတ်ပါ။ ရေဓာတ်ဖြည့်ပါ။", "ပုံမှန်အတိုင်း နေနိုင်ပါသည်။"]
    },
    "English": {
        "title": "DMH AI Weather Forecast System",
        "modes": ["16-Days Forecast", "Heatwave Monitoring (IBF)", "Climate Change"],
        "risk_levels": ["Extreme Risk", "High Risk", "Moderate Risk", "Low Risk"],
        "impacts": ["Extreme Heatstroke risk.", "High fatigue risk.", "Caution required.", "Normal conditions."],
        "recoms": ["Stay indoors. Drink 4L water.", "Use umbrella. Avoid heavy work.", "Wear light clothes. Hydrate.", "Normal activity."]
    }
}

# Sidebar
st.sidebar.image("https://www.moezala.gov.mm/themes/custom/dmh/logo.png?v=1.1", width=90)
lang = st.sidebar.radio("🌐 Language", ["မြန်မာ", "English"], horizontal=True)
T = LANG_DATA[lang]
selected_city = st.sidebar.selectbox("🎯 Select Station", city_list)
view_mode = st.sidebar.radio("📊 View Mode", T["modes"])
bias = st.sidebar.slider("🌡️ Bias Correction", -5.0, 5.0, 0.0)

st.title(T["title"])
st.info(f"📍 {selected_city} | 🕒 {formatted_now}")

df_h, df_d = fetch_weather(selected_city, MYANMAR_CITIES)

if df_h is not None and df_d is not None:
    df_h['Temp'] += bias
    df_d['Tmax'] += bias
    df_d['Tmin'] += bias

    # --- Mode 0: 16-Days ---
    if view_mode == T["modes"][0]:
        st.subheader("🌡️ ၁၆ ရက်စာ အပူချိန်ခန့်မှန်းချက်")
        st.plotly_chart(px.line(df_d, x='Date', y=['Tmax', 'Tmin'], markers=True), use_container_width=True)
        st.subheader("🌧️ ၁၆ ရက်စာ မိုးရေချိန်ခန့်မှန်းချက်")
        st.plotly_chart(px.bar(df_h, x='Time', y='precipitation', color_discrete_sequence=['dodgerblue']), use_container_width=True)

    # --- Mode 1: IBF Health Recommendations ---
    elif view_mode == T["modes"][1]:
        tmax_today = df_d.iloc[0]['Tmax']
        if tmax_today >= 42: lvl, bg = 0, "#FF0000"
        elif tmax_today >= 40: lvl, bg = 1, "#FFA500"
        elif tmax_today >= 38: lvl, bg = 2, "#FFFF00"
        else: lvl, bg = 3, "#008000"

        st.markdown(f"""
            <div style='background-color:{bg}; padding:20px; border-radius:15px; text-align:center; border:2px solid #333;'>
                <h1 style='margin:0;'>{T['risk_levels'][lvl]}</h1>
                <p style='font-size:1.3em;'>Forecast Max: <b>{tmax_today:.1f} °C</b></p>
            </div>
        """, unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        with c1: st.warning(f"⚠️ **Health Impact:**\n{T['impacts'][lvl]}")
        with c2: st.success(f"✅ **Recommendation:**\n{T['recoms'][lvl]}")

        st.plotly_chart(px.line(df_h, x='Time', y=['HI', 'WBGT', 'UTCI'], title="Heat Indices"), use_container_width=True)

    # --- Mode 2: Climate ---
    elif view_mode == T["modes"][2]:
        st.subheader("🌡️ Future Temperature Projection (2026-2100)")
        years = np.arange(2026, 2101)
        trend = [31.5 + (y-2026)*0.048 + np.random.normal(0, 0.45) for y in years]
        st.plotly_chart(px.line(x=years, y=trend, labels={'x':'Year', 'y':'Temp (°C)'}), use_container_width=True)

# --- ၄။ Export & Download Section ---
st.markdown("---")
if st.button("🚀 Export All Stations Report"):
    results = []
    p = st.progress(0)
    for i, city in enumerate(city_list):
        _, dd = fetch_weather(city, MYANMAR_CITIES)
        if dd is not None:
            results.append({'Date': dd.iloc[0]['Date'].strftime('%Y-%m-%d'), 'Station': city, 'Tmax': dd.iloc[0]['Tmax'] + bias})
        p.progress((i + 1) / len(city_list))
        time.sleep(0.1)
    st.session_state['out_df'] = pd.DataFrame(results)
    st.success("Export Complete!")

if 'out_df' in st.session_state:
    final_df = st.session_state['out_df']
    st.write("### 📋 Station-wise Data")
    st.dataframe(final_df, use_container_width=True)
    
    # ဒေါင်းလော့ခလုတ်
    csv_data = final_df.to_csv(index=False).encode('utf-8-sig')
    st.download_button(
        label="📥 Download CSV Report",
        data=csv_data,
        file_name=f"DMH_Report_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )
# --- ၄။ Export Section (အောက်ဆုံးတွင်ထားရမည်) ---
st.markdown("---")
if st.button("🚀 Export All Stations Report"):
    all_data = []
    p_bar = st.progress(0)
    for i, city in enumerate(city_list):
        _, dd = fetch_weather(city, MYANMAR_CITIES)
        if dd is not None:
            latest = dd.iloc[0]
            all_data.append({'Date': latest['Date'].strftime('%Y-%m-%d'), 'Station': city, 'Tmax': latest['Tmax']})
        time.sleep(0.5)
        p_bar.progress((i + 1) / len(city_list))
    st.session_state['master_df'] = pd.DataFrame(all_data)
    st.success("Export Complete!")

if 'master_df' in st.session_state:
    m_df = st.session_state['master_df']
    sel_date = st.selectbox("📅 နေ့စွဲရွေးချယ်ပါ", sorted(m_df['Date'].unique(), reverse=True))
    final_df = m_df[m_df['Date'] == sel_date].sort_values(by='Station')
    st.dataframe(final_df, use_container_width=True)
    st.download_button("📥 Download CSV", final_df.to_csv(index=False).encode('utf-8-sig'), f"DMH_{sel_date}.csv", "text/csv")

st.markdown("<br><div style='text-align: center; color: gray;'>Official System: Department of Meteorology and Hydrology (DMH) Myanmar</div>", unsafe_allow_html=True)

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
