import json
import sqlite3
from selenium import webdriver
from selenium.webdriver.common.by import By
import time
from datetime import datetime, timedelta

# Path to the SQLite database
DB_PATH = 'rate_history.db'

def get_page_data(driver, page, total_usdt, threshold=10000):
    # Open the specific page on Binance's P2P market for USDT to EGP
    url = f"https://p2p.binance.com/en/trade/all-payments/USDT?fiat=EGP&page={page}"
    driver.get(url)
    time.sleep(5)  # Wait for the page to load

    # Locate all table rows containing data
    table_rows = driver.find_elements(By.CSS_SELECTOR, 'tr.bn-web-table-row')

    if not table_rows:
        print("No rows found in the table.")
        return [], total_usdt

    data = []
    for row in table_rows:
        try:
            # Extract relevant data from each row
            advertiser = row.find_element(By.CSS_SELECTOR, 'a.text-primaryText').text.strip()
            price = float(row.find_element(By.CSS_SELECTOR, 'div.headline5').text.strip())
            availability = row.find_elements(By.CSS_SELECTOR, 'div.body3')[0].text.strip().replace(' USDT', '').replace(',', '')
            min_max = row.find_elements(By.CSS_SELECTOR, 'div.bn-flex')[1].text.strip()
            payment_methods = [method.text for method in row.find_elements(By.CSS_SELECTOR, 'div.PaymentMethodItem__text')]

            available_usdt = float(availability)
            if total_usdt + available_usdt >= threshold:
                data.append({
                    'advertiser': advertiser,
                    'price': price,
                    'availability': available_usdt,
                    'min_max': min_max,
                    'payment_methods': payment_methods
                })
                total_usdt += available_usdt
                break
            else:
                data.append({
                    'advertiser': advertiser,
                    'price': price,
                    'availability': available_usdt,
                    'min_max': min_max,
                    'payment_methods': payment_methods
                })
                total_usdt += available_usdt
        except Exception as e:
            print(f"Error parsing row: {e}")
            continue

    return data, total_usdt

def calculate_weighted_average(data, threshold=10000):
    # Calculate the weighted average price based on the data collected
    total_usdt = 0
    total_egp = 0

    for row in data:
        available_usdt = row['availability']
        price = row['price']

        if total_usdt + available_usdt >= threshold:
            required_usdt = threshold - total_usdt
            total_egp += required_usdt * price
            total_usdt += required_usdt
            break
        else:
            total_usdt += available_usdt
            total_egp += available_usdt * price

    weighted_avg_price = total_egp / total_usdt if total_usdt != 0 else 0
    return weighted_avg_price, total_usdt

def create_database():
    # Create the SQLite database and table if it does not exist
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS exchange_rates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            datetime TEXT,
            session_number INTEGER,
            advertiser TEXT,
            price REAL,
            availability REAL,
            min_max TEXT,
            payment_methods TEXT,
            weighted_avg_price REAL,
            percentage_change REAL
        )
    ''')
    conn.commit()
    conn.close()

def get_previous_day_price():
    # Get the weighted average price from approximately 24 hours ago
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT weighted_avg_price FROM exchange_rates
        WHERE datetime <= datetime('now', '-1 day')
        ORDER BY datetime DESC LIMIT 1
    ''')
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

def save_data_to_db(data, session_number, weighted_avg_price, percentage_change):
    # Save the scraped data to the database
    datetime_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    for row in data:
        cursor.execute('''
            INSERT INTO exchange_rates (datetime, session_number, advertiser, price, availability, min_max, payment_methods, weighted_avg_price, percentage_change)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (datetime_now, session_number, row['advertiser'], row['price'], row['availability'], row['min_max'], ', '.join(row['payment_methods']), weighted_avg_price, percentage_change))

    conn.commit()
    conn.close()

def get_next_session_number():
    # Get the next session number for the database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT MAX(session_number) FROM exchange_rates')
    result = cursor.fetchone()
    conn.close()
    return (result[0] + 1) if result[0] is not None else 0

def scrape_and_calculate():
    # Main function to scrape data and calculate the weighted average price
    create_database()
    driver = webdriver.Chrome()
    all_data = []
    page = 1
    total_usdt = 0

    while total_usdt < 10000:
        print(f"Scraping page {page}...")
        page_data, total_usdt = get_page_data(driver, page, total_usdt)
        if not page_data:
            print("No data found on the page, stopping...")
            break
        all_data.extend(page_data)
        print(f"Total USDT so far: {total_usdt}")
        page += 1
        time.sleep(5)

    weighted_avg_price, total_usdt = calculate_weighted_average(all_data)
    previous_day_price = get_previous_day_price()
    if previous_day_price:
        percentage_change = ((weighted_avg_price - previous_day_price) / previous_day_price) * 100
    else:
        percentage_change = 0

    session_number = get_next_session_number()
    save_data_to_db(all_data, session_number, weighted_avg_price, percentage_change)
    driver.quit()

    print(f"Weighted Average Price: {weighted_avg_price}")
    print(f"Total USDT: {total_usdt}")

if __name__ == "__main__":
    scrape_and_calculate()
