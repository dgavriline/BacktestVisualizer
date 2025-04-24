from pathlib import Path
from uuid import uuid4
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from models import BacktestResult, Summary, Trade, BalanceCurve, BacktestRequest
from bot_logic import DipBuyBot

app = FastAPI(title="Backtest Bot API", version="1.0")

bot = DipBuyBot()
tasks = {}  # Dictionary to hold in-progress and completed tasks

@app.post("/start-backtest")
def start_backtest(request: BacktestRequest, background_tasks: BackgroundTasks):
    task_id = str(uuid4())
    tasks[task_id] = {
        "status": "in_progress",
        "request": request.dict(),
        "result": None,
        "error": None
    }

    def run():
        try:
            result = bot.run_backtest(tasks[task_id]["request"])
            tasks[task_id]["result"] = result
            tasks[task_id]["status"] = "complete"

            summary = result.get("summary", {})
            print(f"\nBacktest Summary for {task_id}:")
            for k, v in summary.items():
                print(f"  {k}: {v}")

        except Exception as e:
            print(f"Error in task {task_id}: {e}")
            tasks[task_id]["status"] = "error"
            tasks[task_id]["error"] = str(e)

    background_tasks.add_task(run)

    print(f"Started backtest with task_id: {task_id}")
    return {"task_id": task_id, "status": "started"}

@app.get("/check-backtest/{task_id}")
def check_backtest(task_id: str):
    task = tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task ID not found")

    if task["status"] == "complete":
        return task["result"]
    elif task["status"] == "error":
        return {"status": "error", "message": task["error"]}
    else:
        return {"status": "in_progress"}
