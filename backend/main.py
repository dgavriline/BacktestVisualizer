from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from models import BacktestResult, Summary, Trade, BalanceCurve, BacktestRequest
from bot_logic import DipBuyBot

app = FastAPI(title="Backtest Bot API", version="1.0")

bot = DipBuyBot()

@app.post("/run-backtest", response_model=BacktestResult)
def run_backtest(request: BacktestRequest):
    try:
        result = bot.run_backtest(request.dict())

        # Log summary to console
        summary = result.get("summary", {})
        print("\nBacktest Summary:")
        for k, v in summary.items():
            print(f"  {k}: {v}")

        return result
    except Exception as e:
        print("Backend error:", e)
        return JSONResponse(status_code=500, content={"error": str(e)})
