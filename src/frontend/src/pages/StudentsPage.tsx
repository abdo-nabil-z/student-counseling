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
      if (draft.id) await api.patch(`/students/${draft.id}/`, payload);
      else await api.post("/students/", payload);
      setDraft(null);
      load();
    } catch (err) {
      const e = err as { response?: { data?: unknown }; message: string };
      alert(
        "Save failed: " +
          (e.response?.data ? JSON.stringify(e.response.data) : e.message),
      );
    } finally {
      setSaving(false);
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
    if (doc) {
      return (
        <a href={doc.download_url} target="_blank" rel="noreferrer">
          {doc.name}
        </a>
      );
    }
    return (
      <label className="icon-btn" title="Upload study plan">
        Upload
        <input
          type="file"
          style={{ display: "none" }}
          onChange={(e) => {
            const f = e.target.files?.[0];
            if (f) uploadPlan(s.id, which, f);
            e.target.value = "";
          }}
        />
      </label>
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
                    <button onClick={() => openMails(s)}>Mails</button>
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
                setDraft({ ...draft, matriculation_number: e.target.value })
              }
            />
            <label>First name</label>
            <input
              value={draft.first_name}
              onChange={(e) =>
                setDraft({ ...draft, first_name: e.target.value })
              }
            />
            <label>Last name</label>
            <input
              value={draft.last_name}
              onChange={(e) =>
                setDraft({ ...draft, last_name: e.target.value })
              }
            />
            <label>Email</label>
            <input
              value={draft.email}
              onChange={(e) => setDraft({ ...draft, email: e.target.value })}
            />
            <label>Course</label>
            <input
              value={draft.course_of_studies ?? ""}
              onChange={(e) =>
                setDraft({ ...draft, course_of_studies: e.target.value })
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
                setDraft({ ...draft, credit_points: Number(e.target.value) })
              }
            />
            <label>Status</label>
            <select
              value={draft.contact_status}
              onChange={(e) =>
                setDraft({ ...draft, contact_status: e.target.value })
              }
            >
              <option value="not_contacted_yet">Not contacted</option>
              <option value="emailed">Emailed</option>
              <option value="confirmed">Confirmed</option>
              <option value="didnt_respond">Didn't respond</option>
            </select>
            <div style={{ marginTop: "1rem", display: "flex", gap: "0.5rem" }}>
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
