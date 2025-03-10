import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
import time
from streamlit_gsheets import GSheetsConnection

# Title
st.title("A/B Testing: Understanding Fare vs. Tip Amounts")

# Business Question
st.markdown("### Business Question: How does fare amount impact tip amount?")

# Connect to Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# Load data from Google Sheets
df = conn.read(worksheet="Sheet1", ttl="10m")  # Ensure correct worksheet name

# Drop empty rows
df = df.dropna()

# Ensure dataset contains required columns
required_columns = {"fare", "tip"}  # Adjust as needed
if not required_columns.issubset(df.columns):
    st.error(f"Error: Google Sheet does not contain the required columns: {required_columns}")
    st.stop()

# Convert columns to numeric
df["fare"] = pd.to_numeric(df["fare"], errors="coerce")
df["tip"] = pd.to_numeric(df["tip"], errors="coerce")

# Remove extreme outliers (for better visualization)
df = df[df["fare"] < 100]  # Assuming reasonable fares under $100
df = df[df["tip"] < 30]    # Assuming tips under $30

# Initialize session state variables
if "step" not in st.session_state:
    st.session_state.step = 1  # Step 1: Show Chart A first
    st.session_state.start_time = None
    st.session_state.time_chart_a = None
    st.session_state.time_chart_b = None

# Function to show Chart A (Bar Chart of Fare Ranges vs. Average Tip)
def show_chart_a():
    st.subheader("Chart A: Average Tip per Fare Range (Bar Chart)")

    # Create fare bins
    bins = [0, 5, 10, 20, 50, 100]  # Fare ranges
    labels = ["$0-$5", "$5-$10", "$10-$20", "$20-$50", "$50+"]

    df["fare_range"] = pd.cut(df["fare"], bins=bins, labels=labels)

    # Group by fare range and calculate average tip
    avg_tips = df.groupby("fare_range")["tip"].mean().reset_index()

    fig, ax = plt.subplots(figsize=(10, 5))
    sns.barplot(x="fare_range", y="tip", data=avg_tips, ax=ax, palette="Blues_d")
    ax.set_xlabel("Fare Range ($)")
    ax.set_ylabel("Average Tip ($)")
    ax.set_title("Bar Chart: Average Tip per Fare Range")
    st.pyplot(fig)

# Function to show Chart B (Scatter Plot with Regression Trendline)
def show_chart_b():
    st.subheader("Chart B: Fare vs. Tip with Trendline (Scatter Plot)")

    fig, ax = plt.subplots(figsize=(10, 5))
    sns.regplot(x=df["fare"], y=df["tip"], scatter_kws={"alpha": 0.5}, line_kws={"color": "red"}, ax=ax)
    ax.set_xlabel("Fare Amount ($)")
    ax.set_ylabel("Tip Amount ($)")
    ax.set_title("Scatter Plot: Fare vs. Tip with Trendline")
    st.pyplot(fig)

# Step 1: Show Chart A first
if st.session_state.step == 1:
    show_chart_a()
    if st.button("Next"):
        st.session_state.time_chart_a = round(time.time() - st.session_state.start_time, 2)
        st.session_state.start_time = time.time()  # Start timing for Chart B
        st.session_state.step = 2
        st.rerun()

# Step 2: Show Chart B after Chart A is completed
elif st.session_state.step == 2:
    show_chart_b()
    if st.button("Finish"):
        st.session_state.time_chart_b = round(time.time() - st.session_state.start_time, 2)
        st.session_state.step = 3
        st.rerun()

# Step 3: Show comparison of response times
elif st.session_state.step == 3:
    st.subheader("A/B Test Results")
    st.write(f"**Time taken for Chart A (Bar Chart):** {st.session_state.time_chart_a} seconds")
    st.write(f"**Time taken for Chart B (Scatter Plot):** {st.session_state.time_chart_b} seconds")

    if st.session_state.time_chart_a < st.session_state.time_chart_b:
        st.success("🚀 Chart A (Bar Chart) was understood faster!")
    elif st.session_state.time_chart_a > st.session_state.time_chart_b:
        st.success("🚀 Chart B (Scatter Plot) was understood faster!")
    else:
        st.info("Both charts took the same time to answer.")

    # Reset the session state for a new test
    if st.button("Restart Test"):
        st.session_state.step = 1
        st.session_state.start_time = time.time()
        st.session_state.time_chart_a = None
        st.session_state.time_chart_b = None
        st.rerun()

# Start timing when the app loads
if st.session_state.step == 1 and st.session_state.start_time is None:
    st.session_state.start_time = time.time()
