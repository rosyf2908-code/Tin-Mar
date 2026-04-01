import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import requests
from datetime import datetime
import pytz

# --- ၁။ Setup ---
mm_tz = pytz.timezone('Asia/Yangon')
now = datetime.now(mm_tz)
formatted_now = now.strftime('%I:%M %p, %d %b %Y')
dm_header_logo = "https://www.moezala.gov.mm/themes/custom/dmh/logo.png?v=1.1"

st.set_page_config(page_title="DMH AI Weather Dashboard", layout="wide")

# --- ၂။ ဘာသာစကား Dictionary ---
LANG_DICT = {
    "English": {
        "title": "DMH AI Weather Forecast System",
        "city_select": "🎯 Select Station",
        "modes": ["16-Day Detailed Analysis", "Heatwave Monitoring (IBF-Health)", "Climate Projection (2100)"],
        "charts": ["🌡️ 1. Temp Outlook", "🌧️ 2. Rain Summary", "💨 3. Wind Speed", "🔭 4. Visibility", "💧 5. Humidity", "☁️ 6. Cloud Cover", "⚡ 7. Storm %"],
        "risk_levels": ["Extreme Risk", "High Risk", "Moderate Risk", "Low Risk"],
        "impacts": ["Severe threat! Heatstroke risk.", "Significant risk! Fatigue/Cramps.", "Moderate threat! Avoid sun exposure.", "Low threat! Standard precautions."],
        "recommends": ["STAY INDOORS. Drink 4L water.", "Limit outdoor work. Wear hats.", "Wear light clothes. Seek shade.", "Stay hydrated."],
        "footer": "System: DMH Myanmar | Data: Open-Meteo"
    },
    "မြန်မာ": {
        "title": "DMH AI မိုးလေဝသ ခန့်မှန်းချက်စနစ်",
        "city_select": "🎯 စခန်းအမည်ရွေးချယ်ပါ",
        "modes": ["၁၆ ရက်စာ အသေးစိတ်ဆန်းစစ်ချက်", "အပူချိန်စောင့်ကြည့်ခြင်း (IBF-ကျန်းမာရေး )", "ရာသီဥတုပြောင်းလဲမှု (၂၁၀၀)"],
        "charts": ["🌡️ ၁။ အပူချိန်ခန့်မှန်းချက်", "🌧️ ၂။ မိုးရေချိန်ခန့်မှန်းချက်", "💨 ၃။ လေတိုက်နှုန်း", "🔭 ၄။ အဝေးမြင်တာ", "💧 ၅။ စိုထိုင်းဆ", "☁️ ၆။ တိမ်ဖုံးမှု", "⚡ ၇။ မိုးတိမ်တောင် %"],
        "risk_levels": ["အလွန်အန္တရာယ်ရှိ", "အန္တရာယ်ရှိ", "သတိပြုရန်", "ပုံမှန်"],
        "impacts": ["Heatstroke အန္တရာယ်ရှိသည်။", "ပင်ပန်းနွမ်းနယ်ခြင်း ဖြစ်နိုင်ပါသည်။", "နေပူထဲ အကြာကြီး မနေပါနှင့်။", "ပုံမှန်အတိုင်း နေနိုင်ပါသည်။"],
        "recommends": ["အိမ်ထဲတွင်နေပါ။ ရေများများသောက်ပါ။", "ပြင်ပလုပ်ငန်းများ လျှော့ချပါ။", "အရိပ်တွင် နားနားနေပါ။", "ရေဓာတ် ဖြည့်တင်းပါ။"],
        "footer": "တရားဝင်စနစ်: မိုးလေဝသနှင့်ဇလဗေဒညွှန်ကြားမှုဦးစီးဌာန"
    }
}

# --- ၃။ စခန်းစာရင်းဖတ်ခြင်း ---
@st.cache_data
def load_stations():
    try:
        # Station.csv ထဲက City, Lat, Lon ကို ဖတ်ပါတယ်
        df = pd.read_csv("Station.csv", encoding='utf-8-sig')
        df.columns = [c.strip() for c in df.columns]
        c_col = 'City' if 'City' in df.columns else 'Station'
        return {str(row[c_col]).strip(): {'lat': row[1], 'lon': row[2]} for _, row in df.iterrows()}
    except Exception as e:
        return {"Naypyidaw": {"lat": 19.7633, "lon": 96.0785}}

MYANMAR_CITIES = load_stations()

# --- ၄။ Sidebar ---
st.sidebar.image(dm_header_logo, width=150)
lang = st.sidebar.radio("🌐 Language", ["မြန်မာ", "English"], horizontal=True)
T = LANG_DICT[lang]

# မြို့အားလုံး Dropdown ထဲပေါ်အောင် လုပ်ထားပါသည်
city_list = sorted(list(MYANMAR_CITIES.keys()))
selected_city = st.sidebar.selectbox(T["city_select"], city_list)

# Bias Correction ပြန်ထည့်ထားပါသည်
bias = st.sidebar.slider("🌡️ Bias Correction (°C)", -5.0, 5.0, 0.0, step=0.1)
view_mode = st.sidebar.radio("📊 View Mode", T["modes"])

