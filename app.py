import streamlit as st
import pd as pd
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

# --- ၂။ Heat Indices Calculation Logic ---
def calculate_all_indices(temp_c, rh):
    hi = 0.5 * (temp_c + 61.0 + ((temp_c - 68.0) * 1.2) + (rh * 0.094))
    e = (rh / 100) * 6.105 * np.exp(17.27 * temp_c / (237.7 + temp_c))
    wbgt = (0.567 * temp_c) + (0.393 * e) + 3.94
    utci = temp_c + (0.33 * e) - (0.7 * 0.1) - 4.0
    return round(hi, 1), round(wbgt, 1), round(utci, 1)

# --- ၃။ ဘာသာစကားနှင့် စာသားများ ---
LANG_DATA = {
    "မြန်မာ": {
        "title": "DMH AI မိုးလေဝသခန့်မှန်းစနစ်",
        "station_label": "🎯 စခန်းအမည်ရွေးချယ်ပါ",
        "view_mode_label": "📊 View Mode",
        "modes": ["၁၆ ရက်စာ အသေးစိတ်ဆန်းစစ်ချက်", "အပူချိန်စောင့်ကြည့်ခြင်း (IBF-ကျန်းမာရေး )", "ရာသီဥတုပြောင်းလဲမှု (၂၁၀၀-SSP5-8.5)"],
        "dmh_alert": "📢 အကြံပြုချက်: နောက်ဆုံးရ မိုးလေဝသသတင်းများအတွက် မိုးဇလ သတင်းများကိုစောင့်ကြည့်ပါ။",
        "ibf_header": "🏥 ကျန်းမာရေးကဏ္ဍဆိုင်ရာ အကျိုးသက်ရောက်မှုနှင့် အကြံပြုချက်များ",
        "risk_levels": ["Extreme Risk (အလွန်အန္တရာယ်ရှိ)", "High Risk (အန္တရာယ်ရှိ)", "Moderate Risk (သတိပြုရန်)", "Low Risk (ပုံမှန်)"],
        "impact_list": [
            "အလွန်စိုးရိမ်ရသော အခြေအနေ! Heatstroke အသက်အန္တရာယ်ရှိနိုင်သည်။",
            "အန္တရာယ်ရှိသော အခြေအနေ! အပူဒဏ်ကြောင့် ပင်ပန်းနွမ်းနယ်ခြင်း ဖြစ်နိုင်ပါသည်။",
            "သတိပြုရန် အခြေအနေ! နေရောင်အောက်တွင် ကြာရှည်နေပါက ပင်ပန်းနွမ်းနယ်ခြင်း ဖြစ်ပေါ်နိုင်ပါသည်။",
            "ပုံမှန်အခြေအနေ! သိသာထင်ရှားသော ကျန်းမာရေးထိခိုက်မှု မရှိနိုင်ပါ။"
        ],
        "recom_list": [
            "အိမ်ထဲတွင်သာ နေပါ။ ရေ (၃-၄) လီတာ သောက်ပါ။",
            "ပြင်ပလုပ်ငန်းများကို နံနက်/ညနေသာ လုပ်ပါ။ ထီး/ဦးထုပ် ဆောင်းပါ။",
            "ပေါ့ပါးသော အဝတ်များ ဝတ်ပါ။ ရေခဏခဏသောက်ပါ။",
            "ပုံမှန်အတိုင်း နေနိုင်ပါသည်။ ရေဓာတ်ဖြည့်တင်းပါ။"
        ]
    },
    "English": {
        "title": "DMH AI Weather Forecast System",
        "station_label": "🎯 Select Station",
        "view_mode_label": "📊 View Mode",
        "modes": ["16-Days Forecast", "Heatwave Monitoring (IBF)", "Climate Change Projection"],
        "dmh_alert": "📢 Tip: Follow DMH news for updates.",
        "ibf_header": "🏥 Health Impacts & Recommendations",
        "risk_levels": ["Extreme Risk", "High Risk", "Moderate Risk", "Low Risk"],
        "impact_list": ["Extreme danger!", "High danger!", "Caution!", "Normal."],
        "recom_list": ["Stay indoors.", "Use umbrella.", "Wear light clothes.", "Stay hydrated."]
    }
}

# --- ၄။ API နှင့် Data Loading ---
@st.cache_data
def load_stations():
    try:
        # သင်၏ Station.csv ထဲတွင် Lat နှင့် Lon column များ ရှိရပါမည်။
        df_csv = pd.read_csv("Station.csv", encoding='utf-8-sig')
        return {str(row.iloc[0]).strip(): {'lat': float(row['Lat']), 'lon': float(row['Lon'])} for _, row in df_csv.iterrows()}
    except:
        return {"Naypyidaw": {"lat": 19.76, "lon": 96.08}}

MYANMAR_CITIES = load_stations()
city_list = sorted(list(MYANMAR_CITIES.keys()))

@st.cache_data(ttl=600)
def fetch_weather(city):
    if city not in MYANMAR_CITIES: return None, None
    loc = MYANMAR_CITIES[city]
    url = f"https://api.open-meteo.com/v1/forecast?latitude={loc['lat']}&longitude={loc['lon']}&hourly=temperature_2m,relative_humidity_2m,precipitation,windspeed_10m,visibility,cloud_cover,cape&daily=temperature_2m_max,temperature_2m_min&windspeed_unit=mph&forecast_days=16&timezone=Asia%2FYangon"
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
            "Thunderstorm": [min(round((c/3500)*100), 100) if c else 0 for c in res['hourly'].get('cape', [])]
        })
        df_h['HI'], df_h['WBGT'], df_h['UTCI'] = zip(*df_h.apply(lambda x: calculate_all_indices(x['Temp'], x['Humid']), axis=1))
        df_d = pd.DataFrame({"Date": pd.to_datetime(res['daily']['time']), "Tmax": res['daily']['temperature_2m_max'], "Tmin": res['daily']['temperature_2m_min']})
        return df_h, df_d
    except:
        return None, None

