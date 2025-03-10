from sqlalchemy import create_engine, text
import pandas as pd
import yfinance as yf
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
from sklearn.model_selection import train_test_split
from datetime import datetime, timedelta
from keys import HOST, DATABASE, USER, PASSWORD

def fetch_market_index_data(start_date, end_date):
    """Fetch S&P 500 historical data using yfinance."""
    try:
        sp500 = yf.download("^GSPC", start = start_date, end = end_date)

        if not isinstance(sp500, pd.DataFrame) or sp500.empty:
            return pd.DataFrame
        
        sp500 = sp500[["Close"]].reset_index()
        sp500.columns = ["s_date", "sp500_price"]
        sp500["s_date"] = pd.to_datetime(sp500["s_date"])
        return sp500
    
    except Exception as e:
        print(f"Error fetching S&P 500 data: {e}")
        return pd.DataFrame()

def evaluate_model():
    """Train, test, and evaluate the ML model using historical data."""
    try:
        # Create SQLAlchemy engine
        engine = create_engine(f"postgresql+psycopg2://{USER}:{PASSWORD}@{HOST}/{DATABASE}")
        print("Engine created successfully.")

        # Load historical prices
        with engine.connect() as conn:
            prices_df = pd.read_sql_query(text("""
                SELECT stock_symbol, s_date, s_price
                From stock_price
                WHERE is_prediction = FALSE
                ORDER BY stock_symbol, s_date
            """), conn)

            trades_df = pd.read_sql_query(text("""
                SELECT stock_symbol, purchase_date, purchase_price
                FROM stock_purchases
            """), conn)
        
        if prices_df.empty:
            print("No historical price data found.")
            return
        

        # Fetch S&P 500 data for the same date range
        start_date = prices_df["s_date"].min()
        end_date = prices_df["s_date"].max() + timedelta(days = 1)
        sp500_df = fetch_market_index_data(start_date, end_date)
        if sp500_df.empty:
            print("Failed to fetch S&P 500 data. Proceeding without market trends.")
            sp500_df = pd.DataFrame(columns = ["s_date", "sp500_price"])
        
        # Merge S&P 500 data with stock prices
        prices_df["s_date"] = pd.to_datetime(prices_df["s_date"])
        sp500_df["s_date"] = pd.to_datetime(sp500_df["s_date"])
        prices_df = prices_df.merge(sp500_df, on = "s_date", how = "left")
        prices_df["sp500_price"] = prices_df["sp500_price"].ffill()

        # Feature engineering and evaluation per stock
        results = []
        for symbol in prices_df["stock_symbol"].unique():
            stock_prices = prices_df[prices_df["stock_symbol"] == symbol].copy()
            stock_trades = trades_df[trades_df["stock_symbol"] == symbol]

            if len(stock_prices) < 20:
                print(f"Skipping {symbol}: insufficient data")
            
            # Create features
            stock_prices["price_diff_5"] = stock_prices["s_price"].pct_change(5).fillna(0)
            stock_prices["price_diff_10"] = stock_prices["s_price"].pct_change(10).fillna(0)
            stock_prices["avg_price"] = stock_prices["s_price"].rolling(30).mean().fillna(stock_prices["s_price"].mean())
            stock_prices["price_std"] = stock_prices["s_price"].rolling(30).std().fillna(0)
            stock_prices["trade_count"] = stock_prices["s_date"].apply(lambda d: len(stock_trades[stock_trades["purchase_date"] <= d.date()]))

            # Market trend features
            stock_prices["sp500_diff_5"] = stock_prices["sp500_price"].pct_change(5).fillna(0)
            stock_prices["sp500_diff_10"] = stock_prices["sp500_price"].pct_change(10).fillna(0)
            stock_prices["sp500_ma_30"] = stock_prices["sp500_price"].rolling(30).mean().fillna(stock_prices["sp500_price"].mean())
            # Target: 1 if price increases in 7 days, 0 otherwise
            stock_prices["target"] = (stock_prices["s_price"].shift(-7) > stock_prices["s_price"]).astype(int)
            stock_prices = stock_prices.dropna()

            if len(stock_prices) < 10:
                print(f"Skipping {symbol}: too few valid rows after preprocessing")
                continue

            # Split data
            X = stock_prices[["avg_price", "price_std", "trade_count", "price_diff_5", "price_diff_10",
                              "sp500_diff_5", "sp500_diff_10", "sp500_ma_30"]]
            y = stock_prices["target"]

            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size = .2, random_state = 42)

            # Train model
            model = RandomForestClassifier(n_estimators = 50, random_state = 42)
            model.fit(X_train, y_train)

            # Evaluate on test set
            y_pred = model.predict(X_test)
            accuracy = accuracy_score(y_test, y_pred)
            precision = precision_score(y_test, y_pred)
            recall = recall_score(y_test, y_pred)
            f1 = f1_score(y_test, y_pred)
            cm = confusion_matrix(y_test, y_pred)

            print(f"\nEvaluation for {symbol}:")
            print(f"Accuracy: {accuracy:.2f}")
            print(f"Precision: {precision:.2f}")
            print(f"Recall: {recall:.2f}")
            print(f"F1-Score: {f1:.2f}")
            print(f"Confusion Matrix: \n{cm}")

            # Simulate trading profit
            test_prices = stock_prices.iloc[-len(y_test):]["s_price"].values
            profit = 0
            for i, (pred, actual_price, prev_price) in enumerate(zip(y_pred, test_prices[1:], test_prices[:-1])):
                if pred == 1:
                    profit += (actual_price - prev_price)
                elif pred == 0:
                    profit += (prev_price - actual_price)
            print(f"Simulated profit for {symbol}: {profit:.2f}")

            results.append((symbol, accuracy, profit, model))

        # Summary
        avg_accuracy = sum(r[1] for r in results) / len(results) if results else 0
        total_profit = sum(r[2] for r in results)
        print(f"\nOverall Average Accuracy: {avg_accuracy:.2f}")
        print(f"Total Simulated Profit: {total_profit:.2f}")

        return results
    except Exception as e:
        print(f"Error in evaluation: {e}")
        raise
                                                                       