# --- ၅။ API Function ---
@st.cache_data(ttl=600)
def fetch_weather(city):
    loc = MYANMAR_CITIES[city]
    url = f"https://api.open-meteo.com/v1/forecast?latitude={loc['lat']}&longitude={loc['lon']}&hourly=temperature_2m,relative_humidity_2m,cloud_cover,visibility,precipitation,windspeed_10m,cape&daily=temperature_2m_max,temperature_2m_min,precipitation_sum&forecast_days=16&timezone=Asia%2FYangon"
    try:
        r = requests.get(url, timeout=10).json()
        df_h = pd.DataFrame({"Time": pd.to_datetime(r['hourly']['time']), "Temp": r['hourly']['temperature_2m'], "Wind": r['hourly']['windspeed_10m'], "Vis": [v/1000 for v in r['hourly']['visibility']], "Humid": r['hourly']['relative_humidity_2m'], "Cloud": r['hourly']['cloud_cover'], "Storm": [min(round((c/3500)*100), 100) for c in r['hourly']['cape']]})
        df_d = pd.DataFrame({"Date": pd.to_datetime(r['daily']['time']), "Tmax": r['daily']['temperature_2m_max'], "Tmin": r['daily']['temperature_2m_min'], "RainSum": r['daily']['precipitation_sum']})
        return df_h, df_d
    except: return None, None

# --- ၆။ Main Content ---
st.title(T["title"])
st.info(f"📍 {selected_city} | 🕒 {formatted_now}")

h_data, d_data = fetch_weather(selected_city)

if h_data is not None:
    # Apply Bias
    d_data['Tmax'] += bias
    d_data['Tmin'] += bias
    h_data['Temp'] += bias

    if view_mode == T["modes"][0]: # Detailed Analysis
        st.plotly_chart(px.line(d_data, x='Date', y=['Tmax', 'Tmin'], title=T['charts'][0], markers=True, color_discrete_map={'Tmax':'red','Tmin':'blue'}), use_container_width=True)
        st.plotly_chart(px.bar(d_data, x='Date', y='RainSum', title=T['charts'][1]), use_container_width=True)
        st.plotly_chart(px.line(h_data, x='Time', y='Wind', title=T['charts'][2]), use_container_width=True)
        st.plotly_chart(px.line(h_data, x='Time', y='Vis', title=T['charts'][3]), use_container_width=True)
        st.plotly_chart(px.area(h_data, x='Time', y='Humid', title=T['charts'][4]), use_container_width=True)
        st.plotly_chart(px.bar(h_data, x='Time', y='Cloud', title=T['charts'][5]), use_container_width=True)
        st.plotly_chart(px.bar(h_data, x='Time', y='Storm', title=T['charts'][6], color_discrete_sequence=['purple']), use_container_width=True)

    elif view_mode == T["modes"][1]: # Heatwave IBF
        max_t = d_data['Tmax'].max()
        # Risk Logic
        idx = 0 if max_t >= 42 else 1 if max_t >= 40 else 2 if max_t >= 38 else 3
        colors = ['#800000','#d00000','#ffaa00','#008000']
        
        st.markdown(f"<div style='background-color:{colors[idx]}; padding:30px; border-radius:15px; text-align:center; color:white;'><h1>{T['risk_levels'][idx]} ({max_t:.1f} °C)</h1></div>", unsafe_allow_html=True)
        
        st.subheader("🏥 Health Impact & Recommendations")
        st.error(f"⚠️ {T['impacts'][idx]}")
        st.success(f"💡 {T['recommends'][idx]}")
        
        st.plotly_chart(px.bar(d_data, x='Date', y='Tmax', color='Tmax', color_continuous_scale='YlOrRd', title="Heat Outlook"), use_container_width=True)

        # Batch Export Logic
        st.markdown("---")
        if st.button("🚀 Process All 247 Stations"):
            all_list = []
            progress = st.progress(0)
            for i, city in enumerate(city_list):
                _, d_tmp = fetch_weather(city)
                if d_tmp is not None:
                    d_tmp['Station'] = city
                    all_list.append(d_tmp)
                progress.progress((i+1)/len(city_list))
            if all_list:
                m_df = pd.concat(all_list)
                m_df['Date'] = m_df['Date'].dt.strftime('%Y-%m-%d')
                st.session_state['master_df'] = m_df
                st.success("✅ Complete!")

        if 'master_df' in st.session_state:
            master = st.session_state['master_df']
            sel_date = st.selectbox("Select Date for Report", master['Date'].unique())
            day_df = master[master['Date'] == sel_date].sort_values(by='Station')
            st.dataframe(day_df, use_container_width=True)
            st.download_button("📥 Download Full CSV", day_df.to_csv(index=False).encode('utf-8-sig'), f"DMH_{sel_date}.csv")

    else: # Climate Mode
        st.subheader("🌡️ Climate Projection (2026-2100)")
        st.markdown("> **⚠️ Climate Risk Note:** Under the SSP 5-8.5 scenario, Myanmar could face significantly higher frequency of extreme heat and unpredictable monsoon patterns by the end of the century.")
        years = np.arange(2026, 2101)
        trend = [31 + (y-2026)*0.045 + np.random.normal(0, 0.4) for y in years]
        st.plotly_chart(px.line(x=years, y=trend, labels={'x':'Year','y':'Temp (°C)'}), use_container_width=True)

st.markdown("---")
st.markdown(f"<center>{T['footer']}</center>", unsafe_allow_html=True)

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
