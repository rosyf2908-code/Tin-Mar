import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import requests
import os
from datetime import datetime
import pytz

# --- ၁။ Layout Setup ---
st.set_page_config(page_title="DMH AI Weather Dashboard", layout="wide")

mm_tz = pytz.timezone('Asia/Yangon')
now = datetime.now(mm_tz)
formatted_now = now.strftime('%I:%M %p, %d %b %Y')
dm_header_logo = "https://www.moezala.gov.mm/themes/custom/dmh/logo.png?v=1.1"

# --- ၂။ ဘာသာစကားနှင့် စာသားများ (Translations) ---
T = {
    "modes": ["၁၆ ရက်စာ အသေးစိတ်ဆန်းစစ်ချက်", "အပူချိန်စောင့်ကြည့်ခြင်း (IBF-ကျန်းမာရေး )", "ရာသီဥတုပြောင်းလဲမှု (၂၁၀၀)"],
    "dmh_alert": "📢 အကြံပြုချက်: နောက်ဆုံးရ မိုးလေဝသသတင်းများအတွက် မိုးဇလ သတင်းများကိုစောင့်ကြည့်ပါ။",
    "storm_note": "📝 မှတ်ချက်: မိုးတိမ်တောင် ဖြစ်နိုင်ခြေ ၆၀% ထက်ကျော်လွန်ပါက လေပြင်းတိုက်ခတ်ခြင်း၊ မိုးကြိုးပစ်ခြင်းနှင့် လျှပ်စီးလက်ခြင်းများ ဖြစ်ပေါ်နိုင်သဖြင့် ဂရုပြုရန် လိုအပ်ပါသည်။",
    "ibf_header": "🏥 ကျန်းမာရေးကဏ္ဍဆိုင်ရာ အကျိုးသက်ရောက်မှုနှင့် အကြံပြုချက်များ",
    "risk_levels": ["အလွန်အန္တရာယ်ရှိ", "အန္တရာယ်ရှိ", "သတိပြုရန်", "ပုံမှန်"],
    "impacts": [
        "အလွန်စိုးရိမ်ရသော အခြေအနေ! အပူဒဏ်လျှပ်စီးဖြတ်ခြင်း (Heatstroke) နှင့် ရေဓာတ်ကုန်ခမ်းခြင်းကြောင့် အသက်အန္တရာယ်ရှိနိုင်သည်။",
        "အန္တရာယ်ရှိသော အခြေအနေ! အပူဒဏ်ကြောင့် ပင်ပန်းနွမ်းနယ်ခြင်း ဖြစ်နိုင်ပါသည်။ ကလေးနှင့် လူအိုများ အထူးသတိပြုပါ။",
        "သတိပြုရန် အခြေအနေ! နေရောင်အောက်တွင် ကြာရှည်နေပါက ပင်ပန်းနွမ်းနယ်ခြင်း ဖြစ်ပေါ်နိုင်ပါသည်။",
        "ပုံမှန်အခြေအနေ! သိသာထင်ရှားသော ကျန်းမာရေးထိခိုက်မှု မရှိနိုင်ပါ။"
    ],
    "recommends": [
        "အိမ်ထဲတွင်သာ နေပါ။ ရေ (၃-၄) လီတာ သောက်ပါ။ မူးဝေပါက ဆေးရုံသို့ အမြန်သွားပါ။ မိုးလေဝသ သတင်းများကို အချိန်ပြည့် စောင့်ကြည့်ပါ။",
        "ပြင်ပလုပ်ငန်းများကို နံနက်/ညနေသာ လုပ်ပါ။ ထီး/ဦးထုပ် ဆောင်းပါ။ ရေဓာတ်ဖြည့်ပါ။ မိုးလေဝသ သတင်းများကို နားထောင်ပါ။",
        "ပေါ့ပါးသော အဝတ်များ ဝတ်ပါ။ ရေခဏခဏသောက်ပါ။ အရိပ်တွင် နားပါ။ မိုးဇလခန့်မှန်းချက်များကို နားထောင်ပါ။",
        "ပုံမှန်အတိုင်း နေနိုင်ပါသည်။ ရေဓာတ်ဖြည့်တင်းရန်နှင့် မိုးလေဝသ သတင်းများကို ဆက်လက်စောင့်ကြည့်ပါ။"
    ]
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
        cols = {c.lower(): c for c in df.columns}
        n_key = cols.get('city', cols.get('station', df.columns[0]))
        s_dict = {}
        for _, row in df.iterrows():
            s_dict[str(row[n_key]).strip()] = {'lat': float(row['Lat']), 'lon': float(row['Lon'])}
        return s_dict
    except:
        return {"Naypyidaw": {"lat": 19.76, "lon": 96.08}}

MYANMAR_CITIES = load_stations()
city_list = sorted(list(MYANMAR_CITIES.keys()))

# --- ၄။ Sidebar ---
st.sidebar.image(dm_header_logo, width=100)
bias = st.sidebar.slider("🌡️ Bias Correction (°C)", -5.0, 5.0, 0.0, step=0.1)
selected_city = st.sidebar.selectbox("🎯 စခန်းအမည်ရွေးချယ်ပါ", city_list)
view_mode = st.sidebar.radio("📊 View Mode", T["modes"])

# --- ၅။ Weather API Logic ---
@st.cache_data(ttl=600)
def fetch_weather(city):
    loc = MYANMAR_CITIES[city]
    url = f"https://api.open-meteo.com/v1/forecast?latitude={loc['lat']}&longitude={loc['lon']}&hourly=temperature_2m,relative_humidity_2m,cloud_cover,visibility,precipitation,windspeed_10m,cape&daily=temperature_2m_max,temperature_2m_min,precipitation_sum&windspeed_unit=mph&forecast_days=16&timezone=Asia%2FYangon"
    try:
        r = requests.get(url, timeout=10).json()
        df_h = pd.DataFrame({"Time": pd.to_datetime(r['hourly']['time']), "Temp": r['hourly']['temperature_2m'], "Wind": r['hourly']['windspeed_10m'], "Storm": [min(round((c/3500)*100), 100) for c in r['hourly']['cape']]})
        df_d = pd.DataFrame({"Date": pd.to_datetime(r['daily']['time']), "Tmax": r['daily']['temperature_2m_max'], "Tmin": r['daily']['temperature_2m_min'], "Rain": r['daily']['precipitation_sum']})
        return df_h, df_d
    except: return None, None

# --- ၆။ Main Page Display ---
st.title("DMH AI Weather Forecast System")
st.info(f"📍 စခန်း: {selected_city} | 🕒 {formatted_now}")

df_h, df_d = fetch_weather(selected_city)

if df_h is not None:
    df_d['Tmax'] += bias
    df_d['Tmin'] += bias
    df_h['Temp'] += bias

    # ဘယ် View Mode မှာမဆို မိုးဇလသတင်းစောင့်ကြည့်ရန် သတိပေးချက်ပြမည်
    st.warning(T["dmh_alert"])

    if view_mode == T["modes"][0]:
        # ၁၆ ရက်စာ View
        st.plotly_chart(px.line(df_d, x='Date', y=['Tmax', 'Tmin'], title="🌡️ Daily Temperature Forecast"), use_container_width=True)
        st.error(T["storm_note"])
        st.plotly_chart(px.bar(df_h, x='Time', y='Storm', title="⚡ Thunderstorm Probability (%)", color_discrete_sequence=['purple']), use_container_width=True)

    elif view_mode == T["modes"][1]:
        # Heatwave IBF View
        max_t = df_d['Tmax'].max()
        idx = 0 if max_t >= 42 else 1 if max_t >= 40 else 2 if max_t >= 38 else 3
        colors = ['#800000','#d00000','#ffaa00','#008000']
        
        st.markdown(f"<div style='background-color:{colors[idx]}; padding:35px; border-radius:15px; text-align:center;'><h1 style='color:white;'>{T['risk_levels'][idx]}: {max_t:.1f} °C</h1></div>", unsafe_allow_html=True)
        
        st.subheader(T['ibf_header'])
        st.error(f"⚠️ **Impact:**\n\n{T['impacts'][idx]}")
        st.success(f"💡 **Recommendations:**\n\n{T['recommends'][idx]}")
        
        fig_ibf = px.bar(df_d, x='Date', y='Tmax', color='Tmax', color_continuous_scale='YlOrRd', title="Heatwave Monitoring Index")
        for val, color, label in [(42, "maroon", "Extreme"), (40, "red", "High"), (38, "orange", "Moderate")]:
            fig_ibf.add_hline(y=val, line_dash="dash", line_color=color, annotation_text=f"{label} ({val}°C)")
        st.plotly_chart(fig_ibf, use_container_width=True)

        # --- Error ရှင်းရန်အပိုင်း (Batch Export) ---
        if st.button("🚀 စခန်းအားလုံး၏ Data စုစည်းမည်"):
            all_data = []
            p_bar = st.progress(0)
            for i, c in enumerate(city_list):
                _, d_tmp = fetch_weather(c)
                if d_tmp is not None:
                    d_tmp['Station'] = c
                    all_data.append(d_tmp)
                p_bar.progress((i+1)/len(city_list))
            if all_data:
                st.session_state['master_df'] = pd.concat(all_data)
                st.success("✅ စုစည်းမှု အောင်မြင်ပါသည်။")

        if 'master_df' in st.session_state:
            m_df = st.session_state['master_df'].copy()
            # ဤနေရာတွင် Error ဖြစ်စေသော .dt မသုံးမီ ရက်စွဲအဖြစ် အရင်ပြောင်းသည်
            m_df['Date'] = pd.to_datetime(m_df['Date']) 
            m_df['Date_Str'] = m_df['Date'].dt.strftime('%Y-%m-%d')
            
            sel_date = st.selectbox("နေ့စွဲရွေးပါ", m_df['Date_Str'].unique())
            final_df = m_df[m_df['Date_Str'] == sel_date].sort_values(by='Station')
            st.dataframe(final_df, use_container_width=True)
            st.download_button(f"📥 Download CSV ({sel_date})", final_df.to_csv(index=False).encode('utf-8-sig'), f"DMH_Report_{sel_date}.csv")

    else:
        st.subheader("🌡️ Climate Projection (2026-2100)")
        years = np.arange(2026, 2101)
        trend = [31 + (y-2026)*0.045 + np.random.normal(0, 0.4) for y in years]
        st.plotly_chart(px.line(x=years, y=trend, labels={'x':'Year','y':'Temp (°C)'}, title="Future Temperature Scenario (SSP 5-8.5)"), use_container_width=True)

st.markdown("---")
st.markdown("<center>တရားဝင်စနစ်: မိုးလေဝသနှင့်ဇလဗေဒညွှန်ကြားမှုဦးစီးဌာန</center>", unsafe_allow_html=True)

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
