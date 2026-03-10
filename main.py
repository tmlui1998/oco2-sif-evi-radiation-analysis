import pandas as pd
import numpy as np
from pygam import LinearGAM, s, f

from config import GEE_TIF_DIR, SIF_DIR, OUT_TABLE_DIR, OUT_FIG_DIR, GRID_SIZE
from GEE_TIFF import monthly_means_from_tifs
from OCO_2_NC4 import (
    read_all_sif_files,
    filter_roi_points,
    add_epsg3067_coordinates,
    monthly_sif_summary,
)
from SIF_to_Grid import (
    build_spatial_dataset_all_months,
    export_grid_to_tif,
    export_sif_track_map_tif,
)
from Plotting import (
    plot_monthly_series,
    plot_sif_vs_radiation,
    plot_sif_track_map,
    plot_example_raster,
    plot_spatial_sif_vs_radiation,
    plot_spatial_sif_vs_evi,
    plot_gridded_sif_map,
    plot_hexbin_sif_vs_evi,
    plot_hexbin_sif_vs_radiation,
    plot_binned_sif_vs_evi,
    plot_binned_sif_vs_radiation,
    plot_gam_partial_effects,
)
#Flowchart
"""

                    ┌──────────────────────────┐
                    │      CONFIGURATION       │
                    │        config.py         │
                    │--------------------------│
                    │ ROI bounds               │
                    │ CRS transformer          │
                    │ Grid size                │
                    │ Project directories      │
                    └─────────────┬────────────┘
                                  │
                     ┌────────────▼────────────┐
                     │      INPUT DATA         │
                     │                         │
                     │ 1) OCO-2 SIF (.nc4)     │
                     │ 2) GEE TIFF rasters     │
                     │    • EVI                │
                     │    • Solar Radiation    │
                     └───────┬─────────┬───────┘
                             │         │
                             │         │
                 ┌───────────▼───┐ ┌──▼────────────┐
                 │ OCO_2_NC4.py  │ │ GEE_TIFF.py   │
                 │---------------│ │---------------│
                 │ read nc4      │ │ read rasters  │
                 │ extract SIF   │ │ compute means │
                 │ filter ROI    │ │ monthly stats │
                 │ convert CRS   │ │               │
                 └───────┬───────┘ └───────┬───────┘
                         │                 │
                         │                 │
                ┌────────▼────────┐   ┌───▼─────────────────┐
                │  SIF dataset    │   │  Monthly EVI / SSR  │
                │                 │   │                     │
                │ lat lon sif     │   │ month EVI_mean      │
                │ time month year │   │ month SSR_mean      │
                │ x y coordinates │   │                     │
                └────────┬────────┘   └──────────┬──────────┘
                         │                       │
                         │                       │
                         └──────────┬────────────┘
                                    │
                                    ▼
                     ┌─────────────────────────┐
                     │     TEMPORAL MERGE      │
                     │        main.py          │
                     │-------------------------│
                     │ Merge monthly datasets  │
                     │                         │
                     │ Output table:           │
                     │ SIF_mean                │
                     │ EVI_mean                │
                     │ SSR_mean                │
                     └─────────────┬───────────┘
                                   │
                                   ▼
                    ┌──────────────────────────┐
                    │     SPATIAL GRID         │
                    │      SIF_to_Grid.py      │
                    │--------------------------│
                    │ Aggregate SIF points     │
                    │ to spatial grid cells    │
                    │                          │
                    │ grid cell stats:         │
                    │ SIF_mean                 │
                    │ SIF_std                  │
                    │ n_obs                    │
                    └─────────────┬────────────┘
                                  │
                                  ▼
                   ┌────────────────────────────┐
                   │  RASTER SAMPLING           │
                   │  SIF_to_Grid.py            │
                   │----------------------------│
                   │ Sample raster values       │
                   │ at grid cell centers       │
                   │                            │
                   │ Add:                       │
                   │ EVI                        │
                   │ SSR                        │
                   └─────────────┬──────────────┘
                                 │
                                 ▼
                   ┌────────────────────────────┐
                   │   SPATIAL ANALYSIS DATASET │
                   │                            │
                   │ Columns:                   │
                   │ x_grid y_grid              │
                   │ SIF_mean                   │
                   │ EVI                        │
                   │ SSR                        │
                   │ month                      │
                   │ n_obs                      │
                   └─────────────┬──────────────┘
                                 │
                                 ▼
                    ┌───────────────────────────┐
                    │  DATA CLEANING            │
                    │  prepare_spatial_model    │
                    │---------------------------│
                    │ Filter low vegetation     │
                    │ Remove bad SIF values     │
                    │ log transform radiation   │
                    └─────────────┬─────────────┘
                                  │
                                  ▼
                     ┌─────────────────────────┐
                     │   STATISTICAL MODEL     │
                     │      fit_spatial_gam    │
                     │-------------------------│
                     │ GAM model               │
                     │                         │
                     │ SIF ~ s(EVI)            │
                     │      + s(log SSR)       │
                     │      + month factor     │
                     │                         │
                     │ Outputs:                │
                     │ predictions             │
                     │ pseudo R²               │
                     │ AIC                     │
                     └─────────────┬───────────┘
                                   │
                                   ▼
                    ┌──────────────────────────┐
                    │      VISUALIZATION       │
                    │       Plotting.py        │
                    │--------------------------│
                    │ Monthly time series      │
                    │ SIF vs EVI plots         │
                    │ SIF vs radiation         │
                    │ Hexbin density plots     │
                    │ GAM partial effects      │
                    │ Spatial maps             │
                    └─────────────┬────────────┘
                                  │
                                  ▼
                     ┌────────────────────────┐
                     │      EXPORT OUTPUTS    │
                     │------------------------│
                     │ CSV tables             │
                     │ PNG figures            │
                     │ GeoTIFF maps           │
                     │                        │
                     │ SIF grids              │
                     │ EVI grids              │
                     │ Radiation grids        │
                     └────────────────────────┘
"""

