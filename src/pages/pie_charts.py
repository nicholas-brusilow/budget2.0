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


st.title("Pie Charts")

df = load()
if df.empty:
    st.info("No visualization data found. Restart the app to generate it.")
    st.stop()

# --- Filters (same persistence pattern as Expenditures page) ---
all_dates = df["date"].dt.date.dropna()
st.session_state.setdefault("date_start", all_dates.min() if len(all_dates) else datetime.date.today())
st.session_state.setdefault("date_end",   datetime.date.today())
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

SCALE_OPTIONS = ["Total", "Per Day", "Per Week", "Per Month"]
scale = st.selectbox("Time Scale", options=SCALE_OPTIONS)

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

spending["amount"] = spending["amount"] / divisor

total_spent = spending["amount"].sum()
st.markdown(f"<p style='font-size:1.4rem;'>{scale_label}: <strong>${total_spent:,.2f}</strong></p>", unsafe_allow_html=True)

cat_data = spending.groupby("category")["amount"].sum().reset_index()
fig = px.pie(cat_data, values="amount", names="category", title=f"{scale_label} by Category", height=700)
fig.update_traces(textposition="inside", texttemplate="$%{value:,.2f}<br>%{percent:.1%}<br>%{label}")
fig.update_layout(showlegend=False)
st.plotly_chart(fig, use_container_width=True)

nec_data = spending.groupby("necessity_level")["amount"].sum().reset_index()
fig = px.pie(nec_data, values="amount", names="necessity_level", title=f"{scale_label} by Necessity Level", height=700)
fig.update_traces(textposition="inside", texttemplate="$%{value:,.2f}<br>%{percent:.1%}<br>%{label}")
fig.update_layout(showlegend=False)
st.plotly_chart(fig, use_container_width=True)
