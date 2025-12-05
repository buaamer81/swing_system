# src/build_features.py

from src.signals.features import build_features_for_universe


def main():
    build_features_for_universe(save=True)


if __name__ == "__main__":
    main()
