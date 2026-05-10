"""TFG-style binary/categorical features for tree-based models."""

from typing import List, Tuple

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


def identify_feature_types(
    X: pd.DataFrame,
    dataset_version: str = "v1",
) -> Tuple[List[str], List[str]]:
    """Identify categorical and numerical feature columns by dataset version.

    v1: no backpack features (VIA, ORDRE excluded).
    v2: VIA and ORDRE treated as categorical.
    Returns (categorical_features, numerical_features).
    """
    if dataset_version == "v1":
        # v1: drop EXPID, EDAT, VIA, ORDRE, NACC (no backpack features)
        drop_cols = {"EXPID", "EDAT", "VIA", "ORDRE", "NACC"}
        becat_cols = [c for c in X.columns if c.endswith("becat")]
        drop_cols.update(becat_cols)
        numerical = [c for c in X.columns if c not in drop_cols]
        categorical: List[str] = []
    else:
        # v2: VIA, ORDRE as categorical; rest as numerical (EXPID always excluded)
        categorical = [c for c in ["VIA", "ORDRE"] if c in X.columns]
        exclude = {"EXPID", "VIA", "ORDRE"}
        numerical = [c for c in X.columns if c not in exclude]

    return categorical, numerical


def build_preprocessor(
    categorical_features: List[str],
    numerical_features: List[str],
) -> ColumnTransformer:
    """Build a ColumnTransformer: OneHotEncoder for categoricals, mean imputation for numericals."""
    transformers = []

    if categorical_features:
        transformers.append((
            "cat",
            OneHotEncoder(handle_unknown="ignore", sparse_output=False),
            categorical_features,
        ))

    if numerical_features:
        transformers.append((
            "num",
            SimpleImputer(strategy="mean"),
            numerical_features,
        ))

    return ColumnTransformer(transformers=transformers)


def get_feature_names_from_preprocessor(
    preprocessor: ColumnTransformer,
    categorical_features: List[str],
    numerical_features: List[str],
) -> List[str]:
    """Extract feature names after preprocessing, in transform order."""
    names = []
    if categorical_features:
        cat_encoder = preprocessor.named_transformers_["cat"]
        names.extend(cat_encoder.get_feature_names_out(categorical_features).tolist())
    names.extend(numerical_features)
    return names
