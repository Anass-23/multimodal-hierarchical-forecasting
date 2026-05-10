"""University model loading from standardized *.educast.json."""

import json
from pathlib import Path
from typing import Dict, List, Set, Tuple

from educast.config import UNIVERSITY_JSON


def load_university_json(path: Path = UNIVERSITY_JSON) -> dict:
    """Load the preprocessed University JSON structure."""
    # DATA NOT INCLUDED — contact the author or see README for access instructions.
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_course_vocabulary(university_data: dict) -> Tuple[List[str], Dict[str, int], Dict[int, str]]:
    """Build sorted course vocabulary. Returns (sorted_course_ids, course_to_idx, idx_to_course)."""
    all_ids: Set[str] = set()
    for dept in university_data.get("departments", []):
        for course in dept.get("courses", []):
            all_ids.add(course["course_id"])

    sorted_ids = sorted(all_ids)
    course_to_idx = {cid: i for i, cid in enumerate(sorted_ids)}
    idx_to_course = {i: cid for i, cid in enumerate(sorted_ids)}
    return sorted_ids, course_to_idx, idx_to_course


def build_course_label_map(university_data: dict, idx_to_course: Dict[int, str]) -> Dict[int, str]:
    """Build mapping from course index to human-readable label."""
    id_to_obj: Dict[str, dict] = {}
    for dept in university_data.get("departments", []):
        for course in dept.get("courses", []):
            id_to_obj.setdefault(course["course_id"], course)

    labels: Dict[int, str] = {}
    for i, cid in idx_to_course.items():
        obj = id_to_obj.get(cid)
        name = obj.get("name") if obj else None
        labels[i] = name if name else cid
    return labels


def build_acronym_maps(
    university_data: dict,
) -> Tuple[Dict[str, str], Dict[str, str], List[str]]:
    """Extract acronym mappings from enriched university JSON.

    Reads the ``acronym`` field added by ``build_json.py``.
    Returns (id_to_acronym, acronym_to_id, sorted_acronym_list).
    """
    id_to_acr: Dict[str, str] = {}
    for dept in university_data.get("departments", []):
        for course in dept.get("courses", []):
            acr = course.get("acronym")
            if acr:
                id_to_acr[course["course_id"]] = acr
    # Also check programmes (may have courses not in departments)
    for prog in university_data.get("programmes", []):
        for course in prog.get("courses", []):
            acr = course.get("acronym")
            if acr and course["course_id"] not in id_to_acr:
                id_to_acr[course["course_id"]] = acr

    acr_to_id = {v: k for k, v in id_to_acr.items()}
    acronym_list = sorted(acr_to_id.keys())
    return id_to_acr, acr_to_id, acronym_list
