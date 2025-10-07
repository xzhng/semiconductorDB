import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from semiconductor_db import ConvergenceDB

st.set_page_config(page_title="Semiconductor Convergence Database", layout="wide")

# Load database
db = ConvergenceDB("convergence_database.csv")

st.title("📊 Semiconductor Convergence Database")
st.write("Explore k-point and energy cutoff convergence across materials.")

# Sidebar for material and test type
materials = db.materials()
material = st.sidebar.selectbox("Select Material", materials)
test_type = st.sidebar.radio("Select Test Type", ["kpt", "encut"])

# Get data
try:
    df = db.get(material, test_type)
    st.success(f"Loaded data for {material} ({test_type})")
except Exception as e:
    st.error(f"No data available: {e}")
    st.stop()

# Plot
fig, ax = plt.subplots()
x_col = "N_kpoints" if test_type == "kpt" else "ENCUT"
ax.plot(df[x_col], df["Energy (eV/atom)"], "-o")
ax.set_xlabel(x_col)
ax.set_ylabel("Energy (eV/atom)")
ax.set_title(f"{material} {test_type} convergence")
st.pyplot(fig)

# Show table
st.dataframe(df, use_container_width=True)
