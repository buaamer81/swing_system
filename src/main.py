from src.config import UNIVERSE
from src.data import placeholder_data
from src.signals import placeholder_signals
from src.backtest import placeholder_backtest
from src.analysis import placeholder_analysis


def main():
    print("=== Personal Swing Trading System ===")
    print(f"Universe: {UNIVERSE}")

    print("Checking modules...")
    print("Data      :", placeholder_data())
    print("Signals   :", placeholder_signals())
    print("Backtest  :", placeholder_backtest())
    print("Analysis  :", placeholder_analysis())

    print("All good. Skeleton is ready.")


if __name__ == "__main__":
    main()
