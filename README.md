# Battery Diagnostics from Impedance — ML Examples

This repository contains a small set of Jupyter notebooks exploring **battery diagnostics from impedance data**.  
The focus is on working with impedance / EIS spectra (and ECM-style features) and building simple ML workflows.

My understanding of the underlying impedance measurements and ECM fitting is mainly based on:

- J. Sihvo, D.-I. Stroe, T. Messo, and T. Roinila,  
  **“A Fast Approach for Battery Impedance Identification Using Pseudo Random Sequence (PRS) Signals,”**  
  *IEEE Transactions on Power Electronics*, vol. 35, no. 3, pp. 2548–2557, 2020.  
  DOI: 10.1109/TPEL.2019.2924286  

- J. Sihvo, T. Roinila, T. Messo, and D.-I. Stroe,  
  **“Novel online fitting algorithm for impedance-based state estimation of Li-ion batteries,”**  
  in *Proc. IECON 2019 – 45th Annual Conference of the IEEE Industrial Electronics Society*, 2019.  
  DOI: 10.1109/IECON.2019.8927338

---

## Repository structure

```
battery-diagnostics-impedance-ml-examples/
├─ LICENSE
├─ README.md
├─ environment.yml
├─ requirements.txt
├─ notebooks/
│   └── 01_eis_soc_exploration.ipynb
├─ data/                    # NOT committed
└─ src/                     # optional helpers
    └─ utils.py
```

- `notebooks/` – main analysis & modelling notebooks.  
- `data/` – local folder for datasets (ignored by git).  
- `src/` – optional Python helpers.

---

## Conda environment

These examples were developed with **conda 25.11.0**.

Create and activate the environment:

```
conda env create -f environment.yml
conda activate batt-imp-ml
jupyter lab
```

The `environment.yml` file lists the main dependencies used in the notebooks.  

For the exact snapshot of the environment used: `requirements.txt`.

```    
pip install -r requirements.txt
```

---

## Data

This repository does **not** include large datasets.

Each notebook has a short "Data" section at the top with:

- download links,
- expected local paths.

To run a notebook:

1. Download the referenced dataset(s) from the provided link(s).  
2. Place the files under the indicated subfolder in `data/`.  
3. Open the notebook and run all cells.

---

## Notebooks overview

- [notebooks/01_eis_soc_exploration.ipynb](notebooks/01_eis_soc_exploration.ipynb) **01 – EIS & SOC Exploration**  
  
  Uses a public LFP SoC EIS dataset (Mustafa et al., Mendeley) to:
  1) load and sanity-check impedance spectra across 11 cells and two repeats,  
  2) visualise Nyquist and Bode plots vs SOC,  
  3) engineer simple impedance features (global stats + |Z|/phase at selected frequencies), and  
  4) train and evaluate SOC regression models (ElasticNet vs RandomForest) with nested GroupKFold splits by battery.

- [notebooks/02_SoH_from_EIS.ipynb](notebooks/02_SoH_from_EIS.ipynb) **02 – SoH from EIS (Rashid et al.)**  

  Uses the Rashid et al. public aging + EIS dataset to:
  1) index and load EIS spectra from Excel files into a tidy long-format table,  
  2) engineer compact impedance features (R_hf/R_lf, |Z|/phase summary stats, |Z|/phase at selected frequencies),  
  3) explore SoH label distribution and (SoH, SOC, T) coverage, and  
  4) train and compare SoH regression models (ElasticNet, XGBoost, Gaussian Process) with nested GroupKFold splits by cell, including GP parity and XGBoost feature-importance plots.


## Planned notebooks

- [WIP] Healthy vs Aged Classification from EIS (also -> DIB_Data; DOI: 10.17632/mn9fb7xdx6.3)
- [WIP] Synthetic Impedance with PyBaMM.

---

