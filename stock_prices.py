import psycopg2
import yfinance as yf
from datetime import datetime, timedelta
from time import sleep
from keys import HOST, DATABASE, USER, PASSWORD


class Stock:    # Class to store the stock information
	def __init__(self, s_symbol,tran_date, close_p):
		self.stockName = s_symbol
		self.t_date = tran_date  # Date as a string "YYYY-MM-DD"
		self.price = float(close_p) if close_p else None


	def __str__(self):
		return f"{self.stockName} {self.t_date} {self.close_p}"

	def print_stock(self):
		print(self.stockName, self.t_date, self.price, sep = ' ')


def fetch_stock_prices(stock_symbol, start_date = None, end_date = None):
	"""Fetch stock prices using yfinance from start to end dates"""
	sleep(1) # Avoid overwhelming yfinance
	try:
		   # Strip any suffix
		stock = yf.Ticker(stock_symbol.split(":")[0])

		# Default to 45 days before today if no start_date, today if no end_date
		if not start_date:
			start_date = datetime.now() - timedelta(days = 45)
		if not end_date:
			end_date = datetime.now()
		
		hist = stock.history(start = start_date, end = end_date)
		if hist.empty:
			print(f"No data found for {stock_symbol}")
			return []
	
		# Convert to list of Stock objects
		stock_prices = []
		for date, row in hist.iterrows():
			date_str = date.strftime("%Y-%m-%d")
			close_price = row["Close"]
			stock_prices.append(Stock(stock_symbol, date_str, close_price))
		return stock_prices
	except Exception as e:
		print(f"Error fetching {stock_symbol} with yfinance: {e}")
		return []

def multiple_purchasers_check():  # Check to see if multiple congress members bought a stock
	"""Load stock prices for symbols with multiple congressional trades."""
	try:
	
		connection = psycopg2.connect(host=HOST, database=DATABASE, user=USER, password=PASSWORD)
		connection.autocommit = True
		cur = connection.cursor()

		# Query stock symbols with multiple buyers in the last 45 days
		cur.execute("""
			SELECT stock_symbol, purchase_date
			FROM stock_purchases
			WHERE purchase_date > CURRENT_DATE - INTERVAL '45 days'
		""")
		purchases = cur.fetchall()

		for purchase in purchases:
			stock_sym, purchase_date = purchase
			one_month_before = purchase_date - timedelta(days = 45)

			# Count unique buyers for this stock
			cur.execute("""
				SELECT COUNT(DISTINCT name) FROM stock_purchases
				WHERE stock_symbol = %s AND purchase_date > %s""", (stock_sym, one_month_before))
			buyer_count = cur.fetchone()[0]

			if buyer_count > 1:
				# Check if prices exist for the stock
				cur.execute("Select COUNT(*) FROM stock_price WHERE stock_symbol = %s", (stock_sym,))
				price_count = cur.fetchone()[0]

				# Fetch prices from 45 days befopre purchase to today
				start_date = one_month_before
				end_date = datetime.now().date()
				historical_prices = fetch_stock_prices(stock_sym, start_date, end_date)

				for price in historical_prices:
					if price.t_date: # Make sure date is valid
						# Check if date exists
						cur.execute("""
				  			Select 1 FROM stock_price 
				  			WHERE stock_symbol = %s AND s_date = %s
				  		""", (stock_sym, price.t_date))
						if not cur.fetchone(): # Insert if it does not already exist
							cur.execute("""
								INSERT INTO stock_price (stock_symbol, s_date, s_price)
				   				VALUES (%s, %s, %s)
				   			""", (price.stockName, price.t_date, price.price))
							print(f"Added {price.t_date} for {stock_sym}")
				print(f"Updated price data for {stock_sym} up to {end_date}")
		cur.close()
		connection.close()
	except psycopg2.Error as e:
		print(f"Database error: {e}")



multiple_purchasers_check()
