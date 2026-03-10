from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import rasterio

from config import GRID_SIZE

def plot_monthly_series(df: pd.DataFrame, out_file: Path) -> None:
    x = df["month"].astype(str)

    fig, ax1 = plt.subplots(figsize=(8, 4))

    ax1.plot(x, df["SIF_mean"], marker="o", label="SIF")
    ax1.plot(x, df["EVI_mean"], marker="s", label="EVI")
    ax1.set_xlabel("Month")
    ax1.set_ylabel("SIF / EVI")
    ax1.legend(loc="upper left")

    ax2 = ax1.twinx()
    ax2.plot(x, df["SSR_mean"], marker="^", linestyle="--", label="Solar radiation")
    ax2.set_ylabel("Solar radiation")

    plt.title("Monthly SIF, EVI, and Solar Radiation")
    plt.tight_layout(rect=[0, 0.04, 1, 1])
    plt.savefig(out_file, dpi=300, bbox_inches="tight")
    plt.close()


def plot_sif_vs_radiation(df: pd.DataFrame, out_file: Path) -> None:
    plt.figure(figsize=(5, 4))
    plt.scatter(df["SSR_mean"], df["SIF_mean"], s=40)

    for _, row in df.iterrows():
        plt.annotate(str(int(row["month"])), (row["SSR_mean"], row["SIF_mean"]))

    plt.xlabel("Monthly Mean Solar Radiation")
    plt.ylabel("Monthly Mean SIF")
    plt.title("Monthly SIF vs Solar Radiation")
    plt.tight_layout(rect=[0, 0.04, 1, 1])
    plt.savefig(out_file, dpi=300, bbox_inches="tight")
    plt.close()


def plot_example_raster(tif_file: Path, title: str, out_file: Path, cmap: str) -> None:
    with rasterio.open(tif_file) as src:
        arr = src.read(1).astype("float64")
        nodata = src.nodata
        if nodata is not None:
            arr[arr == nodata] = np.nan

        extent = [
            src.bounds.left,
            src.bounds.right,
            src.bounds.bottom,
            src.bounds.top
        ]

    plt.figure(figsize=(6, 5))
    plt.imshow(arr, cmap=cmap, extent=extent, origin="upper")
    plt.colorbar()
    plt.xlabel("Easting (m)")
    plt.ylabel("Northing (m)")
    plt.title(title)
    plt.tight_layout(rect=[0, 0.04, 1, 1])
    plt.savefig(out_file, dpi=300, bbox_inches="tight")
    plt.close()


def plot_sif_track_map(df_roi: pd.DataFrame, out_file: Path) -> None:
    plt.figure(figsize=(6, 6))
    sc = plt.scatter(
        df_roi["x"],
        df_roi["y"],
        c=df_roi["sif"],
        s=4,
        cmap="viridis"
    )
    plt.colorbar(sc, label="SIF")
    plt.xlabel("Easting (m)")
    plt.ylabel("Northing (m)")
    plt.title("OCO-2 SIF Observations over Southern Finland")
    plt.tight_layout(rect=[0, 0.04, 1, 1])
    plt.savefig(out_file, dpi=300, bbox_inches="tight")
    plt.close()


def plot_spatial_sif_vs_radiation(df: pd.DataFrame, out_file: Path) -> None:
    plt.figure(figsize=(6, 5))
    plt.scatter(df["SSR"], df["SIF_mean"], s=12, alpha=0.6)

    plt.xlabel("Solar Radiation")
    plt.ylabel("Gridded SIF")
    plt.title("Spatial Correlation across All Months: SIF vs Solar Radiation")
    plt.tight_layout(rect=[0, 0.04, 1, 1])
    plt.savefig(out_file, dpi=300, bbox_inches="tight")
    plt.close()


def plot_spatial_sif_vs_evi(df: pd.DataFrame, out_file: Path) -> None:
    plt.figure(figsize=(6, 5))
    plt.scatter(df["EVI"], df["SIF_mean"], s=12, alpha=0.6)

    plt.xlabel("EVI")
    plt.ylabel("Gridded SIF")
    plt.title("Spatial Correlation across All Months: SIF vs EVI")
    plt.tight_layout(rect=[0, 0.04, 1, 1])
    plt.savefig(out_file, dpi=300, bbox_inches="tight")
    plt.close()


def plot_gridded_sif_map(
    df: pd.DataFrame,
    out_file: Path,
    grid_size: int = GRID_SIZE
) -> None:
    plt.figure(figsize=(6, 6))
    sc = plt.scatter(
        df["x_grid"] + grid_size / 2,
        df["y_grid"] + grid_size / 2,
        c=df["SIF_mean"],
        s=45,
        cmap="viridis"
    )
    plt.colorbar(sc, label="Gridded SIF")
    plt.xlabel("Easting (m)")
    plt.ylabel("Northing (m)")
    plt.title("Gridded SIF Map (All Matched Cells, All Months)")
    plt.tight_layout(rect=[0, 0.04, 1, 1])
    plt.savefig(out_file, dpi=300, bbox_inches="tight")
    plt.close()

def plot_hexbin_sif_vs_evi(df: pd.DataFrame, out_file: Path) -> None:
    plt.figure(figsize=(6, 5))
    hb = plt.hexbin(df["EVI"], df["SIF_mean"], gridsize=50, mincnt=1)
    plt.colorbar(hb, label="Cell count")
    plt.xlabel("EVI")
    plt.ylabel("Gridded SIF")
    plt.title("Hexbin Density: SIF vs EVI")
    plt.tight_layout(rect=[0, 0.04, 1, 1])
    plt.savefig(out_file, dpi=300, bbox_inches="tight")
    plt.close()


