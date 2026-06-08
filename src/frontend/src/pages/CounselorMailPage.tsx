import { useState } from "react";
import { useLocation, useParams } from "react-router-dom";
import type { Counselor } from "../types/counselor";

type MailType = "preparation" | "invitation";

const PREPARATION = `Hallo {{counselor}},

anbei finden Sie die Unterlagen zur Vorbereitung auf das Beratungsgespräch: den Studienplan der/des Studierenden, die Leistungsübersicht (sofern vorhanden) sowie das Formular für das Beratungsprotokoll.

Viele Grüße
Helge Parzyjegla

~~~ English below ~~~

Dear {{counselor}},

Please find attached the documents to prepare for the counseling session: the student's study plan, the transcript of records (if available), and the counseling minutes form.

Best regards,
Helge Parzyjegla`;

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

const SUBJECTS: Record<MailType, string> = {
  preparation:
    "Unterlagen zur Studienberatung / Counseling preparation documents",
  invitation:
    "Terminbestätigung Studienberatung / Counseling appointment confirmation",
};

function CounselorMailPage() {
  const { counselorId } = useParams();
  const location = useLocation();
  const counselor =
    (location.state as { counselor?: Counselor } | null)?.counselor ?? null;

  const [mailType, setMailType] = useState<MailType>("preparation");
  const [date, setDate] = useState("");
  const [time, setTime] = useState("");
  const [place, setPlace] = useState("Konrad-Zuse-Haus (AE22), Raum 273");

  const name = counselor
    ? `${counselor.title} ${counselor.first_name} ${counselor.last_name}`.trim()
    : "{{counselor_name}}";

  // ---- if / else: choose the template for the selected email type ----
  // eslint-disable-next-line no-useless-assignment
  let body = "";
  if (mailType === "preparation") {
    body = PREPARATION;
  } else {
    body = INVITATION.replaceAll("{{date}}", date || "{{date}}")
      .replaceAll("{{time}}", time || "{{time}}")
      .replaceAll("{{location}}", place);
  }
  body = body.replaceAll("{{counselor}}", name);

  return (
    <section>
      <h2>
        Counselor Mail {counselor ? `– ${name}` : `(Counselor #${counselorId})`}
      </h2>

      <div className="card">
        <label>Email Type</label>
        <select
          value={mailType}
          onChange={(e) => setMailType(e.target.value as MailType)}
        >
          <option value="preparation">Preparation Documents</option>
          <option value="invitation">Calendar Invitation</option>
        </select>

        {/* preparation: show document attachments */}
        {mailType === "preparation" && (
          <div className="attachments">
            <label>Attach Study Plan</label>
            <input type="file" />
            <label>Attach Transcript</label>
            <input type="file" />
            <label>Attach Minutes Form</label>
            <input type="file" />
          </div>
        )}

        {/* invitation: show appointment details */}
        {mailType === "invitation" && (
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
        <textarea rows={16} value={body} readOnly />

        <button>Send Email</button>
      </div>
    </section>
  );
}

export default CounselorMailPage;
