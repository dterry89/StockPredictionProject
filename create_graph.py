from sqlalchemy import create_engine, text
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from scipy.interpolate import make_interp_spline
import pandas as pd
from keys import HOST, DATABASE, USER, PASSWORD, MYPATH

def create_graph():
	"""Generate a smoothed stock price graph from the stock_price table."""
	try: 
		# Create SQLAlchemy engine
		engine = create_engine(f"postgresql+psycopg2://{USER}:{PASSWORD}@{HOST}/{DATABASE}")

		# Fetch data with pandas and SQLAlchemy
		query = """
			SELECT stock_symbol, s_date, s_price, is_prediction
			FROM stock_price
			ORDER by s_date"""
		
		with engine.connect() as conn:
			df = pd.read_sql_query(text(query), conn)

		if df.empty:
			print("No stock price data found.")
			return
		
		# Group by stock symbol
		stock_groups = df.groupby("stock_symbol")

		for symbol, group in stock_groups:
			# Split the real and predicted data
			real_data = group[group["is_prediction"] == False]
			pred_data = group[group["is_prediction"] == True]

			# Set up plot
			plt.figure(figsize = (10,6))

			if not real_data.empty:
				dates = pd.to_datetime(real_data["s_date"])
				prices = real_data["s_price"].astype(float)
				# Create a smooth curve
				xnew = pd.date_range(dates.min(), dates.max(), periods = 300)
				spl = make_interp_spline(dates, prices, k = 3)
				smooth = spl(xnew)

				# Plot the data
				plt.plot(xnew, smooth, label=f"{symbol} Historical", color = "blue")
				plt.scatter(dates, prices, color = "blue", s = 10)  

			if not pred_data.empty:
				pred_dates = pd.to_datetime(pred_data["s_date"])
				pred_prices = pred_data["s_price"].astype(float)
				plt.plot(pred_dates, pred_prices, label = f"{symbol} Predicted", color = "orange", ls = "--")
				plt.scatter(pred_dates, pred_prices, color = "orange", s = 10)

				# Format
				ax = plt.gca()
				ax.xaxis.set_major_locator(mdates.DayLocator(interval = 7))
				ax.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d"))
				plt.xlabel("Date")
				plt.ylabel("Price (USD)")
				plt.title(f"Stock Price Tend: {symbol}")
				plt.grid(True)
				plt.legend()

			symbol = symbol.split(":")[0]
			# Save the plot
			plt.savefig(MYPATH + f"{symbol}_price_trend.png")
			plt.close()
			print(f"Saved graph for {symbol}")
		
	except Exception as e:
		print(f"Error: {e}")
		raise




	

if __name__== "__main__":
	create_graph()
