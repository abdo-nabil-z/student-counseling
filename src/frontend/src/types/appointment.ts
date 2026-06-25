import type { Slot } from "./slots";
import type { Student } from "./student";
import type { Counselor } from "./counselor";
import type { DocumentInfo } from "./document";

// The backend may return student/counselor either as an ID or as a nested object,
// so we accept both shapes.
export interface Appointment {
  id: number;
  student: number | Student;
  counselor: number | Counselor;
  slot: Slot;
  start_time: string;
  end_time: string;
  status: "pending" | "booked" | "completed" | "cancelled" | "missed";
  location: string | null;
  minutes: DocumentInfo | null;
  created_at: string;
  updated_at: string;
}
