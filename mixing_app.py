import pandas as pd
import streamlit as st
import numpy as np

st.logo("logo.png")

# create pages
main_pg = st.Page("intro.py", title="Overview", icon="1️⃣")
system_pg = st.Page("system.py", title="System", icon="2️⃣")
reactors_pg = st.Page("reactors.py", title="Reactor", icon="3️⃣")
rxn_pg = st.Page("rxns.py", title="Reactions", icon="4️⃣")
mixing_pg = st.Page("mixing.py", title="Mixing", icon="5️⃣")
# results_pg = st.Page("results.py", title="Results", icon="6️⃣")
report_pg = st.Page("report.py", title="Report", icon="6️⃣")
theory_pg = st.Page("theory.py", title="Theory", icon="7️⃣")

# add navigation side pane
pg = st.navigation([main_pg,
                    system_pg,
                    reactors_pg,
                    rxn_pg,
                    mixing_pg,
                    report_pg,
                    theory_pg])

# set page icon
st.set_page_config(page_title="Mixing App", page_icon="➕")

# import data files
try:
    st.session_state['materials_df'] = pd.read_csv("properties/materials.csv")
    st.session_state['reactions_df'] = pd.read_csv("properties/reactions.csv")
    st.session_state['reactors_df'] = pd.read_csv("properties/reactors.csv")
except Exception as e:
    st.error(f"Data import error! {e}")

pg.run()

