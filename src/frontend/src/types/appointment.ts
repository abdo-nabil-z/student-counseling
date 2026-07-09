import type { Slot } from "./slots";
import type { Student } from "./student";
import type { Counselor } from "./counselor";
import type { DocumentInfo } from "./document";

// Matches the backend Appointment: start_time + duration_minutes (no end_time).
// student/counselor come back nested (or as an ID); slot may be null.
export interface Appointment {
  id: number;
  student: number | Student;
  counselor: number | Counselor;
  slot: Slot | null;
  start_time: string;
  duration_minutes: number;
  status: "pending" | "booked" | "completed" | "cancelled" | "missed";
  location: string | null;
  minutes: DocumentInfo | null;
  created_at: string;
  updated_at: string;
}
