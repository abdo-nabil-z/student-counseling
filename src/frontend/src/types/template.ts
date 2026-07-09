export type Purpose =
  | "testmail"
  | "student_invitation"
  | "student_reminder"
  | "forced_appointment_assignment"
  | "appointment_invitation"
  | "counselor_preparation_instruction"
  | "appointment_cancellation"
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
  error:
    | string
    | {
        error_type: string;
        message: string;
        line?: number;
        variable?: string;
      };
}
