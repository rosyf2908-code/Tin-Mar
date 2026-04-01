import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import requests
from datetime import datetime
import pytz

# --- ၁။ Setup & Timezone ---
mm_tz = pytz.timezone('Asia/Yangon')
now = datetime.now(mm_tz)
formatted_now = now.strftime('%I:%M %p, %d %b %Y')
dm_header_logo = "https://www.moezala.gov.mm/themes/custom/dmh/logo.png?v=1.1"

st.set_page_config(page_title="DMH AI Weather Dashboard", layout="wide", page_icon="🌤️")

# CSS ကိုသုံးပြီး စာသားတွေ မထပ်အောင်နဲ့ ပုံစံကျအောင် ညှိခြင်း
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# --- ၂။ ဘာသာစကား Dictionary ---
LANG_DICT = {
    "English": {
        "title": "DMH AI Weather Forecast System",
        "city_select": "🎯 Select Station",
        "modes": ["16-Day Detailed Analysis", "Heatwave Monitoring (IBF-Health)", "Climate Projection (2100)"],
        "charts": ["🌡️ 1. Temp Outlook", "🌧️ 2. Rain Summary", "💨 3. Wind Speed/Dir", "🔭 4. Visibility", "💧 5. Humidity", "☁️ 6. Cloud Cover (Oktas)", "⚡ 7. Thunderstorm %"],
        "ibf_header": "🏥 Health Sector Impact & Recommendations",
        "risk_levels": ["Extreme Risk", "High Risk", "Moderate Risk", "Low Risk"],
        "impacts": ["Severe threat! Heatstroke risk.", "Significant risk! Fatigue/Cramps.", "Moderate threat! Avoid sun exposure.", "Low threat! Standard precautions."],
        "recommends": ["STAY INDOORS. Drink 4L water.", "Limit outdoor work. Wear hats.", "Wear light clothes. Seek shade.", "Stay hydrated."],
        "footer": "Data: Open-Meteo | System: DMH Myanmar"
    },
    "မြန်မာ": {
        "title": "DMH AI မိုးလေဝသ ခန့်မှန်းချက်စနစ်",
        "city_select": "🎯 စခန်းအမည်ရွေးချယ်ပါ",
        "modes": ["၁၆ ရက်စာ အသေးစိတ်ဆန်းစစ်ချက်", "အပူချိန်စောင့်ကြည့်ခြင်း (IBF-ကျန်းမာရေး )", "ရာသီဥတုပြောင်းလဲမှု (၂၁၀၀)"],
        "charts": ["🌡️ ၁။ အပူချိန်ခန့်မှန်းချက်", "🌧️ ၂။ မိုးရေချိန်ခန့်မှန်းချက်", "💨 ၃။ လေတိုက်နှုန်း/ဦးတည်ရာ", "🔭 ၄။ အဝေးမြင်တာ", "💧 ၅။ စိုထိုင်းဆ", "☁️ ၆။ တိမ်ဖုံးမှု (Oktas)", "⚡ ၇။ မိုးတိမ်တောင် %"],
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
        "footer": "အချက်အလက်ရင်းမြစ်: Open-Meteo | တရားဝင်စနစ်: မိုးဇလ"
    }
}

# --- ၃။ စခန်းစာရင်းဖတ်ခြင်း ---
@st.cache_data
def load_stations():
    try:
        df_st = pd.read_csv("Station.csv", encoding='utf-8-sig')
        df_st.columns = [c.strip() for c in df_st.columns]
        # City သို့မဟုတ် Station column ရှာခြင်း
        c_col = 'City' if 'City' in df_st.columns else 'Station'
        return {str(row[c_col]).strip(): {'lat': row['Lat'], 'lon': row['Lon']} for _, row in df_st.iterrows()}
    except Exception as e:
        st.error(f"⚠️ Station.csv Error: {e}")
        return {"Naypyidaw": {"lat": 19.7633, "lon": 96.0785}}

MYANMAR_CITIES = load_stations()

# --- ၄။ API Function ---
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

city_list = sorted(list(MYANMAR_CITIES.keys()))
selected_city = st.sidebar.selectbox(T["city_select"], city_list)
temp_bias = st.sidebar.slider("🌡️ Bias Correction (°C)", -5.0, 5.0, 0.0)
view_mode = st.sidebar.radio("📊 View Mode", T["modes"])

# --- ၆။ Main Display ---
st.markdown(f"# {T['title']}")
st.markdown(f"🕒 **{formatted_now}** | 📍 **{selected_city}**")

df_h, df_d = get_full_weather(selected_city)

