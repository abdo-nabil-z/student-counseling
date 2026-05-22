# Workflow for Organizing Mandatory Study Counseling Sessions

## 1. Input Data from the Study Office

The process starts with an email from the study office containing an Excel sheet with the students who must participate in mandatory study counseling.

The student data contains the following information:

* Matriculation number
* First name(s)
* Last name(s)
* Email address
* Course of studies
* Current study semester
* Credit points (CP) achieved so far


NOTE:
- No fixed format
- Copy Paste is fine

Feature IDEA: 
- Open the file as a table and select which column responds to which field

---

## 2. Planning Counseling Capacity

Based on the number of students, the required number of counselors is determined.

For each counselor, the following information is maintained:

* Title
* First name(s)
* Last name(s)
* Chair / organizational unit
* Office address
  * Building and room number (e.g., `AE22-R273`)
* Email address
* Additional CC recipients (e.g., secretary)
* Available time slot(s)




Feature:
- Persist counselors contacts




### Time Slot Information

Each time slot contains:

* Date
* Start time
* End time

Typically, counselors provide availability blocks of 2–3 hours. These blocks are then split into individual 30-minute counseling appointments. 

---

## 3. Initial Invitation Email to Students

Are sent after all available time slots have been determined

Students receive an email informing them about the mandatory counseling and offering available appointment windows.

The email text may look as follows:
```
[For English text, please see below.]

Einladung zur verpflichtenden Studienberatung

Hallo {{vorname}} {{nachname}},

aufgrund von Verzögerungen in Ihrem Studienverlauf lädt Sie der Bereich Informatik > gemäß den Studienbestimmungen zu einer verpflichtenden Studienberatung ein.

In diesem Gespräch möchten wir Ihren bisherigen Studienfortschritt erfassen und gemeinsam mit Ihnen einen individuellen Studienplan erarbeiten, mit dem Sie Ihr Studium erfolgreich abschließen können. Ein Beratungsgespräch dauert ca. 30 Minuten.

Bitte senden Sie uns mindestens eine Woche vor dem Beratungstermin per E-Mail einen Entwurf Ihres Studienplans für die kommenden vier Semester. Daraus sollte hervorgehen, in welchem Semester Sie welche der noch fehlenden Kurse belegen und absolvieren möchten sowie wann Sie planen, Ihre Abschlussarbeit zu schreiben.

Für die Beratungsgespräche stehen an folgenden Tagen jeweils 30-minütige Termine innerhalb der angegebenen Zeitfenster zur Verfügung. Die Termine werden in der Reihenfolge des Eingangs vergeben:

20.04.2026: Termine zwischen 14:00 und 17:00 Uhr
21.04.2026: Termine zwischen 09:00 und 12:00 Uhr
27.04.2026: Termine zwischen 15:15 und 18:15 Uhr

Bitte wählen Sie einen Wunschterminblock sowie eine Alternative aus dem oben genannten Angebot und teilen Sie uns Ihre Auswahl bis spätestens 13.04.2026 per E-Mail mit.

Die Studienberatung findet vor Ort in der Albert-Einstein-Straße 21 und 22 statt (außer bei ausgewiesenen Online-Terminen). Sie erhalten rechtzeitig eine Einladung mit der genauen Uhrzeit und Raumangabe per E-Mail.

Viele Grüße
Helge Parzyjegla


~~~ English text below. ~~~


Invitation for Mandatory Study Counseling

Dear {{vorname}} {{nachname}},

Due to delays in your study progress, the Department of Computer Science invites you, in accordance with the study regulations, to a mandatory study counseling session.

In this meeting, we would like to review your study progress and work with you to create an individual study plan that will help you successfully complete your studies. Each counseling session lasts approximately 30 minutes.

Please email us a draft of your study plan for the next four semesters at least one week before the appointment. The plan should indicate in which semesters you intend to take and complete the remaining courses and when you plan to write your thesis.

A limited number of 30-minute consultation slots are available on the following days within the indicated time windows. Appointments will be allocated in the order of requests received:

20.04.2026: slots between 2:00 p.m. and 5:00 p.m.
21.04.2026: slots between 9:00 a.m. and 12:00 p.m.
27.04.2026: slots between 3:15 p.m. and 6:15 p.m.

Please select one preferred date and one alternative from the options above and let us know your choice by email no later than 13.04.2026.

The counseling will take place in person at Albert-Einstein-Straße 21 and 22 (unless stated otherwise for online slots). You will receive an invitation with the exact time and room by email.

Best regards,
Helge Parzyjegla
```

---

## 4. Reminder Process

If students do not respond to the initial invitation email, they receive a reminder email.

The reminder may contain an updated list of still-available time slots.

The reminder email may look as follows:

