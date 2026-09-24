import type { Student } from "./student";
import type { Counselor } from "./counselor";
import type { Slot } from "./slots";

export interface CounselingSessionDetail {
  id: number;
  student: Student | null;
  counselor: Counselor | null;
  slot: Slot | null;
  status: "pending" | "booked" | "completed" | "cancelled" | "missed";
  notes: string | null;
  initial_study_plan: string | null;
  final_study_plan: string | null;
  created_at: string;
  updated_at: string;
}
