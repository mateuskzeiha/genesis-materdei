import streamlit as st

import reveal_dashboard
import predict_dashboard
import act_dashboard

st.set_page_config(page_title="Genesis — MVP", layout="wide")

st.title("Genesis — MVP (Reveal / Predict / Act)")
st.caption("Entender → prever → agir")

tab_reveal, tab_predict, tab_act = st.tabs(["REVEAL", "PREDICT", "ACT"])

with tab_reveal:
    reveal_dashboard.render()

with tab_predict:
    predict_dashboard.render()

with tab_act:
    act_dashboard.render()
