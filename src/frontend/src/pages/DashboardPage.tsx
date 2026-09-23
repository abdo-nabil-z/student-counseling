import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../api/client";
import type { Student } from "../types/student";
import type { Counselor } from "../types/counselor";
import type { Appointment } from "../types/appointment";

interface SlotStatusSegment {
  status: "free" | "taken";
  start: string;
  end: string;
}

interface SlotStatusSlot {
  id: number;
  date: string;
  start_time: string;
  end_time: string;
  segments: SlotStatusSegment[];
}

interface CounselorSlotStatus {
  counselor: {
    id: number;
    full_name: string;
    email: string;
    office_address: string;
  };
  slots: SlotStatusSlot[];
}

interface AvailableSlot {
  key: string;
  counselor: Counselor;
  slotId: number;
  date: string;
  startTime: string;
  endTime: string;
}

function timeToMinutes(dateTime: string): number {
  const time = dateTime.slice(11, 16);
  const [hours, minutes] = time.split(":").map(Number);

  return hours * 60 + minutes;
}

function minutesToTime(totalMinutes: number): string {
  const hours = Math.floor(totalMinutes / 60);
  const minutes = totalMinutes % 60;

  return `${String(hours).padStart(2, "0")}:${String(minutes).padStart(
    2,
    "0",
  )}`;
}

function createAvailableSlots(
  slotStatuses: CounselorSlotStatus[],
  counselors: Counselor[],
): AvailableSlot[] {
  const result: AvailableSlot[] = [];
  const now = new Date();

  slotStatuses.forEach((counselorStatus) => {
    const counselor = counselors.find(
      (item) => item.id === counselorStatus.counselor.id,
    );

    if (!counselor) return;

    counselorStatus.slots.forEach((slot) => {
      const freeSegments = slot.segments.filter(
        (segment) => segment.status === "free",
      );

      freeSegments.forEach((segment) => {
        const freeStart = timeToMinutes(segment.start);
        const freeEnd = timeToMinutes(segment.end);

        for (let current = freeStart; current + 30 <= freeEnd; current += 30) {
          const startTime = minutesToTime(current);
          const endTime = minutesToTime(current + 30);

          const appointmentDateTime = new Date(`${slot.date}T${startTime}:00`);

          // Do not show appointments that are already in the past.
          if (appointmentDateTime < now) continue;

          result.push({
            key: `${counselor.id}-${slot.id}-${startTime}`,
            counselor,
            slotId: slot.id,
            date: slot.date,
            startTime,
            endTime,
          });
        }
      });
    });
  });

  return result.sort((first, second) =>
    `${first.date}T${first.startTime}`.localeCompare(
      `${second.date}T${second.startTime}`,
    ),
  );
}

function DashboardPage() {
  const navigate = useNavigate();

  const [students, setStudents] = useState<Student[]>([]);
  const [counselors, setCounselors] = useState<Counselor[]>([]);
  const [appointments, setAppointments] = useState<Appointment[]>([]);

  const [availableSlots, setAvailableSlots] = useState<AvailableSlot[]>([]);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  function load() {
    setLoading(true);
    setError(null);

    Promise.all([
      api.get<Student[]>("/students/"),
      api.get<Counselor[]>("/counselors/"),
      api.get<Appointment[]>("/appointments/"),
      api.get<CounselorSlotStatus[]>("/counselors/slot-status/"),
    ])
      .then(
        ([
          studentsResponse,
          counselorsResponse,
          appointmentsResponse,
          slotStatusResponse,
        ]) => {
          setStudents(studentsResponse.data);
          setCounselors(counselorsResponse.data);
          setAppointments(appointmentsResponse.data);

          setAvailableSlots(
            createAvailableSlots(
              slotStatusResponse.data,
              counselorsResponse.data,
            ),
          );
        },
      )
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    load();
  }, []);

  function bookAppointment(slot: AvailableSlot) {
    navigate("/appointments", {
      state: {
        counselorId: slot.counselor.id,
        slotId: slot.slotId,
        startTime: slot.startTime,
        endTime: slot.endTime,
        location: slot.counselor.office_address,
      },
    });
  }

  return (
    <section>
      <h2>Dashboard</h2>
      {error && <p style={{ color: "red" }}>Backend error: {error}</p>}
      <div className="dashboard-grid">
        <div
          className="card"
          onClick={() => navigate("/students")}
          style={{ cursor: "pointer" }}
        >
          <h3>Total Students</h3>
          <p>{loading ? "Loading…" : students.length}</p>
        </div>
        <div
          className="card"
          onClick={() => navigate("/counselors")}
          style={{ cursor: "pointer" }}
        >
          <h3>Total Counselors</h3>
          <p>{loading ? "Loading…" : counselors.length}</p>
        </div>
        <div
          className="card"
          onClick={() => navigate("/appointments")}
          style={{ cursor: "pointer" }}
        >
          <h3>Appointments Planned</h3>
          <p>{loading ? "Loading…" : appointments.length}</p>
        </div>
      </div>

      <div className="page-header">
        <h3>Available slots</h3>
        {!loading && <span>{availableSlots.length} available</span>}
      </div>

      {loading && <p>Loading available appointments…</p>}

      {!loading && !error && (
        <div className="table-wrapper">
          <table>
            <thead>
              <tr>
                <th>Counsellor</th>
                <th>Chair</th>
                <th>Date</th>
                <th>Available slot</th>
                <th>Office</th>
                <th>Email</th>
                <th>Action</th>
              </tr>
            </thead>

            <tbody>
              {availableSlots.length === 0 && (
                <tr>
                  <td colSpan={7}>
                    No complete 30-minute appointments are available.
                  </td>
                </tr>
              )}

              {availableSlots.map((slot) => (
                <tr key={slot.key}>
                  <td>
                    {slot.counselor.title} {slot.counselor.first_name}{" "}
                    {slot.counselor.last_name}
                  </td>

                  <td>{slot.counselor.chair || "—"}</td>

                  <td>{slot.date}</td>

                  <td>
                    {slot.startTime}–{slot.endTime}
                  </td>

                  <td>{slot.counselor.office_address || "—"}</td>

                  <td>
                    <a href={`mailto:${slot.counselor.email}`}>
                      {slot.counselor.email}
                    </a>
                  </td>

                  <td>
                    <button onClick={() => bookAppointment(slot)}>
                      Book appointment
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}

export default DashboardPage;
