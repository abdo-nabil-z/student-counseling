import { Fragment, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import type { Counselor } from "../types/counselor";
import type {
  CounselorSlotStatus,
  SlotStatusSlot,
} from "../types/counselorSlotStatus";
//
// import { openMailClient } from "../types/Mailto";
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

/** 2026-09-12 -> 12/09/2026 */
function formatDate(date: string) {
  return new Date(`${date}T00:00:00`).toLocaleDateString("en-GB", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  });
}

/** 09:00:00 -> 09:00 (also accepts a full ISO datetime) */
function formatTime(time: string) {
  if (!time) return "";
  if (time.includes("T")) {
    return new Date(time).toLocaleTimeString("en-GB", {
      hour: "2-digit",
      minute: "2-digit",
    });
  }
  return time.slice(0, 5);
}

/** ISO datetime -> "HH:MM", read directly off the string so we never shift
 *  the intended slot time by converting through the browser's local timezone. */
function isoToHHMM(iso: string): string {
  return iso.slice(11, 16);
}

function minutesBetweenIso(startIso: string, endIso: string): number {
  const [sh, sm] = isoToHHMM(startIso).split(":").map(Number);
  const [eh, em] = isoToHHMM(endIso).split(":").map(Number);
  return Math.max(0, eh * 60 + em - (sh * 60 + sm));
}

/** The first free segment in a slot, used to prefill the booking form. */
function firstFreeSegment(slot: SlotStatusSlot) {
  return slot.segments.find(
    (seg) => seg.status === "free" && minutesBetweenIso(seg.start, seg.end) > 0,
  );
}

