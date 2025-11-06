from pathlib import Path

EDUCAST: str = (
    "EduCast: A multimodal hierarchical forecasting framework for university enrollments"
)

# Data paths
DATA_DIR: Path = Path(__file__).resolve().parent.parent.parent / "data"
RAW_DATA_DIR: Path = DATA_DIR / "raw"
RTU_DATA_DIR: Path = RAW_DATA_DIR / "RTU_data_private"
