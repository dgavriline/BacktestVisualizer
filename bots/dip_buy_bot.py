import yfinance as yf
import pandas as pd
import requests
from datetime import timedelta
from io import StringIO
import plotly.graph_objects as go
import plotly.express as px


class DipBuyBot:
    def run_backtest(self, config: dict) -> dict:
        start = config.get("start", "2022-01-01")
        end = config.get("end", "2025-04-01")
        dip_pct = config.get("dip_threshold", 0.03)
        hold_days = config.get("hold_days", 10)
        gain_threshold = config.get("gain_threshold", 0.10)
        initial_cash = config.get("initial_cash", 10000)
        max_alloc_amount = config.get("max_alloc_amount", 500)
        dip_lookback_days = config.get("dip_lookback_days", 30)

        # Load historical S&P 500 membership data
        hist_df = pd.read_csv("S&P 500 Historical Components Mar 10 2025.csv")
        hist_df["date"] = pd.to_datetime(hist_df["date"])
        hist_df.set_index("date", inplace=True)

        def get_constituents_on_date(target_date):
            valid_dates = hist_df.index[hist_df.index <= target_date]
            if len(valid_dates) == 0:
                return set()
            most_recent_date = valid_dates.max()
            tickers = hist_df.loc[most_recent_date, "tickers"]
            return set(tickers.split(","))

        all_tickers = set()
        for tickers in hist_df["tickers"]:
            all_tickers.update(tickers.split(","))

        cash = initial_cash
        positions = []
        trade_log = {}
        balance_by_date = {}
        cash_by_date = {}
        positions_by_date = {}

        # Download and process historical price data for all tickers in the history
        price_data = {}
        for ticker in all_tickers:
            df = yf.download(ticker, start=start, end=end, auto_adjust=True, progress=False)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.droplevel(1)
            if df.empty or "Close" not in df.columns:
                continue
            df["Peak"] = df["Close"].rolling(window=dip_lookback_days, min_periods=1).max()
            df["Dip"] = (df["Peak"] - df["Close"]) / df["Peak"]
            price_data[ticker] = df

        all_dates = sorted(set().union(*[df.index for df in price_data.values()]))

        for date in all_dates:
            current_constituents = get_constituents_on_date(date)

            # SELL logic
            new_positions = []
            for position in positions:
                ticker = position["ticker"]
                if ticker not in price_data or date not in price_data[ticker].index:
                    new_positions.append(position)
                    continue

                price = price_data[ticker].loc[date]["Close"]
                days_held = (date - position["entry_date"]).days
                gain = (price - position["entry_price"]) / position["entry_price"]

                if gain >= gain_threshold or days_held >= hold_days:
                    cash += position["shares"] * price
                    pnl = (price - position["entry_price"]) * position["shares"]
                    reason = "gain" if gain >= gain_threshold else "timeout"
                    trade_log.setdefault(ticker, []).append({
                        "ticker": ticker,
                        "entry_date": position["entry_date"].strftime("%Y-%m-%d"),
                        "exit_date": date.strftime("%Y-%m-%d"),
                        "entry_price": position["entry_price"],
                        "exit_price": price,
                        "pnl": pnl,
                        "pnl_pct": (price - position["entry_price"]) / position["entry_price"] * 100,
                        "exit_reason": reason
                    })
                else:
                    new_positions.append(position)
            positions = new_positions

            # BUY logic
            for ticker in current_constituents:
                if ticker not in price_data:
                    continue
                df = price_data[ticker]
                if any(pos["ticker"] == ticker for pos in positions):
                    continue
                if date not in df.index:
                    continue
                if df.loc[date]["Dip"] >= dip_pct:
                    price = df.loc[date]["Close"]
                    alloc_cash = min(cash, max_alloc_amount)
                    shares = int(alloc_cash // price)
                    if shares > 0:
                        cash -= shares * price
                        positions.append({
                            "ticker": ticker,
                            "entry_date": date,
                            "entry_price": price,
                            "shares": shares
                        })

            # Track balance
            pos_val = 0
            for position in positions:
                ticker = position["ticker"]
                if ticker in price_data and date in price_data[ticker].index:
                    price = price_data[ticker].loc[date]["Close"]
                    pos_val += position["shares"] * price

            total_balance = cash + pos_val
            balance_by_date[date] = total_balance
            cash_by_date[date] = cash
            positions_by_date[date] = pos_val

        sorted_dates = sorted(balance_by_date)
        balance_curve = [balance_by_date[d] for d in sorted_dates]
        flat_trades = [t for trades in trade_log.values() for t in trades]

        # Export trades to CSV
        df_trades = pd.DataFrame(flat_trades)
        df_trades.to_csv("backtest_trades.csv", index=False)

        # Pie chart of trade outcomes
        def classify_trade(row):
            if row["exit_reason"] == "timeout" and row["pnl"] < 0:
                return "Timeout Loss"
            elif row["exit_reason"] == "timeout" and 0 <= row["pnl_pct"] > 0:
                return "Timeout Gain"
            else:
                return "Gain"

        df_trades["category"] = df_trades.apply(classify_trade, axis=1)

        fig_pie = px.pie(df_trades, names="category", title="Trade Outcomes", color="category",
                         color_discrete_map={"Timeout Loss": "red", "Timeout Gain": "orange", "Gain": "green"})
        fig_pie.show()

        # Plotly graph of account value, cash, and positions
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=sorted_dates, y=balance_curve, mode='lines', name='Total Account Value', line=dict(color='blue')))
        fig.add_trace(go.Scatter(x=sorted_dates, y=[cash_by_date[d] for d in sorted_dates], mode='lines', name='Cash', line=dict(color='green')))
        fig.add_trace(go.Scatter(x=sorted_dates, y=[positions_by_date[d] for d in sorted_dates], mode='lines', name='Positions Value', line=dict(color='orange')))
        fig.update_layout(title='Account Value, Cash & Positions Over Time', xaxis_title='Date', yaxis_title='USD')
        fig.show()

        return {
            "balance_curve": {
                "dates": [d.strftime("%Y-%m-%d") for d in sorted_dates],
                "balances": balance_curve
            },
            "trades": flat_trades,
            "summary": {
                "final_balance": balance_curve[-1] if balance_curve else initial_cash,
                "total_return_pct": ((balance_curve[-1] / initial_cash - 1) * 100) if balance_curve else 0,
                "num_trades": len(flat_trades)
            }
        }

    # def get_sp500_tickers(self) -> list:
    #     url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
    #     response = requests.get(url)
    #     table = pd.read_html(StringIO(response.text))
    #     tickers = table[0]['Symbol'].tolist()
    #     return [symbol.replace('.', '-') for symbol in tickers]
