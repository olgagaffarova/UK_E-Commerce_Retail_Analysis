############################################################
# 🗽 NYC CITIBIKE 2022 DASHBOARD
# Author: Olga Gaffarova
# Goal: Reduce bike shortages by 50% at top 20% busiest stations
############################################################

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')

# ───────────────────────────────────────────────
# CONFIGURATION
# ───────────────────────────────────────────────
sns.set_theme(style="darkgrid")
plt.style.use('dark_background')

st.set_page_config(page_title="CitiBike 2022", layout="wide")

# Sidebar Navigation
st.sidebar.title("📊 Dashboard Navigation")
page = st.sidebar.radio(
    "Go to:",
    ["Intro", "Seasonality & Weather", "Top 14% Routes (Pareto)", "Recommendations"]
)

# ───────────────────────────────────────────────
# LOAD DATA
# ───────────────────────────────────────────────
top15 = pd.read_csv('02 Streamlit/top15_dashboard.csv', index_col=0)
df_group = pd.read_csv('02 Streamlit/df_group_dashboard.csv', index_col=0)
df_daily_weather = pd.read_csv('02 Streamlit/df_daily_weather_dashboard.csv', index_col=0)
donors_receivers = pd.read_csv('02 Streamlit/donors_receivers.csv', index_col=0)
df_daily_precipitations =  = pd.read_csv('02 Streamlit/df_daily_precipitations.csv', index_col=0)

# ───────────────────────────────────────────────
# PAGE 1: INTRO
# ───────────────────────────────────────────────
if page == "Intro":
    st.title("🚴 CitiBike 2022: Understanding New York’s Bike Network")
    st.markdown("""
    **Goal:** Reduce bike shortages by up to **50%** in 2023 at the **top 20% busiest stations**, 
    which together handle **80% of all CitiBike demand**, by optimizing redistribution.

    Since **2013**, New York City’s *CitiBike* has grown into a network of **33,000 bikes**
    and **4,600 docking stations** across **Manhattan**, **Brooklyn**, and **Queens**.
    
    This dashboard explores CitiBike’s 2022 usage data to understand:
    - When people ride (seasonal and weather effects)  
    - Where the busiest routes are (Pareto analysis)  
    - Which stations face shortages or overflow (imbalance analysis)
    """)

    st.markdown("### Top 15 Most Popular Start Stations in New York")

    fig = go.Figure(
        go.Bar(
            x=top15['start_station_name'],
            y=top15['trips_per_station'],
            marker=dict(
                color=top15['trips_per_station'],
                colorscale='Blues',
                showscale=True,
                colorbar=dict(title='Trip Count')
            ),
            text=top15['trips_per_station'],
            textposition='outside'
        )
    )

    fig.update_layout(
        title='Top 15 Most Popular Start Stations in New York',
        xaxis_title='Station Name',
        yaxis_title='Number of Trips',
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(color='black', size=11),
        xaxis=dict(tickangle=-45, categoryorder='total descending'),
        height=600,
        margin=dict(l=40, r=40, t=80, b=120)
    )

    st.plotly_chart(fig, use_container_width=True)

# ───────────────────────────────────────────────
# PAGE 2: SEASONALITY & WEATHER
# ───────────────────────────────────────────────
elif page == "Seasonality & Weather":
    st.title("🌦️ Seasonality and Weather Impact on CitiBike Demand")
    st.markdown("""
    This section explores how **temperature** and **precipitation** affect CitiBike ridership.  
    Colder or rainy days tend to reduce daily rides, while warm and dry conditions encourage more cycling.
    """)

    # --- DAILY RIDES VS AVERAGE TEMPERATURE ---
    st.subheader("🚴 Daily Bike Rides and Average Temperature (2022)")
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(
        go.Scatter(
            x=df_daily_weather['date'],
            y=df_daily_weather['bike_rides_daily'],
            name='Bike Rides',
            mode='lines',
            line=dict(color='#0ea5e9', width=2)
        ),
        secondary_y=False
    )

    fig.add_trace(
        go.Scatter(
            x=df_daily_weather['date'],
            y=df_daily_weather['avgTemp'],
            name='Avg Temperature (°C)',
            mode='lines',
            line=dict(color='#a855f7', width=2, dash='dot')
        ),
        secondary_y=True
    )

    fig.update_layout(
        title='Daily Bike Rides and Average Temperature — 2022',
        template='plotly_white',
        hovermode='x unified',
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
        height=600,
        margin=dict(l=40, r=40, t=80, b=40)
    )

    fig.update_xaxes(title_text="Date")
    fig.update_yaxes(title_text="Number of Bike Rides", secondary_y=False)
    fig.update_yaxes(title_text="Average Temperature (°C)", secondary_y=True)
    st.plotly_chart(fig, use_container_width=True)

    
    
    # --- DAILY RIDES VS PRECIPITATION ---
  
