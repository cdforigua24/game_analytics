import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from utils import preprocess_csv_funnel, preprocess_active_users
import plotly.express as px
import numpy as np

# Sidebar menu
st.sidebar.title("Menu")
option = st.sidebar.radio(
    "Choose an option:",
    ('Funnel', 'Active Users Heatmap 24H')
)

st.title("In-Game Analytics App")

if option == 'Funnel':
    st.header("Conversion Funnel Analysis 📊")

    cols = st.columns(3)
    with cols[0]:
        harbor_registrations = st.number_input("Harbor Hub", min_value=0, value=0, key='hub')
    with cols[1]:
        steam_keys_granted = st.number_input("Keys Granted", min_value=0, value=0, key='granted')
    with cols[2]:
        steam_keys_claimed = st.number_input("Keys Claimed", min_value=0, value=0, key='claimed')

    st.subheader("External Data CSV")
    uploaded_file = st.file_uploader("Choose Helika CSV file", type="csv")
    filter_organic = st.checkbox("Filter organic users")
    organic_users_file = None

    if filter_organic:
        st.markdown("Upload a CSV file containing users to ignore (CSV File with Email Column):")
        organic_users_file = st.file_uploader("Users to Ignore CSV", type="csv", key="ignore_users")

    if 'csv_uploaded' not in st.session_state:
        st.session_state['csv_uploaded'] = False

    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        st.write("CSV Preview:")
        st.dataframe(df.head())

        ignored_users_df = None
        if filter_organic and organic_users_file:
            ignored_users_df = pd.read_csv(organic_users_file, sep=";")

        new_user_regs, started_games, economic_purchases = preprocess_csv_funnel(df, ignored_users_df)
        st.session_state['csv_uploaded'] = True  

    create_funnel_btn = st.button("Create Funnel", disabled=not st.session_state['csv_uploaded'])

    if create_funnel_btn:
        funnel_labels = [
            "Harbor Hub Registrations",
            "Steam Keys Granted",
            "Steam Keys Claimed",
            "New User Registrations",
            "Players Completed 1 Game",
            "Players Economic/Purchase"
        ]

        funnel_values = [
            harbor_registrations,
            steam_keys_granted,
            steam_keys_claimed,
            new_user_regs,
            started_games,
            economic_purchases
        ]

        st.subheader("📈 Full Conversion Funnel")

        fig = go.Figure(go.Funnel(
            y=funnel_labels,
            x=funnel_values,
            textinfo="value+percent initial",
            marker={
                "color": ["#FF5C7E", "#3C00FF", "#A100FF", "#6D0ACF", "#8E2DE2", "#4A00E0", "#240090"],
                "line": {"width": 2, "color": "white"}
            },
            connector={"line": {"color": "lightgray", "width": 2}}
        ))

        fig.update_layout(
            title={
                "text": "📊 In-game Analytics Conversion Funnel",
                "x": 0.5,
                "y": 0.95,
                "xanchor": "center",
                "yanchor": "top",
                "font": {"size": 22, "color": "#FF5C7E"}
            },
            plot_bgcolor="#0E1117",
            paper_bgcolor="#0E1117",
            font={"color": "white", "family": "Arial", "size": 14},
            margin={"l": 150, "r": 150, "t": 80, "b": 80},
            autosize=True
        )

        st.plotly_chart(fig, use_container_width=True)
        
elif option == 'Active Users Heatmap 24H':
    st.header("🔥 Active Users Heatmap 24H")

    # Date filters
    cols = st.columns(2)
    with cols[0]:
        start_date = st.date_input("Start Date")
    with cols[1]:
        end_date = st.date_input("End Date")

    # Timezone selection (default: Eastern Time)
    timezone = st.selectbox("Select Timezone", [
        "America/Toronto",  # Eastern Time
        "America/Winnipeg",  # Central Time
        "America/Edmonton",  # Mountain Time
        "America/Vancouver"  # Pacific Time
    ], index=0)

    # CSV Upload
    uploaded_file = st.file_uploader("Upload Active Users CSV", type="csv")

    if uploaded_file:
        st.write("CSV Preview:")
        df = pd.read_csv(uploaded_file)
        st.dataframe(df.head())

        # Generate button
        generate_chart_btn = st.button("Generate Chart")

        if generate_chart_btn:
            with st.spinner("Processing data..."):
                heatmap_data = preprocess_active_users(df, start_date, end_date, timezone)

                if not heatmap_data.empty:
                    # Ensure the matrix is properly shaped
                    heatmap_matrix = heatmap_data["avg_users"].values.reshape(-1, 1)  # Fix issue

                    # Plot heatmap (Hour on Y-axis)
                    fig = px.imshow(
                        heatmap_matrix,
                        labels={"x": "Active Users", "y": "Hour"},
                        y=heatmap_data["hour"],  # Hours on y-axis
                        color_continuous_scale="viridis"
                    )

                    fig.update_layout(
                        title="Average Active Users Over 24 Hours (Converted to Selected Timezone)",
                        yaxis_title="Hour of the Day",
                        xaxis_title="Active Users",
                        coloraxis_colorbar_title="Avg Users",
                        autosize=True
                    )

                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.error("No data found for the selected date range.")


#if __name__ == "__main__":
#    ignored_users_df =  pd.read_csv("Exclude Email List.csv", sep=";")
#    df = pd.read_csv("playtest2_with_new_registry.csv")
#    preprocess_csv_funnel(df, ignored_users_df)

