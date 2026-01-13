import pandas as pd
import streamlit as st
import numpy as np
import functions as f

# define reaction rate data
if 'rxn_rate' not in st.session_state:
    st.session_state.rxn_rate = {}
    st.session_state.rxn_rate['no_reagents'] = 1
    st.session_state.rxn_rate['k'] = 10

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
# get effective rate constant k
st.session_state.rxn_rate['k'] = float(col1.text_input("Overall rate constant (k)", 10.0))
# get effective concentration C_eff
st.session_state.rxn_rate['C_eff'] = float(col2.text_input("Effective concentration (C_eff)", 0.1))
# get heat of reaction dH_rxn [kJ/mol]
st.session_state.rxn_rate['dH_rxn'] = float(col1.text_input("Heat of reaction [kJ/mol] (exo<0; endo>0)", 1.0))
# calc reaction rate r_rxn [mol/kg/s]
st.session_state.rxn_rate['r_rxn'] = st.session_state.rxn_rate['k'] * st.session_state.rxn_rate['C_eff']
# calc heat generated Q [kW]
st.session_state.rxn_rate['Q'] = (st.session_state.rxn_rate['r_rxn'] * st.session_state.rxn_rate['dH_rxn']
                                     * mix[('Mass', 'kg')]) * (-1)

col1.metric("Reaction rate [mol/kg/s]", f"{st.session_state.rxn_rate['r_rxn']:.3f}", border=True)
col2.write("Placeholder")
col2.write("")
col2.write("")
col2.write("")
col2.metric("Heat Generation [kW]", f"{st.session_state.rxn_rate['Q']:.2f}", border=True)
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