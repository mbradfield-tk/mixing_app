import pandas as pd
import streamlit as st
import numpy as np
import plotly.express as px

# ----------------------------------------------------------
version = 0.1
# ----------------------------------------------------------

st.title("Mixing Scale-Up Tool")
st.badge(f"Version {version}")
st.image("mix_effect.jpg", use_container_width=False,
         width=400)