from pathlib import Path

import pytest

from educast.constants import DATA_DIR, EDUCAST, RAW_DATA_DIR, RTU_DATA_DIR


def test_educast_constant_content():
    """Simple test on EDUCAST constant"""
    expected = "EduCast: A multimodal hierarchical forecasting framework for university enrollments"
    assert isinstance(EDUCAST, str)
    assert EDUCAST == expected
    assert len(EDUCAST) > 0


@pytest.mark.parametrize("substring", ["EduCast", "forecasting", "university"])
def test_constant_contains_keywords(substring):
    """Check that important words appear in the EDUCAST constant."""
    assert substring in EDUCAST


class TestDataPathConstants:
    def test_data_dir_is_path(self):
        """DATA_DIR, RAW_DATA_DIR and RTU_DATA_DIR should be pathlib.Path instances."""
        assert isinstance(DATA_DIR, Path)
        assert isinstance(RAW_DATA_DIR, Path)
        assert isinstance(RTU_DATA_DIR, Path)

    def test_data_dir_names_and_relations(self):
        """Logical relations verification"""
        assert DATA_DIR.name == "data"
        assert RAW_DATA_DIR == DATA_DIR / "raw"
        assert RTU_DATA_DIR == RAW_DATA_DIR / "RTU data"

    @pytest.mark.parametrize("p", ["DATA_DIR", "RAW_DATA_DIR", "RTU_DATA_DIR"])
    def test_paths_are_absolute(self, p):
        """Paths should be absolute so they resolve correctly when used in code."""
        value = globals()[p]
        assert value.is_absolute(), f"{p} should be absolute"
