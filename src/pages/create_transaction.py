import os
import sys
import datetime
import pandas as pd
import streamlit as st

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUTPUT = os.path.join(ROOT, "expenditures.csv")

sys.path.insert(0, os.path.join(ROOT, "src"))
from categoricals import EXPENDITURE_CATEGORIES, ALL_SUBCATEGORIES, NECESSITY

MANUAL_ACCOUNTS = ["Cash", "Crypto"]

st.title("Create Transaction")

c1, c2, c3 = st.columns(3)
with c1:
    date = st.date_input("Date", value=datetime.date.today())
with c2:
    amount = st.number_input("Amount (negative = money out)", value=0.00, step=0.01, format="%.2f")
with c3:
    account = st.selectbox("Account", options=MANUAL_ACCOUNTS)

description = st.text_input("Description")

c4, c5, c6 = st.columns(3)
with c4:
    category = st.selectbox("Category", options=[""] + EXPENDITURE_CATEGORIES)
with c5:
    sub_opts = [""] + ([s for s in ALL_SUBCATEGORIES if s.startswith(category + ":")] if category else [])
    subcategory = st.selectbox("Subcategory", options=sub_opts)
with c6:
    necessity_level = st.selectbox("Necessity Level", options=[""] + NECESSITY)

if st.button("Add Transaction", type="primary"):
    if not description.strip():
        st.error("Description is required.")
    else:
        date_str = date.strftime("%Y-%m-%d")
        new_row = {
            "date": date_str,
            "amount": amount,
            "description": description.strip(),
            "account": account,
            "category": category,
            "subcategory": subcategory,
            "necessity_level": necessity_level,
            "timescale": date_str,
            "timescale_end": date_str,
            "ignore": False,
        }

        if os.path.exists(OUTPUT):
            df = pd.read_csv(OUTPUT)
        else:
            df = pd.DataFrame(columns=list(new_row.keys()))

        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        df.to_csv(OUTPUT, index=False)
        st.success(f"Transaction added: {description.strip()} on {date_str}")
