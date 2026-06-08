import { useState } from "react";
import { useNavigate } from "react-router-dom";
import type { Counselor } from "../types/counselor";
// import Modal from "../components/common/Modal";
import Modal from "../components/common/Model";

const INITIAL_COUNSELORS: Counselor[] = [
  {
    id: 1,
    title: "Prof. Dr.",
    first_name: "Thomas",
    last_name: "Schmidt",
    chair: "Software Engineering",
    office_address: "AE22-R273",
    email: "schmidt@example.com",
    additional_cc: ["secretary@example.com"],
  },
];

function CounselorsPage() {
  const navigate = useNavigate();
  const [counselors, setCounselors] = useState<Counselor[]>(INITIAL_COUNSELORS);
  const [draft, setDraft] = useState<Counselor | null>(null);

  function openMail(c: Counselor) {
    navigate(`/counselors/${c.id}/mail`, { state: { counselor: c } });
  }

  function saveDraft() {
    if (!draft) return;
    setCounselors((prev) => prev.map((c) => (c.id === draft.id ? draft : c)));
    setDraft(null);
  }

  return (
    <section>
      <div className="page-header">
        <h2>Counselors</h2>
        <button>Add Counselor</button>
      </div>

      <div className="table-wrapper">
        <table>
          <thead>
            <tr>
              <th>Title</th>
              <th>Name</th>
              <th>Chair</th>
              <th>Office</th>
              <th>Email</th>
              <th>CC</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {counselors.map((c) => (
              <tr key={c.id}>
                <td>{c.title}</td>
                <td>
                  {c.first_name} {c.last_name}
                </td>
                <td>{c.chair}</td>
                <td>{c.office_address}</td>
                <td>{c.email}</td>
                <td>{c.additional_cc.join(", ")}</td>
                <td>
                  <button onClick={() => setDraft({ ...c })}>Edit</button>
                  <button>Add Slot</button>
                  <button onClick={() => openMail(c)}>Mail</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {draft && (
        <Modal title="Edit Counselor" onClose={() => setDraft(null)}>
          <div className="card">
            <label>Title</label>
            <input
              value={draft.title}
              onChange={(e) => setDraft({ ...draft, title: e.target.value })}
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
            <label>Chair</label>
            <input
              value={draft.chair}
              onChange={(e) => setDraft({ ...draft, chair: e.target.value })}
            />
            <label>Office</label>
            <input
              value={draft.office_address}
              onChange={(e) =>
                setDraft({ ...draft, office_address: e.target.value })
              }
            />
            <label>Email</label>
            <input
              value={draft.email}
              onChange={(e) => setDraft({ ...draft, email: e.target.value })}
            />
            <label>CC (comma-separated)</label>
            <input
              value={draft.additional_cc.join(", ")}
              onChange={(e) =>
                setDraft({
                  ...draft,
                  additional_cc: e.target.value
                    .split(",")
                    .map((x) => x.trim())
                    .filter(Boolean),
                })
              }
            />
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

export default CounselorsPage;
