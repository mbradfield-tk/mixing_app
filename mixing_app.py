import pandas as pd
import streamlit as st
import numpy as np

st.logo("assets/logo.png")

# create pages
main_pg = st.Page("intro.py", title="Overview", icon="1️⃣")
system_pg = st.Page("system.py", title="System", icon="2️⃣")
reactors_pg = st.Page("reactors.py", title="Reactor", icon="3️⃣")
rxn_pg = st.Page("rxns.py", title="Reactions", icon="4️⃣")
# bourne_pg = st.Page("bourne.py", title="Bourne Protocol", icon="5️⃣")
bourne2_pg = st.Page("bourne2.py", title="Bourne Protocol", icon="5️⃣")
sensitivity_pg = st.Page("sensitivity.py", title="Sensitivity Analysis", icon="6️⃣")
mixing_pg = st.Page("mixing.py", title="Mixing", icon="7️⃣")
# results_pg = st.Page("results.py", title="Results", icon="7️⃣")
scaling_pg = st.Page("scaling.py", title="Scaling", icon="8️⃣")
report_pg = st.Page("report.py", title="Report", icon="9️⃣")
theory_pg = st.Page("theory.py", title="Theory", icon="🔟")

# add navigation side pane
pg = st.navigation([main_pg,
                    system_pg,
                    reactors_pg,
                    rxn_pg,
                    # bourne_pg,
                    bourne2_pg,
                    sensitivity_pg,
                    mixing_pg,
                    scaling_pg,
                    report_pg,
                    theory_pg])

# set page icon
st.set_page_config(page_title="Mixing App", page_icon="➕")

# import data files
try:
    st.session_state['materials_df'] = pd.read_csv("properties/materials.csv")
    st.session_state['reactions_df'] = pd.read_csv("properties/reactions.csv")
    st.session_state['reactors_df'] = pd.read_csv("properties/reactors.csv")
    st.session_state['data_kla_df'] = pd.read_csv("data/measured_kla.csv")
    
    # create vessel name column for easier selection in scaling page
    st.session_state['reactors_df']["name"] = st.session_state['reactors_df']["owner"] + "-" + st.session_state['reactors_df']["reactor"]
except Exception as e:
    st.error(f"Data import error! {e}")

pg.run()

