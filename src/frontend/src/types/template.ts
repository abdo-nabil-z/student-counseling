export type Purpose =
  | "student_invitation"
  | "student_reminder"
  | "forced_appointment_assignment"
  | "appointment_invitation"
  | "counselor_preparation_instruction"
  | "appointment_cancellation"
  | "counselor_availability_request"
  | "counselor_appointments_summary"
  | "general_mail"
  | "study_plan"
  | "appointment_minutes";

export interface Template {
  purpose: Purpose;
  content: string;
  updated_at: string;
}

export interface ContextVariable {
  path: string;
  type: string;
  directive: string;
  description: string;
}

export interface RenderError {
  error: {
    code: string;
    message: string;
    details?: {
      type?: string;
      message?: string;
      line?: number;
      variable?: string;
    } | null;
    request_id: string;
  };
}
