import { useEffect, useRef, useState } from "react";
import { Autocomplete, TextField } from "@mui/material";
import api from "../api/client";
import Modal from "../components/common/Model";

import type { Appointment } from "../types/appointment";
import type { Counselor } from "../types/counselor";
import type { Student } from "../types/student";
import type {
  ContextVariable,
  Purpose,
  RenderError,
  Template,
} from "../types/template";

// ---- Static metadata the backend doesn't expose directly ----

type InputKind = "counselor" | "student" | "student_counselor";

interface PurposeMeta {
  label: string;
  category: "Email" | "Document";
  inputKind: InputKind;
}

const PURPOSE_META: Record<Purpose, PurposeMeta> = {
  testmail: { label: "Test Mail", category: "Email", inputKind: "counselor" },
  student_invitation: {
    label: "Initial Invitation (Student)",
    category: "Email",
    inputKind: "student",
  },
  student_reminder: {
    label: "Reminder (Student)",
    category: "Email",
    inputKind: "student",
  },
  forced_appointment_assignment: {
    label: "Forced Appointment Assignment",
    category: "Email",
    inputKind: "student_counselor",
  },
  appointment_invitation: {
    label: "Appointment Invitation",
    category: "Email",
    inputKind: "student_counselor",
  },
  counselor_preparation_instruction: {
    label: "Preparation Instruction (Counselor)",
    category: "Email",
    inputKind: "student_counselor",
  },
  appointment_cancellation: {
    label: "Appointment Cancellation",
    category: "Email",
    inputKind: "student_counselor",
  },
  counselor_availability_request: {
    label: "Availability Request (Counsellor)",
    category: "Email",
    inputKind: "counselor",
  },
  counselor_appointments_summary: {
    label: "Accepted Appointments Summary (Counsellor)",
    category: "Email",
    inputKind: "counselor",
  },
  study_plan: {
    label: "Study Plan",
    category: "Document",
    inputKind: "student",
  },
  appointment_minutes: {
    label: "Appointment Minutes",
    category: "Document",
    inputKind: "student_counselor",
  },
};

const PURPOSE_ORDER = Object.keys(PURPOSE_META) as Purpose[];

function formatDate(iso: string) {
  if (!iso) return "—";
  return new Date(iso).toLocaleString();
}

async function getApiErrorMessage(
  error: unknown,
  fallback: string,
): Promise<string> {
  let data = (
    error as {
      response?: {
        data?: unknown;
      };
    }
  ).response?.data;

  // PDF requests return errors as Blob objects.
  if (data instanceof Blob) {
    try {
      data = JSON.parse(await data.text()) as RenderError;
    } catch {
      return fallback;
    }
  }

  const apiError = (data as RenderError | undefined)?.error;

  if (!apiError) {
    return fallback;
  }

  const details = apiError.details;

  if (details?.message) {
    return (
      `${apiError.message} ${details.message}` +
      (details.line ? ` (line ${details.line})` : "") +
      (details.variable ? ` [variable: ${details.variable}]` : "")
    );
  }

  return apiError.message || fallback;
}

// ---------------------------------------------------------------------------

