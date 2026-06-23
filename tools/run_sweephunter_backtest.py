"""Drive one headless MT5 Strategy Tester run for SweepHunter; return the EA ledger path."""
from __future__ import annotations
import os, subprocess, time
from pathlib import Path

FTMO_DATA = Path(os.environ["APPDATA"]) / "MetaQuotes/Terminal/81A933A9AFC5DE3C23B15CAB19C63850"
TERMINAL = Path(r"C:\Program Files\FTMO Global Markets MT5 Terminal\terminal64.exe")

def build_tester_ini(symbol, from_date, to_date, expert, set_file, report, label):
    return "\n".join([
        "[Tester]", f"Expert={expert}", f"Symbol={symbol}", "Period=M1", "Model=1",
        "Optimization=0", f"FromDate={from_date}", f"ToDate={to_date}", "Deposit=10000",
        "Currency=USD", "Leverage=1:100", f"Report={report}", "ReplaceReport=1",
        "ShutdownTerminal=1", f"ExpertParameters={set_file}", "",
    ])

def ledger_path_for(data_dir, label):
    return str(Path(data_dir).parent / "Common" / "Files" / "SweepHunter" / f"ledger_{label}.csv")

def run(symbol, from_date, to_date, set_file, label, data_dir=FTMO_DATA, terminal=TERMINAL, timeout=1800):
    report = str(Path(data_dir) / f"sh_report_{label}.htm")
    ini = build_tester_ini(symbol, from_date, to_date, "SweepHunter\\SweepHunter_EA.ex5", set_file, report, label)
    ini_path = Path(data_dir) / f"sh_tester_{label}.ini"
    ini_path.write_text(ini, encoding="utf-16")
    tester_presets = Path(data_dir) / "MQL5" / "Profiles" / "Tester"
    tester_presets.mkdir(parents=True, exist_ok=True)
    src_set = Path("tested-strategies/SweepHunter/mt5/Presets") / set_file
    lines = [ln for ln in src_set.read_text().splitlines() if not ln.strip().startswith("InpLedgerLabel=")]
    lines.append(f"InpLedgerLabel={label}")
    (tester_presets / set_file).write_text("\n".join(lines) + "\n", encoding="utf-8")
    ledger = ledger_path_for(data_dir, label)
    if os.path.exists(ledger): os.remove(ledger)
    subprocess.run([str(terminal), f"/config:{ini_path}"], check=False, timeout=timeout)
    for _ in range(60):
        if os.path.exists(ledger): break
        time.sleep(1)
    if not os.path.exists(ledger):
        raise RuntimeError(f"no ledger produced for {label} — check {report}")
    return ledger

if __name__ == "__main__":
    import sys
    sym = sys.argv[1] if len(sys.argv) > 1 else "XAUUSD"
    frm = sys.argv[2] if len(sys.argv) > 2 else "2024.01.01"
    to  = sys.argv[3] if len(sys.argv) > 3 else "2024.06.30"
    setf = sys.argv[4] if len(sys.argv) > 4 else "SweepHunter_smoke.set"
    print(run(sym, frm, to, setf, "smoke"))
