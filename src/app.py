import os
import sys
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import preprocessing

st.set_page_config(
    page_title="Budget",
    layout="wide",
    initial_sidebar_state="expanded",
)

if "preprocessed" not in st.session_state:
    preprocessing.run()
    st.session_state["preprocessed"] = True

pg = st.navigation([
    st.Page("pages/expenditures.py", title="Expenditures", icon=":material/receipt_long:"),
    st.Page("pages/create_transaction.py", title="Create Transaction", icon=":material/add_circle:"),
    st.Page("pages/pie_charts.py", title="Pie Charts", icon=":material/pie_chart:"),
])
pg.run()
