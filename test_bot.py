# test_bot.py

from bots.dip_buy_bot import DipBuyBot

bot = DipBuyBot()

config = {
    "start": "2022-01-03",
    "end": "2025-04-12",
    "dip_threshold": 0.10,
    "gain_threshold": 0.10,
    "hold_days": 10,
    "initial_cash": 1000000,
    "max_alloc_amount": 75000,
    "dip_lookback_days": 2
}

result = bot.run_backtest(config)

print("\n=== Summary ===")
print(result["summary"])

print("\n=== Sample Trades ===")
for trade in result["trades"][:5]:
    print(trade)

print("\n=== Balance Curve (last 5 points) ===")
dates = result["balance_curve"]["dates"][-5:]
balances = result["balance_curve"]["balances"][-5:]
for d, b in zip(dates, balances):
    print(f"{d}: ${b:.2f}")
