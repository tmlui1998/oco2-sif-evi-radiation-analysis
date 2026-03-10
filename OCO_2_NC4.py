import re
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

from config import LAT_MIN, LAT_MAX, LON_MIN, LON_MAX, PREFERRED_SIF_VAR, transformer


def date_from_filename(filename: str) -> pd.Timestamp:
    m = re.search(r"_(\d{6})_", filename)
    if not m:
        raise ValueError(f"Cannot parse date from filename: {filename}")
    return pd.to_datetime(m.group(1), format="%y%m%d")


def choose_sif_variable(ds: xr.Dataset, preferred: str = PREFERRED_SIF_VAR) -> str:
    if preferred in ds.variables:
        return preferred
    candidates = [v for v in ds.data_vars if "sif" in v.lower()]
    if not candidates:
        raise KeyError("No SIF variable found in dataset.")
    return candidates[0]


def extract_sif_file(nc4_file: Path) -> pd.DataFrame:
    ds = xr.open_dataset(nc4_file)
    sif_var = choose_sif_variable(ds)

    lat = ds["Latitude"].values
    lon = ds["Longitude"].values
    sif = ds[sif_var].values

    lat = np.asarray(lat).ravel()
    lon = np.asarray(lon).ravel()
    sif = np.asarray(sif).ravel()

    date = date_from_filename(nc4_file.name)
    time_series = pd.Series([date] * len(lat))

    df = pd.DataFrame({
        "time": time_series,
        "lat": lat,
        "lon": lon,
        "sif": sif
    })

    ds.close()
    return df


def read_all_sif_files(folder: Path) -> pd.DataFrame:
    nc4_files = sorted(folder.glob("*.nc4"))
    if not nc4_files:
        raise FileNotFoundError(f"No .nc4 files found in {folder}")

    parts = []
    for f in nc4_files:
        try:
            parts.append(extract_sif_file(f))
        except Exception as e:
            print(f"Skipping {f.name}: {e}")

    if not parts:
        raise RuntimeError("No valid SIF files could be read.")

    df = pd.concat(parts, ignore_index=True)
    df = df.replace([np.inf, -np.inf], np.nan)
    df = df.dropna(subset=["time", "lat", "lon", "sif"])
    df = df[(df["sif"] > -5) & (df["sif"] < 10)].copy()

    df["year"] = df["time"].dt.year
    df["month"] = df["time"].dt.month
    return df


def filter_roi_points(df: pd.DataFrame) -> pd.DataFrame:
    return df[
        (df["lat"] >= LAT_MIN) & (df["lat"] <= LAT_MAX) &
        (df["lon"] >= LON_MIN) & (df["lon"] <= LON_MAX)
    ].copy()


def add_epsg3067_coordinates(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    x, y = transformer.transform(out["lon"].values, out["lat"].values)
    out["x"] = x
    out["y"] = y
    return out


def monthly_sif_summary(df_roi: pd.DataFrame) -> pd.DataFrame:
    return (
        df_roi.groupby(["year", "month"], as_index=False)
        .agg(
            SIF_mean=("sif", "mean"),
            SIF_std=("sif", "std"),
            n_obs=("sif", "size")
        )
        .sort_values(["year", "month"])
        .reset_index(drop=True)
    )