def predict_future_prices(results, prices_df, trades_df):

    """Predict future prices using trained models."""

    try:
        # Create SQLAlchemy Engine
        engine = create_engine(f"postgresql+psycopg2://{USER}:{PASSWORD}@{HOST}/{DATABASE}")
        print("Engine created successfully.")


        # Fetch S&P 500 data for recent dates
        start_date = prices_df["s_date"].max() - timedelta(days = 60)
        end_date = datetime.now().date() + timedelta(days = 1)
        sp500_df = fetch_market_index_data(start_date, end_date)
        if sp500_df.empty:
            print("Failed to fetch S&P 500 data for prediction. Proceeding without market trends.")
            sp500_df = pd.DataFrame(columns = ["s_date", "sp500_price"])
        
        prices_df["s_date"] = pd.to_datetime(prices_df["s_date"])
        sp500_df["s_date"] = pd.to_datetime(sp500_df["s_date"])
        future_dates = [pd.Timestamp(datetime.now().date() + timedelta(days = i)) for i in range (1,8)]

        prices_df = prices_df.merge(sp500_df, on = "s_date", how = "left")
        prices_df["sp500_price"] = prices_df["sp500_price"].ffill()

        with engine.connect() as conn:
            for symbol, _, _, model in results:
                stock_prices = prices_df[prices_df["stock_symbol"] == symbol].tail(30)
                stock_trades = trades_df[trades_df["stock_symbol"] == symbol]

                if len(stock_prices) < 10:
                    continue
                

                features = pd.DataFrame({
                    "avg_price": [stock_prices["s_price"].mean()],
                    "price_std": [stock_prices["s_price"].std() or 0],
                    "trade_count": [len(stock_trades)],
                    "price_diff_5": [stock_prices["s_price"].pct_change(5).iloc[-1] or 0],
                    "price_diff_10": [stock_prices["s_price"].pct_change(10).iloc[-1] or 0],
                    "sp500_diff_5": [stock_prices["sp500_price"].pct_change(5).iloc[-1] or 0],
                    "sp500_diff_10": [stock_prices["sp500_price"].pct_change(10).iloc[-1] or 0],
                    "sp500_ma_30": [stock_prices["sp500_price"].rolling(30).mean().iloc[-1] or stock_prices["sp500_price"].mean()]
                })

                last_price = stock_prices["s_price"].iloc[-1]
                
                for future_date in future_dates:
                    pred = model.predict(features)[0]
                    future_price = float(last_price * (1.01 if pred == 1 else .99))
                    date_str = future_date.strftime('%Y-%m-%d %H:%M:%S')
                    conn.execute(text("""
                        INSERT INTO stock_price (stock_symbol, s_date, s_price, is_prediction)
                        VALUES (:symbol, :date, :price, TRUE)
                        ON CONFLICT DO NOTHING
                    """), {"symbol": symbol, "date": date_str, "price": future_price})
                    conn.commit()
                print(f"Predicted prices for {symbol}")
        
    except Exception as e:
        print(f"Error in prediction: {e}")
        raise


if __name__== "__main__":
    # Evaluate and train models
    results = evaluate_model()

    # Predict future prices using trained models
    if results:
        engine = create_engine(f"postgresql+psycopg2://{USER}:{PASSWORD}@{HOST}/{DATABASE}")
        with engine.connect() as conn:
            prices_df = pd.read_sql_query(text("SELECT stock_symbol, s_date, s_price FROM stock_price WHERE is_prediction = FALSE"), conn)
            trades_df = pd.read_sql_query(text("SELECT stock_symbol, purchase_date, purchase_price FROM stock_purchases"), conn)
        predict_future_prices(results, prices_df, trades_df)
        
