import streamlit as st
import pandas as pd
import json
import os
import sys
import altair as alt

# Add parent directory to path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from utils.stats_manager import StatsManager

st.set_page_config(page_title="Analytics", page_icon="📊", layout="wide")

st.title("📊 Security Analytics Dashboard")

# Load Custom CSS & FontAwesome
def load_assets(css_file):
    with open(css_file) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    # Inject FontAwesome for Icons
    st.markdown('<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">', unsafe_allow_html=True)

try:
    load_assets(os.path.join(os.path.dirname(__file__), 'style.css'))
except: pass

from streamlit_extras.metric_cards import style_metric_cards

st.markdown('<h1><span><i class="fa-solid fa-chart-line"></i></span> Security Analytics Dashboard</h1>', unsafe_allow_html=True)

# Sidebar Filters
st.sidebar.header("🔍 Filter Options")
date_range = st.sidebar.date_input("Select Date Range", [])

# Load Data from DB
def load_security_data():
    stats_mgr = StatsManager()
    data = stats_mgr.get_stats()
    events = data.get('events', [])
    
    if not events:
        return pd.DataFrame()
    
    df = pd.DataFrame(events)
    # Convert datetime strings to datetime objects
    df['datetime'] = pd.to_datetime(df['datetime'])
    return df

df = load_security_data()

# Apply Filters
# Apply Filters
if df.empty:
    st.info("No analytics data available yet. Run the Live Monitor to generate events.")
else:
    # Event Type Filter
    event_types = df['type'].unique().tolist()
    selected_types = st.sidebar.multiselect("Event Types", event_types, default=event_types)
    
    if selected_types:
        df = df[df['type'].isin(selected_types)]
    
    # Date Filtering (Optional)
    # if date_range: ... 
    # KPI Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    total_events = len(df)
    weapon_count = len(df[df['type'] == 'WEAPON'])
    fight_count = len(df[df['type'] == 'FIGHT'])
    abandon_count = len(df[df['type'] == 'ABANDONED_LUGGAGE'])
    
    col1.metric("Total Events", total_events)
    col2.metric("Weapons Detected", weapon_count, delta_color="inverse")
    col3.metric("Fights Detected", fight_count, delta_color="inverse")
    col4.metric("Luggage Abandoned", abandon_count, delta_color="inverse")
    
    style_metric_cards(background_color="#1F2937", border_left_color="#4F8BF9", border_radius_px=10, box_shadow=True)
    
    if st.button("🔄 Refresh Data"):
        st.rerun()

    
    st.markdown("---")
    
    # Charts Row 1
    c1, c2 = st.columns(2)
    
    with c1:
        st.subheader("Event Distribution")
        if 'type' in df.columns:
            chart_data = df['type'].value_counts().reset_index()
            chart_data.columns = ['Event Type', 'Count']
            
            base = alt.Chart(chart_data).encode(
                theta=alt.Theta("Count", stack=True),
                color=alt.Color("Event Type", scale=alt.Scale(scheme='category20b'))
            )
            pie = base.mark_arc(outerRadius=120)
            text = base.mark_text(radius=140).encode(
                text="Count",
                order=alt.Order("Count", sort="descending")
            )
            st.altair_chart(pie + text, use_container_width=True)

    with c2:
        st.subheader("Event Timeline")
        timeline = alt.Chart(df).mark_circle(size=60).encode(
            x='datetime',
            y='type',
            color='type',
            tooltip=['datetime', 'type', 'details']
        ).interactive()
        st.altair_chart(timeline, use_container_width=True)

    # Detailed Data Table
    st.subheader("Recent Event Log")
    st.dataframe(df.sort_values(by='datetime', ascending=False), use_container_width=True)
