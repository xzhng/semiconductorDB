import pandas as pd
import numpy as np
import re
import matplotlib.pyplot as plt

def get_kpt_convergence(df, material, structure, functional="PBE", per_atom=True):
    """Return (N_kpoints, Energy) for k-point convergence of a given material/structure/functional."""
    sub = df[
        (df["material"] == material)
        & (df["structure"] == structure)
        & (df["functional"] == functional)
        & (df["test_type"] == "kpt")
    ].copy()
    if sub.empty:
        raise ValueError(f"No k-point data for {material} ({structure}, {functional})")

    extracted = sub["parameter"].str.extract(r"k(\d+)x(\d+)x(\d+)").astype(float)
    sub["kgrid"] = list(zip(extracted[0], extracted[1], extracted[2]))
    sub["N_kpoints"] = sub["kgrid"].apply(lambda x: np.prod(x))

    energy_col = "energy_per_atom" if per_atom else "energy_total"
    sub = sub[["N_kpoints", energy_col]].sort_values("N_kpoints").reset_index(drop=True)
    sub.rename(columns={energy_col: "Energy (eV/atom)"}, inplace=True)
    return sub


def get_encut_convergence(df, material, structure, functional="PBE", per_atom=True):
    """Return (ENCUT, Energy) for cutoff convergence of a given material/structure/functional."""
    sub = df[
        (df["material"] == material)
        & (df["structure"] == structure)
        & (df["functional"] == functional)
        & (df["test_type"] == "encut")
    ].copy()
    if sub.empty:
        raise ValueError(f"No ENCUT data for {material} ({structure}, {functional})")

    sub["ENCUT"] = sub["parameter"].str.extract(r"(\d+)").astype(float)
    sub = sub.dropna(subset=["ENCUT"]).sort_values("ENCUT")

    energy_col = "energy_per_atom" if per_atom else "energy_total"
    sub = sub[["ENCUT", energy_col]].reset_index(drop=True)
    sub.rename(columns={energy_col: "Energy (eV/atom)"}, inplace=True)
    return sub


class ConvergenceDB:
    """Lightweight handler for convergence test database (multi-structure, multi-functional)."""

    def __init__(self, csv_path="convergence_database.csv"):
        self.df = pd.read_csv(csv_path)

    def materials(self):
        return sorted(self.df["material"].unique())

    def structures(self, material):
        sub = self.df[self.df["material"] == material]
        if sub.empty:
            return []
        return sorted(sub["structure"].unique())

    def functionals(self, material, structure):
        """List available functionals for a given material/structure."""
        sub = self.df[
            (self.df["material"] == material) & (self.df["structure"] == structure)
        ]
        return sorted(sub["functional"].unique())

    def get(self, material=None, structure=None, conv_type=None,
            functional="PBE", per_atom=True, *args):
        """
        Retrieve convergence data.

        Args:
            material (str): material name
            structure (str): structure label
            conv_type (str): "kpt" or "encut"
            functional (str): exchange-correlation functional (default: "PBE")
            per_atom (bool): whether to use per-atom energy
        """
        if conv_type == "kpt":
            return get_kpt_convergence(self.df, material, structure, functional, per_atom)
        elif conv_type == "encut":
            return get_encut_convergence(self.df, material, structure, functional, per_atom)
        else:
            raise ValueError("conv_type must be 'kpt' or 'encut'")

    def plot(self, material, structure, functional="PBE"):
        """Plot both k-point and ENCUT convergence for a given material, structure, and functional."""
        fig, axs = plt.subplots(1, 2, figsize=(10, 4))
        try:
            kpt = self.get(material=material, structure=structure, conv_type="kpt", functional=functional)
            axs[0].plot(kpt["N_kpoints"], kpt.iloc[:, 1], "-o")
            axs[0].set_xlabel("Total k-points")
            axs[0].set_ylabel("Energy (eV/atom)")
            axs[0].set_title(f"{material} ({structure}, {functional}) k-point convergence")
        except Exception as e:
            axs[0].text(0.5, 0.5, f"No kpt data\n{e}", ha="center", va="center")

        try:
            encut = self.get(material=material, structure=structure, conv_type="encut", functional=functional)
            axs[1].plot(encut["ENCUT"], encut.iloc[:, 1], "-o", color="orange")
            axs[1].set_xlabel("ENCUT (eV)")
            axs[1].set_ylabel("Energy (eV/atom)")
            axs[1].set_title(f"{material} ({structure}, {functional}) ENCUT convergence")
        except Exception as e:
            axs[1].text(0.5, 0.5, f"No encut data\n{e}", ha="center", va="center")

        plt.tight_layout()
        plt.show()
