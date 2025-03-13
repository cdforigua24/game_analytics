import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from utils import preprocess_csv_funnel, scrape_steamdb_chart

# Sidebar menu
st.sidebar.title("Menu")
option = st.sidebar.radio(
    "Choose an option:",
    ('Funnel', 'Web Scraping')
)

st.title("In-Game Analytics App")

if option == 'Funnel':
    st.header("Conversion Funnel Analysis 📊")

    cols = st.columns(4)
    with cols[0]:
        harbor_registrations = st.number_input("Harbor Hub", min_value=0, value=0, key='hub')
    with cols[1]:
        steam_keys_granted = st.number_input("Keys Granted", min_value=0, value=0, key='granted')
    with cols[2]:
        steam_keys_claimed = st.number_input("Keys Claimed", min_value=0, value=0, key='claimed')
    with cols[3]:
        in_game_registrations = st.number_input("In-game Reg.", min_value=0, value=0, key='ingame')

    st.subheader("External Data CSV")
    uploaded_file = st.file_uploader("Choose Helika CSV file", type="csv")

    if 'csv_uploaded' not in st.session_state:
        st.session_state['csv_uploaded'] = False

    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        st.write("CSV Preview:")
        st.dataframe(df.head())

        new_user_regs, started_games, economic_purchases = preprocess_csv_funnel(df)
        st.session_state['csv_uploaded'] = True  

    create_funnel_btn = st.button("Create Funnel", disabled=not st.session_state['csv_uploaded'])

    if create_funnel_btn:
        funnel_labels = [
            "Harbor Hub Registrations",
            "Steam Keys Granted",
            "Steam Keys Claimed",
            "Organic In-game Registrations",
            "New User Registrations",
            "Players Completed 1 Game",
            "Players Economic/Purchase"
        ]

        funnel_values = [
            harbor_registrations,
            steam_keys_granted,
            steam_keys_claimed,
            in_game_registrations,
            new_user_regs,
            started_games,
            economic_purchases
        ]

        funnel_values, funnel_labels = zip(*sorted(zip(funnel_values, funnel_labels), reverse=True))

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

elif option == 'Web Scraping':
    st.header("SteamDB Web Scraping 🔍")

    st.sidebar.subheader("SteamDB Configuration")
    app_url = st.sidebar.text_input("SteamDB URL", "https://steamdb.info/app/2914840/charts/")

    # Button to start scraping
    if st.button("Start Scraping"):
        with st.spinner('Scraping SteamDB data...'):
            chart_data = scrape_steamdb_chart(app_url, "1m")

            if not chart_data.empty:
                st.success("Data successfully scraped!")

                st.subheader("📊 Player Count Over Time (1 Month)")
                st.dataframe(chart_data)

                st.subheader("📈 Player Count Chart")
                st.line_chart(chart_data.set_index('Date')['Users'])
            else:
                st.error("No data was scraped. Please check the URL and try again.")
