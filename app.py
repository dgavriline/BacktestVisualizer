import requests
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import time

# Set up the app layout
st.set_page_config(page_title="Dip Buy Backtester", layout="wide")
st.title("📈 Dip Buy Strategy Backtest")

# Sidebar for configuration
st.sidebar.header("Configure Backtest")
yesterday = datetime.today() - timedelta(days=1)
start_date = st.sidebar.date_input("Start Date", pd.to_datetime("2015-01-03"))
end_date = st.sidebar.date_input("End Date", yesterday)
dip_threshold = st.sidebar.slider("Dip Threshold (%)", 1, 50, 15) / 100
gain_threshold = st.sidebar.slider("Gain Threshold (%)", 1, 50, 10) / 100
hold_days = st.sidebar.slider("Hold Period (business days)", 1, 30, 2)
dip_lookback_days = st.sidebar.slider("Dip Lookback Days", 1, 60, 15)
max_alloc = st.sidebar.number_input("Max Allocation per Trade ($)", 100, 1000000, 100000, step=100)
initial_cash = st.sidebar.number_input("Initial Cash ($)", 1000, 10000000, 1000000, step=1000)

# Run backtest
if st.sidebar.button("Run Backtest"):
    config = {
        "start": str(start_date),
        "end": str(end_date),
        "dip_threshold": dip_threshold,
        "hold_days": hold_days,
        "gain_threshold": gain_threshold,
        "initial_cash": initial_cash,
        "max_alloc_amount": max_alloc,
        "dip_lookback_days": dip_lookback_days
    }

    st.info("Submitting backtest task...")

    try:
        # Step 1: Submit job
        response = requests.post("https://backtest-api-app.icymoss-e1d44fae.eastus.azurecontainerapps.io/start-backtest", json=config)
        response.raise_for_status()
        task = response.json()
        task_id = task["task_id"]

        st.success(f"Task submitted. Task ID: {task_id}")
        with st.spinner("Running backtest (this may take a few minutes)..."):

            # Step 2: Poll the backend
            while True:
                poll_response = requests.get(f"https://backtest-api-app.icymoss-e1d44fae.eastus.azurecontainerapps.io/check-backtest/{task_id}")
                poll_response.raise_for_status()
                result = poll_response.json()

                if result.get("status") == "in_progress":
                    time.sleep(60)
                    continue
                elif result.get("status") == "error":
                    st.error("Backtest failed.")
                    st.stop()
                else:
                    break

        # Step 3: Display results
        st.subheader("Summary")
        st.json(result["summary"])

        df_trades = pd.DataFrame(result['trades'])

        def classify_trade(row):
            if row["exit_reason"] == "timeout" and row["pnl"] < 0:
                return "Timeout Loss"
            elif row["exit_reason"] == "timeout" and 0 <= row["pnl_pct"] > 0:
                return "Timeout Gain"
            else:
                return "Gain"

        df_trades["category"] = df_trades.apply(classify_trade, axis=1)

        # Pie chart of trade outcomes
        st.subheader("Trade Outcomes")
        fig_pie = px.pie(
            df_trades,
            names="category",
            title="Trade Outcomes",
            color="category",
            color_discrete_map={"Timeout Loss": "red", "Timeout Gain": "orange", "Gain": "green"}
        )
        st.plotly_chart(fig_pie, use_container_width=True)

        st.subheader("Account Value Over Time")
        fig_line = go.Figure()
        fig_line.add_trace(go.Scatter(
            x=result["balance_curve"]["dates"],
            y=result["balance_curve"]["balances"],
            mode='lines',
            name='Total Account Value',
            line=dict(color='blue')
        ))
        st.plotly_chart(fig_line, use_container_width=True)

        st.subheader("Trade Log")
        st.dataframe(df_trades)

        st.download_button("Download Trades CSV", df_trades.to_csv(index=False), "trades.csv")

    except requests.exceptions.RequestException as e:
        st.error(f"Backend error: {e}")
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")
