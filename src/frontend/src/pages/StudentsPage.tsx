import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import type { Student } from "../types/student";
import Modal from "../components/common/Model";
import api from "../api/client";

function EditIcon() {
  return (
    <svg
      width="16"
      height="16"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d="M12 20h9" />
      <path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4 12.5-12.5z" />
    </svg>
  );
}

function MailIcon() {
  return (
    <svg
      width="16"
      height="16"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <rect x="2" y="4" width="20" height="16" rx="2" />
      <path d="m22 7-10 6L2 7" />
    </svg>
  );
}

function TrashIcon() {
  return (
    <svg
      width="16"
      height="16"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <polyline points="3 6 5 6 21 6" />
      <path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
      <line x1="10" y1="11" x2="10" y2="17" />
      <line x1="14" y1="11" x2="14" y2="17" />
    </svg>
  );
}

const EMPTY: Student = {
  id: 0,
  matriculation_number: "",
  first_name: "",
  last_name: "",
  email: "",
  course_of_studies: "",
  current_study_semester: 1,
  credit_points: 0,
  contact_status: "not_contacted_yet",
};

const MAX_DISPLAY_FILENAME_LENGTH = 10;

function formatFileName(fileName: string): string {
  if (fileName.length <= MAX_DISPLAY_FILENAME_LENGTH) {
    return fileName;
  }

  const lastDot = fileName.lastIndexOf(".");

  // If the filename has no extension, simply truncate it.
  if (lastDot <= 0 || lastDot === fileName.length - 1) {
    return `${fileName.slice(0, MAX_DISPLAY_FILENAME_LENGTH - 3)}...`;
  }

  const extension = fileName.slice(lastDot);
  const nameWithoutExtension = fileName.slice(0, lastDot);

  // Number of characters available for the filename itself,
  // after accounting for "..." and the extension.
  const availableNameLength =
    MAX_DISPLAY_FILENAME_LENGTH - extension.length - 3;

  // If the extension itself is very long, keep the extension
  // and show an ellipsis before it.
  if (availableNameLength <= 0) {
    return `...${extension}`;
  }

  return nameWithoutExtension.slice(0, availableNameLength) + "..." + extension;
}