function CounselorsPage() {
  const navigate = useNavigate();

  const [counselors, setCounselors] = useState<Counselor[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [draft, setDraft] = useState<Counselor | null>(null);
  const [saving, setSaving] = useState(false);

  // Which counselor's availability is currently expanded
  const [expandedCounselorId, setExpandedCounselorId] = useState<number | null>(
    null,
  );

  // Availability data loaded per counselor, fetched lazily on first expand
  const [availability, setAvailability] = useState<
    Record<number, CounselorSlotStatus>
  >({});
  // Counselor whose availability is currently loading
  const [loadingAvailability, setLoadingAvailability] = useState<number | null>(
    null,
  );

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
    navigate("/mail", {
      state: {
        targetType: "counselor",
        targetIds: [c.id],
      },
    });
  }

  function openSlots(c: Counselor) {
    navigate(`/slots?counselor=${c.id}`);
  }

  /** Toggle a counselor's availability panel, loading it the first time it's opened. */
  async function handleAvailabilityClick(counselorId: number) {
    if (expandedCounselorId === counselorId) {
      setExpandedCounselorId(null);
      return;
    }

    setExpandedCounselorId(counselorId);

    // Already loaded — don't re-fetch.
    if (availability[counselorId]) return;

    setLoadingAvailability(counselorId);
    try {
      const response = await api.get<CounselorSlotStatus>(
        `/counselors/${counselorId}/slot-status/`,
      );
      setAvailability((previous) => ({
        ...previous,
        [counselorId]: response.data,
      }));
    } catch (err) {
      console.error("Failed to load counselor availability:", err);
      alert("Could not load counselor availability.");
      setExpandedCounselorId(null);
    } finally {
      setLoadingAvailability(null);
    }
  }

  /** Navigate to the Appointments page with this slot's first free window
   *  pre-filled, using router state — AppointmentPage reads its prefill
   *  from location.state, not from URL query params. */
  function handleBookAppointment(c: Counselor, slot: SlotStatusSlot) {
    const free = firstFreeSegment(slot);
    if (!free) return;

    navigate("/appointments", {
      state: {
        counselorId: c.id,
        slotId: slot.id,
        startTime: isoToHHMM(free.start),
        endTime: isoToHHMM(free.end),
        location: c.office_address,
      },
    });
  }

  async function saveDraft() {
    if (!draft) return;
    setSaving(true);
    try {
      if (draft.id === 0) {
        await api.post("/counselors/", draft);
      } else {
        await api.patch(`/counselors/${draft.id}/`, draft);
      }
      setDraft(null);
      load();
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
                <th>Availability</th>
                <th>Actions</th>
              </tr>
            </thead>

            <tbody>
              {counselors.length === 0 && (
                <tr>
                  <td colSpan={7}>No counselors yet.</td>
                </tr>
              )}

              {counselors.map((c) => {
                const counselorAvailability = availability[c.id];
                const isExpanded = expandedCounselorId === c.id;

                return (
                  <Fragment key={c.id}>
                    {/* Counselor row */}
                    <tr>
                      <td>{c.title}</td>
                      <td>
                        {c.first_name} {c.last_name}
                      </td>
                      <td>{c.chair}</td>
                      <td>{c.office_address}</td>
                      <td>{c.email}</td>

                      <td>
                        <button
                          type="button"
                          onClick={() => handleAvailabilityClick(c.id)}
                        >
                          View {isExpanded ? "▲" : "▼"}
                        </button>
                      </td>

                      <td>
                        <button onClick={() => setDraft({ ...c })}>Edit</button>
                        <button onClick={() => openMail(c)}>Mail</button>
                        <button onClick={() => removeCounselor(c)}>
                          Delete
                        </button>
                        <button onClick={() => openSlots(c)}>Slots</button>
                      </td>
                    </tr>

                    {/* Expanded availability panel */}
                    {isExpanded && (
                      <tr>
                        <td colSpan={7}>
                          <div
                            style={{
                              padding: "20px",
                              background: "#f7f7f7",
                              borderRadius: "8px",
                              margin: "5px 0 10px 0",
                            }}
                          >
                            <h3 style={{ marginTop: 0, marginBottom: "16px" }}>
                              Availability — {c.first_name} {c.last_name}
                            </h3>

                            {loadingAvailability === c.id && (
                              <p>Loading availability...</p>
                            )}

                            {counselorAvailability && (
                              <>
                                {counselorAvailability.slots.length > 0 ? (
                                  <div>
                                    {counselorAvailability.slots.map((slot) => {
                                      const bookable =
                                        firstFreeSegment(slot) !== undefined;

                                      return (
                                        <div
                                          key={slot.id}
                                          style={{
                                            background: "white",
                                            border: "1px solid #ddd",
                                            borderRadius: "8px",
                                            padding: "14px",
                                            marginBottom: "10px",
                                          }}
                                        >
                                          <div
                                            style={{
                                              display: "flex",
                                              justifyContent: "space-between",
                                              alignItems: "center",
                                              gap: "16px",
                                            }}
                                          >
                                            <div>
                                              <strong>
                                                {formatDate(slot.date)}
                                              </strong>
                                              <span
                                                style={{ marginLeft: "12px" }}
                                              >
                                                {formatTime(slot.start_time)} –{" "}
                                                {formatTime(slot.end_time)}
                                              </span>
                                            </div>

                                            <button
                                              type="button"
                                              onClick={() =>
                                                handleBookAppointment(c, slot)
                                              }
                                              disabled={!bookable}
                                              title={
                                                bookable
                                                  ? "Book the first free time in this slot"
                                                  : "No free time left in this slot"
                                              }
                                            >
                                              {bookable
                                                ? "Book appointment"
                                                : "Fully booked"}
                                            </button>
                                          </div>

                                          {slot.segments.length > 0 && (
                                            <div
                                              style={{
                                                marginTop: "12px",
                                                paddingTop: "10px",
                                                borderTop: "1px solid #eee",
                                              }}
                                            >
                                              {slot.segments.map(
                                                (segment, index) => (
                                                  <div
                                                    key={index}
                                                    style={{
                                                      display: "flex",
                                                      justifyContent:
                                                        "space-between",
                                                      alignItems: "center",
                                                      padding: "5px 0",
                                                      fontSize: "14px",
                                                    }}
                                                  >
                                                    <span>
                                                      {formatTime(
                                                        segment.start,
                                                      )}{" "}
                                                      –{" "}
                                                      {formatTime(segment.end)}
                                                    </span>
                                                    <span>
                                                      {segment.status === "free"
                                                        ? "Available"
                                                        : `Booked${
                                                            segment.appointment
                                                              ?.student
                                                              ?.full_name
                                                              ? ` – ${segment.appointment.student.full_name}`
                                                              : ""
                                                          }`}
                                                    </span>
                                                  </div>
                                                ),
                                              )}
                                            </div>
                                          )}
                                        </div>
                                      );
                                    })}
                                  </div>
                                ) : (
                                  <p>No availability slots found.</p>
                                )}
                              </>
                            )}
                          </div>
                        </td>
                      </tr>
                    )}
                  </Fragment>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* Add / edit counselor modal */}
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