```
[For English text, please see below.]

Hallo,

dies ist eine freundliche Erinnerung, um einen Termin für die verpflichtende  Studienberatung mit uns zu vereinbaren.

Falls Sie sich nicht bis zum 15. April 2026 melden, müssen wir Ihnen einen Termin zuweisen.

Vielen Dank,
Helge Parzyjegla


~~~ English text below. ~~~


Hello,

This is a friendly reminder to negotiate an appointment for the mandatory study counseling.

If you do not negotiate an appointment until 15th April 2026, we have to assign a date.

Many thanks,
Helge Parzyjegla
```

---

## 5. Assignment of Counseling Appointments

If a student still does not respond after the reminder, an appointment is assigned.

In these cases:

* A dedicated time slot is selected that was not part of the original public list.
* Usually, the counseling is performed by me.
* The assigned counselor may therefore not appear in the original list of counselors and available slots.

The assignment email may look as follows:

```
[For English text please see below.]

Hallo {{Vorname}} {{Nachname}},

leider haben wir bisher nichts von Ihnen gehört, weshalb wir Ihnen den folgenden Termin zur verpflichtenden Studienberatung zuweisen.

Ihre Studienberatung findet am 19.05.2026 um {{Uhrzeit}} im Konrad-Zuse-Haus (AE22) Raum 273 statt.

Bitte lassen Sie mir hierzu bis zum 15.05.2026 Ihren Studienplan für die nächsten max. 4 Semester zukommen.

Viele Grüße
Helge Parzyjegla


~~~ English text below. ~~~


Hello {{Vorname}} {{Nachname}},

Unfortunately, we have not heard from you yet, which is why we are assigning you the following date for your mandatory counseling session.

Your study counseling will take place on 19.05.2026 at {{Uhrzeit}} in the Konrad-Zuse-Building (AE22) room 273.

Please send me your study plan for the next max. 4 semesters by 15.05.2026.

Best regards,
Helge Parzyjegla
```

---

## 6. Collection of Study Plans and Additional Documents

Students are asked to provide a study plan covering the next four semesters.

These study plans may arrive in different formats, including:

* PDF documents
* Plain text emails
  * that can be printed out as PDF document
  * that can be copied and pasted and converted into Markdown and then into a PDF

FEATURE: Markdown online tool?

Additionally, a transcript of records may be required.

The transcript of records may either:

* Be submitted by the student, or
* Be provided directly by the study office



---

## 7. Generation of Appointment-Related Emails

After a counseling appointment has been scheduled or assigned, several emails are generated.

### 7.1 Calendar Invitation Email

One email is sent to:

* The student and
* The assigned counselor

This email contains:

* Calendar invitation
* Date and time
* Location or online meeting information
* Name of the counselor

FEAT: Selector for location (always editable)

The purpose is to simplify appointment management and ensure all participants have the necessary logistical information.

### 7.2 Counselor Preparation Email

A second email is sent only to the counselor.

This email contains:

* The student's study plan (if available)
* The transcript of records (if available)
* A form for documenting the counseling minutes

---

## 8. Counseling Session Documentation

After the counseling session:

* The counseling minutes are collected.
* Revised study plans are collected.
* All relevant documents are bundled together.
* The complete bundle is forwarded to the study office.
* This happens usually only once after all counselings have been completed.

---

## 9. Documentation of No-Shows and Missing Responses

If a student:

* Does not respond to emails, and
* Does not attend the counseling session,

this must also be documented.

The documentation should include:

* Short counseling minutes documenting the no-show
* Copies of the previously sent emails

The purpose is to document that reasonable attempts were made to contact the student and offer counseling.

FEAT: Backend logging service

---

# Requirements for the Counseling Minutes Form

Currently, no finalized template for counseling minutes exists. However, the following information should be included.

## Required Content

### Student Information

* Name
* Matriculation number
* Degree program
* Current semester
* Credit points achieved so far

### Counselor Information

* Name
* Organizational unit: Chair (DB, Software Engineering, "Institute" etc)

### Appointment Information

* Date
* Time
* Location
* Online or in-person indicator

### Counseling Type

Indication whether the session is:

* First counseling session (non-binding study plan) : There can be many!
* Second counseling session (Binding study plan)


### Discussion Topics

The counseling minutes should provide sections for documenting:

* Summary of courses completed so far: (empty if transcript of records is present)
* Problems during studying (identifying core issues, if any. Not used to shame anyone)
* Proposed study plan and comments
* Information about a second counseling session
* Miscellaneous notes

FEAT: Make document self-described

---

# Requirements for the Minutes Form Format

The counseling minutes form should ideally be implemented as an editable PDF form.

## Editable PDF Requirements

The PDF should contain prefilled but editable form fields.

This is important because changes may occur after the form was generated, for example:

* A counselor becomes unavailable and another counselor takes over.
* Date or time changes due to rescheduling.

In such cases, the information should be editable directly within the PDF form.

## Online and Paper-Based Usage

The form should support both:

* Online completion
* Printed paper-based completion

Therefore:

* The layout should remain usable when printed.
* Signature fields must be included.
* The counselor must be able to sign the form manually after printing or digitally when completed electronically.



