import os
import datetime
import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
VISUAL_OUTPUT = os.path.join(ROOT, "visual_expenditures.csv")


def load():
    if not os.path.exists(VISUAL_OUTPUT):
        return pd.DataFrame()
    df = pd.read_csv(VISUAL_OUTPUT)
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    for col in ["category", "necessity_level"]:
        df[col] = df[col].fillna("")
    return df


def cumulative_line(spending, group_col, title, blank_label):
    spending = spending.copy()
    spending[group_col] = spending[group_col].replace("", blank_label)
    daily = spending.groupby(["date", group_col])["amount"].sum().reset_index()
    pivot = daily.pivot(index="date", columns=group_col, values="amount").fillna(0)
    full_range = pd.date_range(pivot.index.min(), pivot.index.max(), freq="D")
    pivot = pivot.reindex(full_range, fill_value=0)
    cumulative = pivot.cumsum().reset_index().rename(columns={"index": "date"})
    melted = cumulative.melt(id_vars="date", var_name=group_col, value_name="Cumulative Spending")
    fig = px.line(
        melted, x="date", y="Cumulative Spending", color=group_col,
        title=title, height=500,
    )
    fig.update_layout(xaxis_title="Date", yaxis_title="Cumulative Spending ($)")
    return fig


st.title("Cumulative Line Plot")

df = load()
if df.empty:
    st.info("No visualization data found. Restart the app to generate it.")
    st.stop()

all_dates = df["date"].dt.date.dropna()
st.session_state.setdefault("date_start", all_dates.min() if len(all_dates) else datetime.date.today())
st.session_state.setdefault("date_end",   all_dates.max() if len(all_dates) else datetime.date.today())
st.session_state.setdefault("filter_categories", [])
st.session_state.setdefault("filter_necessity", [])

def unique_vals(series):
    return sorted(v for v in series.dropna().unique() if str(v).strip())

st.markdown("**Date Filter**")
dcol1, dcol2 = st.columns(2)
with dcol1:
    date_start = st.date_input("From", value=st.session_state["date_start"])
with dcol2:
    date_end = st.date_input("To", value=st.session_state["date_end"])
st.session_state["date_start"] = date_start
st.session_state["date_end"] = date_end

col1, col2 = st.columns(2)
with col1:
    filter_cats = st.multiselect("Category", options=unique_vals(df["category"]), default=st.session_state["filter_categories"])
with col2:
    filter_nec = st.multiselect("Necessity Level", options=unique_vals(df["necessity_level"]), default=st.session_state["filter_necessity"])
st.session_state["filter_categories"] = filter_cats
st.session_state["filter_necessity"] = filter_nec

mask = pd.Series(True, index=df.index)
mask &= df["date"].dt.date >= date_start
mask &= df["date"].dt.date <= date_end
if filter_cats:
    mask &= df["category"].isin(filter_cats)
if filter_nec:
    mask &= df["necessity_level"].isin(filter_nec)

spending = df[mask & (df["amount"] < 0)].copy()
spending["amount"] = spending["amount"].abs()

if spending.empty:
    st.info("No spending data for the selected filters.")
    st.stop()

st.plotly_chart(
    cumulative_line(spending, "category", "Cumulative Spending by Category", "Uncategorized"),
    use_container_width=True,
)
st.plotly_chart(
    cumulative_line(spending, "necessity_level", "Cumulative Spending by Necessity Level", "Unassigned"),
    use_container_width=True,
)
