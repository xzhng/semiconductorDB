# SemiconductorDB

SemiconductorDB is a lightweight Python package for managing and visualizing convergence data in semiconductor calculations.  
It provides a simple database-like interface for storing k-point and ENCUT convergence tests, retrieving results, and generating plots.

---

## Features

- Analyze and visualize k-point and ENCUT convergence trends  
- Unified interface for multiple materials  
- Designed for ab initio workflows (e.g., VASP, Quantum ESPRESSO)  
- Built-in plotting utilities using Matplotlib  

---

## Installation

Clone the repository and install in editable mode:

```bash
git clone git@github.com:xzhng/semiconductorDB.git
cd semiconductorDB
pip install -e .
```

## usages: temporary listing everything

```bash
# Convergence
from semiconductor_db import ConvergenceDB
conv = ConvergenceDB()

kpts = conv.get(material="GaN", structure="zb", conv_type="kpt")
encut = conv.get(material="GaN", structure="zb", conv_type="encut")
conv.plot(material="GaN", structure="zb")

# E-V / Vinet
from semiconductor_db import e_v_db
ev = e_v_db()

E0 = ev.get(material="AlAs", structure="zb", fit_param="E")
V0 = ev.get(material="AlAs", structure="zb", fit_param="V")
B = ev.get(material="AlAs", structure="zb", fit_param="B")
Bprime = ev.get(material="AlAs", structure="zb", fit_param="Bp")
curve = ev.get(material="AlAs", structure="zb", fit_param="E-V")
print(E0,V0,B,Bprime)
print(curve)
```

## web interface

The code currently uses streamlit for web interface. To access, do: 
```bash
streamlit run app.py
```
