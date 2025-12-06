import streamlit as st
import pandas as pd
from pathlib import Path

from utils import load_today_signals, load_historical_signals, load_weekly_watchlist
from charts import plot_signal_chart

st.set_page_config(page_title="Swing System - Today's Signals", layout="wide")

st.title("📈 Swing System — Today's Signals")

st.write(
    "This is your Week 9 dashboard. Once the signal pipeline is wired, "
    "this page will show today's swing candidates and historical breakouts."
)

# ---------------------------------------------------------
# SIDEBAR: VIEW MODE
# ---------------------------------------------------------
st.sidebar.header("View")

view_mode = st.sidebar.radio("View", ["Today", "Historical", "Watchlist"], index=0)

# ---------------------------------------------------------
# LOAD DATA BASED ON VIEW MODE
# ---------------------------------------------------------
reports_dir = Path("reports")

if view_mode == "Today":
    signals_path = reports_dir / "today_signals.csv"
    signals_df = load_today_signals(allow_demo=True)
    csv_exists = signals_path.exists() and signals_path.stat().st_size > 0

    if csv_exists:
        mode_text = "LIVE DATA (today's scan or fallback)"
        mode_icon = "✅"
    else:
        mode_text = "DEMO MODE (static examples)"
        mode_icon = "🧪"

    st.markdown(f"**Mode:** {mode_icon} {mode_text}")

    if not csv_exists:
        st.info(
            "No real swing scan file was found, so you're seeing demo examples (AAPL/MSFT). "
            "Run `python -m src.run_today_signals` to generate live data from your universe."
        )

elif view_mode == "Historical":
    signals_path = reports_dir / "historical_signals.csv"
    signals_df = load_historical_signals()
    csv_exists = signals_path.exists() and signals_path.stat().st_size > 0 and not signals_df.empty

    mode_text = "HISTORICAL BREAKOUTS (backtest-style signals)"
    mode_icon = "📚"
    st.markdown(f"**Mode:** {mode_icon} {mode_text}")

    if not csv_exists:
        st.warning(
            "No historical breakout file was found or it is empty.\n\n"
            "Run `python -m src.run_historical_breakouts` to generate "
            "historical signals from your processed data."
        )
        st.stop()

else:  # Watchlist
    signals_path = reports_dir / "weekly_watchlist.csv"
    signals_df = load_weekly_watchlist()
    csv_exists = signals_path.exists() and signals_path.stat().st_size > 0 and not signals_df.empty

    mode_text = "WEEKLY WATCHLIST (top A/B setups)"
    mode_icon = "⭐"
    st.markdown(f"**Mode:** {mode_icon} {mode_text}")

    if not csv_exists:
        st.info(
            "No weekly_watchlist.csv was found or it is empty.\n\n"
            "Run:\n"
            "`python -m src.run_today_signals` then\n"
            "`python -m src.run_weekly_watchlist`\n"
            "to generate this week's watchlist."
        )
        st.stop()

# Ensure 'date' is a datetime if present
if "date" in signals_df.columns:
    signals_df["date"] = pd.to_datetime(signals_df["date"], errors="coerce")

# ---------------------------------------------------------
# SIDEBAR FILTERS (COMMON)
# ---------------------------------------------------------
st.sidebar.header("Filters")

min_score = st.sidebar.slider("Minimum Score", 0, 100, 70)

min_price = st.sidebar.number_input("Min Price ($)", min_value=0.0, value=5.0, step=0.5)
max_price = st.sidebar.number_input("Max Price ($)", min_value=0.0, value=500.0, step=1.0)

# Ticker filter (both modes)
tickers = sorted(signals_df["ticker"].unique()) if not signals_df.empty else []
ticker_filter = st.sidebar.multiselect(
    "Tickers",
    options=tickers,
    default=tickers,
)

grade_filter = st.sidebar.multiselect(
    "Risk Grade",
    options=sorted(signals_df["grade"].unique()) if not signals_df.empty else [],
    default=list(signals_df["grade"].unique()) if not signals_df.empty else [],
)

setup_options = ["All"] + (sorted(signals_df["setup"].unique()) if not signals_df.empty else [])
setup_filter = st.sidebar.selectbox("Setup Type", options=setup_options)

sort_by_options = ["score", "rr"]
if view_mode == "Historical" and "date" in signals_df.columns:
    sort_by_options.insert(0, "date")

sort_by = st.sidebar.selectbox("Sort by", options=sort_by_options)

