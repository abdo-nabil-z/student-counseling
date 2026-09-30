import { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import api from "../api/client";
import Modal from "../components/common/Model";
import type { Counselor } from "../types/counselor";
import type { Student } from "../types/student";
import type { Slot } from "../types/slots";
import type { Appointment } from "../types/appointment";
import type { DocumentInfo } from "../types/document";

const STATUS_OPTIONS = [
  "pending",
  "booked",
  "completed",
  "cancelled",
  "missed",
];

const STATUS_COLORS: Record<string, string> = {
  pending: "#9ca3af",
  booked: "#3b82f6",
  completed: "#16a34a",
  cancelled: "#6b7280",
  missed: "#dc2626",
};

interface AppointmentPrefill {
  counselorId: number;
  slotId: number;
  startTime: string;
  endTime: string;
  location: string;
}

interface AppointmentOverlapWarning {
  message: string;
  overlapCount: number;
}

function getAppointmentOverlapWarning(
  error: unknown,
): AppointmentOverlapWarning | null {
  const apiError = (
    error as {
      response?: {
        data?: {
          error?: {
            code?: string;
            message?: string;
            details?: {
              overlapping_appointments?: unknown[];
              can_override?: boolean;
            };
          };
        };
      };
    }
  ).response?.data?.error;

  if (
    apiError?.code !== "appointment_overlap_warning" ||
    !apiError.details?.can_override
  ) {
    return null;
  }

  return {
    message:
      apiError.message ??
      "This appointment overlaps another active appointment.",
    overlapCount: apiError.details.overlapping_appointments?.length ?? 0,
  };
}

function addMinutes(hhmm: string, mins: number): string {
  const [h, m] = hhmm.split(":").map(Number);
  const total = h * 60 + m + mins;
  return `${String(Math.floor(total / 60) % 24).padStart(2, "0")}:${String(total % 60).padStart(2, "0")}`;
}
function minutesBetween(start: string, end: string): number {
  const [sh, sm] = start.split(":").map(Number);
  const [eh, em] = end.split(":").map(Number);
  return eh * 60 + em - (sh * 60 + sm);
}
function idOf(v: number | { id: number }): number {
  return typeof v === "object" ? v.id : v;
}
function TrashIcon() {
  return (
    <svg
      width="13"
      height="13"
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
    </svg>
  );
}

function AppointmentPage() {
  const navigate = useNavigate();
  const routeLocation = useLocation();

  const prefill = (routeLocation.state as AppointmentPrefill | null) ?? null;

  const [counselors, setCounselors] = useState<Counselor[]>([]);
  const [students, setStudents] = useState<Student[]>([]);
  const [appointments, setAppointments] = useState<Appointment[]>([]);

  const [counselorId, setCounselorId] = useState(
    prefill ? String(prefill.counselorId) : "",
  );

  const [slots, setSlots] = useState<Slot[]>([]);

  const [slotId, setSlotId] = useState(prefill ? String(prefill.slotId) : "");

  const [startTime, setStartTime] = useState(prefill?.startTime ?? "");

  const [endTime, setEndTime] = useState(prefill?.endTime ?? "");

  const [studentId, setStudentId] = useState("");

  const [location, setLocation] = useState(prefill?.location ?? "");

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [formError, setFormError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  // Edit-appointment modal state
  const [editing, setEditing] = useState<Appointment | null>(null);
  const [editCounselorId, setEditCounselorId] = useState("");
  const [editSlots, setEditSlots] = useState<Slot[]>([]);
  const [editSlotId, setEditSlotId] = useState("");
  const [editDate, setEditDate] = useState("");
  const [editStartTime, setEditStartTime] = useState("");
  const [editDuration, setEditDuration] = useState("30");
  const [editLocation, setEditLocation] = useState("");
  const [editStatus, setEditStatus] = useState("booked");
  const [editSaving, setEditSaving] = useState(false);
  const [editError, setEditError] = useState<string | null>(null);

  function reloadAll() {
    Promise.all([
      api.get<Student[]>("/students/"),
      api.get<Appointment[]>("/appointments/"),
    ])
      .then(([s, a]) => {
        setStudents(s.data);
        setAppointments(a.data);
      })
      .catch((e) => setError(e.message));
  }

  useEffect(() => {
    Promise.all([
      api.get<Counselor[]>("/counselors/"),
      api.get<Student[]>("/students/"),
      api.get<Appointment[]>("/appointments/"),
    ])
      .then(([c, s, a]) => {
        setCounselors(c.data);
        setStudents(s.data);
        setAppointments(a.data);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (!counselorId) return;
    api
      .get<Slot[]>(`/counselors/${counselorId}/slots/`)
      .then((r) => setSlots(r.data))
      .catch(() => setSlots([]));
  }, [counselorId]);

  // Fetch slots for whichever counselor is selected in the edit modal
  useEffect(() => {
    if (!editing || !editCounselorId) return;
    api
      .get<Slot[]>(`/counselors/${editCounselorId}/slots/`)
      .then((r) => setEditSlots(r.data))
      .catch(() => setEditSlots([]));
  }, [editing, editCounselorId]);

  function onCounselorChange(v: string) {
    setCounselorId(v);
    setSlotId("");
    setStartTime("");
    setEndTime("");

    const selectedCounselor = counselors.find(
      (counselor) => counselor.id === Number(v),
    );

    setLocation(selectedCounselor?.office_address ?? "");
    if (!v) setSlots([]);
  }
  function onSlotChange(v: string) {
    setSlotId(v);
    const slot = slots.find((s) => String(s.id) === v);
    if (slot) {
      const s = slot.start_time.slice(0, 5);
      setStartTime(s);
      setEndTime(addMinutes(s, 30));
    } else {
      setStartTime("");
      setEndTime("");
    }
  }

  const selectedSlot = slots.find((s) => String(s.id) === slotId) || null;
  const apptEnd = (a: Appointment) =>
    addMinutes(a.start_time.slice(11, 16), a.duration_minutes);
  const bookedInSlot = appointments
    .filter((a) => a.slot && a.slot.id === Number(slotId))
    .map((a) => `${a.start_time.slice(11, 16)}–${apptEnd(a)}`);
  const availableStudents = students.filter(
    (s) => !appointments.some((a) => idOf(a.student) === s.id),
  );

  const studentObj = (val: number | Student) =>
    typeof val === "object" ? val : students.find((x) => x.id === val);
  const counselorObj = (val: number | Counselor) =>
    typeof val === "object" ? val : counselors.find((x) => x.id === val);
  const studentLabel = (val: number | Student) => {
    const s = studentObj(val);
    return s ? `${s.first_name} ${s.last_name}` : `#${String(val)}`;
  };
  const counselorLabel = (val: number | Counselor) => {
    const c = counselorObj(val);
    return c ? `${c.title} ${c.last_name}` : `#${String(val)}`;
  };

  function mailStudent(a: Appointment) {
    const s = studentObj(a.student);
    if (!s) return;
    navigate("/mail", {
      state: {
        targetType: "student",
        targetIds: [s.id],
      },
    });
  }
  // function mailCounselor(a: Appointment) {
  //   const c = counselorObj(a.counselor);
  //   if (!c) return;
  //   navigate("/mail", {
  //     state: {
  //       targetType: "counselor",
  //       targetIds: [c.id],
  //     },
  //   });
  // }

  function openEdit(a: Appointment) {
    setEditing(a);
    setEditError(null);
    setEditCounselorId(String(idOf(a.counselor)));
    setEditSlots([]); // refetched by the effect above once editCounselorId is set
    setEditSlotId(a.slot ? String(a.slot.id) : "");
    setEditDate(a.start_time.slice(0, 10));
    setEditStartTime(a.start_time.slice(11, 16));
    setEditDuration(String(a.duration_minutes));
    setEditLocation(a.location ?? "");
    setEditStatus(a.status);
  }

  function onEditCounselorChange(v: string) {
    setEditCounselorId(v);
    setEditSlotId("");
    setEditSlots([]);

    const selectedCounselor = counselors.find(
      (counselor) => counselor.id === Number(v),
    );

    setEditLocation(selectedCounselor?.office_address ?? "");
  }

  function onEditSlotChange(v: string) {
    setEditSlotId(v);
    const slot = editSlots.find((s) => String(s.id) === v);
    if (slot) {
      setEditDate(slot.date);
      setEditStartTime(slot.start_time.slice(0, 5));
    }
  }

  async function saveEdit() {
    if (!editing) return;
    if (!editCounselorId || !editDate || !editStartTime || !editDuration) {
      setEditError("Counselor, date, start time, and duration are required.");
      return;
    }
    const duration = Number(editDuration);
    if (!Number.isFinite(duration) || duration <= 0) {
      setEditError("Duration must be a positive number of minutes.");
      return;
    }
    setEditSaving(true);
    setEditError(null);

    const payload = {
      counselor: Number(editCounselorId),
      slot: editSlotId ? Number(editSlotId) : null,
      start_time: `${editDate}T${editStartTime}:00`,
      duration_minutes: duration,
      location: editLocation || null,
      status: editStatus,
    };

    try {
      try {
        await api.patch(`/appointments/${editing.id}/`, payload);
      } catch (requestError: unknown) {
        const warning = getAppointmentOverlapWarning(requestError);

        if (!warning) throw requestError;

        const confirmed = window.confirm(
          `${warning.message}\n\n` +
            `${warning.overlapCount} overlapping appointment(s) found. ` +
            `Save anyway?`,
        );

        if (!confirmed) return;

        await api.patch(`/appointments/${editing.id}/`, {
          ...payload,
          allow_overlap: true,
        });
      }

      setEditing(null);
      reloadAll();
    } catch (e) {
      const err = e as { response?: { data?: unknown }; message: string };
      setEditError(
        "Could not save changes: " +
          (err.response?.data
            ? JSON.stringify(err.response.data)
            : err.message),
      );
    } finally {
      setEditSaving(false);
    }
  }

  async function uploadMinutes(appointmentId: number, file: File) {
    const fd = new FormData();
    fd.append("file", file);
    fd.append("name", file.name);
    try {
      await api.post(`/appointments/${appointmentId}/minutes/`, fd);
      reloadAll();
    } catch (err) {
      alert("Minutes upload failed: " + (err as Error).message);
    }
  }
  async function deleteDoc(docId: number) {
    if (!window.confirm("Delete this document?")) return;
    try {
      await api.delete(`/documents/${docId}/`);
      reloadAll();
    } catch (err) {
      alert("Delete failed: " + (err as Error).message);
    }
  }

  async function deleteAppointment(a: Appointment) {
    if (
      !window.confirm(
        `Delete the appointment for ${studentLabel(a.student)}? This cannot be undone.`,
      )
    )
      return;
    try {
      await api.delete(`/appointments/${a.id}/`);
      reloadAll();
    } catch (err) {
      alert("Delete failed: " + (err as Error).message);
    }
  }

  async function createAppointment() {
    if (
      !counselorId ||
      !slotId ||
      !studentId ||
      !startTime ||
      !endTime ||
      !selectedSlot
    ) {
      setFormError("Pick a counselor, slot, student, and start/end time.");
      return;
    }
    const duration = minutesBetween(startTime, endTime);
    if (duration <= 0) {
      setFormError("End time must be after start time.");
      return;
    }
    const slotStart = selectedSlot.start_time.slice(0, 5);
    const slotEnd = selectedSlot.end_time.slice(0, 5);
    if (startTime < slotStart || endTime > slotEnd) {
      if (
        !window.confirm(
          `The time ${startTime}–${endTime} is outside the slot window (${slotStart}–${slotEnd}). Create it anyway?`,
        )
      )
        return;
    }
    setSaving(true);
    setFormError(null);

    const payload = {
      student: Number(studentId),
      counselor: Number(counselorId),
      slot: Number(slotId),
      start_time: `${selectedSlot.date}T${startTime}:00`,
      duration_minutes: duration,
      location: location || null,
    };

    try {
      try {
        await api.post("/appointments/create-appointment/", payload);
      } catch (requestError: unknown) {
        const warning = getAppointmentOverlapWarning(requestError);

        if (!warning) throw requestError;

        const confirmed = window.confirm(
          `${warning.message}\n\n` +
            `${warning.overlapCount} overlapping appointment(s) found. ` +
            `Create anyway?`,
        );

        if (!confirmed) return;

        await api.post("/appointments/create-appointment/", {
          ...payload,
          allow_overlap: true,
        });
      }

      const createdStudent = students.find((s) => s.id === Number(studentId));
      const createdDate = selectedSlot.date;
      const createdTime = startTime;
      const createdPlace = location || "";

      setStudentId("");
      setLocation("");
      reloadAll();

      if (
        createdStudent &&
        window.confirm(
          `Appointment created for ${createdStudent.first_name} ${createdStudent.last_name}. Send the invitation email now?`,
        )
      ) {
        navigate(`/students/${createdStudent.id}/mail`, {
          state: {
            student: createdStudent,
            date: createdDate,
            time: createdTime,
            place: createdPlace,
          },
        });
      }
    } catch (e) {
      const err = e as { response?: { data?: unknown }; message: string };
      setFormError(
        "Could not create appointment: " +
          (err.response?.data
            ? JSON.stringify(err.response.data)
            : err.message),
      );
    } finally {
      setSaving(false);
    }
  }

  function DocCell({ doc }: { doc: DocumentInfo | null | undefined }) {
    if (!doc) return <>—</>;
    return (
      <span style={{ display: "inline-flex", alignItems: "center", gap: 6 }}>
        <a href={doc.download_url} target="_blank" rel="noreferrer">
          {doc.name}
        </a>
        <button
          className="icon-btn icon-btn--danger"
          title="Delete document"
          onClick={() => deleteDoc(doc.id)}
        >
          <TrashIcon />
        </button>
      </span>
    );
  }

  return (
    <section>
      <h2>Appointments</h2>
      {loading && <p>Loading…</p>}
      {error && <p style={{ color: "red" }}>Error: {error}</p>}

      {!loading && !error && (
        <>
          <div className="page-header">
            <h3>All appointments</h3>
            <span>{appointments.length} total</span>
          </div>

          <div className="table-wrapper">
            <table>
              <thead>
                <tr>
                  <th>Student</th>
                  <th>Counselor</th>
                  <th>Date</th>
                  <th>Time</th>
                  <th>Place</th>
                  <th>Status</th>
                  <th>Initial plan</th>
                  <th>Final plan</th>
                  <th>Minutes</th>
                  <th>Mail</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {appointments.length === 0 && (
                  <tr>
                    <td colSpan={11}>No appointments yet.</td>
                  </tr>
                )}
                {appointments.map((a) => {
                  const s = studentObj(a.student);
                  return (
                    <tr key={a.id}>
                      <td>{studentLabel(a.student)}</td>
                      <td>{counselorLabel(a.counselor)}</td>
                      <td>{a.start_time.slice(0, 10)}</td>
                      <td>
                        {a.start_time.slice(11, 16)}–{apptEnd(a)}
                      </td>
                      <td>{a.location || "—"}</td>
                      <td>
                        <span
                          style={{
                            background: STATUS_COLORS[a.status] ?? "#9ca3af",
                            color: "#fff",
                            borderRadius: 6,
                            padding: "2px 8px",
                            fontSize: 12,
                          }}
                        >
                          {a.status}
                        </span>
                      </td>
                      <td>
                        <DocCell doc={s?.initial_study_plan} />
                      </td>
                      <td>
                        <DocCell doc={s?.final_study_plan} />
                      </td>
                      <td>
                        {a.minutes && (
                          <>
                            <DocCell doc={a.minutes} />
                            <br />
                          </>
                        )}
                        <label className="icon-btn" title="Upload minutes PDF">
                          {a.minutes ? "Replace" : "Upload"}
                          <input
                            type="file"
                            style={{ display: "none" }}
                            onChange={(e) => {
                              const f = e.target.files?.[0];
                              if (f) uploadMinutes(a.id, f);
                              e.target.value = "";
                            }}
                          />
                        </label>
                      </td>
                      <td>
                        <div
                          style={{
                            display: "flex",
                            flexDirection: "column",
                            gap: 4,
                          }}
                        >
                          <button onClick={() => mailStudent(a)}>
                            Send Mail
                          </button>
                          {/* <button onClick={() => mailCounselor(a)}>
                            Mail counselor
                          </button> */}
                        </div>
                      </td>
                      <td>
                        <div
                          style={{
                            display: "flex",
                            flexDirection: "column",
                            gap: 4,
                          }}
                        >
                          <button onClick={() => openEdit(a)}>Edit</button>
                          <button
                            className="icon-btn--delete"
                            onClick={() => deleteAppointment(a)}
                          >
                            Delete
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          <div
            className="card"
            style={{ marginTop: "1.5rem", marginBottom: "1.5rem" }}
          >
            <h3>Book a new appointment</h3>
            <label>Counselor</label>
            <select
              value={counselorId}
              onChange={(e) => onCounselorChange(e.target.value)}
            >
              <option value="">— select —</option>
              {counselors.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.title} {c.first_name} {c.last_name}
                </option>
              ))}
            </select>

            <label>Availability slot</label>
            <select
              value={slotId}
              onChange={(e) => onSlotChange(e.target.value)}
              disabled={!counselorId}
            >
              <option value="">— select —</option>
              {slots.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.date} · {s.start_time.slice(0, 5)}–{s.end_time.slice(0, 5)}
                </option>
              ))}
            </select>

            {slotId && bookedInSlot.length > 0 && (
              <p style={{ fontSize: 13, color: "#666" }}>
                Already booked in this slot: {bookedInSlot.join(", ")}
              </p>
            )}

            <div style={{ display: "flex", gap: "1rem" }}>
              <div style={{ flex: 1 }}>
                <label>Start time</label>
                <input
                  type="time"
                  value={startTime}
                  onChange={(e) => setStartTime(e.target.value)}
                  disabled={!slotId}
                />
              </div>
              <div style={{ flex: 1 }}>
                <label>End time</label>
                <input
                  type="time"
                  value={endTime}
                  onChange={(e) => setEndTime(e.target.value)}
                  disabled={!slotId}
                />
              </div>
            </div>
            {startTime && endTime && minutesBetween(startTime, endTime) > 0 && (
              <p style={{ fontSize: 13, color: "#666" }}>
                Duration: {minutesBetween(startTime, endTime)} min
              </p>
            )}

            <label>Student</label>
            <select
              value={studentId}
              onChange={(e) => setStudentId(e.target.value)}
            >
              <option value="">— select —</option>
              {availableStudents.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.first_name} {s.last_name} ({s.matriculation_number})
                </option>
              ))}
            </select>

            <label>Place / location</label>
            <input
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              placeholder="e.g. AE22-R273 or Zoom link"
            />

            {formError && <p style={{ color: "red" }}>{formError}</p>}
            <div style={{ marginTop: "1rem" }}>
              <button onClick={createAppointment} disabled={saving}>
                {saving ? "Creating…" : "Create appointment"}
              </button>
            </div>
          </div>

          {editing && (
            <Modal
              title={`Edit Appointment — ${studentLabel(editing.student)}`}
              onClose={() => setEditing(null)}
            >
              <label>Counselor</label>
              <select
                value={editCounselorId}
                onChange={(e) => onEditCounselorChange(e.target.value)}
              >
                <option value="">— select —</option>
                {counselors.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.title} {c.first_name} {c.last_name}
                  </option>
                ))}
              </select>

              <label>Availability slot (optional)</label>
              <select
                value={editSlotId}
                onChange={(e) => onEditSlotChange(e.target.value)}
                disabled={!editCounselorId}
              >
                <option value="">— none / custom time —</option>
                {editSlots.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.date} · {s.start_time.slice(0, 5)}–
                    {s.end_time.slice(0, 5)}
                  </option>
                ))}
              </select>

              <div style={{ display: "flex", gap: "1rem" }}>
                <div style={{ flex: 1 }}>
                  <label>Date</label>
                  <input
                    type="date"
                    value={editDate}
                    onChange={(e) => setEditDate(e.target.value)}
                  />
                </div>
                <div style={{ flex: 1 }}>
                  <label>Start time</label>
                  <input
                    type="time"
                    value={editStartTime}
                    onChange={(e) => setEditStartTime(e.target.value)}
                  />
                </div>
                <div style={{ flex: 1 }}>
                  <label>Duration (min)</label>
                  <input
                    type="number"
                    min={1}
                    value={editDuration}
                    onChange={(e) => setEditDuration(e.target.value)}
                  />
                </div>
              </div>

              <label>Place / location</label>
              <input
                value={editLocation}
                onChange={(e) => setEditLocation(e.target.value)}
                placeholder="e.g. AE22-R273 or Zoom link"
              />

              <label>Status</label>
              <select
                value={editStatus}
                onChange={(e) => setEditStatus(e.target.value)}
              >
                {STATUS_OPTIONS.map((s) => (
                  <option key={s} value={s}>
                    {s}
                  </option>
                ))}
              </select>

              {editError && <p style={{ color: "red" }}>{editError}</p>}

              <div
                style={{ marginTop: "1rem", display: "flex", gap: "0.5rem" }}
              >
                <button onClick={saveEdit} disabled={editSaving}>
                  {editSaving ? "Saving…" : "Save changes"}
                </button>
                <button type="button" onClick={() => setEditing(null)}>
                  Cancel
                </button>
              </div>
            </Modal>
          )}
        </>
      )}
    </section>
  );
}

export default AppointmentPage;
