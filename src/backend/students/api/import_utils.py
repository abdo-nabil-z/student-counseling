import io
import pandas as pd

from pypdf import PdfReader


EXPECTED_COLUMNS = [
    "matriculation_number",
    "first_name",
    "last_name",
    "email",
    "course_of_studies",
    "current_study_semester",
    "credit_points",
]


COLUMN_ALIASES = {
    "matriculation": "matriculation_number",
    "matriculation_number": "matriculation_number",
    "matriculation number": "matriculation_number",
    "matrikelnummer": "matriculation_number",
    "student_number": "matriculation_number",

    "first_name": "first_name",
    "first name": "first_name",
    "vorname": "first_name",

    "last_name": "last_name",
    "last name": "last_name",
    "nachname": "last_name",
    "surname": "last_name",

    "email": "email",
    "e-mail": "email",
    "email address": "email",

    "course_of_studies": "course_of_studies",
    "course": "course_of_studies",
    "course of studies": "course_of_studies",
    "studiengang": "course_of_studies",

    "current_study_semester": "current_study_semester",
    "study semester": "current_study_semester",
    "semester": "current_study_semester",
    "fachsemester": "current_study_semester",

    "credit_points": "credit_points",
    "credit points": "credit_points",
    "credits": "credit_points",
    "ects": "credit_points",
}


def normalize_column_name(name):
    name = str(name).strip().lower()
    name = name.replace("-", "_")

    return COLUMN_ALIASES.get(name, name)


def normalize_dataframe(df):
    df = df.copy()

    renamed = {}

    for column in df.columns:
        normalized = normalize_column_name(column)
        renamed[column] = normalized

    df.rename(columns=renamed, inplace=True)

    # Keep only known columns
    existing = [
        column
        for column in EXPECTED_COLUMNS
        if column in df.columns
    ]

    df = df[existing]

    # Replace NaN with empty strings
    df = df.fillna("")

    # Convert everything to string first
    for column in df.columns:
        df[column] = df[column].astype(str).str.strip()

    return df


def read_excel(file):
    file.seek(0)

    df = pd.read_excel(file)

    return normalize_dataframe(df)


def read_csv(file):
    file.seek(0)

    df = pd.read_csv(file)

    return normalize_dataframe(df)


def read_pdf(file):
    """
    Basic PDF parser.

    This works for text-based PDFs where the student information
    is available as selectable text.

    Scanned PDFs require OCR.
    """

    file.seek(0)

    reader = PdfReader(file)

    text = ""

    for page in reader.pages:
        page_text = page.extract_text()

        if page_text:
            text += page_text + "\n"

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    students = []

    # Try to identify rows separated by whitespace.
    for line in lines:
        parts = line.split()

        # We need at least:
        # matriculation first last email
        if len(parts) < 4:
            continue

        # Ignore obvious header rows
        lower_line = line.lower()

        if (
            "matriculation" in lower_line
            or "matrikelnummer" in lower_line
            or "first name" in lower_line
        ):
            continue

        email = next(
            (
                part
                for part in parts
                if "@" in part
            ),
            None,
        )

        if not email:
            continue

        email_index = parts.index(email)

        if email_index < 3:
            continue

        matriculation_number = parts[0]
        first_name = parts[1]
        last_name = parts[2]

        students.append(
            {
                "matriculation_number": matriculation_number,
                "first_name": first_name,
                "last_name": last_name,
                "email": email,
                "course_of_studies": "",
                "current_study_semester": "",
                "credit_points": "",
            }
        )

    return pd.DataFrame(students)


def parse_file(uploaded_file):
    filename = uploaded_file.name.lower()

    if filename.endswith(".xlsx") or filename.endswith(".xls"):
        return read_excel(uploaded_file)

    if filename.endswith(".csv"):
        return read_csv(uploaded_file)

    if filename.endswith(".pdf"):
        return read_pdf(uploaded_file)

    raise ValueError(
        "Unsupported file type. Please upload XLSX, XLS, CSV or PDF."
    )