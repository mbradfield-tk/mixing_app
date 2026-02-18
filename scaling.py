import streamlit as st
import pandas as pd
import functions as f
import plotly.express as px
import numpy as np


# get reactors dataframe
df_reactors = st.session_state['reactors_df'].copy()

# get reaction rate data
rxn_rate = st.session_state['rxn_rate'].copy()

# initialize reactors properties dictionary
if 'rScale' in st.session_state:
    rScale = st.session_state.rScale
else:
    rScale = {"lab": {},
              "pilot": {},
              "commercial": {}}

st.header("Scaling Assessment")
st.subheader("Reactors")

col1, col2 = st.columns(2)

# get reactor names by scale
lab_reactors = df_reactors[(df_reactors["property"] == "Scale") & (df_reactors["value"] == "lab")].copy()
pilot_reactors = df_reactors[(df_reactors["property"] == "Scale") & (df_reactors["value"] == "pilot")].copy()
comm_reactors = df_reactors[(df_reactors["property"] == "Scale") & (df_reactors["value"] == "commercial")].copy()

# select reactor for each scale
r_lab = col1.selectbox("Select lab reactor:", lab_reactors["name"].unique())
r_pilot = col1.selectbox("Select pilot reactor:", pilot_reactors["name"].unique())
r_commercial = col1.selectbox("Select commercial reactor:", comm_reactors["name"].unique())

# get reactor properties and add to rScale dict as dict
rScale["lab"] = df_reactors[df_reactors["name"] == r_lab].copy()
rScale["lab"] = dict(zip(zip(rScale["lab"]["property"], rScale["lab"]["units"]), rScale["lab"]["value"]))
rScale["pilot"] = df_reactors[df_reactors["name"] == r_pilot].copy()
rScale["pilot"] = dict(zip(zip(rScale["pilot"]["property"], rScale["pilot"]["units"]), rScale["pilot"]["value"]))
rScale["commercial"] = df_reactors[df_reactors["name"] == r_commercial].copy()
rScale["commercial"] = dict(zip(zip(rScale["commercial"]["property"], rScale["commercial"]["units"]), rScale["commercial"]["value"]))

# convert to dataframes for display
r_lab_df = pd.DataFrame(rScale["lab"].values(), index=pd.MultiIndex.from_tuples(rScale["lab"].keys()), columns=["Value"])
r_pilot_df = pd.DataFrame(rScale["pilot"].values(), index=pd.MultiIndex.from_tuples(rScale["pilot"].keys()), columns=["Value"])
r_comm_df = pd.DataFrame(rScale["commercial"].values(), index=pd.MultiIndex.from_tuples(rScale["commercial"].keys()), columns=["Value"])

# merge into single df for display
r_df = pd.concat([r_lab_df, r_pilot_df, r_comm_df], axis=1, keys=["Lab", "Pilot", "Commercial"])

# sort by category (property type)
r_df = r_df.sort_index(level=0)
st.dataframe(r_df)

# function to run scale analysis on selected reactors
def scale_analysis():
    # check if reaction rate defined
    if "rxn_rate" not in st.session_state:
        st.warning("Please define reaction rate parameters in the Reaction Kinetics and Heat section before checking scale-dependency.")
    # check if mixture properties defined
    elif "mixture" not in st.session_state:
        st.warning("Please define system properties in the System section before checking scale-dependency.")
    else:
        # get mixture properties
        all_props = st.session_state.mixture
        mix = all_props[all_props["Compound"] == "Mixture"].to_dict('records')[0]
        # get density [kg/m3]
        rho = mix[("Density", "kg/m3")]
        # gas-liquid assessment
        lst = ["lab", "commercial"] #, "pilot", "commercial"]
        scale_results = []
        for scale in lst:
            # get volume and agitation ranges for scale
            Vmin = float(rScale[scale][("Volume Min", "L")])
            Vmax = float(rScale[scale][("Volume Max", "L")])
            Nmin = float(rScale[scale][("Agitation Min", "rpm")])
            Nmax = float(rScale[scale][("Agitation Max", "rpm")])
            # get discrete volumes by dividing range by 5
            V_range = [Vmin + i*(Vmax-Vmin)/5 for i in range(6)]
            N_range = [Nmin + i*(Nmax-Nmin)/5 for i in range(6)]
            # calculate kla for each volume-agitation speed combination
            for V in V_range:
                # get mass [kg]
                M = V * rho / 1000
                for N in N_range:
                    # TODO: account for multiple impellers
                    Po = float(rScale[scale][("Impeller 1 Np", "-")])
                    Di = float(rScale[scale][("Impeller 1 Diameter", "m")])
                    # calculate power input P [W]
                    P = f.power_input(Po=Po, rho_L=rho, N=N, D=Di)
                    kla = f.kLa_gas_drawdown(A=0.07, b=0.53, P=P, M=M)
                    # calculate Damkohler number for mass transfer to reaction (Da = r_rxn / kla)
                    if kla > 0:
                        Da1 = rxn_rate['r_rxn'] / kla
                    else:
                        Da1 = float('inf')

                    scale_results.append({"Scale": scale,
                                        "Volume (L)": V,
                                        "Agitation (rpm)": N,
                                        "P/M (W/kg)": P/M,
                                        "kla (1/s)": kla,
                                        "Da_1": Da1})
        scale_results = pd.DataFrame(scale_results)
        # sort by kla value
        scale_results = scale_results.sort_values(by="kla (1/s)", ascending=True)
        st.subheader("Gas-Liquid Mass Transfer Analysis")
        # plot kla vs P/M for each scale
        fig = px.line(scale_results, x="P/M (W/kg)", y="kla (1/s)", color="Scale", title=f"Gas-liquid mass transfer coefficient (kla)")
        st.plotly_chart(fig)
        # plot Da_1 vs P/M for each scale
        fig2 = px.line(scale_results, x="P/M (W/kg)", y="Da_1", color="Scale", title=f"Damkohler number for mass transfer vs reaction (Da_1)",
                        log_y=True)
        # add horizontal line at Da_1=1.0
        fig2.add_hline(y=1.0, line_dash="dash", line_color="red",
                        annotation_text="Da_1=1 (system is mass transfer limited above line)", annotation_position="top left")
        st.plotly_chart(fig2)

        # find where Da_1 > 1 in dataframe and display table of those conditions
        mass_transfer_limited = scale_results[scale_results["Da_1"] > 1].copy()
        st.subheader("Mass Transfer Limited Conditions (Da_1 > 1)")
        st.dataframe(mass_transfer_limited)

        st.divider()
        st.subheader("Micromixing Analysis")

        st.divider()
        st.subheader("Solid-Liquid Mass Transfer Analysis")

# show reaction rate
st.write(f"Reaction rate: {rxn_rate['r_rxn']:.3f} mol/kg/s")

# may need to use global state for this for results to persist after button click and page changes
analyse = st.button("Check Scale-dependency")

st.divider()

# to ensure that outputs appear below the button
if analyse:
    scale_analysis()