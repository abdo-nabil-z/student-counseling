import { useEffect, useState } from "react";
import api from "../api/client";
import Modal from "../components/common/Model";
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

  const handleSave = () => {
    setSaving(true);
    setSaveError(null);
    setSaveSuccess(false);
    api
      .put(`/templates/${purpose}/update/`, { content })
      .then(() => {
        setSaveSuccess(true);
        onSaved();
      })
      .catch((err) => {
        const message =
          err?.response?.data?.error ??
          err?.response?.data?.content?.[0] ??
          "Could not save template.";
        setSaveError(String(message));
      })
      .finally(() => setSaving(false));
  };

  const copyDirective = (directive: string) => {
    navigator.clipboard?.writeText(directive).catch(() => {
      /* clipboard not available, ignore */
    });
  };

  return (
    <Modal title={`Edit Template — ${meta.label}`} onClose={onClose}>
      <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
        <label>Content</label>
        <textarea
          rows={14}
          value={content}
          onChange={(e) => setContent(e.target.value)}
          style={{ fontFamily: "monospace", width: "100%" }}
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
              padding: "0.75rem",
              maxHeight: 220,
              overflow: "auto",
            }}
          >
            {variablesLoading && <p>Loading variables…</p>}
            {!variablesLoading && variables.length === 0 && (
              <p>No variables available for this purpose.</p>
            )}
            {!variablesLoading &&
              variables.map((v) => (
                <div
                  key={v.path}
                  style={{
                    marginBottom: "0.5rem",
                    paddingBottom: "0.5rem",
                    borderBottom: "1px dashed #eee",
                  }}
                >
                  <div>
                    <code>{v.path}</code>{" "}
                    <span style={{ color: "#888" }}>({v.type})</span>
                  </div>
                  <div style={{ fontSize: "0.85em", color: "#555" }}>
                    {v.description}
                  </div>
                  <div
                    style={{
                      display: "flex",
                      gap: "0.5rem",
                      alignItems: "center",
                    }}
                  >
                    <pre
                      style={{
                        background: "#f5f5f5",
                        padding: "2px 6px",
                        margin: 0,
                        whiteSpace: "pre-wrap",
                      }}
                    >
                      {v.directive}
                    </pre>
                    <button
                      type="button"
                      onClick={() => copyDirective(v.directive)}
                    >
                      Copy
                    </button>
                  </div>
                </div>
              ))}
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
  const [counselorId, setCounselorId] = useState("");
  const [studentId, setStudentId] = useState("");
  const [rendering, setRendering] = useState(false);
  const [rendered, setRendered] = useState<string | null>(null);
  const [renderError, setRenderError] = useState<string | null>(null);

  const needsCounselor =
    meta.inputKind === "counselor" || meta.inputKind === "student_counselor";
  const needsStudent =
    meta.inputKind === "student" || meta.inputKind === "student_counselor";

  const buildPayload = (): Record<string, number> => {
    const payload: Record<string, number> = {};
    if (needsCounselor) payload.counselor_id = Number(counselorId);
    if (needsStudent) payload.student_id = Number(studentId);
    return payload;
  };

  const canRender =
    (!needsCounselor || counselorId.trim() !== "") &&
    (!needsStudent || studentId.trim() !== "");

  const handleRender = () => {
    setRendering(true);
    setRendered(null);
    setRenderError(null);
    api
      .post<{ rendered: string }>(
        `/templates/${purpose}/render/`,
        buildPayload(),
      )
      .then((res) => setRendered(res.data.rendered))
      .catch((err) => {
        const data: RenderError | undefined = err?.response?.data;
        const detail = data?.error;
        if (typeof detail === "string") {
          setRenderError(detail);
        } else if (detail) {
          setRenderError(
            `${detail.error_type}: ${detail.message}` +
              (detail.line ? ` (line ${detail.line})` : "") +
              (detail.variable ? ` [variable: ${detail.variable}]` : ""),
          );
        } else {
          setRenderError("Could not render preview.");
        }
      })
      .finally(() => setRendering(false));
  };

  return (
    <div>
      <h4>Test Render</h4>
      <div
        style={{
          display: "flex",
          gap: "0.5rem",
          alignItems: "flex-end",
          flexWrap: "wrap",
        }}
      >
        {needsCounselor && (
          <div>
            <label>Counselor ID</label>
            <input
              type="number"
              value={counselorId}
              onChange={(e) => setCounselorId(e.target.value)}
              style={{ display: "block" }}
            />
          </div>
        )}
        {needsStudent && (
          <div>
            <label>Student ID</label>
            <input
              type="number"
              value={studentId}
              onChange={(e) => setStudentId(e.target.value)}
              style={{ display: "block" }}
            />
          </div>
        )}
        <button onClick={handleRender} disabled={!canRender || rendering}>
          {rendering ? "Rendering…" : "Render Preview"}
        </button>
      </div>

      {renderError && (
        <p style={{ color: "crimson", whiteSpace: "pre-wrap" }}>
          {renderError}
        </p>
      )}
      {rendered !== null && (
        <>
          <label>Rendered Output</label>
          <textarea
            rows={12}
            value={rendered}
            readOnly
            style={{ width: "100%" }}
          />
        </>
      )}
    </div>
  );
}

export default TemplatesPage;
