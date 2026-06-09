import os
import sys
import pandas as pd
import streamlit as st

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUTPUT = os.path.join(ROOT, "expenditures.csv")

sys.path.insert(0, os.path.join(ROOT, "src"))
from categoricals import EXPENDITURE_CATEGORIES, ALL_SUBCATEGORIES, NECESSITY

EDITABLE_COLS = ["category", "subcategory", "necessity_level", "ignore"]


def load():
    if not os.path.exists(OUTPUT):
        return pd.DataFrame()
    df = pd.read_csv(OUTPUT)
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    df["ignore"] = df["ignore"].astype(str).str.lower() == "true"
    for col in ["category", "subcategory", "necessity_level"]:
        df[col] = df[col].fillna("")
    return df


st.title("Expenditures")

df = load()
if df.empty:
    st.info("No expenditure data found. Add raw data files and restart.")
    st.stop()

# --- Filters ---
def unique_vals(series):
    return sorted(v for v in series.dropna().unique() if str(v).strip())

col1, col2, col3 = st.columns(3)
with col1:
    sel_cats = st.multiselect("Category", options=unique_vals(df["category"]))
with col2:
    sel_subs = st.multiselect("Subcategory", options=unique_vals(df["subcategory"]))
with col3:
    sel_nec = st.multiselect("Necessity Level", options=unique_vals(df["necessity_level"]))

mask = pd.Series(True, index=df.index)
if sel_cats:
    mask &= df["category"].isin(sel_cats)
if sel_subs:
    mask &= df["subcategory"].isin(sel_subs)
if sel_nec:
    mask &= df["necessity_level"].isin(sel_nec)

filtered = df[mask].copy()

col_caption, col_btn = st.columns([8, 1])
with col_caption:
    st.caption(f"Showing {len(filtered)} of {len(df)} transactions")
with col_btn:
    save_clicked = st.button("Save Changes", type="primary", use_container_width=True)

# --- Table ---
disabled_cols = [c for c in filtered.columns if c not in EDITABLE_COLS]

edited = st.data_editor(
    filtered,
    column_config={
        "date":            st.column_config.TextColumn("Date"),
        "amount":          st.column_config.NumberColumn("Amount", format="%.2f"),
        "description":     st.column_config.TextColumn("Description"),
        "account":         st.column_config.TextColumn("Account"),
        "category":        st.column_config.SelectboxColumn("Category", options=EXPENDITURE_CATEGORIES, required=False),
        "subcategory":     st.column_config.SelectboxColumn("Subcategory", options=ALL_SUBCATEGORIES, required=False),
        "necessity_level": st.column_config.SelectboxColumn("Necessity Level", options=NECESSITY, required=False),
        "timescale":       st.column_config.TextColumn("Timescale"),
        "timescale_end":   st.column_config.TextColumn("Timescale End"),
        "ignore":          st.column_config.CheckboxColumn("Ignore"),
    },
    disabled=disabled_cols,
    use_container_width=True,
    hide_index=True,
    num_rows="fixed",
    key="expenditures_editor",
)

if save_clicked:
    df.update(edited[EDITABLE_COLS])
    df.to_csv(OUTPUT, index=False)
    del st.session_state["expenditures_editor"]
    st.rerun()
