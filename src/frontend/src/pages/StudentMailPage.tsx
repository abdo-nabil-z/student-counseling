import { useState } from "react";
import { useLocation, useParams } from "react-router-dom";
import type { Student } from "../types/student";

type MailType = "invitation" | "reminder" | "assignment";

const INVITATION = `Einladung zur verpflichtenden Studienberatung

Hallo {{name}},

aufgrund von Verzögerungen in Ihrem Studienverlauf lädt Sie der Bereich Informatik gemäß den Studienbestimmungen zu einer verpflichtenden Studienberatung ein. Ein Beratungsgespräch dauert ca. 30 Minuten.

Bitte senden Sie uns mindestens eine Woche vor dem Termin einen Entwurf Ihres Studienplans für die kommenden vier Semester.

Bitte wählen Sie einen Wunschtermin sowie eine Alternative aus dem Angebot und teilen Sie uns Ihre Auswahl per E-Mail mit.

Die Studienberatung findet vor Ort in der Albert-Einstein-Straße 21 und 22 statt.

Viele Grüße
Helge Parzyjegla

~~~ English below ~~~

Dear {{name}},

Due to delays in your study progress, the Department of Computer Science invites you to a mandatory study counseling session (approx. 30 minutes).

Please email us a draft of your study plan for the next four semesters at least one week before the appointment.

Please choose a preferred date and an alternative from the available slots and let us know by email.

The counseling will take place in person at Albert-Einstein-Straße 21 and 22.

Best regards,
Helge Parzyjegla`;

const REMINDER = `Hallo {{name}},

dies ist eine freundliche Erinnerung, um einen Termin für die verpflichtende Studienberatung zu vereinbaren. Falls Sie sich nicht melden, müssen wir Ihnen einen Termin zuweisen.

Vielen Dank,
Helge Parzyjegla

~~~ English below ~~~

Hello {{name}},

This is a friendly reminder to arrange an appointment for the mandatory study counseling. If you do not respond, we will have to assign a date.

Many thanks,
Helge Parzyjegla`;

const ASSIGNMENT = `Hallo {{name}},

leider haben wir bisher nichts von Ihnen gehört, weshalb wir Ihnen den folgenden Termin zur verpflichtenden Studienberatung zuweisen.

Ihre Studienberatung findet am {{date}} um {{time}} in {{location}} statt.

Bitte lassen Sie mir Ihren Studienplan für die nächsten max. 4 Semester zukommen.

Viele Grüße
Helge Parzyjegla

~~~ English below ~~~

Hello {{name}},

Unfortunately, we have not heard from you yet, so we are assigning you the following appointment for your mandatory counseling session.

Your study counseling will take place on {{date}} at {{time}} in {{location}}.

Please send me your study plan for the next max. 4 semesters.

Best regards,
Helge Parzyjegla`;

const SUBJECTS: Record<MailType, string> = {
  invitation:
    "Einladung zur verpflichtenden Studienberatung / Invitation for Mandatory Study Counseling",
  reminder:
    "Erinnerung: verpflichtende Studienberatung / Reminder: Mandatory Study Counseling",
  assignment: "Zugewiesener Beratungstermin / Assigned Counseling Appointment",
};

function StudentMailPage() {
  const { studentId } = useParams();
  const location = useLocation();
  const student =
    (location.state as { student?: Student } | null)?.student ?? null;

  const [mailType, setMailType] = useState<MailType>("invitation");
  const [date, setDate] = useState("");
  const [time, setTime] = useState("");
  const [place, setPlace] = useState("Konrad-Zuse-Haus (AE22), Raum 273");

  const name = student
    ? `${student.first_name} ${student.last_name}`
    : "{{vorname}} {{nachname}}";

  // ---- if / else: choose the template for the selected email type ----
  // eslint-disable-next-line no-useless-assignment
  let body = "";
  if (mailType === "invitation") {
    body = INVITATION;
  } else if (mailType === "reminder") {
    body = REMINDER;
  } else {
    body = ASSIGNMENT.replaceAll("{{date}}", date || "{{date}}")
      .replaceAll("{{time}}", time || "{{time}}")
      .replaceAll("{{location}}", place);
  }
  body = body.replaceAll("{{name}}", name);

  return (
    <section>
      <h2>Student Mail {student ? `– ${name}` : `(Student #${studentId})`}</h2>

      <div className="card">
        <label>Email Type</label>
        <select
          value={mailType}
          onChange={(e) => setMailType(e.target.value as MailType)}
        >
          <option value="invitation">Initial Invitation</option>
          <option value="reminder">Reminder</option>
          <option value="assignment">Appointment Assignment</option>
        </select>

        {/* appointment details show ONLY for the assignment type */}
        {mailType === "assignment" && (
          <div className="appointment-details">
            <label>Date</label>
            <input
              type="date"
              value={date}
              onChange={(e) => setDate(e.target.value)}
            />
            <label>Time</label>
            <input
              type="time"
              value={time}
              onChange={(e) => setTime(e.target.value)}
            />
            <label>Location</label>
            <input value={place} onChange={(e) => setPlace(e.target.value)} />
          </div>
        )}

        <label>Subject</label>
        <input value={SUBJECTS[mailType]} readOnly />

        <label>Email Body (preview)</label>
        <textarea rows={18} value={body} readOnly />

        <button>Send Email</button>
      </div>
    </section>
  );
}

export default StudentMailPage;
