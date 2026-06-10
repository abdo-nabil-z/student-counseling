import { useEffect, useState } from "react";
import api from "../api/client";
import type { Counselor } from "../types/counselor";
import type { AvailabilityBlock } from "../types/slots";

function SlotsPage() {
  const [counselors, setCounselors] = useState<Counselor[]>([]);
  const [selectedId, setSelectedId] = useState<number | "">("");
  const [blocks, setBlocks] = useState<AvailabilityBlock[]>([]);
  const [reloadKey, setReloadKey] = useState(0);
  const [date, setDate] = useState("");
  const [start, setStart] = useState("");
  const [end, setEnd] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .get<Counselor[]>("/counselors/")
      .then((res) => setCounselors(res.data))
      .catch((err) => setError(err.message));
  }, []);

  useEffect(() => {
    if (selectedId === "") {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setBlocks([]);
      return;
    }
    api
      .get<AvailabilityBlock[]>(`/counselors/${selectedId}/availability-blocks`)
      .then((res) => setBlocks(res.data))
      .catch((err) => setError(err.message));
  }, [selectedId, reloadKey]);

  async function createBlock() {
    if (selectedId === "" || !date || !start || !end) {
      alert("Pick a counselor and fill date, start and end time.");
      return;
    }
    setSaving(true);
    try {
      await api.post(`/counselors/${selectedId}/availability-blocks`, {
        date,
        start_time: start,
        end_time: end,
      });
      setDate("");
      setStart("");
      setEnd("");
      setReloadKey((k) => k + 1);
    } catch (err) {
      alert("Create failed: " + (err as Error).message);
    } finally {
      setSaving(false);
    }
  }

  return (
    <section>
      <h2>Time Slots & Availability</h2>
      {error && <p style={{ color: "red" }}>Error: {error}</p>}

      <div className="card">
        <h3>Create Availability Block</h3>

        <label>Counselor</label>
        <select
          value={selectedId}
          onChange={(e) =>
            setSelectedId(e.target.value === "" ? "" : Number(e.target.value))
          }
        >
          <option value="">Select counselor</option>
          {counselors.map((c) => (
            <option key={c.id} value={c.id}>
              {c.title} {c.first_name} {c.last_name}
            </option>
          ))}
        </select>

        <label>Date</label>
        <input
          type="date"
          value={date}
          onChange={(e) => setDate(e.target.value)}
        />
        <label>Start Time</label>
        <input
          type="time"
          value={start}
          onChange={(e) => setStart(e.target.value)}
        />
        <label>End Time</label>
        <input
          type="time"
          value={end}
          onChange={(e) => setEnd(e.target.value)}
        />

        <div style={{ marginTop: "1rem" }}>
          <button onClick={createBlock} disabled={saving}>
            {saving ? "Saving…" : "Create Block"}
          </button>
        </div>
      </div>

      {selectedId !== "" && (
        <div className="card">
          <h3>Availability Blocks</h3>
          {blocks.length === 0 && (
            <p>No availability blocks for this counselor yet.</p>
          )}
          {blocks.length > 0 && (
            <table>
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Start</th>
                  <th>End</th>
                </tr>
              </thead>
              <tbody>
                {blocks.map((b) => (
                  <tr key={b.id}>
                    <td>{b.date}</td>
                    <td>{b.start_time.slice(0, 5)}</td>
                    <td>{b.end_time.slice(0, 5)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}
    </section>
  );
}

export default SlotsPage;
