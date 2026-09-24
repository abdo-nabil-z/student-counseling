export interface SlotStatusStudent {
  id: number;
  matriculation_number: string;
  first_name: string;
  last_name: string;
  full_name: string;
}

export interface SlotStatusAppointment {
  id: number;
  status: string;
  start_time: string;
  duration_minutes: number;
  end_time: string;
  location: string;
  student: SlotStatusStudent;
}

export interface SlotStatusSegment {
  status: "free" | "taken";
  start: string;
  end: string;
  appointment: SlotStatusAppointment | null;
}

export interface SlotStatusSlot {
  id: number;
  date: string;
  start_time: string;
  end_time: string;
  segments: SlotStatusSegment[];
}

export interface CounselorSlotStatus {
  counselor: {
    id: number;
    full_name: string;
    email: string;
    office_address: string;
  };
  slots: SlotStatusSlot[];
}
