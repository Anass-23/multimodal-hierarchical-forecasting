import json

import pandas as pd

from educast.constants import EPSEM_DATA_DIR, INTERIM_DATA_DIR
from educast.data.models import (  # ClickstreamData,
    AcademicHistory,
    AttemptedCourse,
    Course,
    Department,
    Programme,
    Student,
    TermType,
    University,
)

# Paths
EPSEM_TIC_DATA_DIR = EPSEM_DATA_DIR / "TIC"
ACRONYMS_FILE = EPSEM_TIC_DATA_DIR / "acronims.tic.csv"
MATRICULES_FILE = EPSEM_TIC_DATA_DIR / "matricules.anon.csv"

UNIVERSITY_NAME = "EPSEM (Escola Politècnica Superior d'Enginyeria de Manresa)"
UNIVERSITY_ID = "UPC-EPSEM"

# Load dataframes
df_acronyms = pd.read_csv(ACRONYMS_FILE)
df_matricules = pd.read_csv(MATRICULES_FILE)
df_acronyms.columns = df_acronyms.columns.str.strip().str.lower()
df_matricules.columns = df_matricules.columns.str.strip().str.lower()

# Courses mapping (in this case from the TIC programme)
course_map = {}
for _, row in df_acronyms.iterrows():
    try:
        cid = str(row["codi"])
        name = str(row["nom"]) if pd.notna(row["nom"]) else cid
        credits = float(row["credits"])
        course_map[cid] = Course(course_id=cid, name=name, credits=credits)
    except Exception as e:
        print(f"Error creating course: {e}")
        exit(1)

# Programee
programme = Programme(
    programme_id="TIC",
    name="Grau en Enginyeria de Sistemes TIC",
    courses=list(course_map.values()),
    credits_required=240,
    term_type=TermType.SEMESTER,  # EPSEM: 2 semesters per year
)

# Students and their AttemptedCourses
students_dict: dict[str, list[AttemptedCourse]] = {}

for _, row in df_matricules.iterrows():
    student_id = str(row["codi_expedient"])

    # Attempted course
    attempt = AttemptedCourse(
        course=course_map[str(row["codi_upc_ud"])],
        year=int(row["curs"]),
        term=int(row["quad"]),
        grade=int(row["nota_num_def"]) if pd.notna(row["nota_num_def"]) else None,
        clickstream=[],
    )

    students_dict.setdefault(student_id, []).append(attempt)

# Save each student as a separate JSON file (not necessary, just for better convenience to review)
students_folder = INTERIM_DATA_DIR / "EPSEM_data_private" / "students"
students_folder.mkdir(parents=True, exist_ok=True)
student_files = []
students_list = []

for student_id, attempts in students_dict.items():
    student_obj = Student(
        student_id=student_id,
        name="Unknown",
        history=AcademicHistory(attempts=attempts),
    )
    students_list.append(student_obj)

    student_path = students_folder / f"{student_id}.json"
    with student_path.open("w", encoding="utf-8") as f:
        json.dump(student_obj.model_dump(mode="json"), f, indent=4, ensure_ascii=False)
    student_files.append(str(student_path))

# Department
department = Department(
    department_id="EMIT",
    name="Departament d'Enginyeria Minera, Industrial i TIC",
    courses=list(course_map.values()),
)

# University
university = University(
    university_id=UNIVERSITY_ID,
    name=UNIVERSITY_NAME,
    departments=[department],
    programmes=[programme],
    students=students_list,
)

export_path = INTERIM_DATA_DIR / "EPSEM_data_private" / "EPSEM.educast.json"
with export_path.open("w", encoding="utf-8") as f:
    json.dump(university.model_dump(mode="json"), f, indent=4, ensure_ascii=False)


print("EduCast export completed")
print()
print(f"Total courses: {len(course_map)}")
print(f"Total students: {len(students_dict)}")
print(f"Total enrollments: {university.total_enrollments}")
