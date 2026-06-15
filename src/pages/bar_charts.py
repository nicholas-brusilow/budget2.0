import os
import datetime
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


st.title("Bar Charts")

df = load()
if df.empty:
    st.info("No visualization data found. Restart the app to generate it.")
    st.stop()

# --- Filters (same persistence pattern as Expenditures page) ---
all_dates = df["date"].dt.date.dropna()
st.session_state.setdefault("date_start", all_dates.min() if len(all_dates) else datetime.date.today())
st.session_state.setdefault("date_end",   datetime.date.today())
st.session_state.setdefault("filter_categories", [])
st.session_state.setdefault("filter_necessity", list(DEFAULT_NECESSITY_FILTER))
st.session_state.setdefault("bar_time_scale", "Total")

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

if "_bar_w_filter_categories" not in st.session_state:
    st.session_state["_bar_w_filter_categories"] = st.session_state["filter_categories"]
if "_bar_w_filter_necessity" not in st.session_state:
    st.session_state["_bar_w_filter_necessity"] = st.session_state["filter_necessity"]

col1, col2 = st.columns(2)
with col1:
    st.multiselect("Category", options=unique_vals(df["category"]), key="_bar_w_filter_categories")
with col2:
    st.multiselect("Necessity Level", options=unique_vals(df["necessity_level"]), key="_bar_w_filter_necessity")

st.session_state["filter_categories"] = st.session_state["_bar_w_filter_categories"]
st.session_state["filter_necessity"] = st.session_state["_bar_w_filter_necessity"]

mask = pd.Series(True, index=df.index)
mask &= df["date"].dt.date >= date_start
mask &= df["date"].dt.date <= date_end
if st.session_state["filter_categories"]:
    mask &= df["category"].isin(st.session_state["filter_categories"])
if st.session_state["filter_necessity"]:
    mask &= df["necessity_level"].isin(st.session_state["filter_necessity"])

SCALE_OPTIONS = ["Total", "Per Day", "Per Week", "Per Month"]
scale = st.selectbox("Time Scale", options=SCALE_OPTIONS, index=SCALE_OPTIONS.index(st.session_state["bar_time_scale"]))
st.session_state["bar_time_scale"] = scale

# Only spending (money out = negative); display as positive values
spending = df[mask & (df["amount"] < 0)].copy()
spending["amount"] = spending["amount"].abs()

if spending.empty:
    st.info("No spending data for the selected filters.")
    st.stop()

spending["category"]        = spending["category"].replace("", "Uncategorized")
spending["necessity_level"] = spending["necessity_level"].replace("", "Unassigned")

num_days = (date_end - date_start).days + 1
if scale == "Per Day":
    divisor = num_days
    scale_label = "Per-Day Spending"
elif scale == "Per Week":
    divisor = num_days / 7
    scale_label = "Per-Week Spending"
elif scale == "Per Month":
    divisor = num_days / 30.4375
    scale_label = "Per-Month Spending"
else:
    divisor = 1
    scale_label = "Total Spending"

scaled = spending.copy()
scaled["amount"] = scaled["amount"] / divisor

total_spent = scaled["amount"].sum()
st.markdown(f"<p style='font-size:1.4rem;'>{scale_label}: <strong>${total_spent:,.2f}</strong></p>", unsafe_allow_html=True)

PALETTE = px.colors.qualitative.Bold

cat_data = scaled.groupby("category")["amount"].sum().reset_index().sort_values("amount", ascending=False)
fig = px.bar(cat_data, x="category", y="amount", title=f"{scale_label} by Category", height=500, text="amount",
             color="category", color_discrete_sequence=PALETTE)
fig.update_traces(texttemplate="$%{text:,.2f}", textposition="outside")
fig.update_layout(xaxis_title="Category", yaxis_title="Amount ($)", showlegend=False)
st.plotly_chart(fig, use_container_width=True)

nec_data = scaled.groupby("necessity_level")["amount"].sum().reset_index().sort_values("amount", ascending=False)
fig = px.bar(nec_data, x="necessity_level", y="amount", title=f"{scale_label} by Necessity Level", height=500, text="amount",
             color="necessity_level", color_discrete_sequence=PALETTE)
fig.update_traces(texttemplate="$%{text:,.2f}", textposition="outside")
fig.update_layout(xaxis_title="Necessity Level", yaxis_title="Amount ($)", showlegend=False)
st.plotly_chart(fig, use_container_width=True)

if st.session_state["filter_categories"]:
    sub_scaled = scaled.copy()
    sub_scaled["subcategory"] = sub_scaled["subcategory"].replace("", "Uncategorized")
    sub_data = sub_scaled.groupby("subcategory")["amount"].sum().reset_index().sort_values("amount", ascending=False)
    fig = px.bar(sub_data, x="subcategory", y="amount", title=f"{scale_label} by Subcategory", height=500, text="amount",
                 color="subcategory", color_discrete_sequence=PALETTE)
    fig.update_traces(texttemplate="$%{text:,.2f}", textposition="outside")
    fig.update_layout(xaxis_title="Subcategory", yaxis_title="Amount ($)", showlegend=False)
    st.plotly_chart(fig, use_container_width=True)