def prepare_spatial_model_data(spatial_all: pd.DataFrame) -> pd.DataFrame:
    df = spatial_all.copy()

    # Remove NaN
    df = df.replace([np.inf, -np.inf], np.nan)
    df = df.dropna(subset=["SIF_mean", "EVI", "SSR", "month", "n_obs"]).copy()

    # Remove very low vegetation / water / snow / bare areas
    # Remove zero/negative radiation
    # Keep only cells with enough SIF observations
    df = df[
        (df["EVI"] >= 0.05) &
        (df["EVI"] <= 1.0) &
        (df["SSR"] > 0) &
        (df["n_obs"] >= 2) &
        (df["SIF_mean"] > -5) &
        (df["SIF_mean"] < 10)
    ].copy()

    # log-transform
    df["log_SSR"] = np.log10(df["SSR"])

    return df

def fit_spatial_gam(df: pd.DataFrame):
    X = df[["EVI", "log_SSR", "month"]].values
    y = df["SIF_mean"].values

    gam = LinearGAM(
        s(0, n_splines=12) +   # EVI
        s(1, n_splines=12) +   # log10(SSR)
        f(2)                   # month factor
    ).fit(X, y)

    df["SIF_pred"] = gam.predict(X)

    stats = gam.statistics_

    pseudo_r2 = stats["pseudo_r2"]["explained_deviance"]
    edof = stats["edof"]
    aic = stats["AIC"]

    print("\n==============================")
    print("GAM MODEL RESULTS")
    print("==============================")

    print(f"N observations: {len(df):,}")
    print(f"Explained deviance (pseudo R²): {pseudo_r2:.4f}")
    print(f"AIC: {aic:.2f}")
    print(f"Effective DOF: {edof:.2f}")

    print("\n--- GAM Summary ---")
    print(gam.summary())

    print("\n--- Term significance ---")
    for i, term in enumerate(["EVI", "Radiation", "Month"]):
        pval = gam.statistics_["p_values"][i]
        print(f"{term}: p = {pval:.3e}")

    pd.DataFrame({
        "metric": [
            "n_obs",
            "pseudo_r2",
            "AIC",
            "edof"
        ],
        "value": [
            len(df),
            pseudo_r2,
            aic,
            edof
        ]
    }).to_csv(
        OUT_TABLE_DIR / "gam_model_metrics.csv",
        index=False
    )
    return gam, df, pseudo_r2

