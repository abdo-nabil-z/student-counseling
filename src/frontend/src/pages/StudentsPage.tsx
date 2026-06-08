import { useState } from "react";
import { useNavigate } from "react-router-dom";
import type { Student } from "../types/student";
import Modal from "../components/common/Model";

const INITIAL_STUDENTS: Student[] = [
  {
    id: 1,
    matriculation_number: "123456",
    first_name: "Max",
    last_name: "Müller",
    email: "max@example.com",
    course_of_studies: "Computer Science",
    current_study_semester: 5,
    credit_points: 70,
    contact_status: "not_contacted_yet",
  },
];

function StudentsPage() {
  const navigate = useNavigate();
  const [students, setStudents] = useState<Student[]>(INITIAL_STUDENTS);
  const [draft, setDraft] = useState<Student | null>(null);

  function openSessions(s: Student) {
    navigate(`/students/${s.id}/mail`, { state: { student: s } });
  }

  function saveDraft() {
    if (!draft) return;
    setStudents((prev) => prev.map((s) => (s.id === draft.id ? draft : s)));
    setDraft(null);
  }

  return (
    <section>
      <div className="page-header">
        <h2>Students</h2>
        <button>Add Student</button>
      </div>

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
                  <button>Assign</button>
                  <button onClick={() => openSessions(s)}>Sessions</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {draft && (
        <Modal title="Edit Student" onClose={() => setDraft(null)}>
          <div className="card">
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
              <button onClick={saveDraft}>Save</button>
              <button onClick={() => setDraft(null)}>Cancel</button>
            </div>
          </div>
        </Modal>
      )}
    </section>
  );
}

export default StudentsPage;
