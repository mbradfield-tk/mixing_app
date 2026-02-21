import pandas as pd
import streamlit as st
import numpy as np

st.header("System Properties")

# get all material properties
df_materials = st.session_state['materials_df'].copy()

# phases
phases = ["Solid", "Liquid", "Gas"]

# ******* INPUT TABLE ********

if 'phases' not in st.session_state:
    st.session_state.phases = None

if 'sys' not in st.session_state:
    initial = {'Compound': 'H2O',
    'Phase': phases[1],
    'Volume [L]': 0.065,
    'Mass [kg]': None,
    'Density [kg/m3]': 1000.0,
    'Dynamic Viscosity [mPa.s]': 1.0,
    'Kinematic Viscosity [m2/s]': 1.0e-6,
    'Surface Tension [N/m]': 0.0728,
    'Particle Size [um]': None,
    }
    st.session_state.sys = pd.DataFrame(initial, index=[0])

if 'mixture' not in st.session_state:
    st.session_state.mixture = pd.DataFrame(columns=st.session_state.sys.columns)

# create multi-index for name>unit hierarchy
def create_new_cols(df):
    columns = df.columns
    names = []
    units = []

    for col in columns:
        # Split on the last occurrence of '[' to handle names with spaces
        if '[' in col:
            name, unit = col.rsplit('[', 1)
        else:
            name, unit = col, ''
        name = name.strip()  # Remove trailing/leading spaces
        unit = unit.rstrip(']').strip()  # Remove ']' and any spaces
        names.append(name)
        units.append(unit)

    # Step 2: Create a MultiIndex from the names and units
    df.columns = pd.MultiIndex.from_arrays([names, units], names=['Property', 'Units'])

    return df

# updates the mixture properties based on inputs table
def update_mixture():

    # complete missing cells
    sys_mod['Mass [kg]'] = np.where(sys_mod['Mass [kg]'].isna(),
                                     (sys_mod['Volume [L]']/1e3)*sys_mod['Density [kg/m3]'],
                                     sys_mod['Mass [kg]'])

    sys_mod['Volume [L]'] = np.where(sys_mod['Volume [L]'].isna(),
                                      (sys_mod['Mass [kg]'] / sys_mod['Density [kg/m3]']) * 1e3,
                                      sys_mod['Volume [L]'])

    sys_mod['Density [kg/m3]'] = np.where(sys_mod['Density [kg/m3]'].isna(),
                                           (sys_mod['Mass [kg]'] / (sys_mod['Volume [L]']/1e3)),
                                           sys_mod['Density [kg/m3]'])
    
    # get phases
    st.session_state.phases = sys_mod['Phase'].unique()

    # check for solids
    if "Solid" in st.session_state.phases:
        st.session_state.solid = True
    else:
        st.session_state.solid = False
        # make aprticle size 0 for all rows
        sys_mod['Particle Size [um]'] = 0.

    df_empty_check = sys_mod.replace('', np.nan).isna()
    if df_empty_check.any().any():
        st.warning("Some cells are still empty after filling. Please check your inputs.")
        stacked_empty = df_empty_check.stack()
        empty_cells = stacked_empty[stacked_empty]
        empty_list = list(empty_cells.index)
        st.write(f"Empty cells at: {empty_list}")

    total_mass = sys_mod['Mass [kg]'].sum()
    total_volume = sys_mod['Volume [L]'].sum()

    # calculate mass and volume fractions
    sys_mod["Mass Frac. [-]"] = sys_mod['Mass [kg]'] / total_mass
    sys_mod["Volume Frac. [-]"] = sys_mod['Volume [L]'] / total_volume

    st.session_state.sys = sys_mod.copy()
    sys_avg = sys_mod.copy()

    # cols to exclude from averaging
    cols_not_avg = ["Compound", "Phase", "Mass Frac. [-]",
                    "Volume Frac. [-]", "Volume [L]", "Mass [kg]"]

    for col in sys_avg.columns:
        # calculate weighted average properties (i.e assumes ideal mixing)
        if col not in cols_not_avg:
            # exclude columns with missing values from averaging
            sys_avg_clean = sys_avg.dropna(subset=[col]).copy()
            try:
                sys_avg[col] = (sys_avg_clean[col] * sys_avg_clean["Mass Frac. [-]"]).sum() / sys_avg_clean["Mass Frac. [-]"].sum()
            except Exception as e:
                st.warning(f"Error calculating average for {col}: {e}")
                sys_avg[col] = 0

    mixture = pd.DataFrame(columns=sys_mod.columns)

    mixture['Compound'] = ['Mixture']
    mixture['Phase'] = ['Liquid']
    mixture['Volume [L]'] = [sys_mod['Volume [L]'].sum()]
    mixture['Mass [kg]'] = [sys_mod['Mass [kg]'].sum()]
    mixture['Mass Frac. [-]'] = [sys_mod['Mass Frac. [-]'].sum()]
    mixture['Volume Frac. [-]'] = [sys_mod['Volume Frac. [-]'].sum()]

    # get average values for properties
    for col in sys_avg.columns:
        if col not in cols_not_avg:
            # get first value in column, since they're all the same
            mixture[col] = [sys_avg[col].values[0]]

    mixture['Density [kg/m3]'] = mixture['Mass [kg]'] / (mixture['Volume [L]']/1e3)
    mixture = pd.concat([sys_mod, mixture], axis=0)

    # create new column names for mixture by extracting the units from [units] and making a tuple (columns, units)
    mixture = create_new_cols(mixture)

    # update state variable
    st.session_state.mixture = mixture

