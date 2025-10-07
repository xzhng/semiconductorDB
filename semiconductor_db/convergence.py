import pandas as pd
import numpy as np
import re
import matplotlib.pyplot as plt

def get_kpt_convergence(df, material, structure, per_atom=True):
    """Return (N_kpoints, Energy) for k-point convergence of a given material and structure."""
    sub = df[
        (df["material"] == material)
        & (df["structure"] == structure)
        & (df["test_type"] == "kpt")
    ].copy()
    if sub.empty:
        raise ValueError(f"No k-point data for {material} ({structure})")

    extracted = sub["parameter"].str.extract(r"k(\d+)x(\d+)x(\d+)").astype(float)
    sub["kgrid"] = list(zip(extracted[0], extracted[1], extracted[2]))
    sub["N_kpoints"] = sub["kgrid"].apply(lambda x: np.prod(x))

    energy_col = "energy_per_atom" if per_atom else "energy_total"
    sub = sub[["N_kpoints", energy_col]].sort_values("N_kpoints").reset_index(drop=True)
    sub.rename(columns={energy_col: "Energy (eV/atom)"}, inplace=True)
    return sub


def get_encut_convergence(df, material, structure, per_atom=True):
    """Return (ENCUT, Energy) for cutoff convergence of a given material and structure."""
    sub = df[
        (df["material"] == material)
        & (df["structure"] == structure)
        & (df["test_type"] == "encut")
    ].copy()
    if sub.empty:
        raise ValueError(f"No ENCUT data for {material} ({structure})")

    sub["ENCUT"] = sub["parameter"].str.extract(r"(\d+)").astype(float)
    sub = sub.dropna(subset=["ENCUT"]).sort_values("ENCUT")

    energy_col = "energy_per_atom" if per_atom else "energy_total"
    sub = sub[["ENCUT", energy_col]].reset_index(drop=True)
    sub.rename(columns={energy_col: "Energy (eV/atom)"}, inplace=True)
    return sub


class ConvergenceDB:
    """Lightweight handler for convergence test database (multi-structure)."""

    def __init__(self, csv_path="convergence_database.csv"):
        self.df = pd.read_csv(csv_path)

    def materials(self):
        """Return sorted list of materials."""
        return sorted(self.df["material"].unique())

    def structures(self, material):
        """Return available structures for a given material."""
        sub = self.df[self.df["material"] == material]
        if sub.empty:
            return []
        return sorted(sub["structure"].unique())

    def get(self, material, structure, test="kpt", per_atom=True):
        """Return DataFrame for a given material, structure, and convergence type."""
        if test == "kpt":
            return get_kpt_convergence(self.df, material, structure, per_atom)
        elif test == "encut":
            return get_encut_convergence(self.df, material, structure, per_atom)
        else:
            raise ValueError("test must be 'kpt' or 'encut'")

    def plot(self, material, structure):
        """Plot both k-point and ENCUT convergence for a given material and structure."""
        fig, axs = plt.subplots(1, 2, figsize=(10, 4))
        try:
            kpt = self.get(material, structure, "kpt")
            axs[0].plot(kpt["N_kpoints"], kpt.iloc[:, 1], "-o")
            axs[0].set_xlabel("Total k-points")
            axs[0].set_ylabel("Energy (eV/atom)")
            axs[0].set_title(f"{material} ({structure}) k-point convergence")
        except Exception as e:
            axs[0].text(0.5, 0.5, f"No kpt data\n{e}", ha="center", va="center")

        try:
            encut = self.get(material, structure, "encut")
            axs[1].plot(encut["ENCUT"], encut.iloc[:, 1], "-o", color="orange")
            axs[1].set_xlabel("ENCUT (eV)")
            axs[1].set_ylabel("Energy (eV/atom)")
            axs[1].set_title(f"{material} ({structure}) ENCUT convergence")
        except Exception as e:
            axs[1].text(0.5, 0.5, f"No encut data\n{e}", ha="center", va="center")

        plt.tight_layout()
        plt.show()
