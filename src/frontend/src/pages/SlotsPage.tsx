import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import api from "../api/client";
import type { Counselor } from "../types/counselor";
import type { Slot } from "../types/slots";

function getTodayDate(): string {
  const today = new Date();

  return [
    today.getFullYear(),
    String(today.getMonth() + 1).padStart(2, "0"),
    String(today.getDate()).padStart(2, "0"),
  ].join("-");
}

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
    if (saving) return;

    setError(null);

    if (selectedId === "" || !date || !start || !end) {
      setError("Select a counselor, date, start time, and end time.");
      return;
    }

    if (date < getTodayDate()) {
      window.alert("Availability slots cannot be created for a past date.");
      return;
    }

    if (start >= end) {
      setError("End time must be after start time.");
      return;
    }

    const counselorId = selectedId;

    setSaving(true);

    try {
      // Fetch the latest slots before checking for a duplicate.
      const response = await api.get<Slot[]>(
        `/counselors/${counselorId}/slots/`,
      );

      const duplicate = response.data.some(
        (slot) =>
          slot.date === date &&
          slot.start_time.slice(0, 5) === start &&
          slot.end_time.slice(0, 5) === end,
      );

      if (duplicate) {
        window.alert(
          "This counselor already has an availability slot " +
            "on this date with the same start and end times.",
        );
        return;
      }
      await api.post(`/counselors/${counselorId}/slots/`, {
        date,
        start_time: start,
        end_time: end,
      });

      setDate("");
      setStart("");
      setEnd("");
      setReloadKey((current) => current + 1);
    } catch (requestError) {
      const error = requestError as {
        response?: { data?: unknown };
        message?: string;
      };

      setError(
        error.response?.data
          ? JSON.stringify(error.response.data)
          : error.message || "Could not create the slot.",
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
          min={getTodayDate()}
          value={date}
          onChange={(event) => setDate(event.target.value)}
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
