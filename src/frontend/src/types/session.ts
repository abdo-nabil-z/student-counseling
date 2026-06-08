export interface CounselingSession {
  id: number;
  student: number;
  counselor: number;
  slot: number;
  notes: string | null;
  status: "pending" | "booked" | "completed" | "cancelled" | "missed";
  initial_study_plan: string | null;
  final_study_plan: string | null;
}
