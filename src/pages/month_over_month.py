import os
import datetime
import calendar
import pandas as pd
import plotly.express as px
import streamlit as st

from categoricals import DEFAULT_NECESSITY_FILTER

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
VISUAL_OUTPUT = os.path.join(ROOT, "visual_expenditures.csv")


def load():
    if not os.path.exists(VISUAL_OUTPUT):
        return pd.DataFrame()
    df = pd.read_csv(VISUAL_OUTPUT)
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    for col in ["category", "subcategory", "necessity_level"]:
        df[col] = df[col].fillna("")
    return df


def get_complete_months(date_start, date_end):
    """Return list of (year, month) for months fully contained in [date_start, date_end]."""
    months = []
    year, month = date_start.year, date_start.month
    while True:
        month_start = datetime.date(year, month, 1)
        month_end = datetime.date(year, month, calendar.monthrange(year, month)[1])
        if month_end > date_end:
            break
        if month_start >= date_start:
            months.append((year, month))
        if month == 12:
            year, month = year + 1, 1
        else:
            month += 1
    return months


st.title("Month-over-Month")

df = load()
if df.empty:
    st.info("No visualization data found. Restart the app to generate it.")
    st.stop()

all_dates = df["date"].dt.date.dropna()
st.session_state.setdefault("date_start", all_dates.min() if len(all_dates) else datetime.date.today())
st.session_state.setdefault("date_end", datetime.date.today())
st.session_state.setdefault("filter_categories", [])
st.session_state.setdefault("filter_necessity", list(DEFAULT_NECESSITY_FILTER))


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

if "_mom_w_filter_categories" not in st.session_state:
    st.session_state["_mom_w_filter_categories"] = st.session_state["filter_categories"]
if "_mom_w_filter_necessity" not in st.session_state:
    st.session_state["_mom_w_filter_necessity"] = st.session_state["filter_necessity"]

col1, col2 = st.columns(2)
with col1:
    st.multiselect("Category", options=unique_vals(df["category"]), key="_mom_w_filter_categories")
with col2:
    st.multiselect("Necessity Level", options=unique_vals(df["necessity_level"]), key="_mom_w_filter_necessity")

st.session_state["filter_categories"] = st.session_state["_mom_w_filter_categories"]
st.session_state["filter_necessity"] = st.session_state["_mom_w_filter_necessity"]

mask = pd.Series(True, index=df.index)
mask &= df["date"].dt.date >= date_start
mask &= df["date"].dt.date <= date_end
if st.session_state["filter_categories"]:
    mask &= df["category"].isin(st.session_state["filter_categories"])
if st.session_state["filter_necessity"]:
    mask &= df["necessity_level"].isin(st.session_state["filter_necessity"])

spending = df[mask & (df["amount"] < 0)].copy()
spending["amount"] = spending["amount"].abs()
spending["category"] = spending["category"].replace("", "Uncategorized")

months = get_complete_months(date_start, date_end)
if not months:
    st.info("No complete months in the selected date range.")
    st.stop()

month_order = [datetime.date(y, m, 1).strftime("%b %Y") for y, m in months]
days_map = {datetime.date(y, m, 1).strftime("%b %Y"): calendar.monthrange(y, m)[1] for y, m in months}

# Filter spending to complete months only
spending["year_month"] = spending["date"].dt.to_period("M")
valid_periods = pd.PeriodIndex([pd.Period(year=y, month=m, freq="M") for y, m in months])
spending = spending[spending["year_month"].isin(valid_periods)].copy()
spending["month_label"] = spending["date"].dt.strftime("%b %Y")

if spending.empty:
    st.info("No spending data for the complete months in the selected range.")
    st.stop()

per_day = st.checkbox("Amount Per Day", value=False)

PALETTE = px.colors.qualitative.Bold

if st.session_state["filter_categories"]:
    mom_data = spending.groupby(["month_label", "category"])["amount"].sum().reset_index()
    mom_data["month_label"] = pd.Categorical(mom_data["month_label"], categories=month_order, ordered=True)
    mom_data = mom_data.sort_values(["month_label", "category"])

    if per_day:
        mom_data["amount"] = mom_data["month_label"].map(days_map).pipe(lambda d: mom_data["amount"] / d)
        total_days = sum(days_map.values())
        avg_per_day = spending["amount"].sum() / total_days
        summary_label = f"Avg Daily Spending (complete months): <strong>${avg_per_day:,.2f}</strong>"
        y_title = "Amount ($/day)"
        chart_title = "Month-over-Month Spending by Category (Per Day)"
        text_fmt = "$%{text:,.2f}"
    else:
        total = mom_data["amount"].sum()
        summary_label = f"Total Spending (complete months): <strong>${total:,.2f}</strong>"
        y_title = "Amount ($)"
        chart_title = "Month-over-Month Spending by Category"
        text_fmt = "$%{text:,.0f}"

    st.markdown(f"<p style='font-size:1.4rem;'>{summary_label}</p>", unsafe_allow_html=True)

    fig = px.bar(
        mom_data,
        x="month_label",
        y="amount",
        color="category",
        barmode="group",
        title=chart_title,
        height=500,
        text="amount",
        color_discrete_sequence=PALETTE,
    )
    fig.update_traces(texttemplate=text_fmt, textposition="outside")
    fig.update_layout(
        xaxis_title="Month",
        yaxis_title=y_title,
        xaxis={"categoryorder": "array", "categoryarray": month_order},
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    mom_data = spending.groupby("month_label")["amount"].sum().reset_index()
    all_months_df = pd.DataFrame({"month_label": month_order})
    mom_data = all_months_df.merge(mom_data, on="month_label", how="left").fillna(0)
    mom_data["month_label"] = pd.Categorical(mom_data["month_label"], categories=month_order, ordered=True)
    mom_data = mom_data.sort_values("month_label")

    if per_day:
        mom_data["amount"] = mom_data["month_label"].map(days_map).pipe(lambda d: mom_data["amount"] / d)
        total_days = sum(days_map.values())
        avg_per_day = spending["amount"].sum() / total_days
        summary_label = f"Avg Daily Spending (complete months): <strong>${avg_per_day:,.2f}</strong>"
        y_title = "Amount ($/day)"
        chart_title = "Month-over-Month Total Spending (Per Day)"
    else:
        total = mom_data["amount"].sum()
        summary_label = f"Total Spending (complete months): <strong>${total:,.2f}</strong>"
        y_title = "Amount ($)"
        chart_title = "Month-over-Month Total Spending"

    st.markdown(f"<p style='font-size:1.4rem;'>{summary_label}</p>", unsafe_allow_html=True)

    fig = px.bar(
        mom_data,
        x="month_label",
        y="amount",
        title=chart_title,
        height=500,
        text="amount",
        color_discrete_sequence=[PALETTE[0]],
    )
    fig.update_traces(texttemplate="$%{text:,.2f}", textposition="outside")
    fig.update_layout(
        xaxis_title="Month",
        yaxis_title=y_title,
        showlegend=False,
        xaxis={"categoryorder": "array", "categoryarray": month_order},
    )
    st.plotly_chart(fig, use_container_width=True)
