"""
mt5_data.py — CLI tool for pulling data from a running MT5 terminal.

Usage:
  python mt5_data.py ticks  <SYMBOL> <N>               # last N ticks
  python mt5_data.py rates  <SYMBOL> <TF> <N>          # last N OHLCV bars
  python mt5_data.py tick   <SYMBOL>                   # latest single tick
  python mt5_data.py symbols                           # list visible symbols
  python mt5_data.py account                           # account info

Timeframes: M1 M5 M15 M30 H1 H4 D1 W1 MN1
Output: JSON to stdout (pipe to file or parse in scripts)

Examples:
  python mt5_data.py tick EURUSD
  python mt5_data.py rates EURUSD M5 100
  python mt5_data.py ticks XAUUSD 500
"""

import sys
import json
import MetaTrader5 as mt5
from datetime import datetime, timezone

def _ts(unix):
    return datetime.fromtimestamp(unix, timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")

TF_MAP = {
    "M1":  mt5.TIMEFRAME_M1,
    "M5":  mt5.TIMEFRAME_M5,
    "M15": mt5.TIMEFRAME_M15,
    "M30": mt5.TIMEFRAME_M30,
    "H1":  mt5.TIMEFRAME_H1,
    "H4":  mt5.TIMEFRAME_H4,
    "D1":  mt5.TIMEFRAME_D1,
    "W1":  mt5.TIMEFRAME_W1,
    "MN1": mt5.TIMEFRAME_MN1,
}


def connect():
    if not mt5.initialize():
        print(json.dumps({"error": f"MT5 init failed: {mt5.last_error()}"}))
        sys.exit(1)


def disconnect():
    mt5.shutdown()


def cmd_account():
    connect()
    a = mt5.account_info()
    t = mt5.terminal_info()
    result = {
        "terminal": t.name,
        "login":    a.login,
        "server":   a.server,
        "currency": a.currency,
        "balance":  a.balance,
        "equity":   a.equity,
        "margin":   a.margin,
        "leverage": a.leverage,
    }
    disconnect()
    print(json.dumps(result, indent=2))


def cmd_symbols():
    connect()
    syms = [s.name for s in mt5.symbols_get() if s.visible]
    disconnect()
    print(json.dumps(syms, indent=2))


def cmd_tick(symbol):
    connect()
    tick = mt5.symbol_info_tick(symbol)
    if tick is None:
        print(json.dumps({"error": f"No tick for {symbol}: {mt5.last_error()}"}))
        disconnect()
        sys.exit(1)
    result = {
        "symbol": symbol,
        "time":   _ts(tick.time),
        "bid":    tick.bid,
        "ask":    tick.ask,
        "last":   tick.last,
        "volume": tick.volume,
        "spread": round((tick.ask - tick.bid) * 10000, 1),  # pips (4-digit pairs)
    }
    disconnect()
    print(json.dumps(result, indent=2))


def cmd_ticks(symbol, n):
    connect()
    ticks = mt5.copy_ticks_from(symbol, datetime.now(timezone.utc), n, mt5.COPY_TICKS_ALL)
    if ticks is None or len(ticks) == 0:
        print(json.dumps({"error": f"No ticks for {symbol}: {mt5.last_error()}"}))
        disconnect()
        sys.exit(1)
    result = [
        {
            "time": _ts(t["time"]),
            "bid":  float(t["bid"]),
            "ask":  float(t["ask"]),
            "last": float(t["last"]),
            "vol":  int(t["volume"]),
        }
        for t in ticks
    ]
    disconnect()
    print(json.dumps(result, indent=2))


def cmd_rates(symbol, tf_str, n):
    tf = TF_MAP.get(tf_str.upper())
    if tf is None:
        print(json.dumps({"error": f"Unknown timeframe: {tf_str}. Use: {list(TF_MAP.keys())}"}))
        sys.exit(1)
    connect()
    rates = mt5.copy_rates_from_pos(symbol, tf, 0, n)
    if rates is None or len(rates) == 0:
        print(json.dumps({"error": f"No rates for {symbol} {tf_str}: {mt5.last_error()}"}))
        disconnect()
        sys.exit(1)
    result = [
        {
            "time":   _ts(r["time"]),
            "open":   float(r["open"]),
            "high":   float(r["high"]),
            "low":    float(r["low"]),
            "close":  float(r["close"]),
            "volume": int(r["tick_volume"]),
        }
        for r in rates
    ]
    disconnect()
    print(json.dumps(result, indent=2))


def usage():
    print(__doc__)
    sys.exit(0)


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        usage()

    cmd = args[0].lower()

    if cmd == "account":
        cmd_account()
    elif cmd == "symbols":
        cmd_symbols()
    elif cmd == "tick" and len(args) == 2:
        cmd_tick(args[1].upper())
    elif cmd == "ticks" and len(args) == 3:
        cmd_ticks(args[1].upper(), int(args[2]))
    elif cmd == "rates" and len(args) == 4:
        cmd_rates(args[1].upper(), args[2].upper(), int(args[3]))
    else:
        usage()
