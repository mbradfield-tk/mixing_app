import streamlit as st
import pandas as pd
import functions as f
import plotly.express as px
st.header("Mixing Sensitivity Analysis")
st.divider()

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
    st.success("Reactor", icon=":material/check:", width=200)
    st.write(f"{r[('Name', '-')]}")
    # get reactor iso image
    owner = r[("Owner", "-")]
    reactor = r[("Reactor", "-")]
    image_path = f"{'assets/reactors/'}{owner}_{reactor}_iso.png"
    st.image(image_path, width=200)
except Exception as e:
    error=True
    st.error(f"Error with reactor selection: {e}",
             icon=":material/error:")

# display system as table
try:
    st.success("System Properties", icon=":material/check:", width=200)
    with st.expander("View system properties table"):
        st.dataframe(pd.DataFrame(mix, index=[0]))
except Exception as e:
    error=True
    st.error(f"Error displaying system properties: {e}",
             icon=":material/error:")

# display reaction kinetics
try:
    if (rxn["r_rxn"] is not None) and (rxn["r_rxn"] != 0):
        st.success("Reaction rate", icon=":material/check:", width=200)
        rxn_rate = rxn['r_rxn']
        st.write(f"{rxn_rate} 1/s")
    else:
        error=True
        st.error("Reaction rate not defined. Please fill in reaction kinetics parameters in the Reactions page.",
                 icon="🚨") #":material/error:")
        
except Exception as e:
    st.error(f"Error displaying reaction kinetics: {e}",
             icon="🚨") #":material/error:")
    error=True


run_analysis = st.button("Check for Mixing Sensitivities",
                         disabled=error)
st.divider()

