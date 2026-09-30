export type EmailPurpose =
  | "student_invitation"
  | "student_reminder"
  | "forced_appointment_assignment"
  | "appointment_invitation"
  | "counselor_preparation_instruction"
  | "appointment_cancellation"
  | "counselor_availability_request"
  | "counselor_appointments_summary"
  | "general_mail";

export type RecipientType = "student" | "counselor" | "external";

export type EmailDeliveryStatus = "draft" | "queued" | "sent" | "failed";

export type EmailAttachmentSource = "existing" | "uploaded" | "generated";

export interface EmailAttachment {
  id: number;
  source: EmailAttachmentSource;
  source_document_id: number | null;
  document_id: number | null;
  name: string;
  content_type: string;
  download_url: string | null;
  created_at: string;
}

export interface EmailDelivery {
  id: number;
  recipient_type: RecipientType;

  student_id: number | null;
  student_name: string | null;

  counselor_id: number | null;
  counselor_name: string | null;

  recipient_email: string;
  cc: string[];
  subject: string;
  body: string;
  status: EmailDeliveryStatus;
  attachments: EmailAttachment[];
  created_at: string;
}

export interface EmailBatch {
  id: number;
  purpose: EmailPurpose;
  created_at: string;
  deliveries: EmailDelivery[];
}

export interface EmailDeliveryListItem {
  id: number;
  recipient_type: RecipientType;

  student: number | null;
  counselor: number | null;

  recipient_email: string;
  recipient_name: string;
  subject: string;
  body: string;
  status: EmailDeliveryStatus;

  error_message: string;
  attempt_count: number;

  sent_at: string | null;
  created_at: string;
  updated_at: string;

  attachments: EmailAttachment[];
}

export interface EmailBatchListItem {
  id: number;
  purpose: EmailPurpose;
  recipient_type: RecipientType | null;
  created_at: string;
  deliveries: EmailDeliveryListItem[];
}

export interface EmailDeliveryStatusInfo {
  id: number;
  recipient_type: RecipientType;

  student_id: number | null;
  student_name: string | null;

  counselor_id: number | null;
  counselor_name: string | null;

  recipient_email: string;
  status: EmailDeliveryStatus;
  attempt_count: number;
  last_error: string;
  next_attempt_at: string | null;
  sent_at: string | null;
  updated_at: string;
}

export interface EmailBatchStatus {
  id: number;
  purpose: EmailPurpose;
  total_count: number;
  draft_count: number;
  queued_count: number;
  sent_count: number;
  failed_count: number;
  deliveries: EmailDeliveryStatusInfo[];
}

export interface ApiErrorResponse {
  error: {
    code: string;
    message: string;
    details: unknown;
    request_id: string;
  };
}
