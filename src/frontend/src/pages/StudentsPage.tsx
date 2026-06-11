import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import type { Student } from "../types/student";
import Modal from "../components/common/Model";
import api from "../api/client";

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
      .get<Student[]>("/students/students/")
      .then((res) => setStudents(res.data))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    load();
  }, []);

  function openSessions(s: Student) {
    navigate(`/students/${s.id}/mail`, { state: { student: s } });
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
        await api.patch(`/students/students/${draft.id}/`, payload);
      } else {
        await api.post("/students/students/", payload);
      }
      setDraft(null);
      load();
    } catch (err) {
      alert("Save failed: " + (err as Error).message);
    } finally {
      setSaving(false);
    }
  }

  async function removeStudent(s: Student) {
    if (!window.confirm(`Delete ${s.first_name} ${s.last_name}?`)) return;
    try {
      await api.delete(`/students/students/${s.id}/`);
      load();
    } catch (err) {
      alert("Delete failed: " + (err as Error).message);
    }
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
                <th>Semester</th>
                <th>CP</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {students.length === 0 && (
                <tr>
                  <td colSpan={8}>No students yet.</td>
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
                    <button onClick={() => setDraft({ ...s })}>Edit</button>
                    <button onClick={() => openSessions(s)}>Sessions</button>
                    <button onClick={() => removeStudent(s)}>Delete</button>
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
