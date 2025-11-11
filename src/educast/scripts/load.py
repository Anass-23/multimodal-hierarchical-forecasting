import json

from educast.data.models import University

with open("EPSEM.educast.json", "r", encoding="utf-8") as f:
    data = json.load(f)

university = University.model_validate(data)

print(university.name)
print(university.students[0].history.attempts[0].course.name)
print(f"Total students: {len(university.students)}")
print(f"Total departments: {len(university.departments)}")
print(f"Total programmes: {len(university.programmes)}")
print(f"Total courses: {len(university.departments[0].courses)}")

for course in university.departments[0].courses[:10]:
    print(f"- {course.course_id}: {course.name} ({course.credits} ECTS)")