function TemplatesPage() {
  const [templates, setTemplates] = useState<Template[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [editingPurpose, setEditingPurpose] = useState<Purpose | null>(null);

  const loadTemplates = () => {
    setLoading(true);
    setLoadError(null);
    api
      .get<Template[]>("/templates/")
      .then((res) => setTemplates(res.data))
      .catch(() => setLoadError("Could not load templates."))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    loadTemplates();
  }, []);

  const templateFor = (purpose: Purpose) =>
    templates.find((t) => t.purpose === purpose);

  return (
    <section>
      <h2>Templates</h2>
      <p>
        Each purpose below has exactly one template. Click a row to edit its
        content, see the variables available to it, and render a live preview.
      </p>

      {loading && <p>Loading templates…</p>}
      {loadError && <p style={{ color: "crimson" }}>{loadError}</p>}

      {!loading && !loadError && (
        <table
          className="card"
          style={{ width: "100%", borderCollapse: "collapse" }}
        >
          <thead>
            <tr style={{ textAlign: "left" }}>
              <th>Purpose</th>
              <th>Category</th>
              <th>Last Updated</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {PURPOSE_ORDER.map((purpose) => {
              const meta = PURPOSE_META[purpose];
              const tpl = templateFor(purpose);
              return (
                <tr key={purpose} style={{ borderTop: "1px solid #ddd" }}>
                  <td>{meta.label}</td>
                  <td>{meta.category}</td>
                  <td>{tpl ? formatDate(tpl.updated_at) : "—"}</td>
                  <td>
                    <button onClick={() => setEditingPurpose(purpose)}>
                      Edit
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      )}

      {editingPurpose && (
        <TemplateEditorModal
          purpose={editingPurpose}
          initialContent={templateFor(editingPurpose)?.content ?? ""}
          onClose={() => setEditingPurpose(null)}
          onSaved={loadTemplates}
        />
      )}
    </section>
  );
}

// ---------------------------------------------------------------------------

interface TemplateEditorModalProps {
  purpose: Purpose;
  initialContent: string;
  onClose: () => void;
  onSaved: () => void;
}

function TemplateEditorModal({
  purpose,
  initialContent,
  onClose,
  onSaved,
}: TemplateEditorModalProps) {
  const meta = PURPOSE_META[purpose];
  const [content, setContent] = useState(initialContent);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [saveSuccess, setSaveSuccess] = useState(false);

  const [variables, setVariables] = useState<ContextVariable[]>([]);
  const [variablesLoading, setVariablesLoading] = useState(true);
  const [showVariables, setShowVariables] = useState(false);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setVariablesLoading(true);
    api
      .get<ContextVariable[]>(`/templates/${purpose}/context-schema/`)
      .then((res) => setVariables(res.data))
      .catch(() => setVariables([]))
      .finally(() => setVariablesLoading(false));
  }, [purpose]);

  async function handleSave() {
    setSaving(true);
    setSaveError(null);
    setSaveSuccess(false);

    try {
      await api.put(`/templates/${purpose}/update/`, content, {
        headers: {
          "Content-Type": "text/plain; charset=utf-8",
        },
      });

      setSaveSuccess(true);
      onSaved();
    } catch (error: unknown) {
      setSaveError(
        await getApiErrorMessage(error, "Could not save the template."),
      );
    } finally {
      setSaving(false);
    }
  }

  function insertDirective(directive: string) {
    const textarea = textareaRef.current;

    const start = textarea?.selectionStart ?? content.length;

    const end = textarea?.selectionEnd ?? content.length;

    const updatedContent =
      content.slice(0, start) + directive + content.slice(end);

    setContent(updatedContent);
    setSaveSuccess(false);

    const newCursorPosition = start + directive.length;

    requestAnimationFrame(() => {
      textarea?.focus();
      textarea?.setSelectionRange(newCursorPosition, newCursorPosition);
    });
  }

  return (
    <Modal
      title={`Edit Template — ${meta.label}`}
      onClose={onClose}
      width="min(1100px, 95vw)"
      maxHeight="92vh"
    >
      <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
        <label>Content</label>
        <textarea
          ref={textareaRef}
          rows={14}
          value={content}
          onChange={(event) => {
            setContent(event.target.value);
            setSaveSuccess(false);
          }}
          style={{
            fontFamily: "monospace",
            width: "100%",
          }}
        />

        <div>
          <button type="button" onClick={() => setShowVariables((v) => !v)}>
            {showVariables ? "Hide" : "Show"} available variables
          </button>
        </div>

        {showVariables && (
          <div
            style={{
              border: "1px solid #ddd",
              borderRadius: 6,
              padding: "0.5rem",
              maxHeight: 230,
              overflowY: "auto",
            }}
          >
            {variablesLoading && (
              <p
                style={{
                  margin: 0,
                  fontSize: "0.85rem",
                }}
              >
                Loading variables…
              </p>
            )}

            {!variablesLoading && variables.length === 0 && (
              <p
                style={{
                  margin: 0,
                  fontSize: "0.85rem",
                }}
              >
                No variables available for this template.
              </p>
            )}

            {!variablesLoading && variables.length > 0 && (
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
                  gap: "0.35rem",
                }}
              >
                {variables.map((variable) => (
                  <div
                    key={variable.path}
                    style={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      gap: "0.5rem",
                      minWidth: 0,
                      padding: "0.3rem 0.4rem",
                      background: "#f9fafb",
                      border: "1px solid #e5e7eb",
                      borderRadius: 5,
                    }}
                  >
                    <code
                      style={{
                        minWidth: 0,
                        overflow: "hidden",
                        textOverflow: "ellipsis",
                        whiteSpace: "nowrap",
                        fontSize: "0.78rem",
                      }}
                    >
                      {variable.path}
                    </code>

                    <button
                      type="button"
                      onClick={() => insertDirective(variable.directive)}
                      style={{
                        flexShrink: 0,
                        margin: 0,
                        padding: "4px 7px",
                        fontSize: "0.75rem",
                        borderRadius: 4,
                      }}
                    >
                      {variable.type === "array" ? "Insert loop" : "Insert"}
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {saveError && <p style={{ color: "crimson" }}>{saveError}</p>}
        {saveSuccess && <p style={{ color: "green" }}>Saved.</p>}

        <div style={{ display: "flex", gap: "0.5rem" }}>
          <button onClick={handleSave} disabled={saving}>
            {saving ? "Saving…" : "Save"}
          </button>
          <button type="button" onClick={onClose}>
            Close
          </button>
        </div>

        <hr style={{ width: "100%" }} />

        <TemplatePreview purpose={purpose} />
      </div>
    </Modal>
  );
}

// ---------------------------------------------------------------------------

function TemplatePreview({ purpose }: { purpose: Purpose }) {
  const meta = PURPOSE_META[purpose];
  const isDocument = meta.category === "Document";
  const [students, setStudents] = useState<Student[]>([]);
  const [counselors, setCounselors] = useState<Counselor[]>([]);
  const [appointments, setAppointments] = useState<Appointment[]>([]);

  const [selectedStudent, setSelectedStudent] = useState<Student | null>(null);

  const [selectedCounselor, setSelectedCounselor] = useState<Counselor | null>(
    null,
  );

  const [selectedAppointment, setSelectedAppointment] =
    useState<Appointment | null>(null);

  const [optionsLoading, setOptionsLoading] = useState(true);
  const [optionsError, setOptionsError] = useState<string | null>(null);
  const [rendering, setRendering] = useState(false);
  const [rendered, setRendered] = useState<string | null>(null);
  const [pdfPreviewUrl, setPdfPreviewUrl] = useState<string | null>(null);
  const [renderError, setRenderError] = useState<string | null>(null);

  useEffect(() => {
    return () => {
      if (pdfPreviewUrl) {
        URL.revokeObjectURL(pdfPreviewUrl);
      }
    };
  }, [pdfPreviewUrl]);

  useEffect(() => {
    Promise.all([
      api.get<Student[]>("/students/"),
      api.get<Counselor[]>("/counselors/"),
      api.get<Appointment[]>("/appointments/"),
    ])
      .then(([studentsResponse, counselorsResponse, appointmentsResponse]) => {
        setStudents(studentsResponse.data);
        setCounselors(counselorsResponse.data);
        setAppointments(appointmentsResponse.data);
      })
      .catch(() => {
        setOptionsError(
          "Could not load students, counsellors, or appointments.",
        );
      })
      .finally(() => setOptionsLoading(false));
  }, []);

  function studentIdOf(value: number | Student): number {
    return typeof value === "number" ? value : value.id;
  }

  function counselorIdOf(value: number | Counselor): number {
    return typeof value === "number" ? value : value.id;
  }

  function studentName(value: number | Student): string {
    if (typeof value === "object") {
      return `${value.first_name} ${value.last_name}`;
    }

    const student = students.find((item) => item.id === value);

    return student
      ? `${student.first_name} ${student.last_name}`
      : `Student #${value}`;
  }

  function counselorName(value: number | Counselor): string {
    if (typeof value === "object") {
      return `${value.title} ${value.first_name} ${value.last_name}`;
    }

    const counselor = counselors.find((item) => item.id === value);

    return counselor
      ? `${counselor.title} ${counselor.first_name} ${counselor.last_name}`
      : `Counsellor #${value}`;
  }

  function buildPayload(): Record<string, number> | null {
    if (meta.inputKind === "counselor") {
      if (!selectedCounselor) return null;

      return {
        counselor_id: selectedCounselor.id,
      };
    }

    if (meta.inputKind === "student") {
      if (!selectedStudent) return null;

      return {
        student_id: selectedStudent.id,
      };
    }

    if (!selectedAppointment) return null;

    return {
      appointment_id: selectedAppointment.id,
      student_id: studentIdOf(selectedAppointment.student),
      counselor_id: counselorIdOf(selectedAppointment.counselor),
    };
  }

  const canRender =
    (meta.inputKind === "counselor" && selectedCounselor !== null) ||
    (meta.inputKind === "student" && selectedStudent !== null) ||
    (meta.inputKind === "student_counselor" && selectedAppointment !== null);

  async function handleRender() {
    const payload = buildPayload();

    if (!payload) return;

    setRendering(true);
    setRendered(null);
    setPdfPreviewUrl(null);
    setRenderError(null);

    try {
      if (isDocument) {
        const response = await api.post<Blob>(
          `/templates/${purpose}/render/`,
          payload,
          {
            responseType: "blob",
          },
        );

        const previewUrl = URL.createObjectURL(response.data);

        setPdfPreviewUrl(previewUrl);
      } else {
        const response = await api.post<{
          rendered: string;
        }>(`/templates/${purpose}/render/`, payload);

        setRendered(response.data.rendered);
      }
    } catch (error: unknown) {
      setRenderError(
        await getApiErrorMessage(
          error,
          "Could not generate the template preview.",
        ),
      );
    } finally {
      setRendering(false);
    }
  }

  return (
    <div>
      <h4>Render preview</h4>

      <p style={{ color: "#6b7280" }}>
        Search for a record by its name or ID and select it to generate the
        preview.
      </p>

      {optionsLoading && <p>Loading available records…</p>}

      {optionsError && <p style={{ color: "crimson" }}>{optionsError}</p>}

      {!optionsLoading && !optionsError && meta.inputKind === "counselor" && (
        <Autocomplete
          options={counselors}
          value={selectedCounselor}
          onChange={(_, value) => setSelectedCounselor(value)}
          getOptionLabel={(counselor) =>
            `#${counselor.id} — ${counselor.title} ${counselor.first_name} ${counselor.last_name}`
          }
          isOptionEqualToValue={(option, value) => option.id === value.id}
          renderInput={(parameters) => (
            <TextField
              {...parameters}
              label="Counsellor"
              placeholder="Search by name or ID"
            />
          )}
        />
      )}

      {!optionsLoading && !optionsError && meta.inputKind === "student" && (
        <Autocomplete
          options={students}
          value={selectedStudent}
          onChange={(_, value) => setSelectedStudent(value)}
          getOptionLabel={(student) =>
            `#${student.id} — ${student.first_name} ${student.last_name} — ${student.matriculation_number}`
          }
          isOptionEqualToValue={(option, value) => option.id === value.id}
          renderInput={(parameters) => (
            <TextField
              {...parameters}
              label="Student"
              placeholder="Search by name, ID, or matriculation number"
            />
          )}
        />
      )}

      {!optionsLoading &&
        !optionsError &&
        meta.inputKind === "student_counselor" && (
          <Autocomplete
            options={appointments}
            value={selectedAppointment}
            onChange={(_, value) => setSelectedAppointment(value)}
            getOptionLabel={(appointment) =>
              `#${appointment.id} — ${studentName(
                appointment.student,
              )} — ${counselorName(
                appointment.counselor,
              )} — ${appointment.start_time.slice(0, 16)}`
            }
            isOptionEqualToValue={(option, value) => option.id === value.id}
            renderInput={(parameters) => (
              <TextField
                {...parameters}
                label="Appointment"
                placeholder="Search by appointment ID, student, or counsellor"
              />
            )}
          />
        )}

      <button
        type="button"
        onClick={handleRender}
        disabled={!canRender || rendering}
        style={{ marginTop: "1rem" }}
      >
        {rendering ? "Rendering…" : "Render preview"}
      </button>

      {renderError && (
        <p
          style={{
            color: "crimson",
            whiteSpace: "pre-wrap",
          }}
        >
          {renderError}
        </p>
      )}

      {!isDocument && rendered !== null && (
        <div style={{ marginTop: "1rem" }}>
          <label>Email preview</label>

          <textarea
            rows={14}
            value={rendered}
            readOnly
            style={{
              width: "100%",
              marginTop: "0.5rem",
            }}
          />
        </div>
      )}

      {isDocument && pdfPreviewUrl && (
        <div style={{ marginTop: "1rem" }}>
          <label>PDF preview</label>

          <iframe
            title={`${meta.label} preview`}
            src={pdfPreviewUrl}
            style={{
              display: "block",
              width: "100%",
              height: "600px",
              marginTop: "0.5rem",
              border: "1px solid #ddd",
              borderRadius: 6,
            }}
          />

          <a
            href={pdfPreviewUrl}
            download={`${purpose}.pdf`}
            style={{
              display: "inline-block",
              marginTop: "0.75rem",
            }}
          >
            Download PDF
          </a>
        </div>
      )}
    </div>
  );
}

export default TemplatesPage;
