import streamlit as st
import pandas as pd

st.header("Theory")

equations = pd.read_csv("properties/equations.csv")
equation_meta = equations[['No.', 'Description', 'Source']].copy()

def display_latex_in_dataframe():
    """
    This function creates and displays a Streamlit table
    with a column containing LaTeX equations (but cannot render Latex in the table).
    """
    st.dataframe(equation_meta, hide_index=True)

    # 3. Display the equations separately for clarity (as a workaround)
    st.write("---")
    st.write("### Rendered Equations")
    
    # Loop through the dataframe to display each equation using st.latex
    for index, row in equations.iterrows():
        st.write(f"**({row['No.']}) {row['Description']}**: ")
        st.latex(row['Equation'])

if __name__ == '__main__':
    display_latex_in_dataframe()

