import React, { useRef, useState } from "react";
import api from "../api/client";

interface Student {
  matriculation_number: string;
  first_name: string;
  last_name: string;
  email: string;
  course_of_studies: string;
  current_study_semester: string | number;
  credit_points: string | number;

  _row?: number;
  _errors?: string[];
  _valid?: boolean;
}

interface PreviewResponse {
  students: Student[];
  total?: number;
  valid?: number;
  invalid?: number;
}

interface ImportResponse {
  message?: string;
  imported?: number;
  created?: number;
  updated?: number;
  errors?: unknown;
}

interface ApiErrorResponse {
  error?: {
    code?: string;
    message?: string;
    details?: Record<string, string[] | string>;
    request_id?: string;
  };
}

const MAX_FILE_SIZE = 10 * 1024 * 1024;

const ALLOWED_EXTENSIONS = [".xlsx", ".xls", ".csv", ".pdf"];

function getFileExtension(filename: string): string {
  const index = filename.lastIndexOf(".");

  if (index === -1) {
    return "";
  }

  return filename.substring(index).toLowerCase();
}

function getErrorMessage(error: unknown, fallback: string): string {
  if (typeof error === "object" && error !== null && "response" in error) {
    const response = (
      error as {
        response?: {
          data?: ApiErrorResponse;
        };
      }
    ).response;

    const apiError = response?.data?.error;

    if (apiError?.message) {
      const messages: string[] = [];

      if (apiError.details) {
        Object.values(apiError.details).forEach((value) => {
          if (Array.isArray(value)) {
            messages.push(...value);
          } else if (typeof value === "string") {
            messages.push(value);
          }
        });
      }

      if (messages.length > 0) {
        return `${apiError.message} ${messages.join(" ")}`;
      }

      return apiError.message;
    }
  }

  if (error instanceof Error && error.message) {
    return error.message;
  }

  return fallback;
}

function validateStudent(student: Student): string[] {
  const errors: string[] = [];

  const matriculationNumber = String(student.matriculation_number ?? "").trim();

  const firstName = String(student.first_name ?? "").trim();

  const lastName = String(student.last_name ?? "").trim();

  const email = String(student.email ?? "").trim();

  const semester = String(student.current_study_semester ?? "").trim();

  const creditPoints = String(student.credit_points ?? "").trim();

  if (!matriculationNumber) {
    errors.push("Matriculation number is required.");
  } else if (!/^\d+$/.test(matriculationNumber)) {
    errors.push("Matriculation number must contain digits only.");
  } else if (matriculationNumber.length > 9) {
    errors.push("Matriculation number must not exceed 9 digits.");
  }

  if (!firstName) {
    errors.push("First name is required.");
  }

  if (!lastName) {
    errors.push("Last name is required.");
  }

  if (!email) {
    errors.push("Email is required.");
  } else {
    const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

    if (!emailPattern.test(email)) {
      errors.push("Invalid email address.");
    }
  }

  if (semester) {
    const semesterNumber = Number(semester);

    if (!Number.isInteger(semesterNumber) || semesterNumber < 1) {
      errors.push("Study semester must be a positive whole number.");
    }
  }

  if (creditPoints) {
    const credits = Number(creditPoints);

    if (Number.isNaN(credits) || credits < 0) {
      errors.push("Credit points must be a non-negative number.");
    }
  }

  return errors;
}

