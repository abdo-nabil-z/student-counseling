export interface AppointmentSlot {
  id: number;
  start_time: string;
  end_time: string;
  status: "available" | "booked" | "cancelled";
}
