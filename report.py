import pandas as pd
import streamlit as st

st.header("Mixing Report")

def download_report():
    if 'report' in st.session_state:
        df_all = pd.concat(st.session_state.report, axis=1)
        df_all.to_csv("mixing_report.csv")
        st.success("Report downloaded successfully!")
    else:
        st.warning("No mixing cases found.")

st.button("Download Report", on_click=download_report)

if 'report' in st.session_state:
    df_all = pd.concat(st.session_state.report, axis=1)
    st.dataframe(df_all)
else:
    st.warning("No mixing cases found.")
