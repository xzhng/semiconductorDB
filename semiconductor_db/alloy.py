import os
import pandas as pd
import numpy as np


class AlloyDB:
    """
    Load and query alloy property data from CSV files inside the `alloy/` folder.

    Each CSV should include:
    ['binary', 'structure', 'functional', 'x_<A>', 'x_<B>', 'formula',
     'lattice_matrix', 'volume(Ang^3)', 'num_atoms', 'total_energy(eV)',
     'bandgap_Gamma(eV)', 'hmix_meV_per_formula']
    """

    def __init__(self, folder_path="alloy", tol=1e-6):
        """
        Parameters
        ----------
        folder_path : str, optional
            Path to the folder containing alloy CSV files.
            Defaults to 'alloy' in the current working directory.
        tol : float, optional
            Tolerance for exact composition match (default: 1e-6).
        """
        self.folder_path = folder_path
        self.match_tol = tol
        self.df = self._load_all_data()

    # ------------------------------------------------------------------
    def _load_all_data(self):
        """Read all .csv files in folder and merge into one DataFrame."""
        if not os.path.isdir(self.folder_path):
            raise FileNotFoundError(f"Alloy folder not found: {self.folder_path}")

        frames = []
        for fname in os.listdir(self.folder_path):
            if fname.endswith(".csv"):
                path = os.path.join(self.folder_path, fname)
                try:
                    frames.append(pd.read_csv(path))
                except Exception as e:
                    print(f"⚠️ Skipping {fname}: {e}")
        if not frames:
            raise ValueError(f"No CSV files found in {self.folder_path}")

        df = pd.concat(frames, ignore_index=True)
        for col in df.columns:
            if col.startswith("x_"):
                df[col] = df[col].astype(float)
        return df

    # ------------------------------------------------------------------
    def binaries(self):
        return sorted(self.df["binary"].unique())

    def structures(self, binary):
        sub = self.df[self.df["binary"] == binary]
        return sorted(sub["structure"].unique())

    def functionals(self, binary, structure):
        sub = self.df[
            (self.df["binary"] == binary)
            & (self.df["structure"] == structure)
        ]
        return sorted(sub["functional"].unique())

    def compositions(self, binary, structure, functional="PBE"):
        sub = self.df[
            (self.df["binary"] == binary)
            & (self.df["structure"] == structure)
            & (self.df["functional"] == functional)
        ]
        cols = [c for c in sub.columns if c.startswith("x_")]
        return np.round(sub[cols].values, 3).tolist()

    # ------------------------------------------------------------------
    def get(self, binary=None, structure=None, property=None,
            functional="PBE", comp=None, as_dict=False):
        """
        Retrieve alloy property data.

        Parameters
        ----------
        binary : str
            e.g. "GaAs InAs" or "InAs GaAs"
        structure : str
            e.g. "zb"
        property : str, optional
            Choose from: GAP, LATTICE, H_MIX, VOLUME
        functional : str, optional
            e.g. "PBE", "HSE"
        comp : list | tuple, required
            Composition as [x_component1, x_component2],
            where order matches the binary string.
            Example: for binary='GaAs InAs', use comp=[0.25, 0.75]
        as_dict : bool, optional
            If True, return a Python dict instead of DataFrame.
        """
        if binary is None or structure is None:
            raise ValueError("binary and structure must be specified.")

        if not (isinstance(comp, (list, tuple)) and len(comp) == 2):
            print("❗Composition must be provided as a list [x_A, x_B].")
            print("Example: for binary='GaAs InAs', use comp=[0.25, 0.75]")
            return None

        try:
            x_1, x_2 = float(comp[0]), float(comp[1])
        except Exception:
            print("❗Both composition entries must be numeric values.")
            return None

        components = binary.split()
        if len(components) != 2:
            print(f"❗Invalid binary format: '{binary}'. Expected two components (e.g. 'GaAs InAs').")
            return None

        comp1, comp2 = components
        possible_orders = [binary, f"{comp2} {comp1}"]

        # Find matching dataset regardless of binary order
        sub = self.df[
            (self.df["binary"].isin(possible_orders))
            & (self.df["structure"] == structure)
            & (self.df["functional"] == functional)
        ].copy()

        if sub.empty:
            print(f"❗No data found for {binary} ({structure}, {functional}).")
            return None

        # Determine which order the dataset uses (from column names)
        cols = [c for c in sub.columns if c.startswith("x_")]
        if len(cols) != 2:
            print("❗Expected two composition columns (x_A, x_B).")
            return None

        col1, col2 = cols

        # Align composition order with the actual column order
        db_components = [col1.replace("x_", ""), col2.replace("x_", "")]
        user_components = [comp1, comp2]

        if db_components == user_components:
            x_target = [x_1, x_2]
        elif db_components == user_components[::-1]:
            x_target = [x_2, x_1]  # flip order if user gave reversed binary
        else:
            print(f"❗Column mismatch: expected {db_components}, got {user_components}")
            return None

        # Strict composition matching
        mask = (
            (np.abs(sub[col1] - x_target[0]) <= self.match_tol) &
            (np.abs(sub[col2] - x_target[1]) <= self.match_tol)
        )
        matched = sub[mask]

        if matched.empty:
            print(f"❗No exact composition match for {binary} with composition [{x_1}, {x_2}].")
            return None

        row = matched.iloc[0]

        # Property mapping
        mapping = {
            "GAP": "bandgap_Gamma(eV)",
            "BANDGAP": "bandgap_Gamma(eV)",
            "H_MIX": "hmix_meV_per_formula",
            "HMIX": "hmix_meV_per_formula",
            "VOLUME": "volume(Ang^3)",
            "VOL": "volume(Ang^3)",
            "LATTICE": "lattice_matrix",
            "LAT": "lattice_matrix",
        }

        if property is None:
            print("ℹ️ No property specified — returning full record.")
            return row.to_dict() if as_dict else pd.DataFrame([row])

        tag = property.strip().upper()
        if tag not in mapping:
            print("❗Invalid property. Use one of: GAP, LATTICE, H_MIX, VOLUME")
            return None

        col = mapping[tag]
        val = row[col]

        # Lattice matrix handling
        if tag in ["LATTICE", "LAT"]:
            if isinstance(val, str):
                try:
                    val = np.array(eval(val))
                except Exception:
                    raise ValueError("Could not parse lattice matrix string.")
            print("Lattice matrix (Ang):")
            print(np.array(val))
            return np.array(val)

        return val

    # ------------------------------------------------------------------
    def __repr__(self):
        n = len(self.df)
        systems = ", ".join(sorted(self.df["binary"].unique()))
        return f"<AlloyDB: {n} entries | systems: {systems}>"
