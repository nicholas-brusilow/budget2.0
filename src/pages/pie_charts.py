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

# Apply persistent filters from session state
today = datetime.date.today()
date_start = st.session_state.get("date_start", df["date"].dt.date.min())
date_end   = st.session_state.get("date_end",   df["date"].dt.date.max())
filter_cats = st.session_state.get("filter_categories", [])
filter_nec  = st.session_state.get("filter_necessity", [])

mask = pd.Series(True, index=df.index)
mask &= df["date"].dt.date >= date_start
mask &= df["date"].dt.date <= date_end
if filter_cats:
    mask &= df["category"].isin(filter_cats)
if filter_nec:
    mask &= df["necessity_level"].isin(filter_nec)

# Only spending (money out = negative); display as positive values
spending = df[mask & (df["amount"] < 0)].copy()
spending["amount"] = spending["amount"].abs()

if spending.empty:
    st.info("No spending data for the selected filters.")
    st.stop()

spending["category"]      = spending["category"].replace("", "Uncategorized")
spending["necessity_level"] = spending["necessity_level"].replace("", "Unassigned")

cat_data = spending.groupby("category")["amount"].sum().reset_index()
fig = px.pie(cat_data, values="amount", names="category", title="Spending by Category", height=700)
fig.update_traces(textposition="inside", textinfo="percent+label")
fig.update_layout(showlegend=False)
st.plotly_chart(fig, use_container_width=True)

nec_data = spending.groupby("necessity_level")["amount"].sum().reset_index()
fig = px.pie(nec_data, values="amount", names="necessity_level", title="Spending by Necessity Level", height=700)
fig.update_traces(textposition="inside", textinfo="percent+label")
fig.update_layout(showlegend=False)
st.plotly_chart(fig, use_container_width=True)
