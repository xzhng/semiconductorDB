import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

st.set_page_config(page_title="Semiconductor DB", layout="wide")

# === TOP FIGURE ===
st.logo("logo.png", size="large")

from semiconductor_db import (
    ConvergenceDB, get_kpt_convergence, get_encut_convergence, e_v_db
)

st.set_page_config(page_title="Semiconductor Database Explorer", layout="wide")
st.title("Semiconductor Database Explorer")

# Sidebar page selector
mode = st.sidebar.radio(
    "Select view",
    ["Convergence Explorer", "E-V / Vinet Fit Explorer"]
)

# ============================================================
# === 1. Convergence Explorer ================================
# ============================================================
if mode == "Convergence Explorer":
    db = ConvergenceDB()

    with st.sidebar:
        st.header("Select Parameters")

        materials = db.materials()
        material = st.selectbox("Material", materials)

        structures = db.structures(material)
        structure = st.selectbox("Structure", structures)

        # #  Functional dropdown
        functionals = db.functionals(material, structure)
        if not functionals:
            functionals = ["PBE"]
        functional = st.selectbox("Functional", functionals, index=functionals.index("PBE") if "PBE" in functionals else 0)

        conv_type = st.selectbox("Convergence Type", ["kpt", "encut"])
        per_atom = st.checkbox("Energy per atom", value=True)
        show_plot = st.checkbox("Show plot", value=True)
        run = st.button("Show results")

    if run:
        try:
            data = db.get(
                material=material,
                structure=structure,
                conv_type=conv_type,
                functional=functional,
                per_atom=per_atom
            )

            st.subheader(f"{conv_type.upper()} convergence for {material} ({structure}, {functional})")
            st.dataframe(data)

            if show_plot:
                fig, ax = plt.subplots()
                if conv_type == "kpt":
                    ax.plot(data["N_kpoints"], data.iloc[:, 1], "-o")
                    ax.set_xlabel("Total k-points")
                    ax.set_ylabel("Energy (eV/atom)" if per_atom else "Energy (eV)")
                else:
                    ax.plot(data["ENCUT"], data.iloc[:, 1], "-o", color="orange")
                    ax.set_xlabel("ENCUT (eV)")
                    ax.set_ylabel("Energy (eV/atom)" if per_atom else "Energy (eV)")
                ax.set_title(f"{material} ({structure}, {functional}) {conv_type} convergence")
                st.pyplot(fig)

        except Exception as e:
            st.error(f"Error: {e}")
            
