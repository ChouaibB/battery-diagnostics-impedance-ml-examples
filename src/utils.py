from __future__ import annotations

from pathlib import Path
from typing import Tuple

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA_ROOT = PROJECT_ROOT / "data" / "DIB_Data"


# ---------------------------------------------------------------------
# Low-level helpers (adapted from 02 – SoH from EIS)
# ---------------------------------------------------------------------

def parse_eis_filename(path: Path) -> dict:
    """
    Parse an EIS filename of the form:
    Cell02_95SOH_15degC_05SOC_9505.xls

    Returns a dict with:
    - filepath, cell_id, soh_pct, temp_c, soc_pct, capacity_code
    """
    stem = path.stem  # drop extension
    parts = stem.split("_")
    if len(parts) != 5:
        raise ValueError(f"Unexpected EIS filename format: {path.name}")

    cell_str, soh_str, temp_str, soc_str, cap_str = parts

    cell_id = int(cell_str.replace("Cell", ""))
    soh_pct = int(soh_str.replace("SOH", ""))
    temp_c = int(temp_str.replace("degC", ""))
    soc_pct = int(soc_str.replace("SOC", ""))
    capacity_code = int(cap_str)

    return {
        "filepath": path,
        "cell_id": cell_id,
        "soh_pct": soh_pct,
        "temp_c": temp_c,
        "soc_pct": soc_pct,
        "capacity_code": capacity_code,
    }


def load_single_eis(path: Path) -> pd.DataFrame:
    """
    Load one EIS .xls file and return a DataFrame with columns:
    frequency_hz, z_real_ohm, z_imag_ohm.

    Any non-numeric rows (e.g. accidental headers) are dropped after
    coercing to numeric.
    """
    df = pd.read_excel(path, header=None)

    # Keep first three columns and assign names
    df = df.iloc[:, :3].copy()
    df.columns = ["frequency_hz", "z_real_ohm", "z_imag_ohm"]

    # Coerce to numeric and drop non-numeric rows
    for col in ["frequency_hz", "z_real_ohm", "z_imag_ohm"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=["frequency_hz", "z_real_ohm", "z_imag_ohm"])

    df = df.astype(
        {
            "frequency_hz": float,
            "z_real_ohm": float,
            "z_imag_ohm": float,
        }
    )

    return df


def load_all_eis(eis_index: pd.DataFrame) -> pd.DataFrame:
    """
    Load all EIS spectra listed in eis_index into a single long-format DataFrame.

    Output columns:
    - cell_id, soh_pct, temp_c, soc_pct, capacity_code
    - frequency_hz, z_real_ohm, z_imag_ohm
    """
    all_records = []

    for _, meta in eis_index.iterrows():
        spec = load_single_eis(meta["filepath"])

        # Attach metadata
        for col in ["cell_id", "soh_pct", "temp_c", "soc_pct", "capacity_code"]:
            spec[col] = meta[col]

        all_records.append(spec)

    return pd.concat(all_records, ignore_index=True)


# ---------------------------------------------------------------------
# Wrapper 1: load + basic processing
# ---------------------------------------------------------------------

def load_and_process_dib_eis(data_root: Path | str = DEFAULT_DATA_ROOT) -> pd.DataFrame:
    """
    Load the Rashid et al. DIB_Data EIS dataset and return a long-format
    EIS DataFrame.

    Output columns:
    - frequency_hz, z_real_ohm, z_imag_ohm
    - cell_id, soh_pct, temp_c, soc_pct, capacity_code

    Any higher-level summaries are left to the notebooks.
    """
    data_root = Path(data_root)
    eis_xls_dir = data_root / ".csvfiles" / "EIS_Test"

    eis_files = sorted(eis_xls_dir.glob("*.xls"))
    if not eis_files:
        raise FileNotFoundError(f"No .xls files found under {eis_xls_dir}")

    eis_index_records = [parse_eis_filename(p) for p in eis_files]
    eis_index_df = pd.DataFrame(eis_index_records)

    eis_long_df = load_all_eis(eis_index_df)
    return eis_long_df


# ---------------------------------------------------------------------
# Wrapper 2: impedance feature engineering
# ---------------------------------------------------------------------

GROUP_COLS = ["cell_id", "soh_pct", "temp_c", "soc_pct"]


def compute_impedance_features(group: pd.DataFrame) -> dict:
    """
    Compute a small set of summary features from one EIS spectrum.

    Per (cell, SoH, T, SOC) test, this returns:
    - R_hf_ohm, R_lf_ohm, delta_R_ohm
    - Zmag_mean / Zmag_std / Zmag_min / Zmag_max
    - phase_mean / phase_std
    - Zmag_f* and phase_f* at a fixed set of target frequencies.
    """
    g = group.sort_values("frequency_hz")

    freq = g["frequency_hz"].to_numpy()
    z_real = g["z_real_ohm"].to_numpy()
    z_imag = g["z_imag_ohm"].to_numpy()
    z_complex = z_real + 1j * z_imag

    mag = np.abs(z_complex)
    phase = np.angle(z_complex)

    # Highest and lowest frequency indices
    idx_hf = np.argmax(freq)
    idx_lf = np.argmin(freq)

    R_hf = z_real[idx_hf]   # approx. ohmic resistance
    R_lf = z_real[idx_lf]   # approx. total resistance

    features = {
        "R_hf_ohm": R_hf,
        "R_lf_ohm": R_lf,
        "delta_R_ohm": R_lf - R_hf,
        "Zmag_mean": float(mag.mean()),
        "Zmag_std": float(mag.std()),
        "Zmag_min": float(mag.min()),
        "Zmag_max": float(mag.max()),
        "phase_mean": float(phase.mean()),
        "phase_std": float(phase.std()),
    }

    # Target frequencies (Hz) at which to sample |Z| and phase
    f_targets = [0.01, 0.1, 1.0, 10.0, 100.0, 1000.0, 10000.0]

    for f_target in f_targets:
        # Find index of closest actual frequency
        idx = int(np.argmin(np.abs(freq - f_target)))
        # Safe suffix for column names, e.g. 0.01 -> "f0p01"
        suffix = str(f_target).replace(".", "p")
        features[f"Zmag_f{suffix}"] = float(mag[idx])
        features[f"phase_f{suffix}"] = float(phase[idx])

    return features


def build_impedance_feature_table(eis_long_df: pd.DataFrame) -> pd.DataFrame:
    """
    Group the long-format EIS data by (cell, SoH, T, SOC) and compute
    engineered impedance features for each spectrum.

    Parameters
    ----------
    eis_long_df : DataFrame
        Output of `load_and_process_dib_eis` (long format).

    Returns
    -------
    features_df : DataFrame
        One row per (cell_id, soh_pct, temp_c, soc_pct) with impedance features.
        This is the ML-ready feature table used by the notebooks.
    """
    feature_records = []

    for keys, group in eis_long_df.groupby(GROUP_COLS):
        feats = compute_impedance_features(group)
        record = dict(zip(GROUP_COLS, keys))
        record.update(feats)
        feature_records.append(record)

    features_df = pd.DataFrame(feature_records)
    return features_df

