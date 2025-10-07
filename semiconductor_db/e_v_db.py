import os
import pandas as pd

class e_v_db:
    """
    Database for E–V curves and fitted Vinet parameters (multi-structure).

    Looks for:
        e_v_data.csv
        vinet_fit_summary.csv

    Access:
        db = e_v_db()
        db.get("GaN", "zb", "E")   -> equilibrium energy (float)
        db.get("GaN", "zb", "E-V") -> DataFrame of (V, E)
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
        """List all materials."""
        mats1 = set(self.ev_data["material"].unique())
        mats2 = set(self.fit_data["material"].unique())
        return sorted(mats1.union(mats2))

    def structures(self, material):
        """List all available structures for a given material."""
        s1 = self.ev_data[self.ev_data["material"] == material]["structure"].unique()
        s2 = self.fit_data[self.fit_data["material"] == material]["structure"].unique()
        return sorted(set(s1).union(s2))

    def get(self, material, structure, quantity):
        """
        Retrieve E–V or fitted parameters for a given material and structure.

        quantity options:
            "E"   : equilibrium energy (eV)
            "V"   : equilibrium volume (Ang^3)
            "B"   : bulk modulus (GPa)
            "Bp"  : bulk modulus derivative (dimensionless)
            "E-V" : returns DataFrame of Volume vs Energy
        """
        quantity = quantity.strip().upper()

        # E–V curve
        if quantity in ["E-V", "EV", "E_V"]:
            sub = self.ev_data[
                (self.ev_data["material"] == material)
                & (self.ev_data["structure"] == structure)
            ].copy()
            if sub.empty:
                raise ValueError(f"No E–V data for {material} ({structure})")
            return sub.rename(columns={"Volume(Ang^3)": "V", "Energy(eV)": "E"})

        # Fitted parameters
        row = self.fit_data[
            (self.fit_data["material"] == material)
            & (self.fit_data["structure"] == structure)
        ]
        if row.empty:
            raise ValueError(f"No fit data for {material} ({structure})")

        mapping = {
            "E": "E (eV)",
            "V": "V (Ang^3)",
            "B": "B (GPa)",
            "BP": "Bp"
        }

        if quantity not in mapping:
            raise ValueError("quantity must be one of: E, V, B, Bp, E-V")

        col = mapping[quantity]
        if col not in row.columns:
            raise ValueError(f"Column '{col}' not found in vinet_fit_summary.csv")

        return float(row[col].iloc[0])
