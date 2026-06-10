import { useEffect, useState } from "react";
import api from "../api/client";
import type { Counselor } from "../types/counselor";
import type { Student } from "../types/student";
import type { AvailabilityBlock, AppointmentSlot } from "../types/slots";

// "14:30" + 30 -> "15:00"
function addMinutes(time: string, minutes: number): string {
  const [h, m] = time.split(":").map(Number);
  const total = h * 60 + m + minutes;
  return `${String(Math.floor(total / 60)).padStart(2, "0")}:${String(total % 60).padStart(2, "0")}`;
}

// candidate 30-min start times inside a block window
function slotStartTimes(start: string, end: string, minutes = 30): string[] {
  const toMin = (t: string) => {
    const [h, m] = t.split(":").map(Number);
    return h * 60 + m;
  };
  const out: string[] = [];
  for (let t = toMin(start); t + minutes <= toMin(end); t += minutes) {
    out.push(
      `${String(Math.floor(t / 60)).padStart(2, "0")}:${String(t % 60).padStart(2, "0")}`,
    );
  }
  return out;
}

function PlanningPage() {
  const [counselors, setCounselors] = useState<Counselor[]>([]);
  const [students, setStudents] = useState<Student[]>([]);
  const [blocks, setBlocks] = useState<AvailabilityBlock[]>([]);
  const [slots, setSlots] = useState<AppointmentSlot[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const [counselorId, setCounselorId] = useState<number | "">("");
  const [blockId, setBlockId] = useState<number | "">("");
  const [startTime, setStartTime] = useState("");
  const [studentId, setStudentId] = useState<number | "">("");

  useEffect(() => {
    api
      .get<Counselor[]>("/counselors/")
      .then((r) => setCounselors(r.data))
      .catch((e) => setError(e.message));
    api
      .get<Student[]>("/students/students/")
      .then((r) => setStudents(r.data))
      .catch((e) => setError(e.message));
  }, []);

  // load the counselor's 3-hour blocks
  useEffect(() => {
    if (counselorId === "") {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setBlocks([]);
      setBlockId("");
      return;
    }
    api
      .get<AvailabilityBlock[]>(
        `/counselors/${counselorId}/availability-blocks`,
      )
      .then((r) => setBlocks(r.data))
      .catch((e) => setError(e.message));
  }, [counselorId]);

  // load existing 30-min slots for the chosen block
  function loadSlots(block: number) {
    api
      .get<AppointmentSlot[]>("/counselors/slots/", { params: { block } })
      .then((r) => setSlots(r.data))
      .catch((e) => setError(e.message));
  }
  useEffect(() => {
    if (blockId === "") {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setSlots([]);
      return;
    }
    loadSlots(blockId);
  }, [blockId]);

  const block = blocks.find((b) => b.id === blockId);
  const candidateTimes = block
    ? slotStartTimes(block.start_time.slice(0, 5), block.end_time.slice(0, 5))
    : [];
  const takenStarts = slots.map((s) => s.start_time.slice(11, 16)); // "HH:MM" already booked

  async function createSlot() {
    if (counselorId === "" || blockId === "" || !startTime || !block) {
      alert("Pick a counselor, a block and a 30-min start time.");
      return;
    }
    const endTime = addMinutes(startTime, 30);
    setSaving(true);
    try {
      // 1) create the 30-min slot in the AppointmentSlot table
      const res = await api.post<AppointmentSlot>("/counselors/slots/", {
        availability_block: blockId,
        start_time: `${block.date}T${startTime}:00`,
        end_time: `${block.date}T${endTime}:00`,
        status: studentId === "" ? "available" : "booked",
      });

      // 2) if a student was chosen, book the session against this slot
      if (studentId !== "") {
        await api.post("/session/create-session/", {
          student: studentId,
          counselor: counselorId,
          slot: res.data.id,
        });
      }

      setStartTime("");
      setStudentId("");
      loadSlots(blockId);
    } catch (err) {
      alert("Failed: " + (err as Error).message);
    } finally {
      setSaving(false);
    }
  }

  return (
    <section>
      <h2>Planning</h2>
      {error && <p style={{ color: "red" }}>Error: {error}</p>}

      <div className="card">
        <h3>Create a 30-min slot</h3>

        <label>Counselor</label>
        <select
          value={counselorId}
          onChange={(e) =>
            setCounselorId(e.target.value === "" ? "" : Number(e.target.value))
          }
        >
          <option value="">Select counselor</option>
          {counselors.map((c) => (
            <option key={c.id} value={c.id}>
              {c.title} {c.first_name} {c.last_name}
            </option>
          ))}
        </select>

        <label>3-hour block</label>
        <select
          value={blockId}
          onChange={(e) =>
            setBlockId(e.target.value === "" ? "" : Number(e.target.value))
          }
          disabled={counselorId === ""}
        >
          <option value="">
            {counselorId === "" ? "Pick a counselor first" : "Select block"}
          </option>
          {blocks.map((b) => (
            <option key={b.id} value={b.id}>
              {b.date} · {b.start_time.slice(0, 5)}–{b.end_time.slice(0, 5)}
            </option>
          ))}
        </select>

        <label>30-min start time</label>
        <select
          value={startTime}
          onChange={(e) => setStartTime(e.target.value)}
          disabled={blockId === ""}
        >
          <option value="">Select time</option>
          {candidateTimes.map((t) => (
            <option key={t} value={t} disabled={takenStarts.includes(t)}>
              {t}–{addMinutes(t, 30)} {takenStarts.includes(t) ? "(taken)" : ""}
            </option>
          ))}
        </select>

        <label>Assign student (optional)</label>
        <select
          value={studentId}
          onChange={(e) =>
            setStudentId(e.target.value === "" ? "" : Number(e.target.value))
          }
        >
          <option value="">— leave open —</option>
          {students.map((s) => (
            <option key={s.id} value={s.id}>
              {s.first_name} {s.last_name} ({s.matriculation_number})
            </option>
          ))}
        </select>

        <div style={{ marginTop: "1rem" }}>
          <button onClick={createSlot} disabled={saving}>
            {saving ? "Saving…" : "Create slot"}
          </button>
        </div>
      </div>

      {blockId !== "" && (
        <div className="card">
          <h3>Slots in this block</h3>
          {slots.length === 0 && <p>No slots created yet.</p>}
          {slots.length > 0 && (
            <table>
              <thead>
                <tr>
                  <th>Start</th>
                  <th>End</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {slots.map((s) => (
                  <tr key={s.id}>
                    <td>{s.start_time.slice(11, 16)}</td>
                    <td>{s.end_time.slice(11, 16)}</td>
                    <td>{s.status}</td>
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

export default PlanningPage;
