import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import type { Counselor } from "../types/counselor";
import Modal from "../components/common/Model";
import api from "../api/client";

const EMPTY: Counselor = {
  id: 0,
  title: "",
  first_name: "",
  last_name: "",
  chair: "",
  office_address: "",
  email: "",
  additional_cc: [],
};

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
function CounselorsPage() {
  const navigate = useNavigate();
  const [counselors, setCounselors] = useState<Counselor[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [draft, setDraft] = useState<Counselor | null>(null);
  const [saving, setSaving] = useState(false);

  function load() {
    setLoading(true);
    api
      .get<Counselor[]>("/counselors/")
      .then((res) => setCounselors(res.data))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    load();
  }, []);

  function openMail(c: Counselor) {
    navigate(`/counselors/${c.id}/mail`, { state: { counselor: c } });
  }
  function openAvailabilityblocks() {
    navigate(`/slots`);
  }

  async function saveDraft() {
    if (!draft) return;
    setSaving(true);
    try {
      if (draft.id === 0) {
        await api.post("/counselors/", draft); // create
      } else {
        await api.patch(`/counselors/${draft.id}/`, draft); // update
      }
      setDraft(null);
      load(); // re-read from the database
    } catch (err) {
      alert("Save failed: " + (err as Error).message);
    } finally {
      setSaving(false);
    }
  }

  async function removeCounselor(c: Counselor) {
    if (!window.confirm(`Delete ${c.first_name} ${c.last_name}?`)) return;
    try {
      await api.delete(`/counselors/${c.id}/`);
      load();
    } catch (err) {
      alert("Delete failed: " + (err as Error).message);
    }
  }

  return (
    <section>
      <div className="page-header">
        <h2>Counselors</h2>
        <button onClick={() => setDraft({ ...EMPTY })}>Add Counselor</button>
      </div>

      {loading && <p>Loading…</p>}
      {error && <p style={{ color: "red" }}>Error: {error}</p>}

      {!loading && !error && (
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
              {counselors.length === 0 && (
                <tr>
                  <td colSpan={7}>No counselors yet.</td>
                </tr>
              )}
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
                    {/* <button onClick={() => setDraft({ ...c })}>Edit</button> */}
                    <button onClick={() => openMail(c)}>Mail</button>
                    {/* <button onClick={() => removeCounselor(c)}>Delete</button> */}
                    <button onClick={() => openAvailabilityblocks()}>
                      Availabilty Blocks
                    </button>
                    <button
                      className="icon-btn"
                      title="Edit"
                      aria-label="Edit"
                      onClick={() => setDraft({ ...c })}
                    >
                      <EditIcon />
                    </button>
                    <button
                      className="icon-btn icon-btn--danger"
                      title="Delete"
                      aria-label="Delete"
                      onClick={() => removeCounselor(c)}
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
          title={draft.id === 0 ? "Add Counselor" : "Edit Counselor"}
          onClose={() => setDraft(null)}
        >
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

export default CounselorsPage;
