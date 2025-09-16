import pandas as pd
import streamlit as st
import numpy as np
import plotly.express as px
import functions as f


l = st.session_state.all_liq_props
s = st.session_state.solid_props
r = st.session_state.reactor
n_l = st.session_state.num_liquids
l_avg = l.loc['mixture'].to_dict()

# dynamic viscosity [mPa.s]
mu = l_avg[("dynamic viscosity", "mPa.s")]
# kinematic viscosity [m2/s]
nu = l_avg[("kinematic viscosity", "m2/s")]
# liquid density [kg/m3]
rho_L = l_avg[("density", "kg/m3")]
# solid density [kg/m3]
rho_S = s[("density", "kg/m3")]
# particle diameter [m]
d_P = s[("dp", "um")] / 1e6
# liquid volume [L]
V_l = l_avg[("volume", "L")]

# handle multiple impellers
imp_count = int(r[("Impeller Count", "#")])
r[("Impeller Diameter", "m")] = max([float(r[(f"Impeller {i} Diameter", "m")]) for i in range(1, imp_count + 1)])

# calculate Reynolds number
Re = int(round(f.Re_STR(rho_L, r[("Impeller Diameter", "m")],
                    r[("Impeller Speed", "rpm")], mu), -2))

# Njs = f(S, nu, rho_L, rho_S, X, d_P, D, g=9.81)
NjsZ = round(f.Njs_Z(1, nu, rho_L,
                     rho_S, s[("loading", "%")], d_P, r[("Impeller Diameter", "m")]), 2)
Dam = 0.5

if Re > 4000:
    flow_regime = "Turbulent"
elif Re > 2000:
    flow_regime = "Transitional"
else:
    flow_regime = "Laminar"

# calculate power input [W]
P = sum([f.power_input(r[(f"Impeller {i} Np", "-")], rho_L,
                         r[("Impeller Speed", "rpm")], r[(f"Impeller {i} Diameter", "m")]) for i in range(1, imp_count + 1)])

# calculate mixing time [s]
tmix = round(f.tm2(r[("Liquid Height", "m")], r[("Internal Diameter", "m")], r[("Impeller Diameter", "m")],
                   V_l, P, mu,
                   rho_L, regime=flow_regime), 1)

# calculate mixing time
# tm = round(f.tm1(0.7, r["liquid volume"], r["Impeller Speed"],
#                         r["Impeller Diameter"]), 1)

res1, res2 = st.columns(2)

res1.metric("Reynolds", Re)
res1.metric("Mixing time (tm) [s]", tmix)
res1.metric("Njs (Zwietering)", NjsZ)

res2.metric("Flow regime", flow_regime)
res2.metric("Damkohler", Dam)

st.subheader("Reaction")

st.subheader("Phase")

st.subheader("Energy")