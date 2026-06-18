import { useEffect, useState } from "react";
import api from "../api/client";
import type { Counselor } from "../types/counselor";
import type { Student } from "../types/student";
import type { AvailabilityBlock, AppointmentSlot } from "../types/slots";
import type { CounselingSessionDetail } from "../types/session";

const STATUS_COLORS: Record<string, string> = {
  pending: "#9ca3af",
  booked: "#3b82f6",
  completed: "#16a34a",
  cancelled: "#6b7280",
  missed: "#dc2626",
};

function addMinutes(hhmm: string, mins: number): string {
  const [h, m] = hhmm.split(":").map(Number);
  const total = h * 60 + m + mins;
  const nh = Math.floor(total / 60) % 24;
  const nm = total % 60;
  return `${String(nh).padStart(2, "0")}:${String(nm).padStart(2, "0")}`;
}

function slotStartTimes(start: string, end: string, step = 30): string[] {
  const toMin = (t: string) => {
    const [h, m] = t.split(":").map(Number);
    return h * 60 + m;
  };
  const out: string[] = [];
  for (let t = toMin(start); t + step <= toMin(end); t += step) {
    out.push(
      `${String(Math.floor(t / 60)).padStart(2, "0")}:${String(t % 60).padStart(2, "0")}`,
    );
  }
  return out;
}

