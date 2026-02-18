import pandas as pd
import streamlit as st
import numpy as np
import plotly.express as px

# ----------------------------------------------------------
version = 0.1
# ----------------------------------------------------------

st.title("Mixing and Scale-Up Tool")
st.badge(f"Version {version}")
st.text_area("Overview",
             "This app is designed to help users understand the impact of mixing on reaction kinetics and scale-up. It allows users to input system properties, define reaction kinetics, and assess mixing performance and scale-dependency across different reactor scales. The app includes a reaction browser for exploring different reaction types and their associated kinetics. Users can compile their cases into a report for comparison and analysis.",
             height="content")
st.divider()
st.text_area("2 System Definition",
             "In the System page, users can input the properties of their reaction mixture, including physical properties and composition. This information is crucial for accurate calculations of mixing performance and reaction kinetics.",
             height="content")
st.text_area("3 Reactor Selection",
             "In the Reactor page, users can select from a list of predefined reactors from the Equipment database. This includes information such as reactor geometry, impeller type, and scale (lab, pilot, commercial).",
             height="content")
st.text_area("4 Reaction Kinetics",
             "In the Reactions page, users can define their reaction kinetics by inputting parameters such as rate constants and heat of reaction. The app will calculate the reaction rate and heat generation based on the defined kinetics and mixture properties.",
             height="content")
# st.image("assets/mix_effect.jpg", width="content")