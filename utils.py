import pandas as pd
import json
import time
import pytz
import numpy as np


def extract_user_id(event_str):
    try:
        event_data = json.loads(event_str.replace("'", "\""))
        user_id = event_data.get('user_id') or event_data.get('user_details', {}).get('user_id')
        return user_id if user_id else None
    except json.JSONDecodeError:
        return None


def preprocess_csv_funnel(df: pd.DataFrame):
    new_user_registry_count = df[df['Event Sub Type'] == 'new_user_registry'].shape[0]

    game_started_df = df[
        (df['Event Type'] == 'gameplay') & 
        (df['Event Sub Type'] == 'game_complete')
    ].copy()
    game_started_df['user_id'] = game_started_df['Event'].apply(extract_user_id)
    players_started_game = game_started_df['user_id'].nunique()

    economic_purchase_df = df[df['Event Type'].isin(['economy', 'purchase'])].copy()
    economic_purchase_df['user_id'] = economic_purchase_df['Event'].apply(extract_user_id)
    players_economic_purchase = economic_purchase_df['user_id'].nunique()

    return new_user_registry_count, players_started_game, players_economic_purchase

def preprocess_active_users(df, start_date, end_date, timezone="America/Toronto"):
    """
    Processes the CSV file to calculate the average number of active users 
    per hour (converted to a specific Canadian timezone) between the given start and end dates.

    Args:
        csv_file (str): Path to the CSV file or uploaded file object.
        start_date (datetime.date): Start date filter.
        end_date (datetime.date): End date filter.
        timezone (str): The target timezone for conversion (default: "America/Toronto" for Eastern Time).

    Returns:
        pd.DataFrame: DataFrame with hourly active user averages.
    """

    # Convert "Streamed At" column to datetime (UTC)
    df["Streamed At"] = pd.to_datetime(df["Streamed At"], errors='coerce', utc=True)

    # Convert to target timezone
    target_tz = pytz.timezone(timezone)
    df["Streamed At"] = df["Streamed At"].dt.tz_convert(target_tz)

    # Drop rows with NaT timestamps
    df = df.dropna(subset=["Streamed At"])

    # Filter based on date range
    df_filtered = df[
        (df["Streamed At"].dt.date >= start_date) & (df["Streamed At"].dt.date <= end_date)
    ]

    # Keep only 'session_created' & 'user_logged_in' events
    df_filtered = df_filtered[
        (df_filtered["Event Type"] == "session_created") &
        (df_filtered["Event Sub Type"] == "user_logged_in")
    ]

    # Extract hour from timestamp (now in the desired timezone)
    df_filtered["hour"] = df_filtered["Streamed At"].dt.hour

    # Calculate the average number of active users per hour
    hourly_data = df_filtered.groupby("hour").size().reset_index(name="avg_users")

    # Ensure all 24 hours are included (even if some have no data)
    all_hours = pd.DataFrame({"hour": np.arange(24)})
    hourly_data = all_hours.merge(hourly_data, on="hour", how="left").fillna(0)

    return hourly_data