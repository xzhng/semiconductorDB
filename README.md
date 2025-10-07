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
from semiconductor_db import ConvergenceDB
db = ConvergenceDB()
print(db)
kpts=db.get("GaN", "kpt")
print(kpts)
encut=db.get("GaN","encut")
print(encut)
db.plot("GaN")