def plot_hexbin_sif_vs_radiation(df: pd.DataFrame, out_file: Path) -> None:
    plt.figure(figsize=(6, 5))
    hb = plt.hexbin(df["SSR"], df["SIF_mean"], gridsize=50, mincnt=1)
    plt.colorbar(hb, label="Cell count")
    plt.xlabel("Solar Radiation")
    plt.ylabel("Gridded SIF")
    plt.title("Hexbin Density: SIF vs Solar Radiation")
    plt.tight_layout(rect=[0, 0.04, 1, 1])
    plt.savefig(out_file, dpi=300, bbox_inches="tight")
    plt.close()


def _binned_summary(df: pd.DataFrame, xcol: str, ycol: str, n_bins: int = 20) -> pd.DataFrame:
    temp = df[[xcol, ycol]].dropna().copy()
    bins = np.linspace(temp[xcol].min(), temp[xcol].max(), n_bins + 1)
    temp["bin"] = pd.cut(temp[xcol], bins=bins, include_lowest=True)

    out = (
        temp.groupby("bin", observed=False)[ycol]
        .agg(["median", "mean", "count"])
        .reset_index()
    )

    out = out[out["count"] >= 10].copy()
    out["x_center"] = [b.mid for b in out["bin"]]
    return out


def plot_binned_sif_vs_evi(df: pd.DataFrame, out_file: Path) -> None:
    b = _binned_summary(df, "EVI", "SIF_mean", n_bins=20)

    plt.figure(figsize=(6, 5))
    plt.plot(b["x_center"], b["median"], marker="o", label="Median SIF")
    plt.plot(b["x_center"], b["mean"], marker="s", label="Mean SIF")
    plt.xlabel("EVI")
    plt.ylabel("Gridded SIF")
    plt.title("Binned Relationship: SIF vs EVI")
    plt.legend()
    plt.tight_layout(rect=[0, 0.04, 1, 1])
    plt.savefig(out_file, dpi=300, bbox_inches="tight")
    plt.close()


def plot_binned_sif_vs_radiation(df: pd.DataFrame, out_file: Path) -> None:
    b = _binned_summary(df, "SSR", "SIF_mean", n_bins=20)

    plt.figure(figsize=(6, 5))
    plt.plot(b["x_center"], b["median"], marker="o", label="Median SIF")
    plt.plot(b["x_center"], b["mean"], marker="s", label="Mean SIF")
    plt.xlabel("Solar Radiation")
    plt.ylabel("Gridded SIF")
    plt.title("Binned Relationship: SIF vs Solar Radiation")
    plt.legend()
    plt.tight_layout(rect=[0, 0.04, 1, 1])
    plt.savefig(out_file, dpi=300, bbox_inches="tight")
    plt.close()


def plot_gam_partial_effects(gam, df: pd.DataFrame, out_file: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))

    # valid reference values from fitted data
    ref_month = int(round(df["month"].median()))
    ref_evi = float(df["EVI"].median())
    ref_log_ssr = float(df["log_SSR"].median()) if "log_SSR" in df.columns else float(np.log10(df["SSR"]).median())

    # -------------------------
    # Partial effect of EVI
    # -------------------------
    evi_grid = np.linspace(df["EVI"].min(), df["EVI"].max(), 200)
    X0 = np.column_stack([
        evi_grid,
        np.full(evi_grid.shape, ref_log_ssr, dtype=float),
        np.full(evi_grid.shape, ref_month, dtype=float),
    ])

    p0, ci0 = gam.partial_dependence(term=0, X=X0, width=0.95)
    ci0 = np.asarray(ci0)

    axes[0].plot(evi_grid, p0, lw=2)
    axes[0].fill_between(evi_grid, ci0[:, 0], ci0[:, 1], alpha=0.25)
    axes[0].set_xlabel("EVI")
    axes[0].set_ylabel("Partial effect on SIF")
    axes[0].set_title(f"GAM response: EVI (month={ref_month})")

    # -------------------------
    # Partial effect of log10(SSR)
    # -------------------------
    log_ssr_grid = np.linspace(df["log_SSR"].min(), df["log_SSR"].max(), 200) if "log_SSR" in df.columns \
        else np.linspace(np.log10(df["SSR"]).min(), np.log10(df["SSR"]).max(), 200)

    X1 = np.column_stack([
        np.full(log_ssr_grid.shape, ref_evi, dtype=float),
        log_ssr_grid,
        np.full(log_ssr_grid.shape, ref_month, dtype=float),
    ])

    p1, ci1 = gam.partial_dependence(term=1, X=X1, width=0.95)
    ci1 = np.asarray(ci1)

    ssr_grid = 10 ** log_ssr_grid

    axes[1].plot(ssr_grid, p1, lw=2)
    axes[1].fill_between(ssr_grid, ci1[:, 0], ci1[:, 1], alpha=0.25)
    axes[1].set_xlabel("Solar Radiation")
    axes[1].set_ylabel("Partial effect on SIF")
    axes[1].set_title(f"GAM response: Solar Radiation (month={ref_month})")

    plt.tight_layout(rect=[0, 0.07, 1, 1])
    plt.savefig(out_file, dpi=300, bbox_inches="tight")
    plt.close()