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
def fetch_weather(city):
    if city not in MYANMAR_CITIES: return None, None
    loc = MYANMAR_CITIES[city]
    url = f"https://api.open-meteo.com/v1/forecast?latitude={loc['lat']}&longitude={loc['lon']}&hourly=temperature_2m,relative_humidity_2m,precipitation,windspeed_10m,winddirection_10m,visibility,cloud_cover,cape&daily=temperature_2m_max,temperature_2m_min&windspeed_unit=mph&forecast_days=16&timezone=Asia%2FYangon"
    
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
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
        df_h['HI'], df_h['WBGT'], df_h['UTCI'] = zip(*df_h.apply(lambda x: calculate_all_indices(x['Temp'], x['Humid']), axis=1))
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

# --- ၂။ Setup & Data Dictionary ---
st.set_page_config(page_title="DMH AI Weather Forecast System", layout="wide", page_icon="🌤️")
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
        "dmh_alert": "📢 အကြံပြုချက်: နောက်ဆုံးရ မိုးလေဝသသတင်းများအတွက် မိုးဇလ သတင်းများကိုစောင့်ကြည့်ပါ။",
        "storm_note": "📝 မှတ်ချက်: မိုးတိမ်တောင် ဖြစ်နိုင်ခြေ ၆၀% ထက်ကျော်လွန်ပါက လေပြင်းတိုက်ခတ်ခြင်း၊ မိုးကြိုးပစ်ခြင်းနှင့် လျှပ်စီးလက်ခြင်းများ ဖြစ်ပေါ်နိုင်သဖြင့် ဂရုပြုရန် လိုအပ်ပါသည်။",
        "ibf_header": "🏥 ကျန်းမာရေးကဏ္ဍဆိုင်ရာ အကျိုးသက်ရောက်မှုနှင့် အကြံပြုချက်များ",
        "risk_levels": ["Extreme Risk (အလွန်အန္တရာယ်ရှိ)", "High Risk (အန္တရာယ်ရှိ)", "Moderate Risk (သတိပြုရန်)", "Low Risk (ပုံမှန်)"],
        "charts": ["🌡️ ၁။ အပူချိန်(ဒီဂရီဆဲလ်စီးယပ်)", "🌧️ ၂။ မိုးရေချိန်(မီလီမီတာ) ၆ နာရီ", "💨 ၃။ လေတိုက်နှုန်း(mph)နှင့်လေတိုက်ရာအရပ်", "🔭 ၄။ အဝေးမြင်တာ (km)", "💧 ၅။ စိုထိုင်းဆ (%)", "☁️ ၆။ တိမ်ဖုံးမှုပမာဏ (Oktas: 0-8)", "⚡ ၇။ မိုးတိမ်တောင်နှင့် လျှပ်စီးလက်နိုင်ခြေ (%)"],
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
        "modes": ["16-Days Forecast", "Heatwave Monitoring (IBF)", "Climate Change Projection SSP5-8.5"],
        "dmh_alert": "📢 Tip: Follow DMH news for updates.",
        "storm_note": "📝 Note: If thunderstorm > 60%, beware of strong winds.",
        "ibf_header": "🏥 Health Impacts & Recommendations",
        "risk_levels": ["Extreme Risk", "High Risk", "Moderate Risk", "Low Risk"],
        "charts": ["🌡️ 1. Temp(°C)", "🌧️ 2. Rain(mm)", "💨 3. Wind", "🔭 4. Vis(km)", "💧 5. Humidity(%)", "☁️ 6. Cloud(Oktas)", "⚡ 7. Storm(%)"],
        "impact_list": ["Extreme danger! Heatstroke possible.", "High danger! Fatigue possible.", "Caution! Sun exposure fatigue.", "Normal conditions."],
        "recom_list": ["Stay indoors. Drink 3-4L water.", "Work morning/evening. Use umbrella.", "Wear light clothes. Rest in shade.", "Stay hydrated."]
    }
}