def import_system():
    uploaded_file = st.session_state.sys_upload
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file, header=[0, 1])
        # combine two column headers into one string 'A [B]'
        df.columns = [f"{col[0]} [{col[1]}]" if ("Unnamed" not in col[1]) else col[0] for col in df.columns]
        # drop rows where Compound is mixture
        df = df[df['Compound'] != 'Mixture']
        st.session_state.sys = df.copy()
        st.success("System imported successfully.")

def export_mixture_properties():
    st.session_state.mixture.to_csv("mixture_properties.csv", index=False)

# st.subheader("System Inputs Table")
st.text_area("System Inputs Table",
             "Add new components by adding a row to the table, then defining the component number and properties, or import an existing mixture from a file.",
             height="content")

st.file_uploader("Upload file with system properties", type=["csv"], key="sys_upload",
                 on_change=import_system)

sys_mod = st.data_editor(st.session_state.sys,
                    num_rows="dynamic",
                    key="system_table",
                    hide_index=True,
                    column_config={
                        'Compound': st.column_config.TextColumn(),
                        'Phase': st.column_config.SelectboxColumn(options=phases),
                        'Volume [L]': st.column_config.NumberColumn(),
                        'Mass [kg]': st.column_config.NumberColumn(),
                        'Dynamic Viscosity [mPa.s]': st.column_config.NumberColumn(),
                        'Density [kg/m3]': st.column_config.NumberColumn(format="%.0f"),
                        'Kinematic Viscosity [m2/s]': st.column_config.NumberColumn(format="%.2e"),
                        'Surface Tension [N/m]': st.column_config.NumberColumn(format="%.2e"),
                        'Particle Size [um]': st.column_config.NumberColumn(),
                        'Mass Frac. [-]': st.column_config.NumberColumn(format="%.3f"),
                        'Volume Frac. [-]': st.column_config.NumberColumn(format="%.3f")
                    }
                )

st.button("Update Mixture", on_click=update_mixture)

st.subheader("Mixture Properties")

# create badges for each phases and display all badges on same row
if st.session_state.phases is not None:
    cols = len(st.session_state.phases)
    badge_cols = st.columns(cols, width=120)

    for i, phase in enumerate(st.session_state.phases):
        if phase == "Solid":
            badge_cols[i].badge(phase, color="orange")
        elif phase == "Liquid":
            badge_cols[i].badge(phase, color="blue")
        elif phase == "Gas":
            badge_cols[i].badge(phase, color="green")

st.dataframe(st.session_state.mixture, hide_index=True, width="stretch",
             column_config={
                 1: st.column_config.TextColumn(), # ('Compound', '')
                 2: st.column_config.TextColumn(), # ('Phase', '')
                 3: st.column_config.NumberColumn(format="%.1e"), # ('Volume', 'L')
                 4: st.column_config.NumberColumn(format="%.1e"), # ('Mass', 'kg')
                 5: st.column_config.NumberColumn(format="%.0f"), # ('Density', 'kg/m3')
                 6: st.column_config.NumberColumn(), # ('Dynamic Viscosity', 'mPa.s')
                 7: st.column_config.NumberColumn(format="%.1e"), # ('Kinematic Viscosity', 'm2/s')
                 8: st.column_config.NumberColumn(format="%.1e"), # ('Surface Tension', 'N/m')
                 9: st.column_config.NumberColumn(), # ('Particle Size', 'um')
                 10: st.column_config.NumberColumn(format="%.2f"), # ('Mass Frac.', '-')
                 11: st.column_config.NumberColumn(format="%.2f") # ('Volume Frac.', '-')
             }
            )

st.button("Export Properties", on_click=export_mixture_properties)

solids = st.session_state.sys[st.session_state.sys['Phase'] == 'Solid']