# ============================================================
# === 2. E-V / Vinet Fit Explorer ============================
# ============================================================
elif mode == "E-V / Vinet Fit Explorer":
    st.header("E-V / Vinet Fit Explorer")

    try:
        db = e_v_db()
    except Exception as e:
        st.error(f"Could not load E-V database: {e}")
        st.stop()

    with st.sidebar:
        st.header("Select Parameters")

        materials = db.list_materials()
        materials = ["All"] + materials  # prepend "All" option
        material = st.selectbox("Material", materials)

        # === Handle structure selection ===
        if material == "All":
            # Collect all unique structures across all materials
            all_structs = sorted(set().union(*[db.structures(m) for m in db.list_materials() if db.structures(m)]))
            if not all_structs:
                all_structs = ["wz", "zb"]  # fallback if nothing found
            structure = st.selectbox("Structure", all_structs)
        else:
            structures = db.structures(material)
            structure = st.selectbox("Structure", structures)

        # === Handle functional selection ===
        if material == "All":
            # Collect all unique functionals across all materials/structures
            all_funcs = sorted(set().union(*[
                db.functionals(m, structure)
                for m in db.list_materials()
                if structure in db.structures(m)
            ]))
            if not all_funcs:
                all_funcs = ["PBE"]
            functional = st.selectbox("Functional", all_funcs)
        else:
            functionals = db.functionals(material, structure)
            if not functionals:
                functionals = ["PBE"]
            functional = st.selectbox(
                "Functional",
                functionals,
                index=functionals.index("PBE") if "PBE" in functionals else 0
            )

        # === Options and run button ===
        if material != "All":
            show_fit = st.checkbox("Show fitted curve", value=True)
            show_table = st.checkbox("Show fitted parameters", value=True)
        run = st.button("Show results")

    if run:
        try:
            # =====================================================
            # === CASE 1: "All" selected — summary of fits =========
            # =====================================================
            if material == "All":
                all_materials = db.list_materials()
                fit_rows = []

                for mat in all_materials:
                    try:
                        # --- Extract fitted parameters for this material ---
                        E0 = db.get(material=mat, structure=structure, fit_param="E", functional=functional)
                        V0 = db.get(material=mat, structure=structure, fit_param="V", functional=functional)
                        B = db.get(material=mat, structure=structure, fit_param="B", functional=functional)
                        Bp = db.get(material=mat, structure=structure, fit_param="Bp", functional=functional)

                        row = db.fit_data[
                            (db.fit_data["material"] == mat)
                            & (db.fit_data["structure"] == structure)
                            & (db.fit_data["functional"] == functional)
                        ]
                        if row.empty:
                            continue

                        Bbar = float(row["Bbar (eV/Ang^3)"].iloc[0])
                        C = float(row["C"].iloc[0])

                        fit_rows.append({
                            "Material": mat,
                            "Structure": structure,
                            "Functional": functional,
                            "E (eV)": E0,
                            "V₀ (Å³)": V0,
                            "B (GPa)": B,
                            "Bp": Bp
                        })

                    except Exception as e:
                        st.warning(f"Skipping {mat}: {e}")
                        continue

                if fit_rows:
                    fit_data_all = pd.DataFrame(fit_rows)
                    fit_data_all = fit_data_all.sort_values(by="V₀ (Å³)", ignore_index=True)
                    st.subheader(f"Fitted Vinet parameters for all materials ({structure}, {functional})")
                    st.dataframe(fit_data_all)
                    st.markdown(
                        "<i>*For detailed relaxation and fitting data, refer to the tag of each individual material.</i>",
                        unsafe_allow_html=True
                    )

                else:
                    st.warning(f"No fitted data found for any material with {structure} ({functional}).")

            # =====================================================
            # === CASE 2: Single material selected ===============
            # =====================================================
            else:
                # Load E-V data
                data = db.get(material=material, structure=structure, fit_param="E-V", functional=functional)
                st.subheader(f"Energy–Volume data for {material} ({structure}, {functional})")
                st.dataframe(data)

                # Extract fitted parameters
                E0 = db.get(material=material, structure=structure, fit_param="E", functional=functional)
                V0 = db.get(material=material, structure=structure, fit_param="V", functional=functional)
                B = db.get(material=material, structure=structure, fit_param="B", functional=functional)
                Bp = db.get(material=material, structure=structure, fit_param="Bp", functional=functional)

                row = db.fit_data[
                    (db.fit_data["material"] == material)
                    & (db.fit_data["structure"] == structure)
                    & (db.fit_data["functional"] == functional)
                ]
                if row.empty:
                    raise RuntimeError(f"No fit data found for {material} ({structure}, {functional})")

                Bbar = float(row["Bbar (eV/Ang^3)"].iloc[0])
                C = float(row["C"].iloc[0])

                # Table
                if show_table:
                    st.write("**Fitted Vinet Parameters**")
                    st.table(
                        pd.DataFrame(
                            [[E0, V0, B, Bp, Bbar, C]],
                            columns=["E (eV)", "V (Å³)", "B (GPa)", "Bp", "B̄ (eV/Å³)", "C"],
                            index=[f"{material} ({structure}, {functional})"],
                        )
                    )

                # Plot
                if show_fit:
                    V = data["V"] if "V" in data.columns else data["Volume(Ang^3)"]
                    E = data["E"] if "E" in data.columns else data["Energy(eV)"]

                    def vinet_energy_mp(V_in, E_in, Bbar_in, C_in, V0_in):
                        x = (V_in / V0_in) ** (1.0 / 3.0)
                        y = C_in * (x - 1.0)
                        return E_in + (C_in ** 2) * Bbar_in * V0_in * (1.0 - (1.0 + y) * np.exp(-y))

                    V_fit = np.linspace(V.min(), V.max(), 300)
                    E_fit = vinet_energy_mp(V_fit, E0, Bbar, C, V0)

                    fig, ax = plt.subplots()
                    ax.plot(V, E, "o", label="DFT data", markersize=6)
                    ax.plot(V_fit, E_fit, "-", color="orange", label="Vinet fit")
                    ax.axvline(V0, linestyle="--", color="gray", alpha=0.5)
                    ax.set_xlabel("Volume (Å³)")
                    ax.set_ylabel("Energy (eV)")
                    ax.set_title(f"{material} ({structure}, {functional}) E–V curve and Vinet fit")
                    ax.legend()
                    st.pyplot(fig)

        except Exception as e:
            st.error(f"Error: {e}")
