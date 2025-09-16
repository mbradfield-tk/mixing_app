import pandas as pd
import streamlit as st
import numpy as np
import functions as f

st.header("Reaction Browser")

rxns = st.session_state['reactions_df'].copy()

reaction = st.selectbox("Select the reaction type:", rxns["Reaction Type"].unique())
kin_cat = rxns[rxns["Reaction Type"]==reaction]["Category"].values[0].upper()

kin_colrs = {"FAST" : ["#7FFFD4", "green"],
                "MEDIUM" : ["#FFF8DC", "orange"],
                "SLOW" : ["#FFB6C1", "red"]}

# tbKin.markdown(f"<span style='color: {kin_colrs[kin_cat]};'>{kin_cat}</span>", unsafe_allow_html=True)

badge_style = f.custom_badge(kin_colrs[kin_cat][0], kin_colrs[kin_cat][1], font_size="20px", padding="8px 15px")
st.markdown(f'<span style="{badge_style}">{kin_cat}</span>', unsafe_allow_html=True)

st.dataframe(rxns)