def main():
    # EVI and SSR
    evi_df = monthly_means_from_tifs(GEE_TIF_DIR, prefix="EVI", value_name="EVI_mean")
    ssr_df = monthly_means_from_tifs(GEE_TIF_DIR, prefix="SSR", value_name="SSR_mean")

    gee_monthly = pd.merge(
        evi_df[["year", "month", "EVI_mean"]],
        ssr_df[["year", "month", "SSR_mean"]],
        on=["year", "month"],
        how="inner"
    ).sort_values(["year", "month"]).reset_index(drop=True)

    gee_monthly.to_csv(OUT_TABLE_DIR / "monthly_evi_ssr_from_tif.csv", index=False)

    # SIF
    sif_all = read_all_sif_files(SIF_DIR)
    sif_roi = filter_roi_points(sif_all)

    if sif_roi.empty:
        raise RuntimeError("No SIF observations found inside the ROI.")

    sif_roi = add_epsg3067_coordinates(sif_roi)

    sif_monthly = monthly_sif_summary(sif_roi)
    sif_monthly.to_csv(OUT_TABLE_DIR / "monthly_sif_finland.csv", index=False)

    # Merge EVI, SSR, and SIF
    merged = pd.merge(
        sif_monthly,
        gee_monthly,
        on=["year", "month"],
        how="inner"
    ).sort_values(["year", "month"]).reset_index(drop=True)

    merged.to_csv(OUT_TABLE_DIR / "monthly_sif_evi_ssr_merged.csv", index=False)

    #Monthly correlations
    corr_sif_ssr = merged["SIF_mean"].corr(merged["SSR_mean"])
    corr_sif_evi = merged["SIF_mean"].corr(merged["EVI_mean"])

    print("\nMerged monthly table:")
    print(merged)

    print(f"\nMonthly correlation SIF vs solar radiation: {corr_sif_ssr:.3f}")
    print(f"Monthly correlation SIF vs EVI: {corr_sif_evi:.3f}")

    #Building the spatial dataset across all months
    spatial_all = build_spatial_dataset_all_months(
        sif_roi=sif_roi,
        gee_tif_dir=GEE_TIF_DIR,
        months=range(4, 11),
        grid_size=GRID_SIZE
    )

    spatial_all.to_csv(OUT_TABLE_DIR / "spatial_sif_evi_ssr_all_months.csv", index=False)

    #Running the spatial model across all months
    spatial_model_df = prepare_spatial_model_data(spatial_all)
    gam_model, spatial_model_df, spatial_pseudo_r2 = fit_spatial_gam(spatial_model_df)

    spatial_model_df.to_csv(
        OUT_TABLE_DIR / "spatial_sif_evi_ssr_all_months_filtered.csv",
        index=False
    )

    pd.DataFrame({
        "model": ["GAM: SIF_mean ~ s(EVI) + s(log10(SSR)) + f(month)"],
        "n_used": [len(spatial_model_df)],
        "pseudo_r2_explained_deviance": [spatial_pseudo_r2]
    }).to_csv(
        OUT_TABLE_DIR / "spatial_gam_model_summary.csv",
        index=False
    )

    print(f"\nSpatial GAM pseudo-R2 = {spatial_pseudo_r2:.3f}")
    print(f"Number of filtered matched spatial observations = {len(spatial_model_df)}")

    #Plotting
    plot_monthly_series(merged, OUT_FIG_DIR / "monthly_sif_evi_ssr.png")
    plot_sif_vs_radiation(merged, OUT_FIG_DIR / "monthly_sif_vs_radiation.png")

    plot_sif_track_map(sif_roi, OUT_FIG_DIR / "sif_track_map_epsg3067.png")

    plot_hexbin_sif_vs_radiation(
        spatial_model_df,
        OUT_FIG_DIR / "hexbin_sif_vs_radiation_all_months.png"
    )

    plot_hexbin_sif_vs_evi(
        spatial_model_df,
        OUT_FIG_DIR / "hexbin_sif_vs_evi_all_months.png"
    )

    plot_binned_sif_vs_radiation(
        spatial_model_df,
        OUT_FIG_DIR / "binned_sif_vs_radiation_all_months.png"
    )

    plot_binned_sif_vs_evi(
        spatial_model_df,
        OUT_FIG_DIR / "binned_sif_vs_evi_all_months.png"
    )

    plot_gam_partial_effects(
        gam_model,
        spatial_model_df,
        OUT_FIG_DIR / "gam_partial_effects_sif_evi_ssr.png"
    )

    plot_gridded_sif_map(
        spatial_all,
        OUT_FIG_DIR / "gridded_sif_map_all_months.png",
        grid_size=GRID_SIZE
    )

    for month in sorted(spatial_all["month"].unique()):
        spatial_m = spatial_all[spatial_all["month"] == month].copy()

        export_grid_to_tif(
            spatial_m,
            "SIF_mean",
            OUT_FIG_DIR / f"sif_grid_2023_{month:02d}.tif"
        )

        export_grid_to_tif(
            spatial_m,
            "EVI",
            OUT_FIG_DIR / f"evi_grid_2023_{month:02d}.tif"
        )

        export_grid_to_tif(
            spatial_m,
            "SSR",
            OUT_FIG_DIR / f"radiation_grid_2023_{month:02d}.tif"
        )

    export_sif_track_map_tif(
        sif_roi,
        OUT_FIG_DIR / "sif_track_map_epsg3067.tif"
    )

    print("\nDone.")
    print(f"Tables:  {OUT_TABLE_DIR.resolve()}")
    print(f"Figures: {OUT_FIG_DIR.resolve()}")


if __name__ == "__main__":
    main()