# only execute when button is pressed
if run_analysis:
    # get reactor and system properties from state variables
    Vmin = float(r[('Volume Min', 'L')])
    Vmax = float(r[('Volume Max', 'L')])
    Nmin = float(r[('Agitation Min', 'rpm')])
    Nmax = float(r[('Agitation Max', 'rpm')])
    rho = float(mix[("Density", "kg/m3")])
    nu = float(mix[("Kinematic Viscosity", "m2/s")])

    # TODO: account for multiple impellers
    Po = float(r[("Impeller 1 Np", "-")])
    Di = float(r[("Impeller 1 Diameter", "m")])

    n_points = 20

    # V_range = [Vmin + i*(Vmax-Vmin)/5 for i in range(6)]
    N_range = [Nmin + i*(Nmax-Nmin)/n_points for i in range(n_points+1)]

    V_series = ['Vmin', 'Vmax']
    V_vals = [Vmin, Vmax]

    sensitivity_results = []
    for i, V in enumerate(V_vals):
        # get mass [kg]
        M = V * rho / 1000
        for N in N_range:
            series = V_series[i]
            
            # calculate power input P [W]
            P = f.power_input(Po=Po, rho_L=rho, N=N, D=Di)

            # *************** Rxn vs Micromixing ****************
            # Da_micro: micromixing time vs reaction time (Da_micro = tmicro / trxn)
            # power per unit volume [W/m3]
            eps = P / (V/1000)
            # calculate micromixing time [s]
            tmicro = f.micro_mixing_rate(eps=eps, nu=nu)**(-1)
            Da_micro = tmicro * rxn_rate

            # *************** Rxn vs Macromixing ****************
            # Da_macro: macromixing time vs reaction time (Da_macro = tmacro / trxn)
            # calculate macromixing time [s]
            tmacro = f.tm2(H=float(r[('Liquid Height', 'm')]),
                           T=float(r[('Internal Diameter', 'm')]),
                           D=Di, V=V/1000,
                           eps=eps,
                           mu=float(mix[("Dynamic Viscosity", "mPa.s")]),
                           rho_L=rho, regime="Turbulent")
            Da_macro = tmacro * rxn_rate
            
            # *************** Rxn vs GL Mass Transfer ****************
            # Da_massT: mass transfer time vs reaction time (Da_massT = tmassT / trxn); tmassT = 1/kla

            kla = f.kLa_gas_drawdown(A=0.07, b=0.53, P=P, M=M)
            # calculate Damkohler number for mass transfer to reaction (Da = r_rxn / kla)
            if kla > 0:
                Da_massT = rxn_rate / kla
            else:
                Da_massT = float('inf')

            # **************** Rxn vs Heat Transfer *****************

            Da_heatT = None

            sensitivity_results.append({"Series": series,
                                "Volume (L)": V,
                                "Agitation (rpm)": N,
                                "P/M (W/kg)": P/M,
                                "P/V (W/m3)": P/(V/1000),
                                "kla (1/s)": kla,
                                "tmicro (s)": tmicro,
                                "tmacro (s)": tmacro,
                                "Da_micro": Da_micro,
                                "Da_macro": Da_macro,
                                "Da_massT": Da_massT,
                                "Da_heatT": Da_heatT})
            
    df_sensitivity = pd.DataFrame(sensitivity_results)
    df_sensitivity.to_csv("sensitivity_results.csv", index=False)

    # *************** Rxn vs Micromixing *****************
    st.subheader("Micromixing")

    # check if Da_micro > 1 for any conditions; if so, display warning
    if (df_sensitivity["Da_micro"] > 1).any():
        st.warning("Possible micromixing sensitivities in selected reactor",
                 icon=":material/warning:")
    else:
        st.success("Micromixing sensitivities are unlikely in selected reactor. Confirm with Bourne protocol.",
                 icon=":material/check:")

    # plot Da_micro vs P/V with each volume (min/max) as separate series
    fig = px.line(df_sensitivity,
                  x="P/V (W/m3)",
                  y="Da_micro",
                  color="Series",
                  title=f"Damkohler number for micromixing vs reaction (Da_micro)")
    # add horizontal line at Da_micro=1.0
    fig.add_hline(y=1.0, line_dash="dash",
                  line_color="red",
                    annotation_text="Da_micro=1 (system is micromixing limited above line)",
                    annotation_position="top left")
    st.plotly_chart(fig)

    micromixing_limited = df_sensitivity[df_sensitivity["Da_micro"] > 1].copy()
    if not micromixing_limited.empty:
        figx = px.line(micromixing_limited,
                        x="Agitation (rpm)",
                        y="Da_micro",
                        color="Series",
                        title=f"Conditions where system is micromixing limited (Da_micro > 1)",)
        # add horizontal line at Da_micro=1.0
        figx.add_hline(y=1.0, line_dash="dash",
                        line_color="red")
        st.plotly_chart(figx)

    # *************** Rxn vs Macromixing *****************
    st.divider()
    st.subheader("Macromixing")

    # check if Da_macro > 1 for any conditions; if so, display warning
    if (df_sensitivity["Da_macro"] > 1).any():
        st.warning("Possible macromixing sensitivities in selected reactor",
                 icon=":material/warning:")
    else:
        st.success("Macromixing sensitivities are unlikely in selected reactor",
                 icon=":material/check:")

    # plot Da_macro vs P/V with each volume (min/max) as separate series
    fig2 = px.line(df_sensitivity,
                  x="P/V (W/m3)",
                  y="Da_macro",
                  color="Series",
                  title=f"Damkohler number for macromixing vs reaction (Da_macro)")
    # add horizontal line at Da_macro=1.0
    fig2.add_hline(y=1.0, line_dash="dash",
                  line_color="red",
                    annotation_text="Da_macro=1 (system is macromixing limited above line)",
                    annotation_position="top left")
    st.plotly_chart(fig2)

    macromixing_limited = df_sensitivity[df_sensitivity["Da_macro"] > 1].copy()
    if not macromixing_limited.empty:
        fig3 = px.line(macromixing_limited,
                        x="Agitation (rpm)",
                        y="Da_macro",
                        color="Series",
                        title=f"Conditions where system is macromixing limited (Da_macro > 1)",)
        # add horizontal line at Da_macro=1.0
        fig3.add_hline(y=1.0, line_dash="dash",
                        line_color="red")
        st.plotly_chart(fig3)

    # *************** Rxn vs Mass Transfer *****************
    st.divider()
    st.subheader("Gas-liquid Mass Transfer")

    # check if Da_massT > 1 for any conditions; if so, display warning
    if (df_sensitivity["Da_massT"] > 1).any():
        st.warning("Possible gas-liquid mass transfer sensitivities",
                 icon=":material/warning:")
    else:
        st.success("Gas-liquid mass transfer sensitivities are unlikely in selected reactor",
                 icon=":material/check:")
        
    # plot Da_massT vs P/V with each volume (min/max) as separate series
    fig4 = px.line(df_sensitivity,
                    x="P/V (W/m3)",
                    y="Da_massT",
                    color="Series",
                    title=f"Damkohler number for gas-liquid mass transfer vs reaction (Da_massT)",
                    log_y=True)
    # add horizontal line at Da_massT=1.0
    fig4.add_hline(y=1.0, line_dash="dash",
                    line_color="red",
                    annotation_text="Da_massT=1 (system is gas-liquid mass transfer limited above line)",
                    annotation_position="top right")
    st.plotly_chart(fig4)

    # check where Da_massT > 1 in dataframe and plot Da_massT vs agitation speed for those conditions
    mass_transfer_limited = df_sensitivity[df_sensitivity["Da_massT"] > 1].copy()
    if not mass_transfer_limited.empty:
        fig5 = px.line(mass_transfer_limited,
                        x="Agitation (rpm)",
                        y="Da_massT",
                        color="Series",
                        title=f"Conditions where system is gas-liquid mass transfer limited (Da_massT > 1)",)
        # add horizontal line at Da_massT=1.0
        fig5.add_hline(y=1.0, line_dash="dash",
                        line_color="red")
        st.plotly_chart(fig5)

    # *************** Rxn vs Heat Transfer *****************
    st.divider()
    st.subheader("Heat Transfer")
