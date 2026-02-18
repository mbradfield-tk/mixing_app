import streamlit as st
import pandas as pd
st.header("Mixing Sensitivity Analysis")

# *************** Get global state variables *****************
# get mixture properties
mix = st.session_state.mixture[st.session_state.mixture["Compound"] == "Mixture"].to_dict('records')[0]
# get reactor properties
r = st.session_state.reactor
# get reaction kinetics
rxn = st.session_state.rxn_rate

# *************** Get inputs *****************
st.subheader("Inputs")
error=False
# reactor
try:
    st.badge(f"Reactor",
         icon=":material/check:", color="green")
    st.write(f"{r[('Name', '-')]}")
except Exception as e:
    error=True
    st.warning(f"Error displaying reactor name: {e}")

# display system as table
try:
    st.badge("System Properties", icon=":material/check:", color="green")
    with st.expander("View system properties table"):
        st.dataframe(pd.DataFrame(mix, index=[0]))
except Exception as e:
    error=True
    st.warning(f"Error displaying system properties: {e}")

# display reaction kinetics
try:
    if (rxn["r_rxn"] is not None) and (rxn["r_rxn"] != 0):
        st.badge("Reaction rate", icon=":material/check:", color="green")
        st.write(f"{rxn['r_rxn']} 1/s")
    else:
        st.badge("Reaction rate", icon=":material/warning:", color="orange")
        st.warning("Reaction rate not defined. Please fill in reaction kinetics parameters in the Reactions page.")
        error=True
        
except Exception as e:
    st.warning(f"Error displaying reaction kinetics: {e}")
    error=True


run_analysis = st.button("Check for Mixing Sensitivities",
                         disabled=error)
st.divider()


# only execute when button is pressed
if run_analysis:
    # *************** Rxn vs Micromixing *****************
    st.subheader("Micromixing")

    # *************** Rxn vs Macromixing *****************
    st.divider()
    st.subheader("Macromixing")

    # *************** Rxn vs Mass Transfer *****************
    st.divider()
    st.subheader("Mass Transfer")

    # *************** Rxn vs Heat Transfer *****************
    st.divider()
    st.subheader("Heat Transfer")
