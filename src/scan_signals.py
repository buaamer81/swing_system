# src/scan_signals.py

from src.signals.engine import scan_universe


def main():
    signals = scan_universe()

    if not signals:
        print("No signals found.")
        return

    print("\n=== Swing Breakout Signals (v0.1) ===")
    print(
        f"{'Ticker':<6} {'Setup':<9} {'Score':>5} "
        f"{'Close':>10} {'Entry':>10} {'Stop':>10} {'Target':>10} {'R':>4}"
    )
    print("-" * 70)
    for s in signals:
        print(
            f"{s.ticker:<6} {s.setup:<9} {s.score:5.1f} "
            f"{s.close:10.2f} {s.entry:10.2f} {s.stop:10.2f} {s.target:10.2f} {s.r_multiple:4.1f}"
        )
    print("\nNotes:")
    for s in signals:
        print(f"{s.ticker}: {s.notes}")


if __name__ == "__main__":
    main()
