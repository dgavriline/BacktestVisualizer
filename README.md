# BacktestVisualizer
A tool that will let users backtest and visualize algotrading strategies

VENV startup: 

source $(poetry env info --path)/bin/activate

How to test: 

1) from root directory:
# Build the container
docker build -t backtest-api . -f backend/Dockerfile

# Run the container
docker run -p 8000:8000 backtest-api

2) http://localhost:8000/docs#/default/run_backtest_run_backtest_post

- "Try it out" button
- paste in test JSON:

{
  "start": "2022-01-03",
  "end": "2025-04-01",
  "dip_threshold": 0.25,
  "gain_threshold": 0.10,
  "hold_days": 5,
  "initial_cash": 1000000,
  "max_alloc_amount": 10000,
  "dip_lookback_days": 30
}

3) for end to end test: 
- run docker container
- split terminal
- in second terminal run: 
    streamlit run app.py

