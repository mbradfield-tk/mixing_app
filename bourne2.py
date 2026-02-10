import streamlit as st
import pandas as pd
import functions as fx

st.title("Bourne Protocol")

st.image("assets/bourne_protocol.png", width=400) # "content"

def reset_bourne_protocol():
    st.session_state.bourne_1_result = False
    st.session_state.bourne_2_result = False
    st.session_state.bourne_3_result = False
    st.session_state.step_1_done = False
    st.session_state.step_2_done = False
    st.session_state.step_3_done = False
    del st.session_state.bourne_1_conditions
    del st.session_state.bourne_2_conditions
    del st.session_state.bourne_3_conditions

st.button("Reset Bourne Protocol", on_click=reset_bourne_protocol)

st.divider()

# get reactor varialbes
r = st.session_state.reactor

if 'bourne_1_result' not in st.session_state:
    st.session_state.bourne_1_result = False

if 'bourne_2_result' not in st.session_state:
    st.session_state.bourne_2_result = False

if 'step_1_done' not in st.session_state:
    st.session_state.step_1_done = False

if 'step_2_done' not in st.session_state:
    st.session_state.step_2_done = False

if 'step_3_done' not in st.session_state:
    st.session_state.step_3_done = False

# ************************ STEP 1 ************************

st.subheader("Step 1 - Stir Speed Sensitivity")

col1, col2 = st.columns(2)

# get stir speed range
rpm_min = r[('Agitation Min', 'rpm')]
rpm_max = r[('Agitation Max', 'rpm')]
rpm_mid = (rpm_min + rpm_max) / 2

# get reactor volume range
V_min = r[('Volume Min', 'L')]
V_max = r[('Volume Max', 'L')]
V_mid = (V_min + V_max) / 2

# get centerpoint conditions
rpm_mid = float(col1.text_input("Centerpoint Stir Speed [rpm]", f"{rpm_mid}"))
V_mid = float(col2.text_input("Centerpoint Volume [L]", f"{V_mid}"))

PV_factor = 10

# Calculate rpm values based on 100x P/V changes
rpm_low = round((1/PV_factor * rpm_mid**3)**(1/3), 0)
rpm_high = round((PV_factor * rpm_mid**3)**(1/3), 0)

# create df of conditions
conditions = {'Volume [L]': [V_mid, V_mid, V_mid],
            'Agitation [rpm]': [rpm_low, rpm_mid, rpm_high],
            'KPI': [None, None, None]}

# create new dataframe if not already in session state; otherwise use existing dataframe to preserve user input
if 'bourne_1_conditions' not in st.session_state:
    st.session_state.bourne_1_conditions = pd.DataFrame(conditions, index=[f"{1/PV_factor} P/V",
                                                                        "P/V", f"{PV_factor} P/V"])

def bourne_1_update():
    st.session_state.bourne_1_conditions = bourne_1_mod.copy()
    df = bourne_1_mod.copy()
    # compare centerpoint KPI to low/high
    try:
        kpi_mid = float(df.loc["P/V", "KPI"])
        kpi_low = float(df.loc[f"{1/PV_factor} P/V", "KPI"])
        kpi_high = float(df.loc[f"{PV_factor} P/V", "KPI"])
    except:
        st.error("Error reading KPI values. Please ensure all KPI values are filled in.")
        return

    if abs(kpi_high-kpi_mid)/kpi_mid > 0.1 or abs(kpi_low-kpi_mid)/kpi_mid > 0.1:
        st.warning("KPI is sensitive to stir speed. Process is mixing sensitive. Proceed to Step 2")
        st.session_state.bourne_1_result = True
    else:
        st.success("KPI is NOT sensitive to stir speed. Exit Bourne Protocol.")
        st.session_state.bourne_1_result = False

    st.session_state.step_1_done = True

# update placeholder variable with user input
# ensure table becomes immutable once step is done to preserve results
if st.session_state.step_1_done:
    st.data_editor(st.session_state.bourne_1_conditions, num_rows="fixed", disabled=True)
else:
    bourne_1_mod = st.data_editor(st.session_state.bourne_1_conditions, num_rows="fixed")

if not st.session_state.step_1_done:
    st.button("Run Step 1", on_click=bourne_1_update)
else:
    st.button("Run Step 1", disabled=True)

# add result if Step 1 is done
if st.session_state.step_1_done:

    st.metric("Step 1 Result",
              "Mixing Sensitive" if st.session_state.bourne_1_result else "Not Mixing Sensitive",
              border=True)
    
st.divider()
    
# ************************ STEP 2 ************************

st.subheader("Step 2 - Feed Rate Sensitivity")

col1, col2 = st.columns(2)

# get centerpoint conditions
feed_mid = float(col1.text_input("Centerpoint Feed Rate (Q) [kg/h]", f"{0.1}"))