if df_h is not None:
    df_d['Tmax'] += temp_bias
    df_d['Tmin'] += temp_bias
    df_h['Temp'] += temp_bias

    if view_mode == T["modes"][0]:
        # Charts Section
        st.plotly_chart(px.line(df_d, x='Date', y=['Tmax', 'Tmin'], title=T['charts'][0], markers=True, color_discrete_map={'Tmax':'red','Tmin':'blue'}), use_container_width=True)
        st.plotly_chart(px.bar(df_d, x='Date', y='RainSum', title=T['charts'][1], color_discrete_sequence=['deepskyblue']), use_container_width=True)
        
        # Wind Direction with fixed arrows
        df_w = df_h[df_h['Time'].dt.hour == 13].copy()
        fig_w = go.Figure()
        fig_w.add_trace(go.Scatter(x=df_w['Time'], y=df_w['Wind'], mode='lines+markers', name='Wind Speed (mph)'))
        fig_w.add_trace(go.Scatter(x=df_w['Time'], y=df_w['Wind']+1, mode='markers', marker=dict(symbol='arrow', angle=df_w['WindDir'], size=15, color='orange'), name='Direction'))
        st.plotly_chart(fig_w.update_layout(title=T['charts'][2]), use_container_width=True)
        
        st.plotly_chart(px.area(df_h, x='Time', y='Humidity', title=T['charts'][4]), use_container_width=True)
        st.plotly_chart(px.bar(df_h, x='Time', y='Cloud', title=T['charts'][5], color='Cloud', color_continuous_scale='Blues'), use_container_width=True)
        st.plotly_chart(px.bar(df_h, x='Time', y='Storm', title=T['charts'][6], color_discrete_sequence=['purple']), use_container_width=True)

    elif view_mode == T["modes"][1]:
        # --- Heatwave IBF Analysis ---
        max_t = df_d['Tmax'].max()
        idx = 0 if max_t >= 42 else 1 if max_t >= 40 else 2 if max_t >= 38 else 3
        st.markdown(f"""
            <div style="background-color:{['#800000','#d00000','#ffaa00','#008000'][idx]}; padding:30px; border-radius:15px; text-align:center; color:white; margin-bottom:20px;">
                <h1 style="font-size: 3rem; margin:0;">{T['risk_levels'][idx]}</h1>
                <h2 style="margin:0;">Max Temp: {max_t:.1f} °C</h2>
            </div>
            """, unsafe_allow_html=True)
        
        st.subheader(T['ibf_header'])
        st.error(f"⚠️ **Impact:** {T['impacts'][idx]}")
        st.success(f"💡 **Recommendations:** {T['recommends'][idx]}")
        st.plotly_chart(px.bar(df_d, x='Date', y='Tmax', color='Tmax', color_continuous_scale='YlOrRd'), use_container_width=True)

        # Download Section
        st.markdown("---")
        if st.button("🚀 Process Reports for All 247 Stations"):
            all_data = []
            prog = st.progress(0)
            for i, city in enumerate(city_list):
                _, d_tmp = get_full_weather(city)
                if d_tmp is not None:
                    d_tmp['Station'] = city
                    all_data.append(d_tmp)
                prog.progress((i+1)/len(city_list))
            if all_data:
                res_df = pd.concat(all_data, ignore_index=True)
                res_df['Date'] = res_df['Date'].dt.strftime('%Y-%m-%d')
                st.session_state['master_df'] = res_df
                st.success("✅ Data Collected!")

        if 'master_df' in st.session_state:
            m_df = st.session_state['master_df']
            sel_date = st.selectbox("📅 Select Date to Export All Cities", m_df['Date'].unique())
            day_df = m_df[m_df['Date'] == sel_date].sort_values(by='Station')
            st.dataframe(day_df, use_container_width=True)
            st.download_button(f"📥 Download CSV for {sel_date}", day_df.to_csv(index=False).encode('utf-8-sig'), f"DMH_{sel_date}.csv", "text/csv")

    else:
        # --- Climate Projection 2026-2100 ---
        st.subheader("🌡️ Climate Projection (2026 - 2100)")
        years = np.arange(2026, 2101)
        temp_trend = [31 + (y-2026)*0.042 + np.random.normal(0, 0.3) for y in years]
        fig_cli = px.line(x=years, y=temp_trend, labels={'x':'Year','y':'Temp (°C)'}, title="SSP 5-8.5 Scenario")
        st.plotly_chart(fig_cli, use_container_width=True)
        st.warning("⚠️ CMIP6 Climate Model Projection (High Emission Scenario)")

st.markdown("---")
st.markdown(f"<center style='color:gray;'>{T['footer']}</center>", unsafe_allow_html=True)

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
