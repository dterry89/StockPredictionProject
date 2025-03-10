import psycopg2
from keys import *



def establish_tables():
	"""Create PostgreSQL tables for stock purchases and historical prices."""

	try:
		connection = psycopg2.connect(host = HOST, database = DATABASE, user = USER, password = PASSWORD)
		connection.autocommit = True
		cur = connection.cursor()

		cur.execute("""
			CREATE TABLE IF NOT EXISTS stock_purchases(id Serial Primary Key, purchase_date DATE,  purchase_price NUMERIC(10,2), stock_symbol Varchar(15),  name Varchar(100), price_before FLOAT, price_after FLOAT)
			""")

		cur.execute("""
			CREATE TABLE IF NOT EXISTS stock_price(id Serial Primary Key, stock_symbol Varchar(15), s_date Date, s_price NUMERIC(10, 2), is_prediction BOOLEAN DEFAULT FALSE)
			""")

		cur.close()
		connection.close()
	except psycopg2.Error as e:
		print(f"Database error: {e}")

if __name__ == "__main__":
	establish_tables()