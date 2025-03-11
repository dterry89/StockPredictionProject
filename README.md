# StockPredictionProject

This project predicts stock price movements by leveraging congressional trade data, historical stock prices, and a Random Forest machine learning model. It scrapes trade data from Capitol Trades, fetches stock prices using `yfinance`, and predicts whether a stock’s price will go up or down over the next 7 days. The predictions are visualized with graphs to help users understand trends.

## Features
- **Congressional Trade Scraping**: Scrapes trade data from [Capitol Trades](https://www.capitoltrades.com) (`scraper.py`).
- **Historical Stock Prices**: Fetches historical stock prices using `yfinance` (`stock_prices.py`).
- **Machine Learning Predictions**: Uses a Random Forest model to predict price movements, incorporating features like average price, price volatility, trade count, and market index trends (S&P 500) (`predict.py`).
- **Visualization**: Generates graphs to compare historical and predicted stock prices (`create_graph.py`).

## Project Structure
- `scraper.py`: Scrapes congressional trades and stores them in a PostgreSQL database.
- `stock_prices.py`: Fetches historical stock prices using `yfinance` and stores them in the database.
- `predict.py`: Trains a Random Forest model and predicts future stock price movements.
- `create_graph.py`: Generates visualizations of historical vs. predicted stock prices.
- `keys.py`: Stores database credentials (not tracked in Git).
- `requirements.txt`: Lists project dependencies.

## Prerequisites
- Python 3.8 or higher
- PostgreSQL database
- Git (to clone the repository)
- A GitHub account (optional, for contributing)

## Setup
Follow these steps to set up and run the project locally.

### 1. Clone the Repository
```bash
git clone https://github.com/dterry89/StockPredictionProject.git  (replace with username of repository owner)
cd StockPredictionProject
```

### 2. Create a Virtual Environment
```bash
python -m venv myenv
source myenv/bin/activate  # macOS/Linux
myenv\Scripts\activate     # Windows
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Set up PostgreSQL
Configure a PostgreSQL database to store the data.
#### Install PostgreSQL:
Follow the installation guide for your operating system [PostgreSQL Downloads](https://www.postgresql.org/download/).
On Ubuntu: `sudo apt install postgresql postgresql-contrib`
On macOS (with Homebrew): `brew install postgresql`
On Windows: Download and run the installer.

#### Start the PostgreSQL Service:
On macOS/Linux: `sudo service postgresql start` or `brew services start postgresql`
On Windows: Start the PostgreSQL service via the task manager or `pgAdmin`.

#### Access PostgreSQL:
Log in to the PostgreSQL prompt:
```bash
psql -U postgres
```
If prompted, set a password for the `postgres` user:
```sql
\password postgres
```
#### Create a Database:
Create a database for the project:
```sql

createdb -U postgres stock_predictions
```

#### Create Tables:
Connect to the database and create the required tables:
```sql

psql -U postgres -d stock_predictions -c "
CREATE TABLE stock_purchases (
    purchase_date DATE,
    purchase_price FLOAT,
    stock_symbol VARCHAR(20),
    name VARCHAR(100)
);
CREATE TABLE stock_price (
    stock_symbol VARCHAR(20),
    s_date DATE,
    s_price FLOAT,
    is_prediction BOOLEAN DEFAULT FALSE
);
"
```

#### Verify the tables:
```sql

\dt
```
### 5. Configure Database Credentials
Create a `keys.py` file to store your PostgreSQL credentials. This file is not tracked in Git (listed in `.gitignore`).

#### Create keys.py:
```bash

touch keys.py
```

#### Edit `keys.py` with your credentials:
```python

HOST = "localhost"
DATABASE = "stock_predictions"
USER = "postgres"  # or your PostgreSQL username
PASSWORD = "your_password"  # Replace with your password
```
#### Ensure the file permissions are restrictive:
    On macOS/Linux: chmod 600 keys.py

    On Windows: Right-click > Properties > Security (restrict to your user).

### 6. Run the Pipeline
Execute the scripts in the following order to scrape data, fetch prices, train the model, and generate visualizations:
Scrape Congressional Trades:
```bash

python scraper.py
```
This populates the `stock_purchases` table with trade data.

Fetch Historical Stock Prices:
```bash

python stock_prices.py
```
This populates the `stock_price` table with historical prices.

Train Model and Predict:
```bash

python predict.py
```
This trains the Random Forest model and adds predicted prices to `stock_price` (marked with `is_prediction = TRUE`).

Generate Graphs:
```bash

python create_graph.py
```
This creates visualization files (e.g., `Stock_Price_Trend_AAPL.png`) in the project directory.

### 7. Verify the Setup
Check the database for data:
```sql

psql -U postgres -d stock_predictions -c "SELECT * FROM stock_purchases LIMIT 5;"
psql -U postgres -d stock_predictions -c "SELECT * FROM stock_price WHERE is_prediction = TRUE LIMIT 5;"
```
Open the generated graph files to confirm visualizations.

#### Troubleshooting
Connection Errors: Ensure PostgreSQL is running and credentials in `keys.py` are correct.

Module Not Found: Verify all dependencies are installed (`pip install -r requirements.txt`).

Permission Denied: Check file permissions for `keys.py` and database access.

Slow Performance: If scripts take too long, ensure your internet connection is stable and disk space is available.




