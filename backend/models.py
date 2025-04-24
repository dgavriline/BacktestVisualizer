from typing import List, Literal
from pydantic import BaseModel
from typing import Literal

class Trade(BaseModel):
    ticker: str
    entry_date: str  # formatted as YYYY-MM-DD
    exit_date: str
    entry_price: float
    exit_price: float
    pnl: float
    pnl_pct: float
    exit_reason: Literal["gain", "timeout"]
    category: Literal["Gain", "Timeout Gain", "Timeout Loss"]

class BalanceCurve(BaseModel):
    dates: List[str]
    balances: List[float]

class Summary(BaseModel):
    final_balance: float
    total_return_pct: float
    num_trades: int

class BacktestResult(BaseModel):
    balance_curve: BalanceCurve
    trades: List[Trade]
    summary: Summary

class BacktestRequest(BaseModel):
    start: str
    end: str
    dip_threshold: float
    gain_threshold: float
    hold_days: int
    initial_cash: float
    max_alloc_amount: float
    dip_lookback_days: int


class TaskStatus(BaseModel):
    task_id: str
    status: Literal["in_progress", "completed", "error"]