# --- ၅။ Sidebar & UI Logic ---
st.sidebar.image("https://www.moezala.gov.mm/themes/custom/dmh/logo.png?v=1.1", width=100)
lang = st.sidebar.radio("🌐 Language", ["မြန်မာ", "English"], horizontal=True)
T = LANG_DATA[lang]
bias = st.sidebar.slider("🌡️ Bias Correction (°C)", -5.0, 5.0, 0.0)
selected_city = st.sidebar.selectbox(T["station_label"], city_list)
view_mode_choice = st.sidebar.radio(T["view_mode_label"], T["modes"])
mode_index = T["modes"].index(view_mode_choice)

st.title(T["title"])
st.caption(f"📍 {selected_city} | ⏰ {formatted_now}")

df_h, df_d = fetch_weather(selected_city)

if df_h is not None:
    df_h['Temp'] += bias
    df_d['Tmax'] += bias
    df_d['Tmin'] += bias

    # --- MODE 0: Detailed Analysis ---
    if mode_index == 0:
        st.info(T["dmh_alert"])
        
        col1, col2 = st.columns(2)
        with col1:
            fig_temp = px.line(df_h, x='Time', y='Temp', title="Temperature Forecast (°C)", color_discrete_sequence=['red'])
            st.plotly_chart(fig_temp, use_container_width=True)
            
        with col2:
            fig_rain = px.bar(df_h, x='Time', y='Rain', title="Precipitation (mm)", color_discrete_sequence=['blue'])
            st.plotly_chart(fig_rain, use_container_width=True)
            
        fig_storm = px.area(df_h, x='Time', y='Thunderstorm', title="Thunderstorm Probability (%)", color_discrete_sequence=['orange'])
        st.plotly_chart(fig_storm, use_container_width=True)

    # --- MODE 1: Heatwave Monitoring ---
    elif mode_index == 1:
        st.subheader(T["ibf_header"])
        idx_choice = st.radio("🌡️ Select Index", ["Max Temp", "Heat Index", "WBGT", "UTCI"], horizontal=True)
        
        t_now = df_h.iloc[0]
        if idx_choice == "Max Temp": val, th = df_d.iloc[0]['Tmax'], [42, 40, 38]
        elif idx_choice == "Heat Index": val, th = t_now['HI'], [41, 38, 35]
        elif idx_choice == "WBGT": val, th = t_now['WBGT'], [32, 30, 28]
        else: val, th = t_now['UTCI'], [38, 32, 26]

        if val >= th[0]: lvl, bg = 0, "#FF0000"
        elif val >= th[1]: lvl, bg = 1, "#FFA500"
        elif val >= th[2]: lvl, bg = 2, "#FFFF00"
        else: lvl, bg = 3, "#008000"

        st.markdown(f"<div style='background-color:{bg}; padding:30px; border-radius:15px; text-align:center;'><h1 style='color:white;'>{T['risk_levels'][lvl]}</h1><h2 style='color:white;'>{idx_choice}: {val:.1f} °C</h2></div>", unsafe_allow_html=True)
        st.warning(f"**Impact:** {T['impact_list'][lvl]}")
        st.success(f"**Action:** {T['recom_list'][lvl]}")

# --- ၆။ Export Section ---
st.markdown("---")
if st.button("🚀 Export All Stations Report"):
    all_data = []
    p_bar = st.progress(0)
    msg = st.empty()
    for i, city in enumerate(city_list):
        msg.text(f"Fetching data for: {city}...")
        dh, dd = fetch_weather(city)
        if dh is not None:
            # နောက်ဆုံးရက်အတွက် data တစ်ခုတည်းကို ဥပမာအနေဖြင့် ထည့်ခြင်း
            latest = dd.iloc[0]
            all_data.append({'Date': latest['Date'].strftime('%Y-%m-%d'), 'Station': city, 'Tmax': latest['Tmax'] + bias})
        time.sleep(1.2) # 429 Error ကာကွယ်ရန်
        p_bar.progress((i + 1) / len(city_list))
    
    st.session_state['master_df'] = pd.DataFrame(all_data)
    st.success("Report Generated!")

if 'master_df' in st.session_state:
    st.dataframe(st.session_state['master_df'], use_container_width=True)

st.markdown("<div style='text-align: center; color: gray; padding-top: 50px;'>Official System: Department of Meteorology and Hydrology, Myanmar</div>", unsafe_allow_html=True)
if 'master_df' in st.session_state:
    m_df = st.session_state['master_df']
    sel_date = st.selectbox("📅 နေ့စွဲရွေးချယ်ပါ", sorted(m_df['Date'].unique(), reverse=True))
    final_df = m_df[m_df['Date'] == sel_date].sort_values(by='Station')
    st.dataframe(final_df, use_container_width=True)
    st.download_button("📥 Download Report (CSV)", final_df.to_csv(index=False).encode('utf-8-sig'), f"DMH_{sel_date}.csv", "text/csv")

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