# Extra filters for Historical mode: date range
if view_mode == "Historical" and not signals_df.empty and "date" in signals_df.columns:
    min_date = signals_df["date"].min().date()
    max_date = signals_df["date"].max().date()
    start_date, end_date = st.sidebar.date_input(
        "Date range",
        (min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )

# ---------------------------------------------------------
# APPLY FILTERS
# ---------------------------------------------------------
filtered = signals_df.copy()

if not filtered.empty:
    filtered = filtered[filtered["score"] >= min_score]
    filtered = filtered[(filtered["entry"] >= min_price) & (filtered["entry"] <= max_price)]

    if ticker_filter:
        filtered = filtered[filtered["ticker"].isin(ticker_filter)]

    if grade_filter:
        filtered = filtered[filtered["grade"].isin(grade_filter)]

    if setup_filter != "All":
        filtered = filtered[filtered["setup"] == setup_filter]

    if view_mode == "Historical" and "date" in filtered.columns:
        mask = (filtered["date"].dt.date >= start_date) & (filtered["date"].dt.date <= end_date)
        filtered = filtered[mask]

    ascending = False
    if sort_by == "date":
        ascending = False  # newest first

    filtered = filtered.sort_values(by=sort_by, ascending=ascending)

# ---------------------------------------------------------
# DISPLAY TABLE
# ---------------------------------------------------------
if view_mode == "Today":
    label = "Today's Candidates"
elif view_mode == "Historical":
    label = "Historical Breakouts"
else:  # Watchlist
    label = "This Week's Watchlist"

st.subheader(f"🧾 {label}")

if filtered.empty:
    st.warning("No setups match your filters.")
else:
    # Show the filtered signals table
    st.dataframe(filtered, width="stretch", hide_index=True)
    st.caption(f"{len(filtered)} candidates shown after filters.")

    # -----------------------------------------------------
    # SIMPLE SIGNAL CHART SECTION (ONE CHART AT A TIME)
    # -----------------------------------------------------
    st.subheader("📊 Signal chart")

    # Work on a copy with a clean index so we can select by label
    filtered_for_select = filtered.reset_index(drop=True).copy()

    # Create a simple text label for the dropdown
    if view_mode == "Today":
        # No date column, just show ticker + setup + grade + entry
        def _make_label(row):
            try:
                entry_str = f"{float(row['entry']):.2f}"
            except Exception:
                entry_str = str(row["entry"])
            return f"{row['ticker']} · {row['setup']} · grade {row['grade']} · entry {entry_str}"
    else:
        # Historical view includes date
        def _make_label(row):
            date_part = ""
            if "date" in row and pd.notna(row["date"]):
                try:
                    date_part = pd.to_datetime(row["date"]).date().isoformat()
                except Exception:
                    date_part = str(row["date"])
            try:
                entry_str = f"{float(row['entry']):.2f}"
            except Exception:
                entry_str = str(row["entry"])
            return f"{date_part} · {row['ticker']} · {row['setup']} · grade {row['grade']} · entry {entry_str}"

    filtered_for_select["__label__"] = filtered_for_select.apply(_make_label, axis=1)

    selected_label = st.selectbox(
        "Pick a signal to view its chart:",
        options=filtered_for_select["__label__"].tolist(),
    )

    # Find the selected row
    selected_row = filtered_for_select.loc[
        filtered_for_select["__label__"] == selected_label
    ].iloc[0]

    # Build and render the chart
    fig = plot_signal_chart(
        ticker=selected_row["ticker"],
        signal_row=selected_row,
        view_mode=view_mode,
        lookback=90,  # simple fixed window
    )

    if fig is None:
        st.warning(
            "No price data available for this ticker in data_processed/. "
            "Make sure data_processed/{TICKER}.csv exists."
        )
    else:
        st.pyplot(fig, clear_figure=True)

        # ---------------------------------------------
        # Simple numeric summary for the selected signal
        # ---------------------------------------------
        ticker = selected_row.get("ticker", "")
        setup = selected_row.get("setup", "")
        grade = selected_row.get("grade", "")
        score = selected_row.get("score", "")

        date_str = ""
        if view_mode == "Historical" and "date" in selected_row.index:
            try:
                date_val = pd.to_datetime(selected_row["date"])
                date_str = date_val.date().isoformat()
            except Exception:
                date_str = str(selected_row["date"])

        # Prices
        def _to_float(val):
            try:
                return float(val)
            except Exception:
                return None

        entry = _to_float(selected_row.get("entry"))
        stop = _to_float(selected_row.get("stop"))
        target = _to_float(selected_row.get("target"))
        rr_col = _to_float(selected_row.get("rr"))

        risk = None
        reward = None
        rr_calc = None

        if entry is not None and stop is not None:
            risk = entry - stop
        if entry is not None and target is not None:
            reward = target - entry
        if risk not in (None, 0) and reward is not None:
            rr_calc = reward / risk

        # Build a short text block
        header_bits = []
        if date_str:
            header_bits.append(date_str)
        if ticker:
            header_bits.append(str(ticker))
        if setup:
            header_bits.append(str(setup))
        if grade:
            header_bits.append(f"grade {grade}")
        if score not in ("", None):
            try:
                header_bits.append(f"score {float(score):.1f}")
            except Exception:
                header_bits.append(f"score {score}")

        st.markdown("### 📌 Signal summary")

        st.markdown("**" + " · ".join(header_bits) + "**")

        lines = []

        if entry is not None:
            lines.append(f"- **Entry:** {entry:.2f}")
        if stop is not None:
            lines.append(f"- **Stop:** {stop:.2f}")
        if target is not None:
            lines.append(f"- **Target:** {target:.2f}")
        if risk is not None:
            lines.append(f"- **Risk per share:** {risk:.2f}")
        if reward is not None:
            lines.append(f"- **Reward per share:** {reward:.2f}")
        if rr_col is not None:
            lines.append(f"- **RR (from signal):** {rr_col:.2f}")
        if rr_calc is not None:
            lines.append(f"- **RR (calc target/stop):** {rr_calc:.2f}")

        if lines:
            st.markdown("\n".join(lines))

# Footer tips
if view_mode == "Today":
    st.caption(
        "Tip: Run `python -m src.run_today_signals` after updating data to refresh this list."
    )
else:
    st.caption(
        "Tip: Run `python -m src.run_historical_breakouts` whenever you update features "
        "to refresh the historical signals dataset."
    )
