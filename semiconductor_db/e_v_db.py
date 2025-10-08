import os
import pandas as pd

class e_v_db:
    """Load E–V and Vinet fit data from multiple CSVs inside `e_v_db/`."""

    def __init__(self, folder_path="e_v_db"):
        self.folder_path = folder_path
        self.ev_data, self.fit_data = self._load_all_data()

    def _load_all_data(self):
        ev_frames, fit_frames = [], []
        if not os.path.isdir(self.folder_path):
            raise FileNotFoundError(f"Folder not found: {self.folder_path}")

        for fname in os.listdir(self.folder_path):
            path = os.path.join(self.folder_path, fname)
            if not fname.endswith(".csv"):
                continue
            try:
                df = pd.read_csv(path)
                if "Volume(Ang^3)" in df.columns and "Energy(eV)" in df.columns:
                    ev_frames.append(df)
                elif "B (GPa)" in df.columns and "E (eV)" in df.columns:
                    fit_frames.append(df)
            except Exception as e:
                print(f"⚠️ Skipping {fname}: {e}")

        if not ev_frames and not fit_frames:
            raise ValueError(f"No valid data found in {self.folder_path}")

        ev_data = pd.concat(ev_frames, ignore_index=True) if ev_frames else pd.DataFrame()
        fit_data = pd.concat(fit_frames, ignore_index=True) if fit_frames else pd.DataFrame()
        return ev_data, fit_data

    def list_materials(self):
        mats1 = set(self.ev_data["material"].unique()) if not self.ev_data.empty else set()
        mats2 = set(self.fit_data["material"].unique()) if not self.fit_data.empty else set()
        return sorted(mats1.union(mats2))

    def structures(self, material):
        s1 = self.ev_data[self.ev_data["material"] == material]["structure"].unique() if not self.ev_data.empty else []
        s2 = self.fit_data[self.fit_data["material"] == material]["structure"].unique() if not self.fit_data.empty else []
        return sorted(set(s1).union(s2))

    def functionals(self, material, structure):
        s1 = self.ev_data[
            (self.ev_data["material"] == material)
            & (self.ev_data["structure"] == structure)
        ]["functional"].unique()
        s2 = self.fit_data[
            (self.fit_data["material"] == material)
            & (self.fit_data["structure"] == structure)
        ]["functional"].unique()
        return sorted(set(s1).union(s2))

    def get(self, material=None, structure=None, fit_param=None, functional="PBE"):
        fit_param = fit_param.strip().upper()

        if fit_param in ["E-V", "EV", "E_V"]:
            sub = self.ev_data[
                (self.ev_data["material"] == material)
                & (self.ev_data["structure"] == structure)
                & (self.ev_data["functional"] == functional)
            ].copy()
            if sub.empty:
                raise ValueError(f"No E–V data for {material} ({structure}, {functional})")
            return sub.rename(columns={"Volume(Ang^3)": "V", "Energy(eV)": "E"})

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
            raise ValueError(f"Column '{col}' not found in file")

        return float(row[col].iloc[0])
