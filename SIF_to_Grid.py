from pathlib import Path

import numpy as np
import pandas as pd
import rasterio
from rasterio.transform import from_origin

from config import GRID_SIZE

def grid_sif_points(df: pd.DataFrame, grid_size: int = GRID_SIZE) -> pd.DataFrame:
    out = df.copy()
    out["x_grid"] = (np.floor(out["x"] / grid_size) * grid_size).astype(int)
    out["y_grid"] = (np.floor(out["y"] / grid_size) * grid_size).astype(int)

    gridded = (
        out.groupby(["year", "month", "x_grid", "y_grid"], as_index=False)
        .agg(
            SIF_mean=("sif", "mean"),
            SIF_std=("sif", "std"),
            n_obs=("sif", "size")
        )
    )
    return gridded


def sample_raster_at_grid_centers(
    tif_file: Path,
    df: pd.DataFrame,
    value_name: str,
    grid_size: int = GRID_SIZE
) -> pd.DataFrame:
    coords = list(zip(
        df["x_grid"].values + grid_size / 2,
        df["y_grid"].values + grid_size / 2
    ))

    with rasterio.open(tif_file) as src:
        sampled = list(src.sample(coords))
        nodata = src.nodata

    values = np.array([v[0] for v in sampled], dtype=float)

    if nodata is not None:
        values[values == nodata] = np.nan

    out = df.copy()
    out[value_name] = values
    return out


def build_spatial_dataset_all_months(
    sif_roi: pd.DataFrame,
    gee_tif_dir: Path,
    months=range(4, 11),
    grid_size: int = GRID_SIZE
) -> pd.DataFrame:
    all_months = []

    for month in months:
        sif_m = sif_roi[sif_roi["month"] == month].copy()
        if sif_m.empty:
            continue

        grid = grid_sif_points(sif_m, grid_size=grid_size)

        evi_tif = gee_tif_dir / f"EVI_2023_{month:02d}.tif"
        ssr_tif = gee_tif_dir / f"SSR_2023_{month:02d}.tif"

        if not evi_tif.exists() or not ssr_tif.exists():
            print(f"Skipping month {month:02d}: missing TIFF(s)")
            continue

        grid = sample_raster_at_grid_centers(evi_tif, grid, "EVI", grid_size=grid_size)
        grid = sample_raster_at_grid_centers(ssr_tif, grid, "SSR", grid_size=grid_size)

        grid = grid.dropna(subset=["SIF_mean", "EVI", "SSR"]).copy()
        all_months.append(grid)

    if not all_months:
        raise RuntimeError("No valid spatial datasets could be built across months.")

    return pd.concat(all_months, ignore_index=True)


def export_grid_to_tif(
    df: pd.DataFrame,
    value_column: str,
    output_file: Path,
    grid_size: int = GRID_SIZE
) -> None:
    x_min = df["x_grid"].min()
    x_max = df["x_grid"].max()
    y_min = df["y_grid"].min()
    y_max = df["y_grid"].max()

    width = int((x_max - x_min) / grid_size) + 1
    height = int((y_max - y_min) / grid_size) + 1

    raster = np.full((height, width), np.nan)

    for _, row in df.iterrows():
        col = int((row["x_grid"] - x_min) / grid_size)
        row_index = int((y_max - row["y_grid"]) / grid_size)
        raster[row_index, col] = row[value_column]

    transform = from_origin(x_min, y_max + grid_size, grid_size, grid_size)

    with rasterio.open(
        output_file,
        "w",
        driver="GTiff",
        height=raster.shape[0],
        width=raster.shape[1],
        count=1,
        dtype="float32",
        crs="EPSG:3067",
        transform=transform,
        nodata=np.nan
    ) as dst:
        dst.write(raster.astype("float32"), 1)


def export_sif_track_map_tif(
    df: pd.DataFrame,
    output_file: Path,
    grid_size: int = GRID_SIZE
) -> None:
    df = df.copy()

    df["x_grid"] = (np.floor(df["x"] / grid_size) * grid_size).astype(int)
    df["y_grid"] = (np.floor(df["y"] / grid_size) * grid_size).astype(int)

    grid = (
        df.groupby(["x_grid", "y_grid"], as_index=False)
        .agg(SIF_mean=("sif", "mean"))
    )

    x_min = grid["x_grid"].min()
    x_max = grid["x_grid"].max()
    y_min = grid["y_grid"].min()
    y_max = grid["y_grid"].max()

    width = int((x_max - x_min) / grid_size) + 1
    height = int((y_max - y_min) / grid_size) + 1

    raster = np.full((height, width), np.nan)

    for _, row in grid.iterrows():
        col = int((row["x_grid"] - x_min) / grid_size)
        row_index = int((y_max - row["y_grid"]) / grid_size)
        raster[row_index, col] = row["SIF_mean"]

    transform = from_origin(x_min, y_max + grid_size, grid_size, grid_size)

    with rasterio.open(
        output_file,
        "w",
        driver="GTiff",
        height=raster.shape[0],
        width=raster.shape[1],
        count=1,
        dtype="float32",
        crs="EPSG:3067",
        transform=transform,
        nodata=np.nan
    ) as dst:
        dst.write(raster.astype("float32"), 1)

def aggregate_spatial_all_months(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate multi-month spatial data to one value per grid cell.
    """
    return (
        df.groupby(["x_grid", "y_grid"], as_index=False)
        .agg(
            SIF_mean=("SIF_mean", "mean"),
            EVI=("EVI", "mean"),
            SSR=("SSR", "mean"),
            n_obs=("n_obs", "sum")
        )
    )