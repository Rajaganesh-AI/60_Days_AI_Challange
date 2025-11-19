# water_tracker.py
"""
Streamlit Water Intake Tracker
- Log daily water (ml).
- Show progress to a goal (default 3000 ml).
- Plot weekly hydration chart (last 7 days).
- Persist data to a local CSV file in the app folder.
"""

from pathlib import Path
from datetime import date, datetime, timedelta
import pandas as pd
import streamlit as st
import altair as alt

# ---------- Config ----------
DATA_FILE = Path("water_data.csv")
DEFAULT_GOAL_ML = 3000  # 3 L

st.set_page_config(page_title="Water Intake Tracker", layout="centered")

# ---------- Utilities ----------
def load_data() -> pd.DataFrame:
    if DATA_FILE.exists():
        df = pd.read_csv(DATA_FILE, parse_dates=["date"])
        # ensure correct dtypes
        df = df[["date", "amount_ml"]]
        df["date"] = pd.to_datetime(df["date"]).dt.normalize()
        df["amount_ml"] = df["amount_ml"].astype(int)
        return df
    else:
        # empty dataframe
        return pd.DataFrame(columns=["date", "amount_ml"])

def save_data(df: pd.DataFrame) -> None:
    # ensure proper format
    df_out = df.copy()
    df_out["date"] = pd.to_datetime(df_out["date"]).dt.date
    df_out.to_csv(DATA_FILE, index=False)

def add_entry(entry_date: date, amount_ml: int) -> None:
    df = load_data()
    new = pd.DataFrame({"date": [pd.to_datetime(entry_date)], "amount_ml": [int(amount_ml)]})
    df = pd.concat([df, new], ignore_index=True)
    save_data(df)

def clear_data() -> None:
    if DATA_FILE.exists():
        DATA_FILE.unlink()

def get_daily_totals(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["date", "total_ml"])
    totals = df.groupby(df["date"].dt.normalize())["amount_ml"].sum().reset_index()
    totals.columns = ["date", "total_ml"]
    totals["date"] = pd.to_datetime(totals["date"]).dt.normalize()
    return totals

def last_n_days_df(totals: pd.DataFrame, n: int = 7) -> pd.DataFrame:
    today = pd.to_datetime(date.today())
    dates = pd.date_range(end=today, periods=n)
    df_full = pd.DataFrame({"date": dates})
    if totals.empty:
        df_full["total_ml"] = 0
    else:
        merged = df_full.merge(totals, on="date", how="left")
        merged["total_ml"] = merged["total_ml"].fillna(0).astype(int)
        df_full = merged
    return df_full

# ---------- UI ----------
st.title("💧 Water Intake Tracker")

# Goal selector (user can change)
goal_ml = st.number_input("Daily goal (ml)", min_value=100, max_value=100000, value=DEFAULT_GOAL_ML, step=100)

st.markdown("---")
st.subheader("Log water")

col1, col2, col3 = st.columns([2,2,1])
with col1:
    entry_amount = st.number_input("Amount (ml)", min_value=1, value=250, step=50, format="%d")
with col2:
    entry_date = st.date_input("Date", value=date.today())
with col3:
    add_btn = st.button("Add")

if add_btn:
    add_entry(entry_date, entry_amount)
    st.success(f"Logged {entry_amount} ml for {entry_date.isoformat()}")

# Load data and compute totals
df_raw = load_data()
totals = get_daily_totals(df_raw)
today = pd.to_datetime(date.today())
today_total = int(totals.loc[totals["date"] == today, "total_ml"].sum()) if not totals.empty else 0

st.subheader("Today's progress")
col_a, col_b = st.columns([3,1])
with col_a:
    st.metric("Total today (ml)", f"{today_total} ml", delta=f"{today_total - (goal_ml if today_total >= goal_ml else 0)}")
    # progress bar (0..1)
    progress_val = min(today_total / float(goal_ml) if goal_ml else 0.0, 1.0)
    st.progress(progress_val)
    st.caption(f"{int(progress_val * 100)}% of {goal_ml} ml goal")
with col_b:
    # simple visual: circular-like indicator using markdown (keeps it simple)
    percent = int(progress_val * 100)
    st.write("Status")
    if percent >= 100:
        st.success("🎉 Goal reached")
    elif percent >= 75:
        st.info("Almost there")
    else:
        st.write(f"{percent}%")

st.markdown("---")
st.subheader("Weekly hydration (last 7 days)")

# Build last 7 days dataset
last7 = last_n_days_df(totals, n=7)

# Altair chart (bar + line)
base = alt.Chart(last7).encode(
    x=alt.X("date:T", title="Date", axis=alt.Axis(format="%b %d")),
)

bars = base.mark_bar().encode(
    y=alt.Y("total_ml:Q", title="Total (ml)")
)

goal_rule = alt.Chart(pd.DataFrame({"goal":[goal_ml]})).mark_rule(color="red", strokeDash=[4,4]).encode(
    y="goal:Q"
)

text = base.mark_text(dy=-10).encode(
    text=alt.Text("total_ml:Q")
)

chart = (bars + goal_rule + text).properties(width=700, height=350)
st.altair_chart(chart, use_container_width=True)

st.markdown("---")
st.subheader("Raw log & management")

if df_raw.empty:
    st.info("No entries yet. Use the form above to log water.")
else:
    # Show complete log sorted desc
    df_show = df_raw.copy()
    df_show["date"] = pd.to_datetime(df_show["date"]).dt.date
    df_show = df_show.sort_values(by="date", ascending=False).reset_index(drop=True)
    st.write("All entries (most recent first):")
    st.dataframe(df_show)

    # Option to download CSV
    csv = df_raw.copy()
    csv["date"] = pd.to_datetime(csv["date"]).dt.date
    csv_bytes = csv.to_csv(index=False).encode("utf-8")
    st.download_button("Download CSV", data=csv_bytes, file_name="water_data.csv", mime="text/csv")

st.write("")
if st.button("Clear all data"):
    clear_data()
    st.warning("All data cleared.")
    st.rerun()

st.markdown("---")
st.caption("Tip: log whenever you drink. Multiple logs per day will be combined to compute the daily total.")
