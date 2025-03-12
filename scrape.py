import psycopg2
from bs4 import BeautifulSoup
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import re
from datetime import date, datetime 
import time
from keys import HOST, DATABASE, USER, PASSWORD 

class StockPurchase:
    def __init__(self):
        self.purchase_date = ''
        self.price = None # Use None for missing numbers
        self.symbol = ''
        self.name = ''

    def __str__(self):
        return f'{self.purchase_date}  {self.price}  {self.symbol}  {self.name}'

    def set_date(self, new_date):
        self.purchase_date = new_date

    def set_price(self, new_price):
        self.price = float(new_price) if new_price else None  # Convert to float or None

    def set_symbol(self, new_symbol):
        self.symbol = new_symbol

    def set_name(self, new_name):
        self.name = new_name

    def transform_date(self):
        """Convert string date to Python date object."""
        try:
            # Handle 'YYYY,MM,DD' format
            matches = re.findall(r'([\d,]+)', self.purchase_date.replace(",",""))
            if len(matches) >= 3:
                year, month, day = map(int, matches[:3])
                return date(year, month, day)
            
            # Handle other common formats if needed
            return datetime.strptime(self.purchase_date, "%d,%b,%Y").date()
        except (ValueError, IndexError) as e:
            print(f"Date parse error for '{self.purchase_date}': {e}")
            return None
    
def scrape_page(page):
    """Scrape congressional stock bought trades from Capitol Trades API."""

    # URL to scrape
    url = f"https://www.capitoltrades.com/trades?txType=buy&assetType=stock&sortBy=-txDate&page={page}"

    # Send a GET request to the webpage
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }  # Mimic a browser to avoid being blocked
    trans_list = []

    for attempt in range(3):
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            # Check if the request was successful

            # Parse the HTML content
            soup = BeautifulSoup(response.text, "html.parser")
            trade_table = soup.find("table")  # Target specific table class

            if not trade_table:
                print(f"Page {page}: No trade table found.")
                return trans_list
            
            rows = trade_table.find_all("tr")[1:]  # Skip header row
            for row in rows:
                cols = row.find_all("td")
                if len(cols) >= 9:  # Adjust based on columns
                    politician= re.findall(r"[A-Z][^A-Z]*\s[A-Z][^A-Z]*",cols[0].text.strip())
                    politician = politician[0] if politician else "N/A"

                    stock = re.findall(r"[A-Z]{1,4}:[A-Z]{2}", cols[1].text.strip())
                    stock = stock[0] if stock else "N/A"
                    if stock == 'OOGL:US':
                        stock = "GOOGL:US"
                    # Obtain and format the date and price
                    date_full = cols[3].text.strip().replace(" ", ",")  
                    date_full = date_full[:-4] + ',' + date_full[-4:]
                    price = cols[8].text.strip().replace("$", '').replace(",", '')
                    price = float(price) if price and price != "N/A" else None

                    purchase = StockPurchase()
                    purchase.set_date(date_full)
                    purchase.set_symbol(stock)
                    purchase.set_price(price)
                    purchase.set_name(politician)
                    trans_list.append(purchase)
            print(f"Page {page}: Scraped {len(trans_list)} trades.")
            return trans_list
        except requests.RequestException as e:
            print(f"Page {page}: Attempt {attempt + 1} failed - {e}")
            time.sleep(2 ** attempt)

    return trans_list


def scrape_trades(max_pages = 40, workers = 5):
    """Scrape congressional trades using multithreading."""

    trans_list = []
    start_time = time.time()

    with ThreadPoolExecutor(max_workers = workers) as executor:
        future_to_page = {executor.submit(scrape_page, page): page for page in range(1, max_pages + 1)}
        for future in as_completed(future_to_page):
            page = future_to_page[future]
            try:
                trades = future.result()
                trans_list.extend(trades)
            except Exception as e:
                print(f"Page {page}: Error - {e}")

    print(f"Scraped {len(trans_list)} trades in {time.time() - start_time:.2f} seconds.")
    return trans_list


def load_tables(trans_list):
    """Insert new trades into PostgreSQL, skipping duplicates."""
    try:
        conn = psycopg2.connect(host=HOST, database=DATABASE, user=USER, password=PASSWORD)
        conn.autocommit = True
        cur = conn.cursor()

        # Fetch existing trades once
        cur.execute("Select purchase_date, stock_symbol, name FROM stock_purchases")
        existing = {(row[0].isoformat() if isinstance(row[0], date) else row[0], row[1], row[2]) for row in cur.fetchall()}
        print(f"Found {len(existing)} existing trades. Sample: {list(existing)[:5]}")

        # Filter new trades and prepare batch
        new_trades = []
        for t in trans_list:
            # Normalize purchase_date to match DB format
            db_date = t.transform_date()
            if db_date is None:
                print(f"Skipping invalid date: {t.purchase_date}")
                continue
            db_date_str = db_date.isoformat()
            key = (db_date_str, t.symbol, t.name.strip())
            print(f"Checking trade: {key}")
            if key not in existing:
                new_trades.append((t.purchase_date, t.price, t.symbol, t.name))
                print(f"Added new trade: {t}")
            else:
                print(f"Trade already exists:{t}")
        
        print(f"Inserting {len(new_trades)} new trades.")
        # Batch insert
        if new_trades:
            cur.executemany("""
                INSERT INTO stock_purchases (purchase_date, purchase_price, stock_symbol, name)
                VALUES (%s, %s, %s, %s)
            """, new_trades)
            conn.commit()
        else:
            print("No new trades to insert.")

        print(f"Batch inserted {len(new_trades)} trades.")

        # Clean up invalid data
        cur.execute("DELETE FROM stock_purchases WHERE stock_symbol = 'N/A' or purchase_price IS NULL or name = 'N/A'")
        print("Cleaned up invalid entries.")

        cur.close()
        conn.close()
    except psycopg2.Error as e:
        print(f"Database error: {e}")

if __name__ == "__main__":
    transactions = scrape_trades(max_pages = 60, workers = 5)
    load_tables(transactions)