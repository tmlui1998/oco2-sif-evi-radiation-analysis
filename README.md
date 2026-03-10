# Abstract
Solar-induced fluorescence (SIF) has emerged as a powerful satellite observable for monitoring terrestrial photosynthesis and vegetation productivity. This repository provides a reproducible Python workflow for analyzing relationships between OCO-2 SIF observations, vegetation activity (EVI), and surface solar radiation (SSR) across Southern Finland.

The workflow integrates satellite observations, geospatial raster data exported from Google Earth Engine, and spatial aggregation techniques to construct a harmonized dataset linking fluorescence signals with environmental drivers. Nonlinear statistical relationships are then evaluated using a Generalized Additive Model (GAM) framework.

# Study Area
The analysis focuses on Southern Finland, a region characterized by boreal forests, agricultural land, and mixed vegetation systems.
The ROI

Latitude: 60.0 – 62.5

Longitude: 23.0 – 26.5

# Data Sources
SIF measurements are obtained from the Orbiting Carbon Observatory-2 (OCO-2) mission. These data provide direct satellite observations of vegetation photosynthetic activity.

EVI and SSR are obtained from Google Earth Engine. These layers represent vegetation greenness and available incoming radiation.

The data are shown below:

<p float="left", align="middle">
  <img src="/figures/SIF.png" width="30%" />
  <img src="/figures/EVI.png" width="30%" /> 
  <img src="/figures/LogSSR.png" width="30%" />
</p>


# Methods
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

# Statistical Model
A Generalized Additive Model (GAM) is used to model nonlinear relationships between SIF and environmental variables. The model used in this study is:

$$ SIF_{mean}=s(EVI)+s(\log_{10}(SSR))+f(month)+\varepsilon $$

Where:

|                      |                                                        |
| -------------------  | ------------------------------------------------------ |
| $SIF_{mean}$        | Mean solar-induced fluorescence in a spatial grid cell |
| $s(EVI)$            | Smooth nonlinear function of vegetation index          |
| $s(\log_{10}(SSR))$ | Smooth nonlinear function of solar radiation           |
| $f(month)$          | Categorical factor representing seasonal variation     |
| $\varepsilon$       | Random residual error                                  |

## Predictor
The EVI represents the vegetation. It is derived from MODIS satellite observations and serves as a proxy for vegetation density and photosynthetic capacity.

The SSR represents the amount of incoming energy available for photosynthesis. Because radiation values are highly skewed, the predictor is log transformed.

Vegetation productivity varies strongly across the growing season. To account for this, the model includes month as a categorical predictor.

### Smoothing Function
The smoothing function is applied to $EVI$ and  $log_{10}(SSR)$. The smooth terms are estimated using penalized splines:

$$ s(x)=\sum_{n=1}^{K}\beta_{n}B_{n}(x) $$

Where:

$B_{n}(x)$ are spline basis functions,

$\beta_{n}$ are coefficients estimated from the data

$K=12$ is the number of spline basis functions

### Model Estimation
The model is estimated using penalized likelihood optimization:

$$ min \left(\sum(y_{i}-\hat y_{i})-\lambda \int (f''(x))^2dx \right) $$

Where:

The first term is the model fit,

The second term is penalty due to excessive curvature, and

$\lambda is the smoothness$

# Result
## Generalized Additive Mode
To quantify these relationships, a Generalized Additive Model (GAM) was fitted using 1873 observations. All model components were statistically significant. These results indicate that vegetation greenness, solar radiation, and seasonal variation all contribute significantly to explaining spatial variation in SIF.

### Model Parameter
| Parameter                    | Value    |
| ---------------------------- | -------- |
| Distribution                 | Normal   |
| Link Function                | Identity |
| Number of Samples            | 1873     |
| Effective Degrees of Freedom | 19.33    |
| Log Likelihood               | -1492.64 |
| AIC                          | 3025.94  |
| AICc                         | 3026.40  |
| GCV                          | 0.2967   |
| Scale                        | 0.5396   |
| Pseudo R²                    | 0.2507   |

### Model Term
| Term               | Lambda | Rank | Effective DOF | p-value  | Significance |
| ------------------ | ------ | ---- | ------------- | -------- | ------------ |
| s(EVI)             | 0.6    | 12   | 8.6           | 4.91e-04 | ***          |
| s(Solar Radiation) | 0.6    | 12   | 8.1           | 2.72e-05 | ***          |
| Month (factor)     | 0.6    | 7    | 2.7           | 2.27e-13 | ***          |
| Intercept          | —      | 1    | 0.0           | 9.06e-09 | ***          |

The partial response curves from the GAM provide further insight into how vegetation and radiation influence fluorescence.

<p float="left", align="middle">
  <img src="/figures/gam_partial_effects_sif_evi_ssr.png" width="80%" />
</p>

The EVI partial effect shows that very sparse vegetation (EVI < 0.15) is associated with lower SIF values. As EVI increases beyond 0.3, the effect becomes increasingly positive, and the slope steepens substantially when EVI exceeds approximately 0.55. Fluorescence emissions increase rapidly once vegetation becomes sufficiently dense.

The solar radiation partial effect shows a weaker and less monotonic pattern. SIF increases moderately as radiation rises at lower levels but flatter at higher radiation levels. This represents A photosynthetic saturation effect, where plants reach a limit in how efficiently they can use incoming sunlight. Beyond this point, increases in radiation do not produce proportional increases in fluorescence.

## Relationship Between SIF and Vegetation Activity

<p float="left", align="middle">
  <img src="/figures/hexbin_sif_vs_evi_all_months.png" width="80%" />
</p>

The highest concentration of observations occurs within the EVI range of approximately 0.25–0.45, where SIF values typically fall between 0.2 and 0.8. This range corresponds to moderate vegetation density in Southern Finland with forests, mixed vegetation, and agricultural fields.

Areas with higher vegetation density (EVI > 0.45) display substantially larger fluorescence signals, sometimes exceeding 1.0. This indicates that denser vegetation canopies tend to emit stronger fluorescence signals because they contain more chlorophyll and higher photosynthetic capacity.

Regions with greener and denser vegetation tend to exhibit stronger fluorescence signals, reflecting higher levels of photosynthetic activity.

## Relationship Between SIF and Solar Radiation

<p float="left", align="middle">
  <img src="/figures/hexbin_sif_vs_radiation_all_months.png" width="80%" />
</p>
Solar radiation represents the primary energy source driving photosynthesis. However, the relationship between them is more complex than the vegetation relationship.

The hexbin density plot of SIF versus solar radiation shows that observations occur in distinct vertical bands corresponding to different monthly radiation levels. Within each radiation band, SIF values vary widely. For instance, even at similar radiation levels, SIF may range from negative values to over 1.5. This variation indicates that radiation alone cannot fully explain fluorescence emissions.

In general, SIF increases as radiation rises. Solar radiation sets the upper limit of photosynthetic activity, but vegetation structure and seasonal conditions determine how efficiently plants use this energy. Plants cannot indefinitely increase photosynthesis as radiation increases. Instead, photosynthesis eventually saturates, meaning additional sunlight does not lead to higher photosynthetic activity.
