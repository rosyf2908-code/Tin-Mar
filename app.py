
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import requests
from datetime import datetime
import pytz
import os

# --- ၁။ Setup ---
mm_tz = pytz.timezone('Asia/Yangon')
now = datetime.now(mm_tz)
dm_header_logo = "https://www.moezala.gov.mm/themes/custom/dmh/logo.png?v=1.1"

st.set_page_config(page_title="DMH AI Weather Dashboard", layout="wide", page_icon="🌤️")

# --- ၂။ ဘာသာစကား Dictionary (အပြည့်အစုံ) ---
LANG_DICT = {
    "English": {
        "title": "DMH AI Weather Forecast System",
        "time_label": "Local Time (MMT)",
        "city_select": "🎯 Select Station/City",
        "view_mode": "📊 View Mode",
        "modes": ["16-Day Detailed Analysis", "Heatwave IBF (Health)", "Climate Projection (2100)"],
        "charts": ["Temp (°C)", "Rainfall (mm)", "Wind (mph)", "Visibility (km)", "Humidity (%)", "Cloud (Oktas)", "Storm (%)"],
        "axis_time": "Time / Date",
        "dmh_alert": "📢 Please monitor official DMH announcements in real-time for latest updates.",
        "ibf_header": "🏥 Health Sector Impact & Recommendations",
        "risk_levels": ["Extreme Risk", "High Risk", "Moderate Risk", "Low Risk"],
        "impacts": [
            "Severe threat! High risk of heatstroke, sunstroke, and critical dehydration for all individuals.",
            "Significant risk! Heat exhaustion and cramps are likely. Vulnerable groups (elderly/children) are at high risk.",
            "Moderate threat! Prolonged exposure may cause fatigue and heat rashes. General discomfort expected.",
            "Low threat! Standard summer conditions. No significant health impact expected."
        ],
        "recommends": [
            "STAY INDOORS. Avoid all outdoor activities. Drink 3-4 liters of water. Seek urgent medical care if dizzy or fainting.",
            "Limit outdoor work to early morning/evening. Wear hats/umbrellas. Increase fluid intake. Stay in cool areas.",
            "Wear light, breathable cotton clothes. Drink water even if not thirsty. Take frequent breaks in shade.",
            "Standard health precautions. Stay hydrated and monitor weather changes."
        ],
        "footer": "Data: Open-Meteo | System: Department of Meteorology and Hydrology"
    },
    "မြန်မာ": {
        "title": "DMH AI မိုးလေဝသ ခန့်မှန်းချက်စနစ်",
        "time_label": "မြန်မာစံတော်ချိန်",
        "city_select": "🎯 စခန်း/မြို့အမည်ရွေးချယ်ပါ",
        "view_mode": "📊 ကြည့်ရှုမည့်ပုံစံ",
        "modes": ["၁၆ ရက်စာ အသေးစိတ်ဆန်းစစ်ချက်", "အပူချိန်နှင့် ကျန်းမာရေး (IBF)", "ရာသီဥတုပြောင်းလဲမှု (၂၁၀၀)"],
        "charts": ["အပူချိန် (°C)", "မိုးရေချိန် (mm)", "လေတိုက်နှုန်း (mph)", "အဝေး



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