function validateDuplicates(students: Student[]): Student[] {
  const matriculationNumbers = new Map<string, number[]>();
  const emails = new Map<string, number[]>();

  students.forEach((student, index) => {
    const row = student._row ?? index + 2;

    const matriculationNumber = String(student.matriculation_number ?? "")
      .trim()
      .toLowerCase();

    const email = String(student.email ?? "")
      .trim()
      .toLowerCase();

    if (matriculationNumber) {
      const rows = matriculationNumbers.get(matriculationNumber) ?? [];

      rows.push(row);

      matriculationNumbers.set(matriculationNumber, rows);
    }

    if (email) {
      const rows = emails.get(email) ?? [];

      rows.push(row);

      emails.set(email, rows);
    }
  });

  return students.map((student, index) => {
    const errors = [...(student._errors ?? [])];

    const row = student._row ?? index + 2;

    const matriculationNumber = String(student.matriculation_number ?? "")
      .trim()
      .toLowerCase();

    const email = String(student.email ?? "")
      .trim()
      .toLowerCase();

    const matriculationRows = matriculationNumbers.get(matriculationNumber);

    if (matriculationRows && matriculationRows.length > 1) {
      errors.push(
        `Duplicate matriculation number found in rows ${matriculationRows.join(
          ", ",
        )}.`,
      );
    }

    const emailRows = emails.get(email);

    if (emailRows && emailRows.length > 1) {
      errors.push(`Duplicate email found in rows ${emailRows.join(", ")}.`);
    }

    return {
      ...student,
      _row: row,
      _errors: errors,
      _valid: errors.length === 0,
    };
  });
}

