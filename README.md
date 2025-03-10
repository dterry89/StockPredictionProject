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
git clone https://github.com/your-username/StockPredictionProject.git
cd StockPredictionProject