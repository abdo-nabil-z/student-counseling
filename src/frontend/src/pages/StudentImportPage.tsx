import { useState } from "react";
import api from "../api/client";

type Student = {
  matriculation_number: string;
  first_name: string;
  last_name: string;
  email: string;
  course_of_studies: string;
  current_study_semester: string;
  credit_points: string;

  _row?: number;
  _errors?: string[];
  _valid?: boolean;
};

export default function StudentImportPage() {
  const [file, setFile] = useState<File | null>(null);

  const [students, setStudents] = useState<Student[]>([]);

  const [loading, setLoading] = useState(false);

  const [message, setMessage] = useState("");

  const [error, setError] = useState("");

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setError("");
    setMessage("");

    const selectedFile = event.target.files?.[0];

    if (!selectedFile) {
      return;
    }

    const allowedExtensions = [".xlsx", ".xls", ".csv", ".pdf"];

    const filename = selectedFile.name.toLowerCase();

    const valid = allowedExtensions.some((extension) =>
      filename.endsWith(extension),
    );

    if (!valid) {
      setError("Please select an XLSX, XLS, CSV or PDF file.");
      return;
    }

    setFile(selectedFile);
    setStudents([]);
  };

  const handlePreview = async () => {
    if (!file) {
      setError("Please select a file first.");
      return;
    }

    setLoading(true);
    setError("");
    setMessage("");

    try {
      const formData = new FormData();

      formData.append("file", file);

      const response = await api.post("/students/import/preview/", formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });

      setStudents(response.data.students);

      setMessage(
        `Found ${response.data.total} students. ` +
          `${response.data.valid} valid, ` +
          `${response.data.invalid} invalid.`,
      );

      // eslint-disable-next-line @typescript-eslint/no-explicit-any
    } catch (err: any) {
      setError(err?.response?.data?.error || "Could not process the file.");
    } finally {
      setLoading(false);
    }
  };

  const handleImport = async () => {
    const validStudents = students.filter((student) => student._valid);

    if (validStudents.length === 0) {
      setError("There are no valid students to import.");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const cleanStudents = validStudents.map(
        ({
          // eslint-disable-next-line @typescript-eslint/no-unused-vars
          _row,
          // eslint-disable-next-line @typescript-eslint/no-unused-vars
          _errors,
          // eslint-disable-next-line @typescript-eslint/no-unused-vars
          _valid,
          ...student
        }) => student,
      );

      const response = await api.post("/students/import/confirm/", {
        students: cleanStudents,
      });

      setMessage(`Successfully imported ${response.data.created} students.`);

      if (response.data.errors?.length) {
        setError(
          `${response.data.errors.length} students could not be imported.`,
        );
      }

      setStudents([]);

      setFile(null);

      // eslint-disable-next-line @typescript-eslint/no-explicit-any
    } catch (err: any) {
      setError(err?.response?.data?.error || "Import failed.");
    } finally {
      setLoading(false);
    }
  };

  const validCount = students.filter((student) => student._valid).length;

  const invalidCount = students.filter((student) => !student._valid).length;

  return (
    <div
      style={{
        padding: "32px",
        maxWidth: "1400px",
        margin: "0 auto",
      }}
    >
      <h1>Import Students</h1>

      <p>Import students from Excel, CSV or PDF.</p>

      {/* Upload */}
      <div
        style={{
          border: "2px dashed #ccc",
          borderRadius: "12px",
          padding: "40px",
          textAlign: "center",
          marginTop: "24px",
        }}
      >
        <input
          type="file"
          accept=".xlsx,.xls,.csv,.pdf"
          onChange={handleFileChange}
        />

        {file && (
          <p style={{ marginTop: "16px" }}>
            Selected file: <strong>{file.name}</strong>
          </p>
        )}

        <button
          onClick={handlePreview}
          disabled={!file || loading}
          style={{
            marginTop: "20px",
            padding: "10px 20px",
            cursor: !file || loading ? "not-allowed" : "pointer",
          }}
        >
          {loading ? "Processing..." : "Preview"}
        </button>
      </div>

      {/* Messages */}
      {message && (
        <div
          style={{
            marginTop: "20px",
            padding: "12px",
            background: "#e8f5e9",
            borderRadius: "8px",
          }}
        >
          {message}
        </div>
      )}

      {error && (
        <div
          style={{
            marginTop: "20px",
            padding: "12px",
            background: "#ffebee",
            color: "#c62828",
            borderRadius: "8px",
          }}
        >
          {error}
        </div>
      )}

      {/* Preview */}
      {students.length > 0 && (
        <div style={{ marginTop: "32px" }}>
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              marginBottom: "16px",
            }}
          >
            <div>
              <strong>{students.length} students found</strong>

              <span
                style={{
                  marginLeft: "20px",
                }}
              >
                Valid: {validCount}
              </span>

              <span
                style={{
                  marginLeft: "20px",
                }}
              >
                Invalid: {invalidCount}
              </span>
            </div>

            <button
              onClick={handleImport}
              disabled={loading || validCount === 0}
              style={{
                padding: "10px 20px",
                fontWeight: "bold",
              }}
            >
              {loading ? "Importing..." : `Import ${validCount} Students`}
            </button>
          </div>

          <div
            style={{
              overflowX: "auto",
              border: "1px solid #ddd",
              borderRadius: "8px",
            }}
          >
            <table
              style={{
                width: "100%",
                borderCollapse: "collapse",
              }}
            >
              <thead>
                <tr>
                  <th>Row</th>
                  <th>Status</th>
                  <th>Matriculation</th>
                  <th>First Name</th>
                  <th>Last Name</th>
                  <th>Email</th>
                  <th>Course</th>
                  <th>Semester</th>
                  <th>Credits</th>
                  <th>Errors</th>
                </tr>
              </thead>

              <tbody>
                {students.map((student, index) => (
                  <tr
                    key={index}
                    style={{
                      background: student._valid ? "white" : "#fff3f3",
                    }}
                  >
                    <td>{student._row}</td>

                    <td>{student._valid ? "✓ Valid" : "✗ Invalid"}</td>

                    <td>{student.matriculation_number}</td>

                    <td>{student.first_name}</td>

                    <td>{student.last_name}</td>

                    <td>{student.email}</td>

                    <td>{student.course_of_studies}</td>

                    <td>{student.current_study_semester}</td>

                    <td>{student.credit_points}</td>

                    <td>{student._errors?.join(", ")}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
