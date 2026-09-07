import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import api from "../api/client";
import type { Counselor } from "../types/counselor";
import type { Slot } from "../types/slots";

function SlotsPage() {
  const [searchParams] = useSearchParams();
  const [counselors, setCounselors] = useState<Counselor[]>([]);
  const [selectedId, setSelectedId] = useState<number | "">("");
  const [slots, setSlots] = useState<Slot[]>([]);
  const [reloadKey, setReloadKey] = useState(0);
  const [date, setDate] = useState("");
  const [start, setStart] = useState("");
  const [end, setEnd] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .get<Counselor[]>("/counselors/")
      .then((res) => {
        setCounselors(res.data);
        const param = searchParams.get("counselor");
        if (param) setSelectedId(Number(param));
        else if (res.data.length > 0) setSelectedId(res.data[0].id);
      })
      .catch((err) => setError(err.message));
  }, [searchParams]);

  useEffect(() => {
    if (selectedId === "") return;
    api
      .get<Slot[]>(`/counselors/${selectedId}/slots/`)
      .then((res) => setSlots(res.data))
      .catch((err) => setError(err.message));
  }, [selectedId, reloadKey]);

  async function createSlot() {
    if (selectedId === "" || !date || !start || !end) {
      alert("Pick a counselor and fill date, start and end time.");
      return;
    }
    setSaving(true);
    try {
      await api.post(`/counselors/${selectedId}/slots/`, {
        date,
        start_time: start,
        end_time: end,
      });
      setDate("");
      setStart("");
      setEnd("");
      setReloadKey((k) => k + 1);
    } catch (err) {
      const e = err as { response?: { data?: unknown }; message: string };
      alert(
        "Create failed: " +
          (e.response?.data ? JSON.stringify(e.response.data) : e.message),
      );
    } finally {
      setSaving(false);
    }
  }

  const selectedCounselor =
    selectedId === ""
      ? undefined
      : counselors.find((counselor) => counselor.id === selectedId);

  return (
    <section>
      <h2>Time Slots & Availability</h2>
      {error && <p style={{ color: "red" }}>Error: {error}</p>}

      {selectedId !== "" && (
        <div className="card">
          <h3>Availability Slots</h3>
          {slots.length === 0 && <p>No slots for this counselor yet.</p>}
          {slots.length > 0 && (
            <table>
              <thead>
                <tr>
                  <th>Counsellor</th>
                  <th>Chair</th>
                  <th>Office</th>
                  <th>Email</th>
                  <th>Date</th>
                  <th>Start</th>
                  <th>End</th>
                </tr>
              </thead>
              <tbody>
                {slots.map((s) => (
                  <tr key={s.id}>
                    <td>
                      {selectedCounselor
                        ? `${selectedCounselor.title} ${selectedCounselor.first_name} ${selectedCounselor.last_name}`
                        : "—"}
                    </td>

                    <td>{selectedCounselor?.chair || "—"}</td>

                    <td>{selectedCounselor?.office_address || "—"}</td>

                    <td>
                      {selectedCounselor?.email ? (
                        <a href={`mailto:${selectedCounselor.email}`}>
                          {selectedCounselor.email}
                        </a>
                      ) : (
                        "—"
                      )}
                    </td>

                    <td>{s.date}</td>
                    <td>{s.start_time.slice(0, 5)}</td>
                    <td>{s.end_time.slice(0, 5)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      <div className="card">
        <h3>Create Availability Slot</h3>
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
          <button onClick={createSlot} disabled={saving}>
            {saving ? "Saving…" : "Create Slot"}
          </button>
        </div>
      </div>
    </section>
  );
}

export default SlotsPage;
