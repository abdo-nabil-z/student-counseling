import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Autocomplete, TextField } from "@mui/material";
import { useLocation, useNavigate } from "react-router-dom";
import api from "../api/client";
import Modal from "../components/common/Model";
import type {
  ApiErrorResponse,
  EmailBatch,
  EmailBatchListItem,
  EmailBatchStatus,
  EmailDelivery,
  EmailPurpose,
} from "../types/mail";
import type { Counselor } from "../types/counselor";
import type { Student } from "../types/student";
import type { Template } from "../types/template";

type TargetType = "student" | "counselor";

interface EmailPurposeOption {
  value: EmailPurpose;
  label: string;
  targetType: TargetType;
  requiresAppointment: boolean;
}

const EMAIL_PURPOSES: EmailPurposeOption[] = [
  {
    value: "student_invitation",
    label: "Initial invitation",
    targetType: "student",
    requiresAppointment: false,
  },
  {
    value: "student_reminder",
    label: "Student reminder",
    targetType: "student",
    requiresAppointment: false,
  },
  {
    value: "forced_appointment_assignment",
    label: "Forced appointment assignment",
    targetType: "student",
    requiresAppointment: true,
  },
  {
    value: "appointment_invitation",
    label: "Appointment invitation",
    targetType: "student",
    requiresAppointment: true,
  },
  {
    value: "counselor_preparation_instruction",
    label: "Counsellor preparation instruction",
    targetType: "student",
    requiresAppointment: true,
  },
  {
    value: "appointment_cancellation",
    label: "Appointment cancellation",
    targetType: "student",
    requiresAppointment: true,
  },
  {
    value: "counselor_availability_request",
    label: "Counsellor availability request",
    targetType: "counselor",
    requiresAppointment: false,
  },
  {
    value: "counselor_appointments_summary",
    label: "Accepted appointments summary",
    targetType: "counselor",
    requiresAppointment: false,
  },
];
const MAILS_PER_PAGE = 20;
function getErrorMessage(error: unknown, fallback: string): string {
  const data = (
    error as {
      response?: {
        data?: ApiErrorResponse;
      };
    }
  ).response?.data;

  const apiError = data?.error;

  if (!apiError) return fallback;

  if (apiError.details) {
    return `${apiError.message} ${JSON.stringify(apiError.details)}`;
  }

  return apiError.message || fallback;
}

function getDeliveryTargetName(delivery: {
  student_name: string | null;
  counselor_name: string | null;
}): string {
  return delivery.student_name ?? delivery.counselor_name ?? "Unknown target";
}

