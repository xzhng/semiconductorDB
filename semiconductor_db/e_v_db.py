import os
import pandas as pd

class e_v_db:
    """
    Database for E–V curves and fitted Vinet parameters (multi-structure, multi-functional).

    Example:
        db = e_v_db()
        db.get(material="GaN", structure="zb", fit_param="E", functional="PBE")
    """

    def __init__(self, base_dir="./"):
        self.base_dir = base_dir
        ev_path = os.path.join(base_dir, "e_v_data.csv")
        fit_path = os.path.join(base_dir, "vinet_fit_summary.csv")

        if not os.path.exists(ev_path):
            raise FileNotFoundError(f"Missing file: {ev_path}")
        if not os.path.exists(fit_path):
            raise FileNotFoundError(f"Missing file: {fit_path}")

        self.ev_data = pd.read_csv(ev_path)
        self.fit_data = pd.read_csv(fit_path)

    def list_materials(self):
        mats1 = set(self.ev_data["material"].unique())
        mats2 = set(self.fit_data["material"].unique())
        return sorted(mats1.union(mats2))

    def structures(self, material):
        s1 = self.ev_data[self.ev_data["material"] == material]["structure"].unique()
        s2 = self.fit_data[self.fit_data["material"] == material]["structure"].unique()
        return sorted(set(s1).union(s2))

    def functionals(self, material, structure):
        """List available functionals for a given material and structure."""
        s1 = self.ev_data[
            (self.ev_data["material"] == material)
            & (self.ev_data["structure"] == structure)
        ]["functional"].unique()
        s2 = self.fit_data[
            (self.fit_data["material"] == material)
            & (self.fit_data["structure"] == structure)
        ]["functional"].unique()
        return sorted(set(s1).union(s2))

    def get(self, material=None, structure=None, fit_param=None, functional="PBE", *args):
        """
        Retrieve E–V curve or fitted parameters for a material, structure, and functional.

        Args:
            material (str): e.g. "GaN"
            structure (str): e.g. "zb", "wz"
            fit_param (str): "E", "V", "B", "Bp", or "E-V"
            functional (str): e.g. "PBE" (default)
        """
        fit_param = fit_param.strip().upper()

        # Handle E–V data
        if fit_param in ["E-V", "EV", "E_V"]:
            sub = self.ev_data[
                (self.ev_data["material"] == material)
                & (self.ev_data["structure"] == structure)
                & (self.ev_data["functional"] == functional)
            ].copy()
            if sub.empty:
                raise ValueError(f"No E–V data for {material} ({structure}, {functional})")
            return sub.rename(columns={"Volume(Ang^3)": "V", "Energy(eV)": "E"})

        # Handle fitted parameters
        row = self.fit_data[
            (self.fit_data["material"] == material)
            & (self.fit_data["structure"] == structure)
            & (self.fit_data["functional"] == functional)
        ]
        if row.empty:
            raise ValueError(f"No fit data for {material} ({structure}, {functional})")

        mapping = {
            "E": "E (eV)",
            "V": "V (Ang^3)",
            "B": "B (GPa)",
            "BP": "Bp",
        }

        if fit_param not in mapping:
            raise ValueError("fit_param must be one of: E, V, B, Bp, E-V")

        col = mapping[fit_param]
        if col not in row.columns:
            raise ValueError(f"Column '{col}' not found in vinet_fit_summary.csv")

        return float(row[col].iloc[0])
