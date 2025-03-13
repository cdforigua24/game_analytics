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


from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import pandas as pd
import time


def scrape_steamdb_chart(url, period="1M"):
    """
    Scrapes SteamDB for the player count chart data.
    
    :param url: SteamDB URL of the game's chart page
    :param period: Time period to scrape (default "1M")
    :return: Pandas DataFrame with Date and Users
    """
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    driver.get(url)

    try:
        # Wait until Highcharts buttons load
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CLASS_NAME, "highcharts-button"))
        )

        # Find all Highcharts buttons (they are <g> elements, not <button>)
        highcharts_buttons = driver.find_elements(By.CLASS_NAME, "highcharts-button")

        # Find the one that contains "1M" inside a <text> tag
        selected_button = None
        for button in highcharts_buttons:
            text_element = button.find_element(By.TAG_NAME, "text")
            if text_element and period in text_element.text:
                selected_button = button
                break

        if not selected_button:
            print("❌ Period button not found!")
            driver.quit()
            return pd.DataFrame()

        # Click using JavaScript since SVG elements may not support direct clicks
        driver.execute_script("arguments[0].dispatchEvent(new MouseEvent('click', {bubbles: true}));", selected_button)
        time.sleep(5)  # Wait for chart to update

        # Parse page source
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        points = soup.select('g.highcharts-markers circle')

        data = []
        for point in points:
            label = point.get('aria-label')
            if label:
                try:
                    date_str, value_str = label.split(', ')
                    date = date_str.replace('Users on ', '').strip()
                    value = int(value_str.replace('Users: ', '').strip())
                    data.append({'Date': date, 'Users': value})
                except ValueError as e:
                    print(f"❌ Parsing error: {e} - Label: {label}")

    except Exception as e:
        print(f"❌ Error: {e}")
        return pd.DataFrame()
    
    finally:
        driver.quit()  # Ensure driver closes properly

    # Convert to DataFrame
    df = pd.DataFrame(data)
    if not df.empty:
        df['Date'] = pd.to_datetime(df['Date'])
        df = df.sort_values('Date')

    print("✅ Extracted Data:", df.head())  # Debugging output
    return df