feed_factor = 3

# Calculate feed rate change based on feed_factor
feed_low = feed_mid / feed_factor
feed_high = feed_factor * feed_mid

rpm_mid = st.session_state.bourne_rpm
V_mid = st.session_state.bourne_volume

# create df of conditions
feed_conditions = {'Feed Rate [kg/h]': [feed_low, feed_mid, feed_high],
            'Agitation [rpm]': [rpm_mid, rpm_mid, rpm_mid],
            'Volume [L]': [V_mid, V_mid, V_mid],
            'KPI': [None, None, None]}

if 'bourne_2_conditions' not in st.session_state:
    st.session_state.bourne_2_conditions = pd.DataFrame(feed_conditions, index=[f"{1/feed_factor} Q", "Q", f"{feed_factor} Q"])

def bourne_2_update():
    st.session_state.bourne_2_conditions = bourne_2_mod.copy()
    df = bourne_2_mod.copy()

    # compare centerpoint KPI to low/high
    kpi_mid = float(df.loc["Q", "KPI"])
    kpi_low = float(df.loc[f"{1/feed_factor} Q", "KPI"])
    kpi_high = float(df.loc[f"{feed_factor} Q", "KPI"])

    if abs(kpi_high-kpi_mid)/kpi_mid > 0.1 or abs(kpi_low - kpi_mid)/kpi_mid > 0.1:
        st.warning("KPI is sensitive to feed rate. Process is meso- or macromixing sensitive. Proceed to Step 3")
        st.session_state.bourne_2_result = True
    else:
        st.success("KPI is NOT sensitive to feed rate. Process is micromixing sensitive.")
        st.session_state.bourne_2_result = False

    st.session_state.step_2_done = True

# ensure table becomes immutable once step is done to preserve results
if st.session_state.step_2_done:
    st.data_editor(st.session_state.bourne_2_conditions, num_rows="fixed", disabled=True)
else:
    bourne_2_mod = st.data_editor(st.session_state.bourne_2_conditions, num_rows="fixed")

if (not st.session_state.step_1_done) or (st.session_state.step_2_done):
    st.button("Run Step 2", disabled=True)
else:
    st.button("Run Step 2", on_click=bourne_2_update)

# add result if Step 2 is done
if st.session_state.step_2_done:

    st.metric("Step 2 Result",
              "Meso-/Macromixing Sensitive" if st.session_state.bourne_2_result else "Micromixing Sensitive",
            border=True)

st.divider()

# ************************ STEP 3 ************************

st.subheader("Step 3 - Feed Location Sensitivity")

col1, col2 = st.columns(2)

rpm_mid = st.session_state.bourne_rpm
V_mid = st.session_state.bourne_volume

# create df of conditions
feed_location = {'Agitation [rpm]': [rpm_mid, rpm_mid, rpm_mid],
                'Volume [L]': [V_mid, V_mid, V_mid],
            'KPI': [None, None, None]}

if 'bourne_3_conditions' not in st.session_state:
    st.session_state.bourne_3_conditions = pd.DataFrame(feed_location, index=["Surface", "Sub-surface", "Impeller Zone"])

def bourne_3_update():
    st.session_state.bourne_3_conditions = bourne_3_mod.copy()
    df = bourne_3_mod.copy()

    # compare centerpoint KPI to low/high
    kpi_mid = float(df.loc["Surface", "KPI"])
    kpi_low = float(df.loc[f"Sub-surface", "KPI"])
    kpi_high = float(df.loc[f"Impeller Zone", "KPI"])

    if abs(kpi_high-kpi_mid)/kpi_mid > 0.1 or abs(kpi_low - kpi_mid)/kpi_mid > 0.1:
        st.warning("KPI is sensitive to feed location. Process is mesomixing sensitive.")
        st.session_state.bourne_3_result = True
    else:
        st.success("KPI is NOT sensitive to feed location. Process is macromixing sensitive.")
        st.session_state.bourne_3_result = False

    st.session_state.step_3_done = True

# ensure table becomes immutable once step is done to preserve results
if st.session_state.step_3_done:
    st.data_editor(st.session_state.bourne_3_conditions, num_rows="fixed", disabled=True)
else:
    bourne_3_mod = st.data_editor(st.session_state.bourne_3_conditions, num_rows="fixed")

if (not st.session_state.step_2_done) or (st.session_state.step_3_done):
    st.button("Run Step 3", disabled=True)
else:
    st.button("Run Step 3", on_click=bourne_3_update)

# add result if Step 3 is done
if st.session_state.step_3_done:

    st.metric("Step 3 Result",
              "Mesomixing Sensitive" if st.session_state.bourne_3_result else "Macromixing Sensitive",
            border=True)
    
st.divider()