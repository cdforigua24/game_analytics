import pandas as pd
import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup


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