import streamlit as st
st.set_page_config(
    page_title="Taxi Fare & Tip A/B Test",
    page_icon="🚖",
    layout="wide"
)

from streamlit_gsheets import GSheetsConnection
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import random
import time
from datetime import datetime
import numpy as np


st.markdown("""
<style>
    .main { background-color: #f8f9fa; padding: 10px; }
    h1 { color: #17408B; font-size: 36px !important; padding-bottom: 10px; border-bottom: 2px solid #C9082A; }
    h2, h3 { color: #17408B; margin-top: 1rem; }
    .stButton button { background-color: #17408B; color: white; border-radius: 6px; padding: 0.5rem 1rem; font-weight: bold; }
    .stButton button:hover { background-color: #C9082A; }
    .timer-container { background-color: #f1f3f4; padding: 10px; border-radius: 10px; border-left: 5px solid #17408B; text-align: center; }
    .timer { font-size: 20px; font-weight: bold; color: #17408B; }
    .chart-container { background-color: white; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); }
</style>
""", unsafe_allow_html=True)


if "start_time" not in st.session_state:
    st.session_state.start_time = None
if "chart_stage" not in st.session_state:
    st.session_state.chart_stage = random.choice(["A", "B"])  
if "chart_shown" not in st.session_state:
    st.session_state.chart_shown = False
if "session_id" not in st.session_state:
    st.session_state.session_id = datetime.now().strftime("%Y%m%d%H%M%S")
    st.session_state.results = []
if "current_time" not in st.session_state:
    st.session_state.current_time = 0.0
if "test_completed" not in st.session_state:
    st.session_state.test_completed = False
if "charts_shown" not in st.session_state:
    st.session_state.charts_shown = set() 

def update_timer():
    if st.session_state.start_time and st.session_state.chart_shown:
        st.session_state.current_time = time.time() - st.session_state.start_time
        st.experimental_rerun()

st.title("🚖 Taxi Fare & Tip Analysis")
st.markdown("### Question: Do higher fares result in higher tips?")

conn = st.connection("gsheets", type=GSheetsConnection)
try:
    if "connections" in st.secrets and "gsheets" in st.secrets["connections"] and "spreadsheet" in st.secrets["connections"]["gsheets"]:
        spreadsheet_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
        df = conn.read(spreadsheet=spreadsheet_url)
    elif "spreadsheet" in st.secrets:
        df = conn.read(spreadsheet=st.secrets["spreadsheet"])
    else:
        st.error("Google Sheet URL not found in secrets. Please check your configuration.")
        st.stop()
except Exception as e:
    st.error(f"Error connecting to Google Sheets: {e}")
    st.stop()

# Convert columns to numeric
df["fare"] = pd.to_numeric(df["fare"], errors="coerce")
df["tip"] = pd.to_numeric(df["tip"], errors="coerce")
df.dropna(inplace=True)

# Start A/B Test
if not st.session_state.chart_shown:
    if st.button("Start the Test"):
        st.session_state.start_time = time.time()
        st.session_state.chart_stage = random.choice(["A", "B"])  
        st.session_state.chart_shown = True
        st.session_state.current_time = 0.0
        st.session_state.test_completed = False
        st.session_state.charts_shown = set()
        st.session_state.charts_shown.add(st.session_state.chart_stage)
        st.rerun()

if st.session_state.chart_shown:

    st.markdown(f'<h3>Chart {st.session_state.chart_stage}</h3>', unsafe_allow_html=True)
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    
    fig, ax = plt.subplots(figsize=(10, 5))
    if st.session_state.chart_stage == "A":
        df["fare_range"] = pd.cut(df["fare"], bins=[0, 5, 10, 20, 50, 100], labels=["$0-$5", "$5-$10", "$10-$20", "$20-$50", "$50+"])
        avg_tips = df.groupby("fare_range")["tip"].mean().reset_index()
        sns.barplot(x="fare_range", y="tip", data=avg_tips, ax=ax, palette="Blues_d")
        ax.set_title("Bar Chart: Average Tip per Fare Range")
    else:
        sns.regplot(x=df["fare"], y=df["tip"], scatter_kws={"alpha": 0.5}, line_kws={"color": "red"}, ax=ax)
        ax.set_title("Scatter Plot: Fare vs. Tip with Trendline")
    
    st.pyplot(fig)
    st.markdown('</div>', unsafe_allow_html=True)


    if st.button("I answered your question"):
        time_taken = time.time() - st.session_state.start_time
        st.session_state.results.append({
            "chart_type": st.session_state.chart_stage,
            "time": round(time_taken, 2)
        })

       
        if st.session_state.chart_stage == "A" and "B" not in st.session_state.charts_shown:
            st.session_state.chart_stage = "B"
            st.session_state.charts_shown.add("B")
            st.session_state.start_time = time.time() 
            st.session_state.current_time = 0.0
        elif st.session_state.chart_stage == "B" and "A" not in st.session_state.charts_shown:
            st.session_state.chart_stage = "A"
            st.session_state.charts_shown.add("A")
            st.session_state.start_time = time.time()
            st.session_state.current_time = 0.0
        else:
            st.session_state.chart_shown = False
            st.session_state.test_completed = True  

        st.rerun()


if st.session_state.test_completed:
    st.subheader("A/B Test Results")
    results_df = pd.DataFrame(st.session_state.results)
    
    if not results_df.empty:
        st.table(results_df.groupby("chart_type")["time"].agg(['mean', 'min', 'max', 'count']).reset_index())
    
    if st.button("🗑️ Reset Results"):
        st.session_state.results = []
        st.session_state.test_completed = False
        st.rerun()
