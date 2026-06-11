import { useEffect, useState } from "react";
import api from "../api/client";
import type { CounselingSessionDetail } from "../types/session";

const STATUS_COLORS: Record<string, string> = {
  pending: "#9ca3af",
  booked: "#3b82f6",
  completed: "#16a34a",
  cancelled: "#6b7280",
  missed: "#dc2626",
};

function fmtDate(dt: string | undefined) {
  return dt ? dt.slice(0, 10) : "—";
}
function fmtTimeRange(slot: CounselingSessionDetail["slot"]) {
  return slot
    ? `${slot.start_time.slice(11, 16)}–${slot.end_time.slice(11, 16)}`
    : "—";
}

function SessionsPage() {
  const [sessions, setSessions] = useState<CounselingSessionDetail[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .get<CounselingSessionDetail[]>("/session/")
      .then((r) => setSessions(r.data))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  return (
    <section>
      <div className="page-header">
        <h2>Sessions</h2>
        {!loading && !error && <span>{sessions.length} total</span>}
      </div>

      {loading && <p>Loading…</p>}
      {error && <p style={{ color: "red" }}>Error: {error}</p>}

      {!loading && !error && (
        <div className="table-wrapper">
          <table>
            <thead>
              <tr>
                <th>Student</th>
                <th>Matric. No.</th>
                <th>Counselor</th>
                <th>Date</th>
                <th>Time</th>
                <th>Status</th>
                <th>Initial plan</th>
                <th>Final plan</th>
                <th>Minutes</th>
                <th>Created</th>
              </tr>
            </thead>
            <tbody>
              {sessions.length === 0 && (
                <tr>
                  <td colSpan={10}>No sessions yet.</td>
                </tr>
              )}
              {sessions.map((s) => (
                <tr key={s.id}>
                  <td>
                    {s.student
                      ? `${s.student.first_name} ${s.student.last_name}`
                      : "—"}
                  </td>
                  <td>{s.student ? s.student.matriculation_number : "—"}</td>
                  <td>
                    {s.counselor
                      ? `${s.counselor.title} ${s.counselor.last_name}`
                      : "—"}
                  </td>
                  <td>{fmtDate(s.slot?.start_time)}</td>
                  <td>{fmtTimeRange(s.slot)}</td>
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
                  <td>{s.final_study_plan ? "Yes" : "—"}</td>
                  <td>{s.notes ? "Yes" : "—"}</td>
                  <td>{fmtDate(s.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}

export default SessionsPage;
