import streamlit as st
import numpy as np
import math
import matplotlib.pyplot as plt
import plotly.express as px
import functions as f

st.header("Reactor Selection")

col1, col2 = st.columns(2)

# get global variables needed here
# l = st.session_state.all_liq_props
all_props = st.session_state.mixture

if 'reactor' in st.session_state:
    r = st.session_state.reactor
else:
    r = {}

# convert dataframe entry to dict for easier accessing
try:
    mix = all_props[all_props["Compound"] == "Mixture"].to_dict('records')[0]
except:
    mix = {}
    st.warning("No mixture properties found. Please check inputs.")

if "Solid" in all_props["Phase"].values:
    s = all_props[all_props["Phase"] == "Solid"].iloc[0].to_dict()

# get reactors dataframe
df_reactors = st.session_state['reactors_df'].copy()
# get kla data
df_kla = st.session_state['data_kla_df'].copy()

owners = df_reactors["owner"].unique().tolist()

# get current selection of owner>reactor if available
if len(r) > 0:
    owner_idx = owners.index(r[("Owner", "-")])
    owner = r[("Owner", "-")]
    reactors = df_reactors[df_reactors["owner"]==owner]["reactor"].unique().tolist()
    reactor_idx = reactors.index(r[("Reactor", "-")])
else:
    owner_idx = 0
    reactor_idx = 0

owner = col1.selectbox("Select owner/location:", df_reactors["owner"].unique(),
                       index=owner_idx)

# select current reactor or default to first one (happens when Owner changes)
if len(r) > 0 and r[("Owner", "-")] == owner:
    reactor = col2.selectbox("Select reactor:", df_reactors[df_reactors["owner"]==owner]["reactor"].unique(),
                            index=reactor_idx)
else:
    reactor = col2.selectbox("Select reactor:", df_reactors[df_reactors["owner"]==owner]["reactor"].unique())

df_kla_selection = df_kla[(df_kla["owner"]==owner) & (df_kla["reactor"]==reactor)].copy()

selected_vessel_name = f"{owner} - {reactor}"

# define agitation speed [rpm]
try:
    if ('Impeller Speed', 'rpm') in r.keys():
        rpm = r[('Impeller Speed', 'rpm')]
    else:
        rpm = 100.0 
    rpm = float(col1.text_input("Agitation speed [rpm]", f"{rpm}"))
except:
    st.error("Agitation speed value error!")

# get properties of chosen vessel
df_selection = df_reactors[(df_reactors["owner"]==owner) & (df_reactors["reactor"]==reactor)].copy()

# store selected reactor props as dict
r = dict(zip(zip(df_selection["property"], df_selection["units"]), df_selection["value"]))

# add selected properties back to dict
r[("Owner", "-")] = owner
r[("Reactor", "-")] = reactor
r[('Impeller Speed', 'rpm')] = rpm

# ensure type float where possible
for key, value in r.items():
    try:
        r[key] = float(value)
    except:
        pass

# calculate dish volume [m3]
r[('Dish Volume', 'm3')] = f.dish_volume(r)

D = r[('Internal Diameter', 'm')]
H = r[('Height (tan-tan)', 'm')]
bottom_dish = r[('Bottom Dish Type', '-')]
top_dish = r[('Top Dish Type', '-')]

r[('Liquid Volume', 'L')] = mix[('Volume', 'L')]

# cylinder cross sectional area [m2]
r[('Area', 'm2')] = np.pi * (r[('Internal Diameter', 'm')] / 2)**2

# liquid height [m]
r[('Liquid Height', 'm')] = (r[('Liquid Volume', 'L')]/1e3 - r[('Dish Volume', 'm3')]) / r[('Area', 'm2')]

# round off volume and display
n_dec = np.log10(r[('Liquid Volume', 'L')])
if n_dec < 0:
    n_dec = int(math.floor(n_dec)*(-1)+1)
elif n_dec < 2:
    n_dec = 2
else:
    n_dec = 0

col2.metric("Liquid Volume [L]", f"{r[('Liquid Volume', 'L')]:.{n_dec}f}")

if r[('Liquid Volume', 'L')] > r[("Volume Max", "L")]:
    st.warning("Warning: Liquid volume exceeds maximum vessel capacity!")

r[("Impellers submerged", "")] = 0
for i in range(1, int(r[("Impeller Count", "#")])+1):
    # check if level above clearance plus half blade height
    if (r[(f"Impeller {i} Clearance", "m")] + r[(f"Impeller {i} Height", "m")]/2) < r[('Liquid Height', 'm')]:
        r[("Impellers submerged", "")] = i

st.dataframe(r)

# set reactor properties as global variable
st.session_state.reactor = r.copy()

# ************* Display CAD Renderings *************
# get file path for isometric rendering based on selection
for pic in ["iso", "side"]:
    file_path_iso = f"{'assets/reactors/'}{owner}_{reactor}_{pic}.png"
    # display rendering if file exists
    try:
        st.image(file_path_iso, caption=f"{selected_vessel_name} {pic} view")
    except:
        st.warning(f"No {pic} rendering found for {selected_vessel_name}.")


# ************* PLOT HYDRODYNAMICS FROM DATA/MODELS *************
st.subheader("Vessel Hydrodynamics")

