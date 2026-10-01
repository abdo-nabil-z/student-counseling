import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Autocomplete, TextField } from "@mui/material";
import { useLocation, useNavigate } from "react-router-dom";
import api from "../api/client";
import Modal from "../components/common/Model";
import type {
  ApiErrorResponse,
  EmailAttachment,
  EmailBatch,
  EmailBatchListItem,
  EmailBatchStatus,
  EmailDelivery,
  EmailPurpose,
} from "../types/mail";
import type { Appointment } from "../types/appointment";
import type { Counselor } from "../types/counselor";
import type { Student } from "../types/student";
import type { Template } from "../types/template";

type TargetType = "student" | "counselor" | "external";
type ExistingDocumentType =
  | "initial_study_plan"
  | "final_study_plan"
  | "appointment_minutes";

type GeneratedPdfPurpose = "study_plan" | "appointment_minutes";

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
  {
    value: "general_mail",
    label: "General email",
    targetType: "external",
    requiresAppointment: false,
  },
];

const EXISTING_DOCUMENT_OPTIONS: Array<{
  value: ExistingDocumentType;
  label: string;
}> = [
  {
    value: "initial_study_plan",
    label: "Initial study plan",
  },
  {
    value: "final_study_plan",
    label: "Final study plan",
  },
  {
    value: "appointment_minutes",
    label: "Appointment minutes",
  },
];

const GENERATED_PDF_OPTIONS: Array<{
  value: GeneratedPdfPurpose;
  label: string;
}> = [
  {
    value: "study_plan",
    label: "Study Plan PDF",
  },
  {
    value: "appointment_minutes",
    label: "Appointment Minutes PDF",
  },
];

function attachmentDownloadUrl(attachment: EmailAttachment): string | null {
  if (attachment.download_url) {
    return attachment.download_url;
  }

  if (attachment.document_id) {
    return `/api/documents/${attachment.document_id}/download/`;
  }

  return null;
}

const MAILS_PER_PAGE = 20;
function extractErrorMessages(value: unknown): string[] {
  if (value === null || value === undefined) {
    return [];
  }

  if (
    typeof value === "string" ||
    typeof value === "number" ||
    typeof value === "boolean"
  ) {
    return [String(value)];
  }

  if (Array.isArray(value)) {
    return value.flatMap(extractErrorMessages);
  }

  if (typeof value === "object") {
    return Object.values(value).flatMap(extractErrorMessages);
  }

  return [];
}

function getErrorMessage(error: unknown, fallback: string): string {
  const data = (
    error as {
      response?: {
        data?: ApiErrorResponse;
      };
    }
  ).response?.data;

  const apiError = data?.error;

  if (!apiError) {
    return fallback;
  }

  const details = extractErrorMessages(apiError.details).join(" ");

  if (details) {
    return `${apiError.message || fallback} ${details}`;
  }

  return apiError.message || fallback;
}

function getDeliveryTargetName(delivery: {
  student_name: string | null;
  counselor_name: string | null;
  recipient_email: string;
}): string {
  return (
    delivery.student_name ?? delivery.counselor_name ?? delivery.recipient_email
  );
}