function AppointmentsPage() {
  // reference data
  const [counselors, setCounselors] = useState<Counselor[]>([]);
  const [students, setStudents] = useState<Student[]>([]);
  const [sessions, setSessions] = useState<CounselingSessionDetail[]>([]);

  // booking form
  const [counselorId, setCounselorId] = useState("");
  const [blocks, setBlocks] = useState<AvailabilityBlock[]>([]);
  const [blockId, setBlockId] = useState("");
  const [takenTimes, setTakenTimes] = useState<string[]>([]);
  const [startTime, setStartTime] = useState("");
  const [studentId, setStudentId] = useState("");

  // ui state
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [formError, setFormError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [reloadKey, setReloadKey] = useState(0);

  function loadSessions() {
    api
      .get<CounselingSessionDetail[]>("/session/")
      .then((r) => setSessions(r.data))
      .catch((e) => setError(e.message));
  }

  // initial load
  useEffect(() => {
    Promise.all([
      api.get<Counselor[]>("/counselors/"),
      api.get<Student[]>("/students/students/"),
      api.get<CounselingSessionDetail[]>("/session/"),
    ])
      .then(([c, s, ss]) => {
        setCounselors(c.data);
        setStudents(s.data);
        setSessions(ss.data);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  // load blocks when the counselor changes
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setBlockId("");
    setStartTime("");
    if (!counselorId) {
      setBlocks([]);
      return;
    }
    api
      .get<AvailabilityBlock[]>(
        `/counselors/${counselorId}/availability-blocks`,
      )
      .then((r) => setBlocks(r.data))
      .catch(() => setBlocks([]));
  }, [counselorId]);

  // load already-taken slot times when the block changes (or after a booking)
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setStartTime("");
    if (!blockId) {
      setTakenTimes([]);
      return;
    }
    api
      .get<AppointmentSlot[]>(`/counselors/slots/?block=${blockId}`)
      .then((r) => setTakenTimes(r.data.map((s) => s.start_time.slice(11, 16))))
      .catch(() => setTakenTimes([]));
  }, [blockId, reloadKey]);

  const selectedBlock = blocks.find((b) => String(b.id) === blockId) || null;
  const times = selectedBlock
    ? slotStartTimes(
        selectedBlock.start_time.slice(0, 5),
        selectedBlock.end_time.slice(0, 5),
      )
    : [];

  async function createAppointment() {
    if (!counselorId || !blockId || !startTime || !selectedBlock) {
      setFormError("Pick a counselor, a block and a time.");
      return;
    }
    setSaving(true);
    setFormError(null);
    try {
      const endTime = addMinutes(startTime, 30);
      const slotRes = await api.post<AppointmentSlot>("/counselors/slots/", {
        availability_block: Number(blockId),
        start_time: `${selectedBlock.date}T${startTime}:00`,
        end_time: `${selectedBlock.date}T${endTime}:00`,
        status: studentId ? "booked" : "available",
      });
      if (studentId) {
        await api.post("/session/create-session/", {
          student: Number(studentId),
          counselor: Number(counselorId),
          slot: slotRes.data.id,
        });
      }
      setStartTime("");
      setStudentId("");
      setReloadKey((k) => k + 1); // refresh taken times
      loadSessions(); // refresh the table
    } catch (e) {
      setFormError("Could not create appointment: " + (e as Error).message);
    } finally {
      setSaving(false);
    }
  }

  return (
    <section>
      <h2>Appointments</h2>

      {loading && <p>Loading…</p>}
      {error && <p style={{ color: "red" }}>Error: {error}</p>}

      {!loading && !error && (
        <>
          {/* ---- Book a new appointment ---- */}
          <div className="card" style={{ marginBottom: "1.5rem" }}>
            <h3>Book a new appointment</h3>

            <label>Counselor</label>
            <select
              value={counselorId}
              onChange={(e) => setCounselorId(e.target.value)}
            >
              <option value="">— select —</option>
              {counselors.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.title} {c.first_name} {c.last_name}
                </option>
              ))}
            </select>

            <label>Availability block</label>
            <select
              value={blockId}
              onChange={(e) => setBlockId(e.target.value)}
              disabled={!counselorId}
            >
              <option value="">— select —</option>
              {blocks.map((b) => (
                <option key={b.id} value={b.id}>
                  {b.date} · {b.start_time.slice(0, 5)}–{b.end_time.slice(0, 5)}
                </option>
              ))}
            </select>

            <label>Time (30 min)</label>
            <select
              value={startTime}
              onChange={(e) => setStartTime(e.target.value)}
              disabled={!blockId}
            >
              <option value="">— select —</option>
              {times.map((t) => (
                <option key={t} value={t} disabled={takenTimes.includes(t)}>
                  {t}–{addMinutes(t, 30)}{" "}
                  {takenTimes.includes(t) ? "(taken)" : ""}
                </option>
              ))}
            </select>

            <label>Student </label>
            <select
              value={studentId}
              onChange={(e) => setStudentId(e.target.value)}
            >
              <option value="">— none —</option>
              {students.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.first_name} {s.last_name} ({s.matriculation_number})
                </option>
              ))}
            </select>

            {formError && <p style={{ color: "red" }}>{formError}</p>}

            <div style={{ marginTop: "1rem" }}>
              <button onClick={createAppointment} disabled={saving}>
                {saving ? "Creating…" : "Create appointment"}
              </button>
            </div>
          </div>

          {/* ---- All appointments ---- */}
          <div className="page-header">
            <h3>All appointments</h3>
            <span>{sessions.length} total</span>
          </div>

          <div className="table-wrapper">
            <table>
              <thead>
                <tr>
                  <th>Student</th>
                  <th>Counselor</th>
                  <th>Date</th>
                  <th>Time</th>
                  <th>Status</th>
                  <th>Study plan</th>
                </tr>
              </thead>
              <tbody>
                {sessions.length === 0 && (
                  <tr>
                    <td colSpan={6}>No appointments yet.</td>
                  </tr>
                )}
                {sessions.map((s) => (
                  <tr key={s.id}>
                    <td>
                      {s.student
                        ? `${s.student.first_name} ${s.student.last_name}`
                        : "—"}
                    </td>
                    <td>
                      {s.counselor
                        ? `${s.counselor.title} ${s.counselor.last_name}`
                        : "—"}
                    </td>
                    <td>{s.slot ? s.slot.start_time.slice(0, 10) : "—"}</td>
                    <td>
                      {s.slot
                        ? `${s.slot.start_time.slice(11, 16)}–${s.slot.end_time.slice(11, 16)}`
                        : "—"}
                    </td>
                    <td>
                      <span
                        style={{
                          background: STATUS_COLORS[s.status] ?? "#9ca3af",
                          color: "#fff",
                          borderRadius: 6,
                          padding: "2px 8px",
                          fontSize: 12,
                        }}
                      >
                        {s.status}
                      </span>
                    </td>
                    <td>{s.initial_study_plan ? "Yes" : "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </section>
  );
}

export default AppointmentsPage;
