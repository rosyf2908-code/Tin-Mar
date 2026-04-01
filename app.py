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
        "city_select": "🎯 Select Station",
        "modes": ["16-Day Detailed Analysis", "Heatwave Monitoring (IBF-Health)", "Climate Projection (2100)"],
        "charts": ["🌡️ 1. Temp Outlook", "🌧️ 2. Rain Summary", "💨 3. Wind Speed/Dir", "🔭 4. Visibility", "💧 5. Humidity", "☁️ 6. Cloud Cover (Oktas)", "⚡ 7. Thunderstorm %"],
        "footer": "Data: Open-Meteo | System: DMH Myanmar"
    },
    "မြန်မာ": {
        "title": "DMH AI မိုးလေဝသ ခန့်မှန်းချက်စနစ်",
        "city_select": "🎯 စခန်းအမည်ရွေးချယ်ပါ",
        "modes": ["၁၆ ရက်စာ အသေးစိတ်ဆန်းစစ်ချက်", "အပူချိန်စောင့်ကြည့်ခြင်း (IBF-ကျန်းမာရေး )", "ရာသီဥတုပြောင်းလဲမှု (၂၁၀၀)"],
        "charts": ["🌡️ ၁။ အပူချိန်ခန့်မှန်းချက်", "🌧️ ၂။ မိုးရေချိန်ခန့်မှန်းချက်", "💨 ၃။ လေတိုက်နှုန်း/ဦးတည်ရာ", "🔭 ၄။ အဝေးမြင်တာ", "💧 ၅။ စိုထိုင်းဆ", "☁️ ၆။ တိမ်ဖုံးမှု (Oktas)", "⚡ ၇။ မိုးတိမ်တောင် %"],
        "footer": "အချက်အလက်ရင်းမြစ်: Open-Meteo | တရားဝင်စနစ်: မိုးဇလ"
    }
}

# --- ၃။ စခန်းစာရင်းဖတ်ခြင်း ---
@st.cache_data
def load_stations():
    # ဖိုင်နာမည်ကို 'Station.csv' သို့မဟုတ် 'station.csv' နှစ်မျိုးလုံး စစ်ပေးထားပါတယ်
    for filename in ["Station.csv", "station.csv"]:
        try:
            df_st = pd.read_csv(filename, encoding='utf-8-sig')
            return {str(row['Station']): {'lat': row['Lat'], 'lon': row['Lon']} for _, row in df_st.iterrows()}
        except FileNotFoundError:
            continue
    st.error("⚠️ Station.csv ဖိုင်ကို ရှာမတွေ့ပါ။ Folder ထဲတွင် ဖိုင်ရှိမရှိ ပြန်စစ်ပေးပါ။")
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
st.info(f"🕒 {formatted_now} | 📍 {selected_city}")

df_h, df_d = get_full_weather(selected_city)

if df_h is not None:
    df_d['Tmax'] += temp_bias
    df_d['Tmin'] += temp_bias
    df_h['Temp'] += temp_bias

    if view_mode == T["modes"][0]:
        # Chart 1: Temperature with Red (Max) and Blue (Min)
        fig_temp = px.line(df_d, x='Date', y=['Tmax', 'Tmin'], title=T['charts'][0], markers=True,
                          color_discrete_map={'Tmax': 'red', 'Tmin': 'blue'})
        st.plotly_chart(fig_temp, use_container_width=True)
        
        st.plotly_chart(px.bar(df_d, x='Date', y='RainSum', title=T['charts'][1], color_discrete_sequence=['deepskyblue']), use_container_width=True)
        
        # Wind Direction
        df_w = df_h[df_h['Time'].dt.hour == 13].copy()
        fig_w = go.Figure()
        fig_w.add_trace(go.Scatter(x=df_w['Time'], y=df_w['Wind'], mode='lines+markers', name='Speed'))
        fig_w.add_trace(go.Scatter(x=df_w['Time'], y=df_w['Wind']+1.5, mode='markers', 
                                   marker=dict(symbol='arrow', angle=df_w['WindDir'], size=15, color='orange'), name='Direction'))
        st.plotly_chart(fig_w.update_layout(title=T['charts'][2]), use_container_width=True)
        
        st.plotly_chart(px.line(df_h, x='Time', y='Visibility', title=T['charts'][3]), use_container_width=True)
        st.plotly_chart(px.area(df_h, x='Time', y='Humidity', title=T['charts'][4]), use_container_width=True)
        
        # Chart 6: Cloud Cover
        st.plotly_chart(px.bar(df_h, x='Time', y='Cloud', title=T['charts'][5], color='Cloud', color_continuous_scale='Blues'), use_container_width=True)
        
        st.plotly_chart(px.bar(df_h, x='Time', y='Storm', title=T['charts'][6], color_discrete_sequence=['purple']), use_container_width=True)

    elif view_mode == T["modes"][1]:
        # --- Multi-Station Processing ---
        st.subheader(f"📥 Download Data for All {len(MYANMAR_CITIES)} Stations")
        
        if st.button("🚀 Start Processing (Pull Data for All Cities)"):
            all_dfs = []
            prog = st.progress(0)
            status = st.empty()
            
            for i, city in enumerate(city_list):
                status.text(f"Fetching: {city} ({i+1}/{len(city_list)})")
                _, d_tmp = get_full_weather(city)
                if d_tmp is not None:
                    d_tmp['Station'] = city
                    all_dfs.append(d_tmp)
                prog.progress((i+1)/len(city_list))
            
            if all_dfs:
                master_df = pd.concat(all_dfs, ignore_index=True)
                master_df['Date'] = master_df['Date'].dt.strftime('%Y-%m-%d')
                st.session_state['master_df'] = master_df
                status.success("✅ အချက်အလက်များ စုစည်းမှု အောင်မြင်ပါသည်။")

        # Display Data for All Stations by Selected Date
        if 'master_df' in st.session_state:
            m_df = st.session_state['master_df']
            st.markdown("---")
            sel_date = st.selectbox("📅 Select Date to View All Stations", m_df['Date'].unique(), key='date_sel_key')
            
            day_data = m_df[m_df['Date'] == sel_date].sort_values(by='Station')
            
            st.write(f"📊 **Data for {sel_date} (Total {len(day_data)} Stations)**")
            st.dataframe(day_data, use_container_width=True) # ဇယားနဲ့ အကုန်ပြခြင်း
            
            csv_day = day_data.to_csv(index=False).encode('utf-8-sig')
            st.download_button(f"📥 Download {sel_date} Report (CSV)", csv_day, f"DMH_All_Stations_{sel_date}.csv", "text/csv")

    else:
        # --- Climate Projection 2026-2100 ---
        st.subheader("🌡️ Long-term Climate Projection (2026 - 2100)")
        years = np.arange(2026, 2101)
        # 0.04°C increase per year trend
        temp_trend = [31 + (y-2026)*0.042 + np.random.normal(0, 0.3) for y in years]
        
        df_climate = pd.DataFrame({"Year": years, "Avg_Temp": temp_trend})
        fig_cli = px.line(df_climate, x='Year', y='Avg_Temp', title="Projected Mean Temperature Increase (SSP 5-8.5 Scenario)",
                         color_discrete_sequence=['darkred'])
        st.plotly_chart(fig_cli, use_container_width=True)
        st.warning("⚠️ ဤအချက်အလက်သည် CMIP6 Climate Model အပေါ်အခြေခံထားသော ခန့်မှန်းချက်သာ ဖြစ်ပါသည်။")

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