function MailPage() {
  const location = useLocation();
  const navigate = useNavigate();

  const initialRouteSelection = useMemo(
    () =>
      (location.state as {
        targetType?: TargetType;
        targetIds?: number[];
      } | null) ?? {},
    [location.state],
  );

  const [students, setStudents] = useState<Student[]>([]);
  const [counselors, setCounselors] = useState<Counselor[]>([]);
  const [templates, setTemplates] = useState<Template[]>([]);

  const [selectedStudents, setSelectedStudents] = useState<Student[]>([]);

  const [selectedCounselors, setSelectedCounselors] = useState<Counselor[]>([]);
  const [purpose, setPurpose] = useState<EmailPurpose | "">("");
  const [batch, setBatch] = useState<EmailBatch | null>(null);
  const [mailHistory, setMailHistory] = useState<EmailBatchListItem[]>([]);
  const [historyPage, setHistoryPage] = useState(0);
  const [historyLoading, setHistoryLoading] = useState(true);
  const [historyError, setHistoryError] = useState<string | null>(null);
  const [batchStatus, setBatchStatus] = useState<EmailBatchStatus | null>(null);
  const batchPreviewRef = useRef<HTMLDivElement | null>(null);

  const [shouldScrollToPreview, setShouldScrollToPreview] = useState(false);
  const [editingDelivery, setEditingDelivery] = useState<EmailDelivery | null>(
    null,
  );
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [savingDelivery, setSavingDelivery] = useState(false);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadMailHistory = useCallback(async () => {
    setHistoryLoading(true);
    setHistoryError(null);

    try {
      const response = await api.get<EmailBatchListItem[]>("/mailing/batches/");

      setMailHistory(response.data);
    } catch (requestError: unknown) {
      setHistoryError(
        getErrorMessage(requestError, "Could not load saved mails."),
      );
    } finally {
      setHistoryLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadMailHistory();
  }, [loadMailHistory]);

  useEffect(() => {
    Promise.all([
      api.get<Student[]>("/students/"),
      api.get<Counselor[]>("/counselors/"),
      api.get<Template[]>("/templates/"),
    ])
      .then(([studentResponse, counselorResponse, templateResponse]) => {
        setStudents(studentResponse.data);
        setCounselors(counselorResponse.data);
        setTemplates(templateResponse.data);

        if (initialRouteSelection.targetType === "student") {
          setSelectedStudents(
            studentResponse.data.filter((student) =>
              initialRouteSelection.targetIds?.includes(student.id),
            ),
          );
        }

        if (initialRouteSelection.targetType === "counselor") {
          setSelectedCounselors(
            counselorResponse.data.filter((counselor) =>
              initialRouteSelection.targetIds?.includes(counselor.id),
            ),
          );
        }
      })
      .catch((requestError: unknown) => {
        setError(
          getErrorMessage(
            requestError,
            "Could not load students, counsellors, or saved templates.",
          ),
        );
      })
      .finally(() => setLoading(false));
  }, [initialRouteSelection]);

  const configuredPurposes = useMemo(() => {
    const configured = new Set(
      templates
        .filter((template) => template.content.trim() !== "")
        .map((template) => template.purpose),
    );

    return EMAIL_PURPOSES.filter((item) => configured.has(item.value));
  }, [templates]);

  const selectedPurpose = EMAIL_PURPOSES.find((item) => item.value === purpose);

  const selectedTargetCount =
    selectedPurpose?.targetType === "counselor"
      ? selectedCounselors.length
      : selectedStudents.length;

  async function generateDrafts() {
    if (!purpose || !selectedPurpose) {
      return;
    }

    const targetIds =
      selectedPurpose.targetType === "counselor"
        ? selectedCounselors.map((counselor) => counselor.id)
        : selectedStudents.map((student) => student.id);

    if (targetIds.length === 0) {
      return;
    }

    setGenerating(true);
    setError(null);
    setBatch(null);
    setBatchStatus(null);

    try {
      const response = await api.post<EmailBatch>("/mailing/batches/", {
        purpose: purpose,
        target_ids: targetIds,
        send_immediately: false,
      });

      setBatch(response.data);
      await loadMailHistory();
    } catch (requestError: unknown) {
      setError(
        getErrorMessage(requestError, "Could not generate the email drafts."),
      );
    } finally {
      setGenerating(false);
    }
  }

  async function saveDelivery() {
    if (!editingDelivery || !batch) return;

    setSavingDelivery(true);
    setError(null);

    try {
      const response = await api.patch<EmailDelivery>(
        `/mailing/deliveries/${editingDelivery.id}/`,
        {
          subject: editingDelivery.subject,
          body: editingDelivery.body,
        },
      );

      setBatch({
        ...batch,
        deliveries: batch.deliveries.map((delivery) =>
          delivery.id === response.data.id ? response.data : delivery,
        ),
      });
      setEditingDelivery(null);
      await loadMailHistory();
    } catch (requestError: unknown) {
      setError(
        getErrorMessage(requestError, "Could not save the email draft."),
      );
    } finally {
      setSavingDelivery(false);
    }
  }

  const refreshStatus = useCallback(async (batchId: number) => {
    try {
      const response = await api.get<EmailBatchStatus>(
        `/mailing/batches/${batchId}/status/`,
      );

      setBatchStatus(response.data);
      setBatch((currentBatch) => {
        if (!currentBatch || currentBatch.id !== batchId) return currentBatch;

        return {
          ...currentBatch,
          deliveries: currentBatch.deliveries.map((delivery) => {
            const deliveryStatus = response.data.deliveries.find(
              (item) => item.id === delivery.id,
            );

            return deliveryStatus
              ? { ...delivery, status: deliveryStatus.status }
              : delivery;
          }),
        };
      });
    } catch (requestError: unknown) {
      setError(
        getErrorMessage(requestError, "Could not refresh the sending status."),
      );
    }
  }, []);

  async function sendBatch() {
    if (!batch) return;

    if (
      !window.confirm(
        `Queue ${batch.deliveries.length} email(s) for sending? Drafts cannot be edited after this.`,
      )
    ) {
      return;
    }

    setSending(true);
    setError(null);

    try {
      const response = await api.post<EmailBatch>(
        `/mailing/batches/${batch.id}/send/`,
      );

      setBatch(response.data);
      await refreshStatus(response.data.id);
      await loadMailHistory();
    } catch (requestError: unknown) {
      setError(
        getErrorMessage(
          requestError,
          "Could not queue the emails for sending.",
        ),
      );
    } finally {
      setSending(false);
    }
  }

  async function resendDelivery(deliveryId: number) {
    setError(null);

    try {
      await api.post(`/mailing/deliveries/${deliveryId}/resend/`);

      if (batch) {
        await refreshStatus(batch.id);
      }

      await loadMailHistory();
    } catch (requestError: unknown) {
      setError(
        getErrorMessage(requestError, "Could not queue this email again."),
      );
    }
  }

  useEffect(() => {
    const batchId = batch?.id;
    const queuedCount = batchStatus?.queued_count ?? 0;

    if (!batchId || queuedCount === 0) return;

    const intervalId = window.setInterval(() => {
      void refreshStatus(batchId);
    }, 3000);

    return () => window.clearInterval(intervalId);
  }, [batch?.id, batchStatus?.queued_count, refreshStatus]);

  const mailHistoryRows = useMemo(
    () =>
      mailHistory.flatMap((savedBatch) =>
        savedBatch.deliveries.map((delivery) => ({
          batchId: savedBatch.id,
          purpose: savedBatch.purpose,
          createdAt: savedBatch.created_at,
          delivery,
        })),
      ),
    [mailHistory],
  );

  const visibleMailHistoryRows = useMemo(() => {
    const start = historyPage * MAILS_PER_PAGE;

    return mailHistoryRows.slice(start, start + MAILS_PER_PAGE);
  }, [historyPage, mailHistoryRows]);

  const historyStart =
    mailHistoryRows.length === 0 ? 0 : historyPage * MAILS_PER_PAGE + 1;

  const historyEnd = Math.min(
    (historyPage + 1) * MAILS_PER_PAGE,
    mailHistoryRows.length,
  );

  const canGoToPreviousHistoryPage = historyPage > 0;

  const canGoToNextHistoryPage = historyEnd < mailHistoryRows.length;

  const hasQueuedMails = mailHistoryRows.some(
    ({ delivery }) => delivery.status === "queued",
  );

  useEffect(() => {
    if (!hasQueuedMails) return;

    const intervalId = window.setInterval(() => {
      void loadMailHistory();
    }, 5000);

    return () => window.clearInterval(intervalId);
  }, [hasQueuedMails, loadMailHistory]);

  async function openSavedBatch(batchId: number) {
    setError(null);

    try {
      const response = await api.get<EmailBatch>(
        `/mailing/batches/${batchId}/`,
      );

      setBatch(response.data);
      setBatchStatus(null);
      setShouldScrollToPreview(true);
    } catch (requestError: unknown) {
      setError(getErrorMessage(requestError, "Could not open this draft."));
    }
  }

  useEffect(() => {
    if (!batch || !shouldScrollToPreview) return;

    batchPreviewRef.current?.scrollIntoView({
      behavior: "smooth",
      block: "start",
    });

    setShouldScrollToPreview(false);
  }, [batch, shouldScrollToPreview]);

  return (
    <section>
      <div className="page-header">
        <h2>Mail</h2>
        <button type="button" onClick={() => navigate("/templates")}>
          Manage templates
        </button>
      </div>

      <p>
        Select a saved email template and one or more recipients. One selected
        recipient creates an individual email; multiple recipients create a bulk
        batch.
      </p>

      {error && <p className="error-text">{error}</p>}
      {loading && <p>Loading students and templates…</p>}

      {!loading && (
        <div className="card" style={{ marginTop: "1.5rem" }}>
          <h3>Create mail</h3>
          <label htmlFor="mail-template">Saved email template</label>
          <select
            id="mail-template"
            value={purpose}
            onChange={(event) => {
              const nextPurpose = event.target.value as EmailPurpose | "";

              const nextPurposeOption = EMAIL_PURPOSES.find(
                (item) => item.value === nextPurpose,
              );

              setPurpose(nextPurpose);
              setBatch(null);
              setBatchStatus(null);

              if (nextPurposeOption?.targetType !== "student") {
                setSelectedStudents([]);
              }

              if (nextPurposeOption?.targetType !== "counselor") {
                setSelectedCounselors([]);
              }
            }}
          >
            <option value="">Select a template</option>
            {configuredPurposes.map((item) => (
              <option key={item.value} value={item.value}>
                {item.label}
              </option>
            ))}
          </select>

          {configuredPurposes.length === 0 && (
            <p>No saved email template has content yet.</p>
          )}

          {selectedPurpose?.requiresAppointment && (
            <p style={{ color: "#6b7280" }}>
              Every selected student must have an appointment. The backend
              obtains the appointment and counsellor automatically.
            </p>
          )}

          {purpose === "counselor_preparation_instruction" && (
            <p style={{ color: "#6b7280" }}>
              These emails are sent to each selected student&apos;s appointment
              counsellor, not to the student.
            </p>
          )}

          {selectedPurpose?.targetType === "student" && (
            <>
              <label>Students</label>

              <label
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "0.5rem",
                  marginBottom: "0.75rem",
                  cursor: "pointer",
                }}
              >
                <input
                  type="checkbox"
                  checked={
                    students.length > 0 &&
                    selectedStudents.length === students.length
                  }
                  onChange={(event) => {
                    setSelectedStudents(event.target.checked ? students : []);

                    setBatch(null);
                    setBatchStatus(null);
                  }}
                />
                Select all students ({students.length})
              </label>

              <Autocomplete
                multiple
                limitTags={3}
                disableCloseOnSelect
                options={students}
                value={selectedStudents}
                onChange={(_, value) => {
                  setSelectedStudents(value);
                  setBatch(null);
                  setBatchStatus(null);
                }}
                getOptionLabel={(student) =>
                  `${student.first_name} ${student.last_name} — ${student.email}`
                }
                isOptionEqualToValue={(option, value) => option.id === value.id}
                renderInput={(parameters) => (
                  <TextField
                    {...parameters}
                    placeholder="Search by student name or email"
                  />
                )}
              />
            </>
          )}

          {selectedPurpose?.targetType === "counselor" && (
            <>
              <label>Counsellors</label>

              <label
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "0.5rem",
                  marginBottom: "0.75rem",
                  cursor: "pointer",
                }}
              >
                <input
                  type="checkbox"
                  checked={
                    counselors.length > 0 &&
                    selectedCounselors.length === counselors.length
                  }
                  onChange={(event) => {
                    setSelectedCounselors(
                      event.target.checked ? counselors : [],
                    );

                    setBatch(null);
                    setBatchStatus(null);
                  }}
                />
                Select all counsellors ({counselors.length})
              </label>

              <Autocomplete
                multiple
                limitTags={3}
                disableCloseOnSelect
                options={counselors}
                value={selectedCounselors}
                onChange={(_, value) => {
                  setSelectedCounselors(value);
                  setBatch(null);
                  setBatchStatus(null);
                }}
                getOptionLabel={(counselor) =>
                  `${counselor.title} ${counselor.first_name} ${counselor.last_name} — ${counselor.email}`
                }
                isOptionEqualToValue={(option, value) => option.id === value.id}
                renderInput={(parameters) => (
                  <TextField
                    {...parameters}
                    placeholder="Search by counsellor name or email"
                  />
                )}
              />
            </>
          )}

          {selectedPurpose && (
            <p style={{ color: "#6b7280" }}>
              {selectedTargetCount} recipient(s) selected
            </p>
          )}

          <button
            type="button"
            onClick={generateDrafts}
            disabled={!purpose || selectedTargetCount === 0 || generating}
          >
            {generating ? "Generating drafts…" : "Generate email drafts"}
          </button>
        </div>
      )}

      {batch && (
        <div
          ref={batchPreviewRef}
          style={{
            marginTop: "1.5rem",
            scrollMarginTop: "1rem",
          }}
        >
          <div className="page-header">
            <h3>Email previews</h3>
            <span>{batch.deliveries.length} email(s)</span>
          </div>

          <div className="table-wrapper">
            <table>
              <thead>
                <tr>
                  <th>Recipient name</th>
                  <th>Email</th>
                  <th>CC</th>
                  <th>Subject</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>

              <tbody>
                {batch.deliveries.map((delivery) => (
                  <tr key={delivery.id}>
                    <td>{getDeliveryTargetName(delivery)}</td>

                    <td>{delivery.recipient_email}</td>

                    <td>{delivery.cc.length ? delivery.cc.join(", ") : "—"}</td>

                    <td>{delivery.subject}</td>

                    <td className="mail-status">{delivery.status}</td>

                    <td>
                      {delivery.status === "draft" && (
                        <button
                          type="button"
                          onClick={() => setEditingDelivery({ ...delivery })}
                        >
                          Review / edit
                        </button>
                      )}

                      {delivery.status === "failed" && (
                        <button
                          type="button"
                          onClick={() => resendDelivery(delivery.id)}
                        >
                          Resend
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {batch.deliveries.every(
            (delivery) => delivery.status === "draft",
          ) && (
            <button type="button" onClick={sendBatch} disabled={sending}>
              {sending ? "Queueing emails…" : "Send reviewed emails"}
            </button>
          )}

          {batch.deliveries.some((delivery) => delivery.status !== "draft") && (
            <button
              type="button"
              onClick={() => batch && refreshStatus(batch.id)}
            >
              Refresh status
            </button>
          )}
        </div>
      )}

      {batchStatus && (
        <div className="card" style={{ marginTop: "1rem" }}>
          <h3>Sending status</h3>
          <p>
            Total: {batchStatus.total_count} | Draft: {batchStatus.draft_count}{" "}
            | Queued: {batchStatus.queued_count} | Sent:{" "}
            {batchStatus.sent_count} | Failed: {batchStatus.failed_count}
          </p>

          {batchStatus.deliveries
            .filter((delivery) => delivery.last_error)
            .map((delivery) => (
              <p key={delivery.id} className="error-text">
                {getDeliveryTargetName(delivery)}: {delivery.last_error}
              </p>
            ))}
        </div>
      )}

      <div className="page-header">
        <h3>Mail history</h3>

        <div className="mail-history-controls">
          <span>
            {historyStart}–{historyEnd} of {mailHistoryRows.length}
          </span>

          <button
            type="button"
            className="mail-history-page-button"
            aria-label="Previous mail history page"
            disabled={!canGoToPreviousHistoryPage}
            onClick={() =>
              setHistoryPage((currentPage) => Math.max(0, currentPage - 1))
            }
          >
            ‹
          </button>

          <button
            type="button"
            className="mail-history-page-button"
            aria-label="Next mail history page"
            disabled={!canGoToNextHistoryPage}
            onClick={() => setHistoryPage((currentPage) => currentPage + 1)}
          >
            ›
          </button>

          <button
            type="button"
            onClick={() => void loadMailHistory()}
            disabled={historyLoading}
          >
            {historyLoading ? "Refreshing…" : "Refresh"}
          </button>
        </div>
      </div>

      {historyError && <p className="error-text">{historyError}</p>}

      <div className="table-wrapper">
        <table className="mail-history-table">
          <thead>
            <tr>
              <th>Created</th>
              <th>Purpose</th>
              <th>Recipient</th>
              <th>Email</th>
              <th>Status</th>
              <th>Action</th>
            </tr>
          </thead>

          <tbody>
            {historyLoading && mailHistoryRows.length === 0 ? (
              <tr>
                <td colSpan={6}>Loading mail history…</td>
              </tr>
            ) : mailHistoryRows.length === 0 ? (
              <tr>
                <td colSpan={6}>No mail history found.</td>
              </tr>
            ) : (
              visibleMailHistoryRows.map(
                ({ batchId, purpose: savedPurpose, createdAt, delivery }) => (
                  <tr key={delivery.id}>
                    <td>{new Date(createdAt).toLocaleString()}</td>

                    <td>
                      {EMAIL_PURPOSES.find(
                        (item) => item.value === savedPurpose,
                      )?.label ?? savedPurpose}
                    </td>

                    <td>{delivery.recipient_name}</td>

                    <td>{delivery.recipient_email}</td>

                    <td>{delivery.status}</td>

                    <td>
                      {delivery.status === "draft" ? (
                        <button
                          type="button"
                          onClick={() => void openSavedBatch(batchId)}
                        >
                          Open draft
                        </button>
                      ) : (
                        "—"
                      )}
                    </td>
                  </tr>
                ),
              )
            )}
          </tbody>
        </table>
      </div>

      {editingDelivery && (
        <Modal
          title={`Review email — ${getDeliveryTargetName(editingDelivery)}`}
          onClose={() => setEditingDelivery(null)}
          width="min(900px, 95vw)"
          maxHeight="92vh"
        >
          <p>
            <strong>To:</strong> {editingDelivery.recipient_email}
          </p>
          <p>
            <strong>CC:</strong>{" "}
            {editingDelivery.cc.length ? editingDelivery.cc.join(", ") : "None"}
          </p>

          <label>Subject</label>
          <input
            value={editingDelivery.subject}
            onChange={(event) =>
              setEditingDelivery({
                ...editingDelivery,
                subject: event.target.value,
              })
            }
          />

          <label>Body</label>
          <textarea
            rows={18}
            value={editingDelivery.body}
            onChange={(event) =>
              setEditingDelivery({
                ...editingDelivery,
                body: event.target.value,
              })
            }
          />

          <button
            type="button"
            onClick={saveDelivery}
            disabled={
              savingDelivery ||
              !editingDelivery.subject.trim() ||
              !editingDelivery.body.trim()
            }
          >
            {savingDelivery ? "Saving…" : "Save draft"}
          </button>
          <button type="button" onClick={() => setEditingDelivery(null)}>
            Cancel
          </button>
        </Modal>
      )}
    </section>
  );
}

export default MailPage;
