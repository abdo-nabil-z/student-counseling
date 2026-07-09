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

  function openslots() {
    navigate("/slots");
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
                {/* <th>CC</th> */}
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
                  {/* <td>{c.additional_cc.join(", ")}</td> */}
                  <td>
                    <button onClick={() => setDraft({ ...c })}>Edit</button>
                    <button onClick={() => openMail(c)}>Mail</button>
                    <button onClick={() => removeCounselor(c)}>Delete</button>
                    <button onClick={() => openslots()}>Slots</button>
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
