"""One-time ETL: enrich EPSEM_semester.educast.json with CSV metadata.

Merges student-level fields (birth_year, access_path, enrollment_order,
access_grade) and attempt-level fields (scholarship, grade_description,
grade_type) from the raw CSV into the existing JSON. Also adds course
acronyms from acronims.tic.csv.

Usage:
    python -m educast.data.build_json

Note: Requires access to the confidential EPSEM raw CSV files.
DATA NOT INCLUDED — contact the author or see README for access instructions.
"""

import csv
import json
from collections import defaultdict
from pathlib import Path

from educast.config import (
    INTERIM_DATA_DIR,
    RAW_ACRONIMS_CSV,
    RAW_MATRICULES_CSV,
    UNIVERSITY_JSON,
)
from educast.data.schema import University


def _load_csv_records(
    matricules_path: Path,
) -> dict:
    """Load raw CSV into dicts grouped by student_id. Returns {student_id: [row_dict, ...]}."""
    by_student = defaultdict(list)
    with open(matricules_path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            by_student[row["codi_expedient"]].append(row)
    return dict(by_student)


def _load_acronym_map(acronims_path: Path) -> dict:
    """Load course_id -> acronym mapping from acronims CSV."""
    mapping = {}
    with open(acronims_path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            mapping[row["codi"]] = row["acronim"]
    return mapping


def _safe_int(val: str) -> int | None:
    if not val or val.strip() == "":
        return None
    try:
        return int(val)
    except ValueError:
        return None


def _safe_float(val: str) -> float | None:
    if not val or val.strip() == "":
        return None
    try:
        return float(val)
    except ValueError:
        return None


def build_enriched_json(
    json_path: Path = UNIVERSITY_JSON,
    matricules_path: Path = RAW_MATRICULES_CSV,
    acronims_path: Path = RAW_ACRONIMS_CSV,
) -> dict:
    """Build enriched university dict from existing JSON + raw CSV.

    Returns the enriched dict (not yet written to disk).
    """
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    csv_by_student = _load_csv_records(matricules_path)
    acronym_map = _load_acronym_map(acronims_path)

    def _enrich_course(course: dict) -> None:
        cid = course.get("course_id", "")
        if cid in acronym_map and "acronym" not in course:
            course["acronym"] = acronym_map[cid]

    for dept in data.get("departments", []):
        for course in dept.get("courses", []):
            _enrich_course(course)
    for prog in data.get("programmes", []):
        for course in prog.get("courses", []):
            _enrich_course(course)

    matched_students = 0
    matched_attempts = 0
    unmatched_students = []

    for student in data.get("students", []):
        sid = student["student_id"]
        csv_rows = csv_by_student.get(sid)

        if not csv_rows:
            unmatched_students.append(sid)
            continue

        matched_students += 1

        # Student-level metadata: constant across rows, take from first
        first = csv_rows[0]
        student["birth_year"] = _safe_int(first["Any_Naix"])
        student["access_path"] = _safe_int(first["via_acces"])
        student["enrollment_order"] = _safe_int(first["ordre_assignacio"])
        student["access_grade"] = _safe_float(first["nota_acces"])

        csv_lookup = defaultdict(list)
        for row in csv_rows:
            key = (int(row["curs"]), int(row["quad"]), row["codi_upc_ud"])
            csv_lookup[key].append(row)

        history = student.get("history", {})
        for attempt in history.get("attempts", []):
            year = attempt.get("year")
            term = attempt.get("term")
            cid = attempt.get("course", {}).get("course_id")
            if not (year and term and cid):
                continue

            _enrich_course(attempt.get("course", {}))

            key = (year, term, cid)
            candidates = csv_lookup.get(key, [])
            if not candidates:
                continue

            # Pick best matching row (by grade if multiple)
            csv_row = candidates[0]
            if len(candidates) > 1:
                grade = attempt.get("grade")
                for c in candidates:
                    csv_grade = _safe_float(c["nota_num_def"])
                    if csv_grade is not None and grade is not None and abs(csv_grade - grade) < 0.01:
                        csv_row = c
                        break

            attempt["scholarship"] = csv_row["BECA"] == "SI"
            attempt["grade_description"] = csv_row["nota_des_def"] or None
            attempt["grade_type"] = csv_row["tipus_qual"] or None
            matched_attempts += 1

    print(f"Matched {matched_students}/{len(data.get('students', []))} students")
    print(f"Enriched {matched_attempts} attempts")
    if unmatched_students:
        print(f"Unmatched students: {len(unmatched_students)}")

    return data


def validate_and_write(
    data: dict,
    output_path: Path | None = None,
) -> University:
    """Validate enriched data with Pydantic and write to disk."""
    university = University.model_validate(data)
    print(f"Validated: {university.total_students} students, "
          f"{university.total_courses} courses, "
          f"{university.total_enrollments} enrollment periods")

    if output_path is None:
        output_path = UNIVERSITY_JSON

    json_data = json.loads(university.model_dump_json())

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)
    print(f"Written to {output_path}")

    return university


if __name__ == "__main__":
    import shutil

    backup = UNIVERSITY_JSON.with_suffix(".educast.json.bak")
    if UNIVERSITY_JSON.exists() and not backup.exists():
        shutil.copy2(UNIVERSITY_JSON, backup)
        print(f"Backed up to {backup}")

    data = build_enriched_json()
    validate_and_write(data)