st.subheader("☔ Daily Bike Rides and Precipitation (2022)")

# Merge rides and weather data
df_daily_precipitations = pd.merge(df_group, df, on="date", how="inner")

# Create dual-axis chart
fig = make_subplots(specs=[[{"secondary_y": True}]])

# --- Bike rides (left y-axis) ---
fig.add_trace(
    go.Scatter(
        x=df_daily_precipitations['date'],
        y=df_daily_precipitations['bike_rides_daily'],
        name='Bike Rides',
        mode='lines',
        line=dict(color='#0ea5e9', width=2)
    ),
    secondary_y=False
)

# --- Precipitation (right y-axis) ---
fig.add_trace(
    go.Scatter(
        x=df_daily_precipitations['date'],
        y=df_daily_precipitations['total_precipitation'],
        name='Total Precipitation (mm)',
        mode='lines',
        line=dict(color='#a855f7', width=2, dash='dot')
    ),
    secondary_y=True
)

# --- Layout ---
fig.update_layout(
    title='Daily Bike Rides and Total Precipitation — 2022',
    template='plotly_white',
    hovermode='x unified',
    legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
    height=600,
    margin=dict(l=40

    
    
    
# ───────────────────────────────────────────────
# PAGE 3: PARETO MAP
# ───────────────────────────────────────────────
elif page == "Top 14% Routes (Pareto)":
    st.title("📍 Pareto Analysis: Top 14% Routes Covering 80% of Trips")
    st.markdown("""
    Applying the **Pareto Principle (80/20 rule)** helps focus on the most significant routes.  
    The **top 14% of all routes** in 2022 account for **80% of total CitiBike trips**.  
    These high-traffic routes reveal where rebalancing and optimization bring the most benefit.
    """)

    st.markdown("### Aggregated Trip Flows in New York (Pareto Ratio)")
    path_to_html = "02 Streamlit/nyc_bike_map.html"
    with open(path_to_html, "r", encoding="utf-8") as f:
        html_data = f.read()
    st.components.v1.html(html_data, height=900, scrolling=True)

# ───────────────────────────────────────────────
# PAGE 4: RECOMMENDATIONS
# ───────────────────────────────────────────────
elif page == "Recommendations":
    st.title("🚲 Identifying Problem Stations and Strategic Recommendations")
    st.markdown("""
    This section identifies **stations with persistent bike shortages or overflows**  
    using the **mean net flow** (rentals − returns) metric across 2022.
    
    - **Positive net flow → Donor stations** (bikes leave → shortage risk)  
    - **Negative net flow → Receiver stations** (bikes accumulate → overflow risk)
    """)

    # Split into two groups
    donors = donors_receivers[donors_receivers['mean_net_flow'] > 0]
    receivers = donors_receivers[donors_receivers['mean_net_flow'] < 0]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=donors['station_name'],
        x=donors['mean_net_flow'],
        name='Donor Stations (Shortage Risk)',
        orientation='h',
        marker_color='royalblue'
    ))

    fig.add_trace(go.Bar(
        y=receivers['station_name'],
        x=receivers['mean_net_flow'],
        name='Receiver Stations (Overflow Risk)',
        orientation='h',
        marker_color='tomato'
    ))

    fig.update_layout(
        title="CitiBike Station Imbalance (Donors vs Receivers)",
        xaxis_title="Mean Net Flow (Rentals − Returns)",
        yaxis_title="Station",
        height=800,
        barmode='overlay',
        xaxis=dict(zeroline=True, zerolinewidth=2, zerolinecolor='black'),
        legend=dict(yanchor="bottom", y=0.01, xanchor="right", x=0.95)
    )

    st.plotly_chart(fig, use_container_width=True)

    st.markdown("### 💡 Strategic Recommendations")
    st.markdown("""
    **1. Scale back fleet during off-season (Nov–Apr):**  
    Reduce active bikes by **30–40%**, matching seasonal demand drops while cutting maintenance costs.
    
    **2. Add docking stations along the waterfront:**  
    High trip density near riverside routes indicates expansion potential to reduce congestion at inner-city docks.
    
    **3. Implement predictive redistribution:**  
    Rebalance bikes between **7–9 AM** and **5–7 PM** from overflow → shortage zones using current fleet.
    
    **4. Prioritize top imbalance clusters:**  
    Focus on ~600 busiest stations (handling 80% of rides) to maximize efficiency and improve rider satisfaction.
    """)

