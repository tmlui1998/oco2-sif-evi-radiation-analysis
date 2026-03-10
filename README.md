### Abstract
Solar-induced fluorescence (SIF) has emerged as a powerful satellite observable for monitoring terrestrial photosynthesis and vegetation productivity. This repository provides a reproducible Python workflow for analyzing relationships between OCO-2 SIF observations, vegetation activity (EVI), and surface solar radiation (SSR) across Southern Finland.

The workflow integrates satellite observations, geospatial raster data exported from Google Earth Engine, and spatial aggregation techniques to construct a harmonized dataset linking fluorescence signals with environmental drivers. Nonlinear statistical relationships are then evaluated using a Generalized Additive Model (GAM) framework.

### Study Area
The analysis focuses on Southern Finland, a region characterized by boreal forests, agricultural land, and mixed vegetation systems.
The ROI

Latitude: 60.0 – 62.5

Longitude: 23.0 – 26.5

### Data Sources
SIF measurements are obtained from the Orbiting Carbon Observatory-2 (OCO-2) mission. These data provide direct satellite observations of vegetation photosynthetic activity.

EVI and SSR are obtained from Google Earth Engine. These layers represent vegetation greenness and available incoming radiation.

### Methods
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
                 ┌───────────▼───┐ ┌──▼────────────┐
                 │ OCO_2_NC4.py  │ │ GEE_TIFF.py   │
                 │---------------│ │---------------│
                 │ read nc4      │ │ read rasters  │
                 │ extract SIF   │ │ compute means │
                 │ filter ROI    │ │ monthly stats │
                 │ convert CRS   │ │               │
                 └───────┬───────┘ └───────┬───────┘
                         │                 │
                ┌────────▼────────┐   ┌───▼─────────────────┐
                │  SIF dataset    │   │  Monthly EVI / SSR  │
                │ lat lon sif     │   │ month EVI_mean      │
                │ time month year │   │ month SSR_mean      │
                │ x y coordinates │   │                     │
                └────────┬────────┘   └──────────┬──────────┘
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
                    │ SIF_mean                 │
                    │ SIF_std                  │
                    │ n_obs                    │
                    └─────────────┬────────────┘
                                  │
                                  ▼
                   ┌────────────────────────────┐
                   │  RASTER SAMPLING           │
                   │  SIF_to_Grid.py            │
                   │ Sample raster values       │
                   │ Add: EVI, SSR              │
                   └─────────────┬──────────────┘
                                 │
                                 ▼
                   ┌────────────────────────────┐
                   │   SPATIAL ANALYSIS DATASET │
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
                    │ prepare_spatial_model     │
                    │ log transform radiation   │
                    └─────────────┬─────────────┘
                                  │
                                  ▼
                     ┌─────────────────────────┐
                     │   STATISTICAL MODEL     │
                     │      fit_spatial_gam    │
                     │ GAM model               │
                     │ SIF ~ s(EVI) + s(log SSR)
                     │ + month factor          │
                     └─────────────┬───────────┘
                                   │
                                   ▼
                    ┌──────────────────────────┐
                    │      VISUALIZATION       │
                    │       Plotting.py        │
                    └─────────────┬────────────┘
                                  │
                                  ▼
                     ┌────────────────────────┐
                     │      EXPORT OUTPUTS    │
                     │ CSV tables, figures    │
                     │ GeoTIFF maps           │
                     └────────────────────────┘

### Statistical Model
