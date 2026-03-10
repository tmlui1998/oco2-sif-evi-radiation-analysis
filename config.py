from pathlib import Path
import warnings
from pyproj import Transformer

warnings.filterwarnings("ignore", category=RuntimeWarning)

# =========================================================
# PATHS AND SETTINGS
# =========================================================

PROJECT_DIR = Path(__file__).resolve().parent.parent
GEE_TIF_DIR = PROJECT_DIR / "data" / "gee_tif"
SIF_DIR = PROJECT_DIR / "data" / "sif_nc4"
OUT_TABLE_DIR = PROJECT_DIR / "output" / "tables"
OUT_FIG_DIR = PROJECT_DIR / "output" / "figures"

OUT_TABLE_DIR.mkdir(parents=True, exist_ok=True)
OUT_FIG_DIR.mkdir(parents=True, exist_ok=True)

# Southern Finland ROI
LAT_MIN, LAT_MAX = 60.0, 62.5
LON_MIN, LON_MAX = 23.0, 26.5

PREFERRED_SIF_VAR = "SIF_757nm"
GRID_SIZE = 1000  # 10 km
transformer = Transformer.from_crs("EPSG:4326", "EPSG:3067", always_xy=True)