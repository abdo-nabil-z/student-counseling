import { useState } from "react";
import { useLocation, useParams } from "react-router-dom";
import type { Counselor } from "../types/counselor";

const SUBJECT =
  "Terminbestätigung Studienberatung / Counseling appointment confirmation";

const INVITATION = `Hallo {{counselor}},

hiermit laden wir Sie zum folgenden Studienberatungstermin ein:

Datum: {{date}}
Uhrzeit: {{time}}
Ort: {{location}}

Eine Kalendereinladung ist beigefügt.

Viele Grüße
Helge Parzyjegla

~~~ English below ~~~

Dear {{counselor}},

This is your calendar invitation for the following study counseling appointment:

Date: {{date}}
Time: {{time}}
Location: {{location}}

A calendar invite is attached.

Best regards,
Helge Parzyjegla`;

function CounselorMailPage() {
  const { counselorId } = useParams();
  const location = useLocation();
  const counselor =
    (location.state as { counselor?: Counselor } | null)?.counselor ?? null;

  const [date, setDate] = useState("");
  const [time, setTime] = useState("");
  const [place, setPlace] = useState("Konrad-Zuse-Haus (AE22), Raum 273");

  const name = counselor
    ? `${counselor.title} ${counselor.first_name} ${counselor.last_name}`.trim()
    : "{{counselor_name}}";

  const body = INVITATION.replaceAll("{{date}}", date || "{{date}}")
    .replaceAll("{{time}}", time || "{{time}}")
    .replaceAll("{{location}}", place)
    .replaceAll("{{counselor}}", name);

  return (
    <section>
      <h2>
        Counselor Mail {counselor ? `– ${name}` : `(Counselor #${counselorId})`}
      </h2>

      <div className="card">
        <h3>Calendar Invitation</h3>

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

        <label>Subject</label>
        <input value={SUBJECT} readOnly />

        <label>Email Body (preview)</label>
        <textarea rows={16} value={body} readOnly />

        <button>Send Email</button>
      </div>
    </section>
  );
}

export default CounselorMailPage;