function parseExternalRecipients(value: string): string[] {
  return Array.from(
    new Set(
      value
        .split(/[\n,;]+/)
        .map((email) => email.trim().toLowerCase())
        .filter(Boolean),
    ),
  );
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
  const [externalRecipientText, setExternalRecipientText] = useState("");
  const [purpose, setPurpose] = useState<EmailPurpose | "">("");
  const [uploadedFiles, setUploadedFiles] = useState<File[]>([]);

  const [existingDocumentTypes, setExistingDocumentTypes] = useState<
    ExistingDocumentType[]
  >([]);

  const [generatedPdfPurposes, setGeneratedPdfPurposes] = useState<
    GeneratedPdfPurpose[]
  >([]);
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
  const [reviewFiles, setReviewFiles] = useState<File[]>([]);

  const [uploadingReviewFiles, setUploadingReviewFiles] = useState(false);
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
  const externalRecipients = useMemo(
    () => parseExternalRecipients(externalRecipientText),
    [externalRecipientText],
  );

  const selectedTargetCount =
    selectedPurpose?.targetType === "counselor"
      ? selectedCounselors.length
      : selectedPurpose?.targetType === "external"
        ? externalRecipients.length
        : selectedStudents.length;

  async function generateDrafts() {
    if (!purpose || !selectedPurpose) {
      return;
    }

    const targetIds =
      selectedPurpose.targetType === "counselor"
        ? selectedCounselors.map((counselor) => counselor.id)
        : selectedPurpose.targetType === "student"
          ? selectedStudents.map((student) => student.id)
          : [];

    if (selectedTargetCount === 0) {
      return;
    }

    setGenerating(true);
    setError(null);
    setBatch(null);
    setBatchStatus(null);

    try {
      const formData = new FormData();

      formData.append("purpose", purpose);
      formData.append("send_immediately", "false");

      targetIds.forEach((targetId) => {
        formData.append("target_ids", String(targetId));
      });

      externalRecipients.forEach((email) => {
        formData.append("external_recipients", email);
      });

      existingDocumentTypes.forEach((documentType) => {
        formData.append("existing_document_types", documentType);
      });

      generatedPdfPurposes.forEach((pdfPurpose) => {
        formData.append("generated_pdf_purposes", pdfPurpose);
      });

      uploadedFiles.forEach((file) => {
        formData.append("uploaded_files", file);
      });

      const response = await api.post<EmailBatch>(
        "/mailing/batches/",
        formData,
      );

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

  async function addReviewAttachments() {
    if (!editingDelivery || reviewFiles.length === 0) {
      return;
    }

    setUploadingReviewFiles(true);
    setError(null);

    try {
      for (const file of reviewFiles) {
        const formData = new FormData();

        formData.append("file", file);

        await api.post(
          `/mailing/deliveries/${editingDelivery.id}/attachments/upload/`,
          formData,
        );
      }

      const response = await api.get<EmailDelivery>(
        `/mailing/deliveries/${editingDelivery.id}/`,
      );

      setEditingDelivery(response.data);

      setBatch((currentBatch) => {
        if (!currentBatch) {
          return currentBatch;
        }

        return {
          ...currentBatch,
          deliveries: currentBatch.deliveries.map((delivery) =>
            delivery.id === response.data.id ? response.data : delivery,
          ),
        };
      });

      setReviewFiles([]);
      await loadMailHistory();
    } catch (requestError: unknown) {
      setError(getErrorMessage(requestError, "Could not add the attachments."));
    } finally {
      setUploadingReviewFiles(false);
    }
  }

  async function removeAttachment(deliveryId: number, attachmentId: number) {
    setError(null);

    try {
      await api.delete(
        `/mailing/deliveries/${deliveryId}/attachments/${attachmentId}/`,
      );

      setBatch((currentBatch) => {
        if (!currentBatch) {
          return currentBatch;
        }

        return {
          ...currentBatch,
          deliveries: currentBatch.deliveries.map((delivery) =>
            delivery.id === deliveryId
              ? {
                  ...delivery,
                  attachments: delivery.attachments.filter(
                    (attachment) => attachment.id !== attachmentId,
                  ),
                }
              : delivery,
          ),
        };
      });

      setEditingDelivery((currentDelivery) =>
        currentDelivery?.id === deliveryId
          ? {
              ...currentDelivery,
              attachments: currentDelivery.attachments.filter(
                (attachment) => attachment.id !== attachmentId,
              ),
            }
          : currentDelivery,
      );

      await loadMailHistory();
    } catch (requestError: unknown) {
      setError(
        getErrorMessage(requestError, "Could not remove the attachment."),
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
                setExistingDocumentTypes([]);
                setGeneratedPdfPurposes([]);
              }

              if (nextPurposeOption?.targetType !== "counselor") {
                setSelectedCounselors([]);
              }

              if (nextPurposeOption?.targetType !== "external") {
                setExternalRecipientText("");
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

          {selectedPurpose?.targetType === "external" && (
            <>
              <label htmlFor="external-recipients">Recipient emails</label>

              <textarea
                id="external-recipients"
                rows={5}
                value={externalRecipientText}
                onChange={(event) => {
                  setExternalRecipientText(event.target.value);
                  setBatch(null);
                  setBatchStatus(null);
                }}
                placeholder={"person@example.com\nanother.person@example.com"}
              />

              <p className="attachment-help">
                Enter one address per line, or separate addresses with commas.
              </p>
            </>
          )}

          {selectedPurpose && (
            <p style={{ color: "#6b7280" }}>
              {selectedTargetCount} recipient(s) selected
            </p>
          )}

          <fieldset className="mail-attachments">
            <legend>Attachments (optional)</legend>

            <label htmlFor="mail-uploaded-files">Upload files</label>

            <input
              id="mail-uploaded-files"
              type="file"
              multiple
              onChange={(event) =>
                setUploadedFiles(Array.from(event.target.files ?? []))
              }
            />

            {uploadedFiles.length > 0 && (
              <p className="attachment-help">
                {uploadedFiles.map((file) => file.name).join(", ")}
              </p>
            )}

            {selectedPurpose?.targetType === "student" && (
              <>
                <p className="attachment-group-title">
                  Attach saved documents{" "}
                  <span className="attachment-heading-help">
                    (each student receives their own saved document)
                  </span>
                </p>
                <div className="attachment-options">
                  {EXISTING_DOCUMENT_OPTIONS.map((option) => (
                    <label key={option.value}>
                      <input
                        type="checkbox"
                        checked={existingDocumentTypes.includes(option.value)}
                        onChange={(event) =>
                          setExistingDocumentTypes((current) =>
                            event.target.checked
                              ? [...current, option.value]
                              : current.filter((item) => item !== option.value),
                          )
                        }
                      />

                      {option.label}
                    </label>
                  ))}
                </div>

                <p className="attachment-group-title">
                  Generate PDFs from templates
                </p>

                <div className="attachment-options">
                  {GENERATED_PDF_OPTIONS.map((option) => (
                    <label key={option.value} className="saved-document-option">
                      <input
                        type="checkbox"
                        checked={generatedPdfPurposes.includes(option.value)}
                        onChange={(event) =>
                          setGeneratedPdfPurposes((current) =>
                            event.target.checked
                              ? [...current, option.value]
                              : current.filter((item) => item !== option.value),
                          )
                        }
                      />

                      {option.label}
                    </label>
                  ))}
                </div>

                <p className="attachment-help">
                  Every selected recipient must have the required saved document
                  or appointment information.
                </p>
              </>
            )}
          </fieldset>

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
                  <th>Attachments</th>
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
                      {delivery.attachments.length > 0
                        ? delivery.attachments
                            .map((attachment) => attachment.name)
                            .join(", ")
                        : "—"}
                    </td>

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
                        <>
                          <button
                            type="button"
                            onClick={() => setEditingDelivery({ ...delivery })}
                          >
                            Review / edit
                          </button>

                          <button
                            type="button"
                            onClick={() => resendDelivery(delivery.id)}
                          >
                            Resend
                          </button>
                        </>
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
              <th>Attachments</th>
              <th>Action</th>
            </tr>
          </thead>

          <tbody>
            {historyLoading && mailHistoryRows.length === 0 ? (
              <tr>
                <td colSpan={7}>Loading mail history…</td>
              </tr>
            ) : mailHistoryRows.length === 0 ? (
              <tr>
                <td colSpan={7}>No mail history found.</td>
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
                      {delivery.attachments.length > 0
                        ? delivery.attachments
                            .map((attachment) => attachment.name)
                            .join(", ")
                        : "—"}
                    </td>

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
          onClose={() => {
            setEditingDelivery(null);
            setReviewFiles([]);
          }}
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

          <h4>Attachments</h4>

          <input
            type="file"
            multiple
            onChange={(event) =>
              setReviewFiles(Array.from(event.target.files ?? []))
            }
          />

          {reviewFiles.length > 0 && (
            <>
              <p className="attachment-help">
                {reviewFiles.map((file) => file.name).join(", ")}
              </p>

              <button
                type="button"
                onClick={addReviewAttachments}
                disabled={uploadingReviewFiles}
              >
                {uploadingReviewFiles
                  ? "Adding attachments…"
                  : "Add attachments"}
              </button>
            </>
          )}
          {editingDelivery.attachments.length === 0 ? (
            <p>No attachments.</p>
          ) : (
            <ul className="attachment-list">
              {editingDelivery.attachments.map((attachment) => {
                const downloadUrl = attachmentDownloadUrl(attachment);

                return (
                  <li key={attachment.id}>
                    {downloadUrl ? (
                      <a href={downloadUrl} target="_blank" rel="noreferrer">
                        {attachment.name}
                      </a>
                    ) : (
                      <span>{attachment.name}</span>
                    )}

                    <button
                      type="button"
                      className="attachment-remove-button"
                      onClick={() =>
                        void removeAttachment(editingDelivery.id, attachment.id)
                      }
                    >
                      Remove
                    </button>
                  </li>
                );
              })}
            </ul>
          )}

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
          <button
            type="button"
            onClick={() => {
              setEditingDelivery(null);
              setReviewFiles([]);
            }}
          >
            Cancel
          </button>
        </Modal>
      )}
    </section>
  );
}

export default MailPage;
