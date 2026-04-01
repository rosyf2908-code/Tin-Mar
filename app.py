import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import requests
from datetime import datetime
import pytz
import time

# --- ၁။ Setup & Timezone ---
mm_tz = pytz.timezone('Asia/Yangon')
now = datetime.now(mm_tz)
formatted_now = now.strftime('%I:%M %p, %d %b %Y')

dm_header_logo = "https://www.moezala.gov.mm/themes/custom/dmh/logo.png?v=1.1"

st.set_page_config(page_title="DMH AI Weather Dashboard", layout="wide", page_icon="🌤️")

# --- ၂။ ဘာသာစကား Dictionary ---
LANG_DICT = {
    "English": {
        "title": "DMH AI Weather Forecast System",
        "time_label": "Current Local Time (MMT)",
        "city_select": "🎯 Select Station/City",
        "view_mode": "📊 View Mode",
        "modes": ["16-Day Detailed Analysis", "Heatwave Monitoring (IBF-Health)", "Climate Projection (2100)"],
        "charts": ["🌡️ 1. Temp Outlook", "🌧️ 2. Rain Summary", "💨 3. Wind Speed/Dir", "🔭 4. Visibility", "💧 5. Humidity", "☁️ 6. Cloud Cover", "⚡ 7. Thunderstorm %"],
        "dmh_alert": "📢 Recommendations: Please monitor DMH official news regularly.",
        "storm_note": "📝 Note: If Thunderstorm Potential > 60%, please beware of strong winds, thunder, and lightning.",
        "ibf_header": "🏥 Health Sector Impact & Recommendations",
        "risk_levels": ["Extreme Risk", "High Risk", "Moderate Risk", "Low Risk"],
        "impacts": ["Severe threat! Heatstroke risk.", "Significant risk! Fatigue/Cramps.", "Moderate threat! Avoid sun exposure.", "Low threat! Standard precautions."],
        "recommends": ["STAY INDOORS. Drink 4L water.", "Limit outdoor work. Wear hats.", "Wear light clothes. Seek shade.", "Stay hydrated."],
        "footer": "Data: Open-Meteo | System: Department of Meteorology and Hydrology"
    },
    "မြန်မာ": {
        "title": "DMH AI မိုးလေဝသ ခန့်မှန်းချက်စနစ်",
        "time_label": "လက်ရှိ မြန်မာစံတော်ချိန်",
        "city_select": "🎯 စခန်း/မြို့အမည်ရွေးချယ်ပါ",
        "view_mode": "📊 ကြည့်ရှုမည့်ပုံစံ",
        "modes": ["၁၆ ရက်စာ အသေးစိတ်ဆန်းစစ်ချက်", "အပူချိန်စောင့်ကြည့်ခြင်း (IBF-ကျန်းမာရေး )", "ရာသီဥတုပြောင်းလဲမှု (၂၁၀၀)"],
        "charts": ["🌡️ ၁။ အပူချိန်ခန့်မှန်းချက်", "🌧️ ၂။ မိုးရေချိန်ခန့်မှန်းချက်", "💨 ၃။ လေတိုက်နှုန်း/ဦးတည်ရာ", "🔭 ၄။ အဝေးမြင်တာ", "💧 ၅။ စိုထိုင်းဆ", "☁️ ၆။ တိမ်ဖုံးမှု", "⚡ ၇။ မိုးတိမ်တောင် %"],
        "dmh_alert": "📢 အကြံပြုချက်: နောက်ဆုံးရ မိုးလေဝသသတင်းများအတွက် မိုးဇလ သတင်းများကိုစောင့်ကြည့်ပါ။",
        "storm_note": "📝 မှတ်ချက်: မိုးတိမ်တောင် ဖြစ်နိုင်ခြေ ၆၀% ကျော်ပါက လေပြင်းနှင့် မိုးကြိုးအန္တရာယ် သတိပြုပါ။",
        "ibf_header": "🏥 ကျန်းမာရေးကဏ္ဍဆိုင်ရာ အကျိုးသက်ရောက်မှုနှင့် အကြံပြုချက်များ",
        "risk_levels": ["အလွန်အန္တရာယ်ရှိ", "အန္တရာယ်ရှိ", "သတိပြုရန်", "ပုံမှန်"],
        "impacts": [
            "အလွန်စိုးရိမ်ရသော အခြေအနေ! Heatstroke နှင့် ရေဓာတ်ကုန်ခမ်းခြင်းကြောင့် အသက်အန္တရာယ်ရှိနိုင်သည်။",
            "အန္တရာယ်ရှိသော အခြေအနေ! အပူဒဏ်ကြောင့် ပင်ပန်းနွမ်းနယ်ခြင်း ဖြစ်နိုင်ပါသည်။ ကလေးနှင့် လူအိုများ သတိပြုပါ။",
            "သတိပြုရန် အခြေအနေ! နေရောင်အောက်တွင် ကြာရှည်နေပါက ပင်ပန်းနွမ်းနယ်ခြင်း ဖြစ်ပေါ်နိုင်သည်။",
            "ပုံမှန်အခြေအနေ! သိသာထင်ရှားသော ကျန်းမာရေးထိခိုက်မှု မရှိနိုင်ပါ။"
        ],
        "recommends": [
            "အိမ်ထဲတွင်သာနေပါ။ ရေ ၄ လီတာသောက်ပါ။ မူးဝေပါက ဆေးရုံအမြန်သွားပါ။",
            "ပြင်ပလုပ်ငန်းများကို နံနက်/ညနေသာလုပ်ပါ။ ထီး/ဦးထုပ် ဆောင်းပါ။",
            "ပေါ့ပါးသော အဝတ်များဝတ်ပါ။ ရေခဏခဏသောက်ပါ။ အရိပ်တွင်နားပါ။",
            "ပုံမှန်အတိုင်းနေနိုင်ပါသည်။ ရေဓာတ်ဖြည့်တင်းပါ။"
        ],
        "footer": "အချက်အလက်ရင်းမြစ်: Open-Meteo | တရားဝင်စနစ်: မိုးလေဝသနှင့်ဇလဗေဒညွှန်ကြားမှုဦးစီးဌာန"
    }
}

