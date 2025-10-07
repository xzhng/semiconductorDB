import streamlit as st
from semiconductor_db import ConvergenceDB, get_kpt_convergence, get_encut_convergence
import matplotlib.pyplot as plt

st.set_page_config(page_title="Semiconductor Convergence Explorer", layout="wide")
st.title("Semiconductor Convergence Explorer")

# Initialize the database
db = ConvergenceDB()

# Sidebar controls
with st.sidebar:
    st.header("Select Parameters")
    materials = db.materials()
    material = st.selectbox("Material", materials)
    conv_type = st.selectbox("Convergence Type", ["kpt", "encut"])
    per_atom = st.checkbox("Energy per atom", value=True)
    show_plot = st.checkbox("Show plot", value=True)
    run = st.button("Show results")

# Main display
if run:
    try:
        if conv_type == "kpt":
            st.subheader(f"K-point convergence for {material}")
            data = get_kpt_convergence(db.df, material, per_atom=per_atom)
        else:
            st.subheader(f"ENCUT convergence for {material}")
            data = get_encut_convergence(db.df, material, per_atom=per_atom)

        st.dataframe(data)

        if show_plot:
            # Create a clean, Streamlit-friendly plot
            fig, ax = plt.subplots()
            if conv_type == "kpt":
                ax.plot(data["N_kpoints"], data.iloc[:, 1], "-o")
                ax.set_xlabel("Total k-points")
                ax.set_ylabel("Energy (eV/atom)")
            else:
                ax.plot(data["ENCUT"], data.iloc[:, 1], "-o", color="orange")
                ax.set_xlabel("ENCUT (eV)")
                ax.set_ylabel("Energy (eV/atom)")
            ax.set_title(f"{material} {conv_type} convergence")
            st.pyplot(fig)

    except Exception as e:
        st.error(f"Error: {e}")

