import type { DocumentInfo } from "./document";

export interface Student {
  id: number;
  matriculation_number: string;
  first_name: string;
  last_name: string;
  email: string;
  course_of_studies: string | null;
  current_study_semester: number | null;
  credit_points: number;
  contact_status: string;
  initial_study_plan?: DocumentInfo | null;
  final_study_plan?: DocumentInfo | null;
}