# --- ၃။ စခန်းစာရင်းကို CSV မှ ဖတ်ခြင်း ---
@st.cache_data
def load_stations():
    try:
        df_st = pd.read_csv("Station.csv")
        return {row['Station']: {'lat': row['Lat'], 'lon': row['Lon']} for _, row in df_st.iterrows()}
    except Exception as e:
        st.error(f"Error loading Station.csv: {e}")
        return {"Naypyidaw": {"lat": 19.7633, "lon": 96.0785}}

MYANMAR_CITIES = load_stations()

# --- ၄။ API Function (Robust Logic) ---
@st.cache_data(ttl=600)
def get_full_weather(city):
    if city not in MYANMAR_CITIES: return None, None
    lat, lon = MYANMAR_CITIES[city]['lat'], MYANMAR_CITIES[city]['lon']
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=temperature_2m,relative_humidity_2m,cloud_cover,visibility,precipitation,windspeed_10m,winddirection_10m,cape&daily=temperature_2m_max,temperature_2m_min,precipitation_sum&windspeed_unit=mph&forecast_days=16&timezone=Asia%2FYangon"
    try:
        r = requests.get(url, timeout=15).json()
        h, d = r['hourly'], r['daily']
        df_h = pd.DataFrame({
            "Time": pd.to_datetime(h['time']), "Temp": h['temperature_2m'],
            "Visibility": [v/1000 if v is not None else 0 for v in h['visibility']],
            "Humidity": h['relative_humidity_2m'],
            "Cloud": [round((c/100)*8) if c is not None else 0 for c in h['cloud_cover']],
            "Wind": h['windspeed_10m'], "WindDir": h['winddirection_10m'],
            "Storm": [min(round((c/3500)*100), 100) if c is not None else 0 for c in h['cape']]
        })
        df_d = pd.DataFrame({
            "Date": pd.to_datetime(d['time']), "Tmax": d['temperature_2m_max'],
            "Tmin": d['temperature_2m_min'], "RainSum": d['precipitation_sum']
        })
        return df_h, df_d
    except: return None, None

# --- ၅။ Sidebar ---
st.sidebar.image(dm_header_logo, width=120)
lang = st.sidebar.selectbox("🌐 Language", ["မြန်မာ", "English"])
T = LANG_DICT[lang]

selected_city = st.sidebar.selectbox(T["city_select"], sorted(list(MYANMAR_CITIES.keys())))
temp_bias = st.sidebar.slider("🌡️ Bias Correction (°C)", -5.0, 5.0, 0.0, step=0.5)
view_mode = st.sidebar.radio(T["view_mode"], T["modes"])

# --- ၆။ Main Display ---
st.markdown(f"# {T['title']}")
st.markdown(f"🕒 **{T['time_label']}:** `{formatted_now}` | 📍 **Station:** `{selected_city}`")
st.info(T["dmh_alert"])

df_h, df_d = get_full_weather(selected_city)

