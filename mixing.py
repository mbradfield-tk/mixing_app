import pandas as pd
import streamlit as st
import numpy as np
import plotly.express as px
import functions as f
import math

st.logo("assets/logo.png")
st.header("Mixing Calculations")

# get global variables needed here
all_props = st.session_state.mixture
mix = all_props[all_props["Compound"] == "Mixture"].to_dict('records')[0]
st.write(mix)


if "Solid" in all_props["Phase"].values:
    s = all_props[all_props["Phase"] == "Solid"].to_dict('records')[0]
    s[("Loading", "%")] = s[('Mass','kg')] / mix[('Mass','kg')] * 100
else:
    s = {}
    st.warning("No solids found in mixture. Dependent calcs will return errors.")

r = st.session_state.reactor
rxn = st.session_state.rxn_rate

# compile mixing case and add to report
def add_case():
    if 'report' not in st.session_state:
        st.session_state.report = []

    case_dict = {
        'Owner' : r[("Owner", "-")],
        'Agitation Speed (rpm)' : r[("Impeller Speed", "rpm")],
        'Liquid Volume (L)' : r[("Liquid Volume", "L")],
        'Solid Loading (%)' : s[("Loading", "%")] if s else 0
    }
    case_no = len(st.session_state.report) + 1
    case_name = f"{r[("Reactor", "-")]}_{case_no}"
    df = pd.DataFrame.from_dict(case_dict, orient='index', columns=[case_name])

    st.session_state.report.append(df)

mix1, mix2 = st.columns(2)

# unpack variables for simplicity >>

# dynamic viscosity [mPa.s]
mu = mix[("Dynamic Viscosity", "mPa.s")]
# kinematic viscosity [m2/s]
nu = mix[("Kinematic Viscosity", "m2/s")]
# liquid density [kg/m3]
rho_L = mix[("Density", "kg/m3")]
# liquid volume [L]
V_l = mix[("Volume", "L")]
# stir speed [rpm]
Nsp = r[("Impeller Speed", "rpm")]
# tank diameter [m]
T = r[("Internal Diameter", "m")]
# liquid height [m]
H = r[("Liquid Height", "m")]

# get solids properties
try:
    # solid density [kg/m3]
    rho_S = s[("Density", "kg/m3")]
    if math.isnan(rho_S):
        st.toast("Solid density is NaN. Did you forget to add a density value?")
        raise ValueError("Solid density is NaN.")
    # particle diameter [m]
    d_P = s[("Particle Size", "um")] / 1e6
except:
    st.error("Error with solids properties.")

rpm_min = float(r[("Agitation Min", "rpm")])
rpm_max = float(r[("Agitation Max", "rpm")])
impellers = int(r[("Impeller Count", "#")])
impeller_diameters = [float(r[(f"Impeller {i} Diameter", "m")]) for i in range(1, impellers + 1)]
impeller_clearances = [float(r[(f"Impeller {i} Clearance", "m")]) for i in range(1, impellers + 1)]

impeller_diameter = max(impeller_diameters)

# x inputs
try:
    rpm_min = float(mix1.text_input("Min agitation (rpm)", f"{rpm_min}"))
except:
    print("value error!")
try:
    rpm_max = float(mix2.text_input("Max agitation (rpm)", f"{rpm_max}"))
except:
    print("value error!")

# mixing settings

cbx1, cbx2, cbx3 = st.columns(3)

gas_drawdown = cbx1.checkbox("Gas drawdown", value=False)

st.button("Add to Report", on_click=add_case)

# select Njs correlation
# Njs_lst = ["Zwietering", "GMB", "Devarajulu"]
# Njs_eqn = st.selectbox("Select Njs calculation:", Njs_lst)

st.subheader("Mixing Summary")

# *************** SUSPENSION CALCS ***************

res1, res2, res3 = st.columns(3)

# calculate Njs using different correlations
# Zwietering
try:
    S = float(r["Zwietering S parameter", "-"])
    # calculate solid mass ratio mS/mL*100 [%]
    X = s[("Loading", "%")]
    Njs_Z = f.Njs_Z(S, nu, rho_L, rho_S, X, d_P, impeller_diameter) * 60

    Nsp_sus_frac = Nsp / Njs_Z

    if Nsp_sus_frac >= 1.2:
        sus_cond_Z = "Suspended"
    elif Nsp_sus_frac >= 1.0:
        sus_cond_Z = "Just Suspended"
    elif Nsp_sus_frac >= 0.8:
        sus_cond_Z = "Maybe Suspended"
    else:
        sus_cond_Z = "Not Suspended"

except:
    Njs_Z = 0.0
    Nsp_sus_frac = 0.0
    sus_cond_Z = "Error"
    st.error("Error calculating Njs (Zwietering). Check system properties and Zwietering parameter.")

res1.metric("Njs Zwietering (rpm)", f"{round(Njs_Z, 0):.0f}",
            delta=f"{Nsp_sus_frac:.2f}*Njs | {sus_cond_Z}",
            border=True)

# GMB
try:
    # get reactor parameters
    z = float(r[("GMB z parameter", "-")])
    Po = float(r[("Impeller 1 Np", "-")])
    C = float(r[("Impeller 1 Clearance", "m")])
    # calculate solids volume fraction Vsol/Vslurry [%]
    Xv = s[("Volume", "L")]/mix[("Volume", "L")]*100

    Njs_GMB = f.Njs_GMB(z, Po, impeller_diameter, rho_L, rho_S, Xv, d_P, C) * 60

    Nsp_sus_frac_GMB = Nsp / Njs_GMB

    if Nsp_sus_frac_GMB >= 1.2:
        sus_cond_GMB = "Suspended"
    elif Nsp_sus_frac_GMB >= 1.0:
        sus_cond_GMB = "Just Suspended"
    elif Nsp_sus_frac_GMB >= 0.8:
        sus_cond_GMB = "Maybe Suspended"
    else:
        sus_cond_GMB = "Not Suspended"

