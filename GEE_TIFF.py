import re
from pathlib import Path

import numpy as np
import pandas as pd
import rasterio


def extract_month_from_name(filename: str) -> int:
    m = re.search(r"_(\d{4})_(\d{2})\.tif$", filename)
    if not m:
        raise ValueError(f"Cannot parse year/month from file name: {filename}")
    return int(m.group(2))


def read_raster_mean(tif_file: Path) -> float:
    with rasterio.open(tif_file) as src:
        arr = src.read(1).astype("float64")
        nodata = src.nodata
        if nodata is not None:
            arr[arr == nodata] = np.nan
        return float(np.nanmean(arr))


def monthly_means_from_tifs(folder: Path, prefix: str, value_name: str) -> pd.DataFrame:
    tif_files = sorted(folder.glob(f"{prefix}_*.tif"))
    if not tif_files:
        raise FileNotFoundError(f"No TIFF files found for prefix '{prefix}' in {folder}")

    records = []
    for tif in tif_files:
        month = extract_month_from_name(tif.name)
        mean_val = read_raster_mean(tif)
        records.append({
            "year": 2023,
            "month": month,
            value_name: mean_val,
            "file": tif.name
        })

    return pd.DataFrame(records).sort_values(["year", "month"]).reset_index(drop=True)