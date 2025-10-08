import os
import pandas as pd
import numpy as np
import re
import matplotlib.pyplot as plt

def get_kpt_convergence(df, material, structure, functional="PBE", per_atom=True):
    sub = df[
        (df["material"] == material)
        & (df["structure"] == structure)
        & (df["functional"] == functional)
        & (df["test_type"] == "kpt")
    ].copy()
    if sub.empty:
        raise ValueError(f"No k-point data for {material} ({structure}, {functional})")

    extracted = sub["parameter"].str.extract(r"k(\d+)x(\d+)x(\d+)").astype(float)
    sub["N_kpoints"] = extracted.prod(axis=1)
    energy_col = "energy_per_atom" if per_atom else "energy_total"
    sub = sub[["N_kpoints", energy_col]].sort_values("N_kpoints").reset_index(drop=True)
    sub.rename(columns={energy_col: "Energy (eV/atom)"}, inplace=True)
    return sub


def get_encut_convergence(df, material, structure, functional="PBE", per_atom=True):
    sub = df[
        (df["material"] == material)
        & (df["structure"] == structure)
        & (df["functional"] == functional)
        & (df["test_type"] == "encut")
    ].copy()
    if sub.empty:
        raise ValueError(f"No ENCUT data for {material} ({structure}, {functional})")

    sub["ENCUT"] = sub["parameter"].str.extract(r"(\d+)").astype(float)
    energy_col = "energy_per_atom" if per_atom else "energy_total"
    sub = sub[["ENCUT", energy_col]].sort_values("ENCUT").reset_index(drop=True)
    sub.rename(columns={energy_col: "Energy (eV/atom)"}, inplace=True)
    return sub


class ConvergenceDB:
    """Load convergence data from multiple CSVs inside the `convergence/` folder."""

    def __init__(self, folder_path="convergence"):
        self.folder_path = folder_path
        self.df = self._load_all_data()

    def _load_all_data(self):
        """Read all .csv files in folder and merge into one DataFrame."""
        if not os.path.isdir(self.folder_path):
            raise FileNotFoundError(f"Folder not found: {self.folder_path}")
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
        return pd.concat(frames, ignore_index=True)

    def materials(self):
        return sorted(self.df["material"].unique())

    def structures(self, material):
        return sorted(self.df[self.df["material"] == material]["structure"].unique())

    def functionals(self, material, structure):
        sub = self.df[(self.df["material"] == material) & (self.df["structure"] == structure)]
        return sorted(sub["functional"].unique())

    def get(self, material=None, structure=None, conv_type=None,
            functional="PBE", per_atom=True):
        if conv_type == "kpt":
            return get_kpt_convergence(self.df, material, structure, functional, per_atom)
        elif conv_type == "encut":
            return get_encut_convergence(self.df, material, structure, functional, per_atom)
        else:
            raise ValueError("conv_type must be 'kpt' or 'encut'")

    # plot data
    def plot(self, material, structure, functional="PBE", per_atom=True):
        """Plot both k-point and ENCUT convergence for a given material, structure, and functional."""
        fig, axs = plt.subplots(1, 2, figsize=(10, 4))

        # Left: k-point convergence
        try:
            kpt = self.get(material=material, structure=structure,
                           conv_type="kpt", functional=functional, per_atom=per_atom)
            axs[0].plot(kpt["N_kpoints"], kpt.iloc[:, 1], "-o")
            axs[0].set_xlabel("Total k-points")
            axs[0].set_ylabel("Energy (eV/atom)" if per_atom else "Energy (eV)")
            axs[0].set_title(f"{material} ({structure}, {functional}) k-point")
        except Exception as e:
            axs[0].text(0.5, 0.5, f"No kpt data\n{e}", ha="center", va="center")

        # Right: ENCUT convergence
        try:
            encut = self.get(material=material, structure=structure,
                             conv_type="encut", functional=functional, per_atom=per_atom)
            axs[1].plot(encut["ENCUT"], encut.iloc[:, 1], "-o", color="orange")
            axs[1].set_xlabel("ENCUT (eV)")
            axs[1].set_ylabel("Energy (eV/atom)" if per_atom else "Energy (eV)")
            axs[1].set_title(f"{material} ({structure}, {functional}) ENCUT")
        except Exception as e:
            axs[1].text(0.5, 0.5, f"No encut data\n{e}", ha="center", va="center")

        plt.tight_layout()
        plt.show()