function StudentsPage() {
  const navigate = useNavigate();

  const [students, setStudents] = useState<Student[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [draft, setDraft] = useState<Student | null>(null);
  const [saving, setSaving] = useState(false);

  function load() {
    setLoading(true);

    api
      .get<Student[]>("/students/")
      .then((res) => setStudents(res.data))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    load();
  }, []);

  function openMails(s: Student) {
    navigate("/mail", {
      state: {
        targetType: "student",
        targetIds: [s.id],
      },
    });
  }

  /**
   * Upload OR replace a study plan.
   * The backend POST endpoint replaces any existing document,
   * so the same call covers both "upload" and "modify".
   */
  async function uploadPlan(
    studentId: number,
    which: "initial" | "final",
    file: File,
  ) {
    const fd = new FormData();

    fd.append("file", file);
    fd.append("name", file.name);

    try {
      await api.post(`/students/${studentId}/${which}-study-plan/`, fd);
      load();
    } catch (err) {
      alert("Upload failed: " + (err as Error).message);
    }
  }

  async function saveDraft() {
    if (!draft) return;

    setSaving(true);

    const payload = {
      matriculation_number: draft.matriculation_number,
      first_name: draft.first_name,
      last_name: draft.last_name,
      email: draft.email,
      course_of_studies: draft.course_of_studies || null,
      current_study_semester: draft.current_study_semester,
      credit_points: Number(draft.credit_points),
      contact_status: draft.contact_status,
    };

    try {
      if (draft.id) {
        await api.patch(`/students/${draft.id}/`, payload);
      } else {
        await api.post("/students/", payload);
      }

      setDraft(null);
      load();
    } catch (err) {
      const e = err as {
        response?: { data?: unknown };
        message: string;
      };

      alert(
        "Save failed: " +
          (e.response?.data ? JSON.stringify(e.response.data) : e.message),
      );
    } finally {
      setSaving(false);
    }
  }

  /**
   * Delete a study-plan document.
   * The Student FK is on_delete=SET_NULL,
   * so removing the Document automatically clears the student's link.
   */
  async function deletePlan(docId: number) {
    if (!window.confirm("Delete this study plan?")) return;

    try {
      await api.delete(`/documents/${docId}/`);
      load();
    } catch (err) {
      alert("Delete failed: " + (err as Error).message);
    }
  }

  async function removeStudent(s: Student) {
    if (!window.confirm(`Delete ${s.first_name} ${s.last_name}?`)) return;

    try {
      await api.delete(`/students/${s.id}/`);
      load();
    } catch (err) {
      alert("Delete failed: " + (err as Error).message);
    }
  }

  function PlanCell({ s, which }: { s: Student; which: "initial" | "final" }) {
    const doc = which === "initial" ? s.initial_study_plan : s.final_study_plan;

    const filePicker = (labelText: string, hint: string) => (
      <label
        title={hint}
        style={{
          cursor: "pointer",
          color: "#5b5bef",
          fontSize: "13px",
          fontWeight: 500,
        }}
      >
        {labelText}

        <input
          type="file"
          style={{ display: "none" }}
          onChange={(e) => {
            const f = e.target.files?.[0];

            if (f) {
              uploadPlan(s.id, which, f);
            }

            e.target.value = "";
          }}
        />
      </label>
    );

    // A document already exists: show the filename and actions.
    if (doc) {
      return (
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            alignItems: "flex-start",
            gap: "2px",
          }}
        >
          <a
            href={doc.download_url}
            target="_blank"
            rel="noreferrer"
            title={doc.name}
            style={{
              display: "inline-block",
              maxWidth: "160px",
              whiteSpace: "nowrap",
            }}
          >
            {formatFileName(doc.name)}
          </a>

          <span
            style={{
              display: "inline-flex",
              gap: "10px",
              alignItems: "center",
            }}
          >
            {filePicker("Modify", "Modify study plan")}

            <button
              type="button"
              onClick={() => deletePlan(doc.id)}
              title="Delete study plan"
              style={{
                background: "none",
                border: "none",
                padding: 0,
                cursor: "pointer",
                color: "#c0392b",
                fontSize: "13px",
                fontWeight: 500,
              }}
            >
              Delete
            </button>
          </span>
        </div>
      );
    }

    // No document yet: show upload action.
    return (
      <div
        style={{
          display: "flex",
          alignItems: "center",
        }}
      >
        {filePicker("Upload", "Upload study plan")}
      </div>
    );
  }

  return (
    <section>
      <div className="page-header">
        <h2>Students</h2>

        <button onClick={() => setDraft({ ...EMPTY })}>Add Student</button>
      </div>

      {loading && <p>Loading…</p>}

      {error && <p style={{ color: "red" }}>Error: {error}</p>}

      {!loading && !error && (
        <div className="table-wrapper">
          <table>
            <thead>
              <tr>
                <th>Matriculation No.</th>
                <th>Name</th>
                <th>Email</th>
                <th>Course</th>
                <th>Sem.</th>
                <th>CP</th>
                <th>Status</th>
                <th>Initial plan</th>
                <th>Final plan</th>
                <th>Actions</th>
              </tr>
            </thead>

            <tbody>
              {students.length === 0 && (
                <tr>
                  <td colSpan={10}>No students yet.</td>
                </tr>
              )}

              {students.map((s) => (
                <tr key={s.id}>
                  <td>{s.matriculation_number}</td>

                  <td>
                    {s.first_name} {s.last_name}
                  </td>

                  <td>{s.email}</td>

                  <td>{s.course_of_studies}</td>

                  <td>{s.current_study_semester}</td>

                  <td>{s.credit_points === -1 ? "—" : s.credit_points}</td>

                  <td>{s.contact_status}</td>

                  <td>
                    <PlanCell s={s} which="initial" />
                  </td>

                  <td>
                    <PlanCell s={s} which="final" />
                  </td>

                  <td>
                    <button
                      className="icon-btn"
                      title="Edit"
                      aria-label="Edit"
                      onClick={() => setDraft({ ...s })}
                    >
                      <EditIcon />
                    </button>

                    <button
                      className="icon-btn"
                      title="Mails"
                      aria-label="Mails"
                      onClick={() => openMails(s)}
                    >
                      <MailIcon />
                    </button>

                    <button
                      className="icon-btn icon-btn--danger"
                      title="Delete"
                      aria-label="Delete"
                      onClick={() => removeStudent(s)}
                    >
                      <TrashIcon />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {draft && (
        <Modal
          title={draft.id === 0 ? "Add Student" : "Edit Student"}
          onClose={() => setDraft(null)}
        >
          <div className="card">
            <label>Matriculation No.</label>

            <input
              value={draft.matriculation_number}
              onChange={(e) =>
                setDraft({
                  ...draft,
                  matriculation_number: e.target.value,
                })
              }
            />

            <label>First name</label>

            <input
              value={draft.first_name}
              onChange={(e) =>
                setDraft({
                  ...draft,
                  first_name: e.target.value,
                })
              }
            />

            <label>Last name</label>

            <input
              value={draft.last_name}
              onChange={(e) =>
                setDraft({
                  ...draft,
                  last_name: e.target.value,
                })
              }
            />

            <label>Email</label>

            <input
              value={draft.email}
              onChange={(e) =>
                setDraft({
                  ...draft,
                  email: e.target.value,
                })
              }
            />

            <label>Course</label>

            <input
              value={draft.course_of_studies ?? ""}
              onChange={(e) =>
                setDraft({
                  ...draft,
                  course_of_studies: e.target.value,
                })
              }
            />

            <label>Semester</label>

            <input
              type="number"
              value={draft.current_study_semester ?? 0}
              onChange={(e) =>
                setDraft({
                  ...draft,
                  current_study_semester: Number(e.target.value),
                })
              }
            />

            <label>Credit points</label>

            <input
              type="number"
              value={draft.credit_points}
              onChange={(e) =>
                setDraft({
                  ...draft,
                  credit_points: Number(e.target.value),
                })
              }
            />

            <label>Status</label>

            <select
              value={draft.contact_status}
              onChange={(e) =>
                setDraft({
                  ...draft,
                  contact_status: e.target.value,
                })
              }
            >
              <option value="not_contacted_yet">Not contacted</option>

              <option value="emailed">Emailed</option>

              <option value="confirmed">Confirmed</option>

              <option value="didnt_respond">Didn't respond</option>
            </select>

            <div
              style={{
                marginTop: "1rem",
                display: "flex",
                gap: "0.5rem",
              }}
            >
              <button onClick={saveDraft} disabled={saving}>
                {saving ? "Saving…" : "Save"}
              </button>

              <button onClick={() => setDraft(null)}>Cancel</button>
            </div>
          </div>
        </Modal>
      )}
    </section>
  );
}

export default StudentsPage;
