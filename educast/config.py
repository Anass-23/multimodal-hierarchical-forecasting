"""Central configuration for all paths, seeds, hyperparameters, and feature dimensions."""

from pathlib import Path

PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent

# DATA NOT INCLUDED — contact the author or see README for access instructions.
DATA_DIR: Path = PROJECT_ROOT / "data"
RAW_DATA_DIR: Path = DATA_DIR / "raw" / "EPSEM_data_private" / "TIC"
INTERIM_DATA_DIR: Path = DATA_DIR / "interim" / "EPSEM_data_private"

RAW_MATRICULES_CSV: Path = RAW_DATA_DIR / "matricules.anon.csv"
RAW_ACRONIMS_CSV: Path = RAW_DATA_DIR / "acronims.tic.csv"
RAW_ACRONIMS_FULL_CSV: Path = RAW_DATA_DIR / "acronims.full.csv"

UNIVERSITY_JSON: Path = INTERIM_DATA_DIR / "EPSEM_semester.educast.json"
RESULTS_DIR: Path = PROJECT_ROOT / "results"

RANDOM_SEED: int = 42

# Feature dimensions
NUM_COURSES: int = 51  # Total courses in EPSEM TIC programme
FEAT_DIM_ENROLLMENT: int = NUM_COURSES  # 51 enrollment flags
FEAT_DIM_GRADES: int = NUM_COURSES  # 51 normalized grades
FEAT_DIM_ATTEMPTS: int = NUM_COURSES  # 51 attempt counts
FEAT_DIM_MULTIHOT: int = NUM_COURSES * 3  # 153-dim multi-hot vector
FEAT_DIM_STUDENT: int = FEAT_DIM_MULTIHOT + 1  # 154 with cumulative GPA

# LSTM hyperparameters
MICRO_WINDOW_SIZE: int = 3
MACRO_WINDOW_SIZE: int = 3
MICRO_HIDDEN_SIZE: int = 128
MACRO_HIDDEN_SIZE: int = 128
MICRO_NUM_LAYERS: int = 1
MACRO_NUM_LAYERS: int = 1
MICRO_DROPOUT: float = 0.2
MACRO_DROPOUT: float = 0.3
MICRO_EPOCHS: int = 100
MACRO_EPOCHS: int = 100
MICRO_BATCH_SIZE: int = 64
MACRO_BATCH_SIZE: int = 4
MICRO_LR: float = 0.001
MACRO_LR: float = 0.001

# Tree / Random Forest hyperparameters
TREE_MAX_DEPTH: int = 4
TREE_RANDOM_STATE: int = RANDOM_SEED
FOREST_N_ESTIMATORS: int = 100
FOREST_MAX_DEPTH: int = 4
FOREST_MAX_FEATURES: str = "sqrt"

# Train/test split
SPLIT_YEAR: int = 2018  # Train on data before this year, test on this year and after
TEST_SIZE: float = 0.2  # For student-level split fallback

# Subject acronym lists by semester (TFG curriculum)
SUBJECTS_Q1 = ["MBE", "F", "I", "ISD", "FMT"]
SUBJECTS_Q2 = ["ES", "TCO1", "TP", "SD", "TCI"]
SUBJECTS_Q3 = ["MAE", "TCO2", "DP", "EM", "CSL"]
SUBJECTS_Q4 = ["SA", "PBN", "ACO", "CSR", "SS"]
SUBJECTS_Q5 = ["PCTR", "GOP", "SO", "XC", "PDS"]
SUBJECTS_Q6 = ["SEN", "ESI", "ASSI", "SEC"]
SUBJECTS_Q7 = ["IS", "SAR"]
SUBJECTS_TFG = ["TFG"]

SUBJECTS_NORMAL = (
    SUBJECTS_Q1 + SUBJECTS_Q2 + SUBJECTS_Q3 + SUBJECTS_Q4
    + SUBJECTS_Q5 + SUBJECTS_Q6 + SUBJECTS_Q7 + SUBJECTS_TFG
)
SUBJECTS_OPTIONAL = ["MIC", "SC", "SSCI", "AE", "GQSIQSMA", "BD", "IU", "RE"]
SUBJECTS_ALL = SUBJECTS_NORMAL + SUBJECTS_OPTIONAL

# Course IDs excluded from MAE evaluation (first-year compulsory + optional)
EXCLUDE_FIRST_YEAR_IDS = ["330212", "330213", "330214", "330215", "330216"]
EXCLUDE_OPTIONAL_IDS = [
    "330054", "330058", "330060", "330063", "330066", "330082",
    "330097", "330099", "330101", "330102", "330119", "330120",
    "330244", "330245", "330246", "330247", "330248", "330249", "330094",
]