# plot kLa for each fill volume
if not df_kla_selection.empty:
    fig_kla = px.scatter(df_kla_selection, x="stir_speed_rpm", y="kLa_per_sec", color="volume_fill_L",
                         title=f"kLa Data for {selected_vessel_name}",
                         labels={"stir_speed_rpm": "Agitation Speed (rpm)",
                                 "kLa_per_sec": "kLa (1/s)",
                                 "volume_fill_L": "Fill Volume (L)"},
                        color_continuous_scale="Turbo",
                        size_max=10)
    
    fig_kla.update_traces(marker=dict(size=10)) 

    fig_kla.update_layout(legend_title_text='Fill Volume (L)')

    st.plotly_chart(fig_kla, use_container_width=True)

#  ************* DRAW VESSEL SCHEMATIC *************

def draw_vessel(ax, diameter, height, bottom_dish, top_dish, dish_ratio):
    radius = diameter / 2
    
    # Draw cylindrical body
    rect_x = -radius
    rect_y = 0
    rect_width = diameter
    rect_height = height
    ax.add_patch(plt.Rectangle((rect_x, rect_y), rect_width, rect_height, fill=False, edgecolor='black', linewidth=2))

    # Draw bottom dish
    if bottom_dish == "Hemispherical":
        # Simple semicircle
        theta = np.linspace(np.pi, 2 * np.pi, 100)
        x_bottom = radius * np.cos(theta)
        y_bottom = radius * np.sin(theta)
        ax.plot(x_bottom, y_bottom, color='black', linewidth=2)
    elif bottom_dish == "ASME 2:1 Elliptical":
        # Elliptical dish approximation (simplified)
        dish_height = radius * dish_ratio
        theta = np.linspace(np.pi, 2 * np.pi, 100)
        x_bottom = radius * np.cos(theta)
        y_bottom = dish_height * np.sin(theta)
        ax.plot(x_bottom, y_bottom, color='black', linewidth=2)
    elif bottom_dish == "Torispherical":
        # Torispherical dish is more complex, here's a highly simplified representation
        # You'd typically need to calculate knuckle and crown radii.
        # For a basic schematic, you might approximate with a flatter ellipse or a series of arcs.
        dish_height = radius * dish_ratio * 0.75 # Slightly flatter for visual distinction
        theta = np.linspace(np.pi, 2 * np.pi, 100)
        x_bottom = radius * np.cos(theta)
        y_bottom = dish_height * np.sin(theta)
        ax.plot(x_bottom, y_bottom, color='black', linewidth=2)
    else:
        st.toast("Unknown bottom dish type. Skipping drawing.")

    # Draw top dish (same logic, shifted up)
    if top_dish == "Hemispherical":
        theta = np.linspace(0, np.pi, 100)
        x_top = radius * np.cos(theta)
        y_top = height + radius * np.sin(theta)
        ax.plot(x_top, y_top, color='black', linewidth=2)
    elif top_dish == "ASME 2:1 Elliptical":
        dish_height = radius * dish_ratio
        theta = np.linspace(0, np.pi, 100)
        x_top = radius * np.cos(theta)
        y_top = height + dish_height * np.sin(theta)
        ax.plot(x_top, y_top, color='black', linewidth=2)
    elif top_dish == "Torispherical":
        dish_height = radius * dish_ratio * 0.75
        theta = np.linspace(0, np.pi, 100)
        x_top = radius * np.cos(theta)
        y_top = height + dish_height * np.sin(theta)
        ax.plot(x_top, y_top, color='black', linewidth=2)
    else:
        st.toast("Unknown top dish type. Skipping drawing.")

    # Add dimensions as text
    font_size = 8
    ax.text(0, height/2, f'H: {height:.2f}m',
            verticalalignment='center',
            horizontalalignment='center',
            fontsize=font_size)
    ax.text(0, height/2*0.8, f'D: {diameter:.2f}m',
            horizontalalignment='center',
            fontsize=font_size)

    ax.set_aspect('equal', adjustable='box')
    ax.set_xlabel("X (m)", fontsize=font_size)
    ax.set_ylabel("Y (m)", fontsize=font_size)
    ax.set_title(f"{selected_vessel_name} Schematic", fontsize=font_size)
    ax.tick_params(axis='x', labelsize=font_size)
    ax.tick_params(axis='y', labelsize=font_size)
    ax.grid(False)
    
    # Adjust limits to fit the vessel
    max_dim = max(diameter, height)
    ax.set_xlim(-diameter * 0.75, diameter * 0.75) # Adjust based on your preferred padding
    ax.set_ylim(-radius * 1.5, height + radius * 1.5) # Adjust based on your preferred padding


if st.button("Draw Vessel"):
    # Define a consistent figure size in inches
    # Adjust these values (e.g., 5, 8) based on your desired output size
    # and the aspect ratio that best fits your largest vessel.
    desired_fig_width_inches = 2
    desired_fig_height_inches = 4
    fig, ax = plt.subplots(figsize=(desired_fig_width_inches, desired_fig_height_inches))

    # Apply a tight layout engine to handle margins consistently
    # 'constrained' is often better than 'tight' for complex layouts with labels
    fig.set_layout_engine('constrained') # or 'tight'

    draw_vessel(ax, D, H, bottom_dish, top_dish, 0.5)

    # Ensure use_container_width is False to respect figsize
    st.pyplot(fig, use_container_width=False)
    plt.close(fig)
