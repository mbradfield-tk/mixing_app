import pandas as pd
import streamlit as st
import numpy as np
import functions as f

# define reaction rate data
if 'rxn_rate' not in st.session_state:
    st.session_state.rxn_rate = {}
    st.session_state.rxn_rate['no_reagents'] = 1
    st.session_state.rxn_rate['k'] = 1.0
    st.session_state.rxn_rate['C_eff'] = 1.0
    st.session_state.rxn_rate['dH_rxn'] = -100.0
    st.session_state.rxn_rate['selected_rxn'] = None

st.session_state.rxn_k_input = st.session_state.rxn_rate['k']
st.session_state.rxn_C_eff_input = st.session_state.rxn_rate['C_eff']
st.session_state.rxn_dH_input = st.session_state.rxn_rate['dH_rxn']

# get system properties
all_props = st.session_state.mixture
# convert dataframe entry to dict for easier accessing
try:
    mix = all_props[all_props["Compound"] == "Mixture"].to_dict('records')[0]
except:
    mix = {}
    st.warning("No mixture properties found. Please check inputs.")

st.header("Reaction Kinetics and Heat")
st.write("Define reaction rate parameters below to estimate a reaction rate for relative rate comparisons.")

# define a rate constant and effective concentration to account for various reaction types
col1, col2 = st.columns(2)

def update_k():
    try:
        st.session_state.rxn_rate['k'] = float(st.session_state.rxn_k_input)
    except ValueError:
        st.error("Invalid input for rate constant. Please enter a number.")

def update_C_eff():
    try:
        st.session_state.rxn_rate['C_eff'] = float(st.session_state.rxn_C_eff_input)
    except ValueError:
        st.error("Invalid input for effective concentration. Please enter a number.")

def update_dH_rxn():
    try:
        st.session_state.rxn_rate['dH_rxn'] = float(st.session_state.rxn_dH_input)
    except ValueError:
        st.error("Invalid input for heat of reaction. Please enter a number.")

# get effective rate constant k
st.session_state.rxn_rate['k'] = float(col1.number_input("Overall rate constant (k)",
                                                        key="rxn_k_input",
                                                        step=0.1,
                                                        min_value=0.0,
                                                        on_change=update_k))

# get effective concentration C_eff
st.session_state.rxn_rate['C_eff'] = float(col2.number_input("Effective concentration (C_eff)",
                                                                step=1.0,
                                                                key="rxn_C_eff_input",
                                                                min_value=0.0,
                                                                on_change=update_C_eff))

# get heat of reaction dH_rxn [kJ/mol]
st.session_state.rxn_rate['dH_rxn'] = float(col1.number_input("Heat of reaction [kJ/mol] (exo<0; endo>0)",
                                                              key="rxn_dH_input",
                                                              step=10.0,
                                                              on_change=update_dH_rxn))

# calc reaction rate r_rxn [mol/kg/s]
st.session_state.rxn_rate['r_rxn'] = st.session_state.rxn_rate['k'] * st.session_state.rxn_rate['C_eff']

# calc heat generated Q [kW]
st.session_state.rxn_rate['Q'] = (st.session_state.rxn_rate['r_rxn'] * st.session_state.rxn_rate['dH_rxn']
                                     * mix[('Mass', 'kg')]) * (-1)

col1.metric("Reaction rate [mol/kg/s]",
            f"{st.session_state.rxn_rate['r_rxn']:.2e}",
            border=True)
col2.write(".")
col2.write("")
col2.write("")
col2.write("")
col2.metric("Heat Generation [kW]", f"{st.session_state.rxn_rate['Q']:.2f}", border=True)
st.header("Reaction Browser")

rxns = st.session_state['reactions_df'].copy()

reaction = st.selectbox("Select the reaction type:", rxns["Reaction"].unique())

# update rxn parameters based on selection and inputs
def select_reaction():
    # get reaction
    selected_rxn = rxns[rxns["Reaction"]==reaction].copy()
    st.session_state.rxn_rate['selected_rxn'] = reaction

    # st.write("Selected reaction rate order of magnitude:", OoM)
    st.session_state.rxn_rate['k'] = float(selected_rxn["Rate"].values[0])
    st.session_state.rxn_k_input = st.session_state.rxn_rate['k']

    # get heat of reaction
    dH_rxn = float(selected_rxn["dH [kJ/mol]"].values[0])
    st.session_state.rxn_rate['dH_rxn'] = dH_rxn
    st.session_state.rxn_dH_input = st.session_state.rxn_rate['dH_rxn']

    # provide reaction info
    st.session_state.rxn_rate['speed'] = selected_rxn["Category"].values[0]
    st.session_state.rxn_rate['heat'] = selected_rxn["Endo/Exo"].values[0]

st.button("Use Selected Reaction", on_click=select_reaction)

if st.session_state.rxn_rate['selected_rxn'] is not None:
    st.badge(f"{st.session_state.rxn_rate['selected_rxn']}",
             icon=":material/check:", color="green")

    speed = st.session_state.rxn_rate['speed'].upper()
    if speed == "FAST":
        st.badge(f"{speed} reaction rate",
                 icon=":material/flash_on:", color="orange")
    elif speed == "MEDIUM":
        st.badge(f"{speed} reaction rate",
                 icon=":material/slow_motion_video:", color="green")
    elif speed == "SLOW":
        st.badge(f"{speed} reaction rate",
                 icon=":material/timer:", color="blue")

    heat = st.session_state.rxn_rate['heat']
    if heat == "Exothermic":
        st.badge(f"{heat}",
                 icon=":material/whatshot:", color="red")
    elif heat == "Endothermic":
        st.badge(f"{heat}",
                 icon=":material/ac_unit:", color="blue")
else:
    st.badge("No reaction selected", icon=":material/close:", color="red")

with st.expander("Reaction Explorer"):
    st.dataframe(rxns)