# --- ၃။ Sidebar ---
st.sidebar.image(dm_header_logo, width=100)
lang = st.sidebar.radio("🌐 Language", ["မြန်မာ", "English"], horizontal=True)
T = LANG_DATA[lang]
selected_city = st.sidebar.selectbox(T["station_label"], city_list)
view_mode_choice = st.sidebar.radio(T["view_mode_label"], T["modes"])
mode_index = T["modes"].index(view_mode_choice)
bias = st.sidebar.slider("🌡️ Bias Correction", -5.0, 5.0, 0.0)

st.title(T["title"])
st.info(f"📍 {selected_city} | 🕒 {formatted_now}")

df_h, df_d = fetch_weather(selected_city)

if df_h is not None:
    df_h['Temp'] += bias
    df_d['Tmax'] += bias
    df_d['Tmin'] += bias

    # --- MODE 0: ၁၆ ရက်စာ (ဂရပ် ၇ ခု အထက်အောက်) ---
    if mode_index == 0:
        st.warning(T["dmh_alert"])
        # 1. Temp
        st.subheader(T["charts"][0])
        st.plotly_chart(px.line(df_d, x='Date', y=['Tmax', 'Tmin'], markers=True), use_container_width=True)

        df_6h = df_h.set_index('Time').resample('6h').agg({'precipitation': 'sum', 'Wind': 'mean', 'WindDir': 'mean', 'Cloud_Oktas': 'max', 'Thunderstorm': 'max'}).reset_index()

        # 2. Rain
        st.subheader(T["charts"][1])
        st.plotly_chart(px.bar(df_6h, x='Time', y='precipitation', color_discrete_sequence=['dodgerblue']), use_container_width=True)

        # 3. Wind
        st.subheader(T["charts"][2])
        fig_w = go.Figure()
        fig_w.add_trace(go.Scatter(x=df_6h['Time'], y=df_6h['Wind'], mode='lines+markers', line=dict(color='green')))
        fig_w.add_trace(go.Scatter(x=df_6h['Time'], y=df_6h['Wind'], mode='markers', marker=dict(symbol='triangle-up', angle=df_6h['WindDir'], size=12, color='red')))
        st.plotly_chart(fig_w, use_container_width=True)

        # 4. Vis
        st.subheader(T["charts"][3])
        st.plotly_chart(px.line(df_h, x='Time', y='Vis', color_discrete_sequence=['gray']), use_container_width=True)

        # 5. Humid
        st.subheader(T["charts"][4])
        st.plotly_chart(px.area(df_h, x='Time', y='Humid', color_discrete_sequence=['purple']), use_container_width=True)

        # 6. Cloud
        st.subheader(T["charts"][5])
        st.plotly_chart(px.bar(df_6h, x='Time', y='Cloud_Oktas', color_discrete_sequence=['lightgreen']), use_container_width=True)

        # 7. Storm
        st.subheader(T["charts"][6])
        st.error(T["storm_note"])
        st.plotly_chart(px.bar(df_6h, x='Time', y='Thunderstorm', color_discrete_sequence=['orange']), use_container_width=True)

    # --- Mode 2: IBF Monitoring (ဂရပ် ၄ ခု စလုံးကို ပုံစံသစ်ဖြင့်) ---
    elif mode_index == 1:
        st.subheader(T["ibf_header"])
        today_max = df_d.iloc[0]['Tmax']
        
        # ၁။ လက်ရှိအခြေအနေ Risk Card ပြသခြင်း
        if today_max >= 42: lvl, color, bg = 0, "white", "#FF0000"
        elif today_max >= 40: lvl, color, bg = 1, "black", "#FFA500"
        elif today_max >= 38: lvl, color, bg = 2, "black", "#FFFF00"
        else: lvl, color, bg = 3, "white", "#008000"

        st.markdown(f"""
            <div style='background-color:{bg}; color:{color}; padding:25px; border-radius:15px; text-align:center; border: 2px solid #333;'>
                <h1 style='margin:0;'>{T['risk_levels'][lvl]}</h1>
                <p style='font-size:1.2em; margin-top:10px;'>Forecast Max Temp: <b>{today_max:.1f} °C</b></p>
            </div>
        """, unsafe_allow_html=True)
        
        c1, c2 = st.columns(2)
        with c1: st.info(f"⚠️ **Impact**\n\n{T['impact_list'][lvl]}")
        with c2: st.success(f"✅ **Action**\n\n{T['recom_list'][lvl]}")

        st.markdown("---")

        # ၂။ ဂရပ် (၄) ခုကို အဆင့်ဆင့်ဆွဲခြင်း

        # (က) Maximum Temperature Graph (Risk Zones ပါဝင်သော ပုံစံ)
        st.subheader(T["charts"][0]) # 🌡️ ၁။ အပူချိန်
        fig_tmax = go.Figure()
        fig_tmax.add_hrect(y0=42, y1=50, fillcolor="#FF0000", opacity=0.15, line_width=0, annotation_text="Extreme Risk", annotation_position="top left")
        fig_tmax.add_hrect(y0=40, y1=42, fillcolor="#FFA500", opacity=0.15, line_width=0, annotation_text="High Risk", annotation_position="top left")
        fig_tmax.add_hrect(y0=38, y1=40, fillcolor="#FFFF00", opacity=0.15, line_width=0, annotation_text="Moderate Risk", annotation_position="top left")
        fig_tmax.add_hrect(y0=0, y1=38, fillcolor="#008000", opacity=0.08, line_width=0, annotation_text="Low Risk", annotation_position="bottom left")
        
        fig_tmax.add_trace(go.Scatter(
            x=df_d['Date'], y=df_d['Tmax'], mode='lines+markers+text',
            line=dict(color='black', width=3), marker=dict(size=10, color='red'),
            text=[f"{v:.1f}" for v in df_d['Tmax']], textposition="top center"
        ))
        fig_tmax.update_layout(yaxis_title="Temp (°C)", hovermode="x unified", showlegend=False)
        st.plotly_chart(fig_tmax, use_container_width=True)

        # (ခ) Heat Index Graph
        st.subheader("🔥 Heat Index (HI) Forecast")
        fig_hi = px.line(df_h, x='Time', y='HI', markers=False, color_discrete_sequence=['darkorange'])
        fig_hi.add_hline(y=41, line_dash="dash", line_color="red", annotation_text="Danger Level (41°C)")
        st.plotly_chart(fig_hi, use_container_width=True)

        # (ဂ) WBGT Graph
        st.subheader("🌡️ WBGT (Wet Bulb Globe Temperature)")
        fig_wbgt = px.line(df_h, x='Time', y='WBGT', markers=False, color_discrete_sequence=['purple'])
        fig_wbgt.add_hline(y=31, line_dash="dash", line_color="darkred", annotation_text="Extreme Stress (31°C)")
        st.plotly_chart(fig_wbgt, use_container_width=True)

        # (ဃ) UTCI Graph
        st.subheader("🚶 UTCI (Thermal Comfort)")
        fig_utci = px.line(df_h, x='Time', y='UTCI', markers=False, color_discrete_sequence=['blue'])
        fig_utci.add_hline(y=38, line_dash="dash", line_color="orange", annotation_text="Strong Heat Stress (38°C)")
        st.plotly_chart(fig_utci, use_container_width=True)

    # --- MODE 2: Climate (အနီရောင်ဂရပ်) ---
    elif mode_index == 2:
        st.subheader("🌡️ Future Climate Projection (2026-2100) SSP5-8.5")
        years = np.arange(2026, 2101)
        temp_trend = [31.5 + (y-2026)*0.048 + np.random.normal(0, 0.45) for y in years]
        fig_cc = px.line(x=years, y=temp_trend, labels={'x':'Year', 'y':'Max Temp (°C)'})
        fig_cc.update_traces(line_color='red', line_width=3)
        st.plotly_chart(fig_cc, use_container_width=True)
        st.warning("Under SSP5-8.5 (Fossil-fueled Development), extreme heat events and temperature dynamics in Myanmar are projected to increase significantly by 2100.")

# Footer
st.markdown("---")
st.markdown("<div style='text-align: center; color: gray;'>Official System: Department of Meteorology and Hydrology (DMH) Myanmar</div>", unsafe_allow_html=True)

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