if df_h is not None:
    df_d['Tmax'] += temp_bias
    df_d['Tmin'] += temp_bias
    df_h['Temp'] += temp_bias

    if view_mode == T["modes"][0]:
        # --- Metrics ---
        m1, m2, m3 = st.columns(3)
        m1.metric("Max Temp Today", f"{df_d['Tmax'].iloc[0]:.1f} °C")
        m2.metric("Min Temp Today", f"{df_d['Tmin'].iloc[0]:.1f} °C")
        m3.metric("Rainfall Today", f"{df_d['RainSum'].iloc[0]:.1f} mm")

        st.plotly_chart(px.line(df_d, x='Date', y=['Tmax', 'Tmin'], title=T['charts'][0], markers=True, color_discrete_map={'Tmax':'red','Tmin':'blue'}), use_container_width=True)
        st.plotly_chart(px.bar(df_d, x='Date', y='RainSum', title=T['charts'][1], color_discrete_sequence=['deepskyblue']), use_container_width=True)
        
        # Wind Direction Arrow Plot
        df_w = df_h[df_h['Time'].dt.hour == 13].copy()
        fig_w = go.Figure()
        fig_w.add_trace(go.Scatter(x=df_w['Time'], y=df_w['Wind'], mode='lines+markers', name='Speed (mph)'))
        fig_w.add_trace(go.Scatter(x=df_w['Time'], y=df_w['Wind']+2, mode='markers', marker=dict(symbol='arrow', angle=df_w['WindDir'], size=15, color='red'), name='Dir'))
        fig_w.update_layout(title=T['charts'][2])
        st.plotly_chart(fig_w, use_container_width=True)
        
        st.plotly_chart(px.area(df_h, x='Time', y='Humidity', title=T['charts'][4]), use_container_width=True)
        st.warning(T["storm_note"])
        st.plotly_chart(px.bar(df_h, x='Time', y='Storm', title=T['charts'][6], color_discrete_sequence=['orange']), use_container_width=True)

    elif view_mode == T["modes"][1]:
        # --- Heatwave IBF Section ---
        max_t = df_d['Tmax'].max()
        idx = 0 if max_t >= 42 else 1 if max_t >= 40 else 2 if max_t >= 38 else 3
        st.markdown(f"<div style='background-color:{['#800000','#d00000','#ffaa00','#008000'][idx]}; padding:30px; border-radius:15px; text-align:center;'><h1 style='color:white;'>{T['risk_levels'][idx]}: {max_t:.1f} °C</h1></div>", unsafe_allow_html=True)
        
        st.subheader(T['ibf_header'])
        st.error(f"⚠️ **Impact:** {T['impacts'][idx]}")
        st.success(f"💡 **Recommendations:** {T['recommends'][idx]}")

        fig_ibf = px.bar(df_d, x='Date', y='Tmax', color='Tmax', color_continuous_scale='YlOrRd')
        fig_ibf.add_hline(y=42, line_dash="dash", line_color="maroon", annotation_text="Extreme (42°C)")
        st.plotly_chart(fig_ibf, use_container_width=True)

        # --- 247 Stations Download Section ---
        st.markdown("---")
        st.subheader(f"🌐 Global Data (Total {len(MYANMAR_CITIES)} Stations)")
        if st.button(f"🚀 Prepare Report for All {len(MYANMAR_CITIES)} Stations"):
            all_list = []
            progress = st.progress(0)
            status = st.empty()
            
            cities = list(MYANMAR_CITIES.keys())
            for i, city in enumerate(cities):
                status.text(f"Fetching: {city} ({i+1}/{len(cities)})")
                _, d_tmp = get_full_weather(city)
                if d_tmp is not None:
                    d_tmp['Station'] = city
                    all_list.append(d_tmp)
                progress.progress((i+1)/len(cities))
            
            if all_list:
                final_all = pd.concat(all_list, ignore_index=True)
                final_all['Date'] = final_all['Date'].dt.strftime('%Y-%m-%d')
                
                # Master CSV
                master_csv = final_all.to_csv(index=False).encode('utf-8-sig')
                st.download_button("📥 Download Master CSV (247 Stations)", master_csv, f"DMH_Full_Forecast_{now.strftime('%Y%m%d')}.csv", "text/csv")
                
                # Date Filter Export
                st.markdown("


# --- ၆။ Data Source Footer ---
st.markdown("---")
st.markdown(f"""
<div style='text-align: center; font-size: 0.85em; color: #666; line-height: 1.6;'>
    <p><b>Forecast Data Source (16-Day):</b> Open-Meteo API (Combining ECMWF IFS, GFS, ICON, and JMA global models).</p>
    <p><b>Heatwave Analysis:</b> Based on Impact-Based Forecasting (IBF) thresholds (P90, P95, P99) and WMO criteria.</p>
    <p><b>Climate Data:</b> IPCC AR6 Assessment Report and CMIP6 Global Climate Models (SSP scenarios).</p>
    <p style='margin-top: 10px; font-weight: bold;'>Official System: Department of Meteorology and Hydrology (DMH) Myanmar</p>
</div>
""", unsafe_allow_html=True)