except:
    Njs_GMB = 0.0
    Nsp_sus_frac_GMB = 0.0
    sus_cond_GMB = "Error"
    st.error("Error calculating Njs (GMB). Check system properties and GMB parameters.")

res2.metric("Njs GMB (rpm)", f"{round(Njs_GMB, 0):.0f}",
            delta=f"{Nsp_sus_frac_GMB:.2f}*Njs | {sus_cond_GMB}",
            border=True)

rpm_frac_max = (rpm_max - Nsp) / Nsp * 100

# display set-point rpm
res3.metric("Impeller Speed (rpm)", f"{Nsp:.0f}", delta=f"{rpm_frac_max:.0f}% to capacity"
            , border=True)

# ************* GLOBAL DIMENSIONLESS NUMBERS *************

Re = f.Re_STR(rho_L, impeller_diameter, Nsp, mu)

if Re >= 10_000:
    flow_regime= "Turbulent"
elif Re < 10_000 and Re >= 10:
    flow_regime = "Transitional"
else:
    flow_regime = "Laminar"

# format Re values
def format_k(value):
    if abs(value) >= 1_000_000:
        return f"{int(round(value / 1_000_000))}M"
    if abs(value) >= 1_000:
        return f"{int(round(value / 1_000))}k"
    else:
        return str(int(value))

Re_str = format_k(Re)

res1.metric("Reynolds", Re_str, delta=f"{flow_regime}",
            border=True, delta_color="off")

# ************* FREE-SURFACE GAS-LIQUID MASS TRANSFER *************

# calculate impeller power input [W]
# TODO: sum power for multiple impellers
P_imp = f.power_input(r[("Impeller 1 Np", "-")], rho_L, Nsp, impeller_diameter)

# kla = A(P/M)^B = f(A,B,P,M)
kla_agitation = f.kLa_gas_drawdown(0.07, 0.53, P_imp, mix[("Mass", "kg")])
res2.metric("kLa (free-surface) (1/s)", f"{kla_agitation:.3f}", delta="Based on agitation only",
        border=True, delta_color="off")

# ************* DAMKOHLER NUMBERS *************

# (1) reaction rate vs convective mixing

# (2) reaction rate vs mass transfer
Da_2 = rxn['r_rxn'] / kla_agitation
Da_2_result = "Mass Transfer Limited" if Da_2 > 10 else "Kinetically Limited" if Da_2 < 0.1 else "Intermediate"
res3.metric("Da II (reaction/mass transfer)", f"{Da_2:.3f}", delta=f"{Da_2_result}",
        border=True, delta_color="off")

# ************* GAS DRAWDOWN *************

if gas_drawdown:
    # calculate gas drawdown
    if ("Gassing System", "-") not in r:
        gassing_system = "vortexing"
    else:
        # default to vortexing
        gassing_system = "vortexing"

    Nmin_gd = f.Nmin_gas_drawdown(impeller_diameters[-1],
                                impeller_clearances[-1],
                                 gassing_system=gassing_system)

    Nmin_gd_frac = Nsp / Nmin_gd

    if Nmin_gd_frac >= 1.0:
        gassing_cond = "Gas drawdown"
    elif Nmin_gd_frac >= 0.8:
        gassing_cond = "Possible gas drawdown"
    else:
        gassing_cond = "No gas drawdown"

    Nmin_gd_delta = (rpm_max - Nmin_gd)/rpm_max*100

    res2.metric("Nmin Gassing (rpm)", f"{round(Nmin_gd, 0):.0f}",
                delta=f"{Nmin_gd_delta:.0f}% {gassing_cond}",
                border=True)

# *************** MIXING TIMES ***************
eps = P_imp / (mix[("Mass", "kg")])  # power per unit mass [W/kg]

# calculate bulk mixing time at selected stir speed [s]
tm_bulk = f.tm2(H, T, impeller_diameter, V_l/1e3,
                eps, mu=mu/1000, rho_L=rho_L, regime=flow_regime)

# calculate micro-mixing rate [1/s]
tau_micro = f.micro_mixing_rate(eps, nu)

# calculate micro-mixing time [s]
tm_micro = 1 / tau_micro

res1.metric("Agitator Power [W]", f"{P_imp:.2f}", delta=f"",
            border=True, delta_color="off")

res2.metric("Mixing Time (bulk) [s]", f"{tm_bulk:.2f}", delta="",
            border=True)

res3.metric("Micro-mixing Time [s]", f"{tm_micro:.2f}", delta="",
            border=True)

# TODO: circulation time (TODO: max flow calc)
# TODO: local mixing constant

# *************** SCAN FOR TRANSITION SCALE ***************
# TODO: calculate when mixing time becomes an issue


# *************** PLOTS ***************

st.subheader("Mixing Performance Plots")

# calculate parameters
x = np.linspace(rpm_min, rpm_max, 50)
y_Re = f.Re_STR(rho_L, impeller_diameter, x, mu)
y_tm = f.tm1(0.7, V_l, x, impeller_diameter)

# create a plots
# Reynolds number vs rpm
fig1 = px.line(x=x, y=y_Re, title="Re vs rpm",
              labels={'x': "RPM",
                      'y': "Re"})

# Mixing time vs rpm
fig2 = px.line(x=x, y=y_tm, title="tm vs rpm",
              labels={'x': "RPM",
                      'y': "s"})

# show plots
st.plotly_chart(fig1)
st.plotly_chart(fig2)