export default function StudentImportPage() {
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const [file, setFile] = useState<File | null>(null);

  const [students, setStudents] = useState<Student[]>([]);

  const [loadingPreview, setLoadingPreview] = useState(false);

  const [loadingImport, setLoadingImport] = useState(false);

  const [error, setError] = useState<string>("");

  const [success, setSuccess] = useState<string>("");

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = event.target.files?.[0] ?? null;

    setError("");
    setSuccess("");
    setStudents([]);

    if (!selectedFile) {
      setFile(null);
      return;
    }

    const extension = getFileExtension(selectedFile.name);

    if (!ALLOWED_EXTENSIONS.includes(extension)) {
      setFile(null);

      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }

      setError("Please select an XLSX, XLS, CSV or PDF file.");

      return;
    }

    if (selectedFile.size > MAX_FILE_SIZE) {
      setFile(null);

      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }

      setError(
        "The selected file is too large. Maximum allowed size is 10 MB.",
      );

      return;
    }

    setFile(selectedFile);
  };

  const handlePreview = async () => {
    if (!file) {
      setError("Please select a file first.");
      return;
    }

    setLoadingPreview(true);
    setError("");
    setSuccess("");
    setStudents([]);

    try {
      const formData = new FormData();

      formData.append("file", file);

      /*
       * Do NOT manually set Content-Type here.
       *
       * Axios/browser will automatically create:
       *
       * multipart/form-data; boundary=...
       */
      const response = await api.post<PreviewResponse>(
        "/students/import/preview/",
        formData,
      );

      const previewStudents = Array.isArray(response.data?.students)
        ? response.data.students
        : [];

      const validatedStudents = previewStudents.map(
        (student: Student, index: number) => {
          const errors = validateStudent(student);

          return {
            ...student,
            _row: student._row ?? index + 2,
            _errors: errors,
            _valid: errors.length === 0,
          };
        },
      );

      const finalStudents = validateDuplicates(validatedStudents);

      setStudents(finalStudents);

      if (finalStudents.length === 0) {
        setError("No student records were found in the selected file.");
      }
    } catch (err: unknown) {
      setError(getErrorMessage(err, "Could not process the selected file."));
    } finally {
      setLoadingPreview(false);
    }
  };

  const handleImport = async () => {
    if (!students.length) {
      setError("Please preview a file before importing.");
      return;
    }

    const validStudents = students.filter((student) => student._valid === true);

    if (validStudents.length === 0) {
      setError("There are no valid students to import.");
      return;
    }

    setLoadingImport(true);
    setError("");
    setSuccess("");

    try {
      /*
       * Keep the original row number.
       * This makes backend errors easier to map
       * back to the original spreadsheet.
       */
      const studentsForImport = validStudents.map((student) => ({
        matriculation_number: String(student.matriculation_number ?? "").trim(),

        first_name: String(student.first_name ?? "").trim(),

        last_name: String(student.last_name ?? "").trim(),

        email: String(student.email ?? "").trim(),

        course_of_studies: String(student.course_of_studies ?? "").trim(),

        current_study_semester: String(
          student.current_study_semester ?? "",
        ).trim(),

        credit_points: String(student.credit_points ?? "").trim(),

        _row: student._row,
      }));

      const response = await api.post<ImportResponse>(
        "/students/import/confirm/",
        {
          students: studentsForImport,
        },
      );

      const importedCount =
        response.data?.imported ??
        response.data?.created ??
        validStudents.length;

      setSuccess(
        response.data?.message ??
          `Successfully imported ${importedCount} student(s).`,
      );

      /*
       * Remove successfully imported rows
       * from the preview.
       */
      setStudents([]);

      setFile(null);

      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    } catch (err: unknown) {
      setError(getErrorMessage(err, "Could not import the students."));
    } finally {
      setLoadingImport(false);
    }
  };

  const handleReset = () => {
    setFile(null);
    setStudents([]);
    setError("");
    setSuccess("");

    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const validCount = students.filter(
    (student) => student._valid === true,
  ).length;

  const invalidCount = students.length - validCount;

  return (
    <div
      style={{
        maxWidth: "1200px",
        margin: "0 auto",
        padding: "40px 24px",
        fontFamily: "Arial, sans-serif",
      }}
    >
      <h1
        style={{
          marginBottom: "8px",
        }}
      >
        Import Students
      </h1>

      <p
        style={{
          color: "#666",
          marginBottom: "30px",
        }}
      ></p>

      {/* Upload section */}
      <div
        style={{
          border: "1px solid #ddd",
          borderRadius: "8px",
          padding: "24px",
          marginBottom: "24px",
          background: "#fafafa",
        }}
      >
        <h2>Select Student File</h2>

        <p>Supported formats: XLSX, XLS, CSV and PDF. Maximum size: 10 MB.</p>
        <p>
          Upload a CSV or Excel file containing one student per row. The first
          row must contain column headers. Required fields are matriculation
          number, first name, last name, email, course, current semester, and
          credit points.
        </p>
        <input
          ref={fileInputRef}
          type="file"
          accept=".xlsx,.xls,.csv,.pdf"
          onChange={handleFileChange}
        />

        {file && (
          <div
            style={{
              marginTop: "12px",
              padding: "10px",
              background: "#fff",
              border: "1px solid #ddd",
              borderRadius: "4px",
            }}
          >
            <strong>Selected file:</strong> {file.name}
          </div>
        )}

        <div
          style={{
            display: "flex",
            gap: "10px",
            marginTop: "20px",
            flexWrap: "wrap",
          }}
        >
          <button
            type="button"
            onClick={handlePreview}
            disabled={!file || loadingPreview || loadingImport}
            style={{
              padding: "10px 18px",
              cursor:
                !file || loadingPreview || loadingImport
                  ? "not-allowed"
                  : "pointer",
            }}
          >
            {loadingPreview ? "Processing..." : "Preview Students"}
          </button>

          <button
            type="button"
            onClick={handleReset}
            disabled={loadingPreview || loadingImport}
            style={{
              padding: "10px 18px",
            }}
          >
            Reset
          </button>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div
          role="alert"
          style={{
            padding: "14px",
            marginBottom: "20px",
            border: "1px solid #dc3545",
            background: "#fff5f5",
            color: "#b02a37",
            borderRadius: "6px",
          }}
        >
          {error}
        </div>
      )}

      {/* Success */}
      {success && (
        <div
          role="status"
          style={{
            padding: "14px",
            marginBottom: "20px",
            border: "1px solid #198754",
            background: "#f0fff4",
            color: "#146c43",
            borderRadius: "6px",
          }}
        >
          {success}
        </div>
      )}

      {/* Preview summary */}
      {students.length > 0 && (
        <div
          style={{
            marginBottom: "20px",
          }}
        >
          <h2>Preview</h2>

          <div
            style={{
              display: "flex",
              gap: "20px",
              marginBottom: "15px",
            }}
          >
            <span>
              <strong>Total:</strong> {students.length}
            </span>

            <span
              style={{
                color: "#198754",
              }}
            >
              <strong>Valid:</strong> {validCount}
            </span>

            <span
              style={{
                color: "#dc3545",
              }}
            >
              <strong>Invalid:</strong> {invalidCount}
            </span>
          </div>

          <div
            style={{
              overflowX: "auto",
              border: "1px solid #ddd",
              borderRadius: "6px",
            }}
          >
            <table
              style={{
                width: "100%",
                borderCollapse: "collapse",
                minWidth: "1100px",
              }}
            >
              <thead>
                <tr
                  style={{
                    background: "#f5f5f5",
                  }}
                >
                  <th style={tableHeaderStyle}>Row</th>

                  <th style={tableHeaderStyle}>Matriculation No.</th>

                  <th style={tableHeaderStyle}>First Name</th>

                  <th style={tableHeaderStyle}>Last Name</th>

                  <th style={tableHeaderStyle}>Email</th>

                  <th style={tableHeaderStyle}>Course</th>

                  <th style={tableHeaderStyle}>Semester</th>

                  <th style={tableHeaderStyle}>Credits</th>

                  <th style={tableHeaderStyle}>Status</th>

                  <th style={tableHeaderStyle}>Errors</th>
                </tr>
              </thead>

              <tbody>
                {students.map((student, index) => (
                  <tr key={`${student._row}-${index}`}>
                    <td style={tableCellStyle}>{student._row ?? index + 2}</td>

                    <td style={tableCellStyle}>
                      {student.matriculation_number}
                    </td>

                    <td style={tableCellStyle}>{student.first_name}</td>

                    <td style={tableCellStyle}>{student.last_name}</td>

                    <td style={tableCellStyle}>{student.email}</td>

                    <td style={tableCellStyle}>{student.course_of_studies}</td>

                    <td style={tableCellStyle}>
                      {student.current_study_semester}
                    </td>

                    <td style={tableCellStyle}>{student.credit_points}</td>

                    <td
                      style={{
                        ...tableCellStyle,
                        fontWeight: "bold",
                        color: student._valid ? "#198754" : "#dc3545",
                      }}
                    >
                      {student._valid ? "Valid" : "Invalid"}
                    </td>

                    <td
                      style={{
                        ...tableCellStyle,
                        color: "#dc3545",
                      }}
                    >
                      {student._errors && student._errors.length > 0 ? (
                        <ul
                          style={{
                            margin: 0,
                            paddingLeft: "18px",
                          }}
                        >
                          {student._errors.map((studentError, errorIndex) => (
                            <li key={errorIndex}>{studentError}</li>
                          ))}
                        </ul>
                      ) : (
                        "-"
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Import button */}
          <div
            style={{
              marginTop: "20px",
            }}
          >
            <button
              type="button"
              onClick={handleImport}
              disabled={validCount === 0 || loadingImport || loadingPreview}
              style={{
                padding: "12px 24px",
                cursor:
                  validCount === 0 || loadingImport || loadingPreview
                    ? "not-allowed"
                    : "pointer",
                fontWeight: "bold",
              }}
            >
              {loadingImport
                ? "Importing..."
                : `Import ${validCount} Valid Student${
                    validCount === 1 ? "" : "s"
                  }`}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

const tableHeaderStyle: React.CSSProperties = {
  padding: "10px",
  borderBottom: "1px solid #ddd",
  textAlign: "left",
  whiteSpace: "nowrap",
};

const tableCellStyle: React.CSSProperties = {
  padding: "10px",
  borderBottom: "1px solid #eee",
  verticalAlign: "top",
};
