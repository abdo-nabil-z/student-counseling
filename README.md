# University Student Counseling Management System

<p align="center">
  <img src="src/frontend/src/assets/hero.png" alt="Project illustration" width="180" />
</p>

<p align="center">
  <strong>A full-stack web application for managing university counseling workflows from student import to semester cleanup.</strong>
</p>

<p align="center">
  <img alt="Python" src="https://img.shields.io/badge/Python-3.12%2B-3776AB?logo=python&logoColor=white" />
  <img alt="Django" src="https://img.shields.io/badge/Django-6.0-092E20?logo=django&logoColor=white" />
  <img alt="React" src="https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=111" />
  <img alt="TypeScript" src="https://img.shields.io/badge/TypeScript-6-3178C6?logo=typescript&logoColor=white" />
  <img alt="SQLite" src="https://img.shields.io/badge/SQLite-Development-003B57?logo=sqlite&logoColor=white" />
</p>

## Overview

This project is an internal university administration tool for organizing counseling sessions between students and academic counselors. It combines a React/TypeScript frontend with a Django REST Framework backend and covers the full semester workflow: importing students, managing counselors and availability, scheduling appointments, handling documents, generating and sending templated emails, exporting semester data, and cleaning semester-specific records.

The application was developed as an academic team project. The codebase emphasizes clear domain separation, API-driven frontend/backend integration, validation, traceable error handling, background email processing, and automated tests.

## What the project demonstrates

- **Modular backend design** using separate Django apps for students, counselors, appointments, documents, templates, PDF generation, and mailing.
- **REST API design** with Django REST Framework, validation, consistent error envelopes, and OpenAPI/Swagger documentation.
- **Scheduling logic** that distinguishes counselor availability from appointments and computes free/taken time dynamically.
- **Conflict handling** for active appointments while still allowing explicitly forced scheduling when required by the workflow.
- **Background email processing** with persisted delivery state, retries, manual resend, attachments, and SMTP configuration.
- **Template-driven communication** using Jinja-style context data for student/counselor emails and generated PDFs.
- **Document lifecycle management** for study plans, counseling minutes, generated files, and cleanup behavior.
- **Semester lifecycle support** including CSV reporting and removal of semester-specific data while persistent configuration remains.
- **Operational observability** through request IDs, structured error responses, application logging, and documented APIs.
- **Automated backend tests** covering the main domain and API behavior.

## Main workflow

```text
Import students
      |
      v
Manage counselors and availability
      |
      v
Create / reschedule appointments
      |
      v
Upload study plans and counseling documents
      |
      v
Generate, review and send emails
      |
      v
Track counseling progress
      |
      v
Export semester report
      |
      v
Semester cleanup
```

## Architecture

```text
                         React + TypeScript
                               Frontend
                                  |
                                  | HTTP / REST
                                  v
                      Django REST Framework API
                                  |
                   +--------------+--------------+
                   |              |              |
                   v              v              v
              Domain apps     Documents      Templates / PDF
                   |              |              |
                   +--------------+--------------+
                                  |
                             SQLite database
                             + file storage
                                  |
                                  v
                         Background mail worker
                                  |
                                  v
                              SMTP server
```

The backend is split into domain-oriented Django applications rather than one large application. Computed data such as counselor free/taken availability is derived from stored slots and appointments instead of being duplicated in the database.

## Tech stack

| Layer | Technology |
| --- | --- |
| Frontend | React 19, TypeScript 6, Vite 8, Material UI, Axios |
| Backend | Python, Django 6.0, Django REST Framework |
| API documentation | drf-spectacular / OpenAPI / Swagger UI / ReDoc |
| Database | SQLite for development |
| Templates | Jinja2 sandboxed rendering |
| PDF generation | Mistune, WeasyPrint, pyHanko |
| Data import/export | pandas, openpyxl, xlrd, CSV |
| Email | Django SMTP backend with a database-backed queue worker |
| File storage | Django `FileField` / local media storage |
| Testing | Django test framework + DRF test client |

## Repository structure

```text
.
├── README.md
├── docker-compose.yml
└── src/
    ├── backend/
    │   ├── consultation_backend/   # Django project configuration
    │   ├── students/               # Student import, CRUD, status, reports
    │   ├── counselors/             # Counselors and availability slots
    │   ├── appointments/           # Appointment scheduling and validation
    │   ├── documents/              # File persistence and cleanup
    │   ├── templates/              # Reusable email/PDF templates
    │   ├── pdf/                    # PDF rendering and persistence
    │   ├── mailing/                # Email batches, deliveries and worker
    │   ├── defaults/               # Default template content
    │   ├── manage.py
    │   └── requirements.txt
    └── frontend/
        ├── src/
        │   ├── api/
        │   ├── components/
        │   ├── pages/
        │   └── types/
        ├── package.json
        └── vite.config.ts
```

---

# Running the project locally

The steps below start from a fresh clone/download and do not rely on an existing database.

## 1. Prerequisites

Install:

- **Python 3.12+**
- **Node.js 20.19+** (or Node 22.12+)
- **npm**
- **Git** if cloning the repository

PDF generation uses WeasyPrint. Depending on your operating system, WeasyPrint may require additional native libraries. If installation fails at that dependency, follow the platform-specific installation instructions in the WeasyPrint documentation.

## 2. Clone or download the repository

With Git:

```bash
git clone <repository-url>
cd <repository-directory>
```

If you downloaded a ZIP file, extract it and open a terminal in the extracted project root — the directory containing `README.md`, `docker-compose.yml`, and `src/`.

## 3. Set up the backend

Move into the backend directory:

```bash
cd src/backend
```

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it.

### Linux / macOS

```bash
source .venv/bin/activate
```

### Windows PowerShell

```powershell
.venv\Scripts\Activate.ps1
```

Install Python dependencies:

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Create/update the local database:

```bash
python manage.py migrate
```

Optional sanity check:

```bash
python manage.py check
```

Start the backend:

```bash
python manage.py runserver 8000
```

The backend is now available at:

```text
http://localhost:8000
```

API documentation:

- Swagger UI: `http://localhost:8000/api/docs/`
- ReDoc: `http://localhost:8000/api/redoc/`
- OpenAPI schema: `http://localhost:8000/api/schema/`

> Keep this terminal running while using the frontend.

## 4. Set up the frontend

Open a **second terminal** from the project root:

```bash
cd src/frontend
npm ci
npm run dev
```

Open:

```text
http://localhost:5173
```

The Vite development server proxies `/api` requests to the Django backend on port `8000`, so no separate frontend API URL configuration is required for local development.

## 5. Start the email worker

Queued emails are processed by a separate Django management command. Open a **third terminal**, activate the same backend virtual environment, and run:

```bash
cd src/backend
python manage.py process_email_queue
```

For a single processing cycle during development/testing:

```bash
python manage.py process_email_queue --once
```

The application can be explored without the worker, but queued email deliveries will not be processed until the worker is running.

## 6. Configure email sending

SMTP credentials are configured from the application's **Mail Settings** page:

```text
http://localhost:5173/mail-settings
```

The backend also exposes:

```text
GET    /api/mailing/settings/
PUT    /api/mailing/settings/
DELETE /api/mailing/settings/
POST   /api/mailing/settings/test/
```

The SMTP password is write-only through the API. When persistent credentials are selected, the password is encrypted before storage.

Email configuration is only required if you want to test real delivery.

## 7. First-run checklist

After starting the backend and frontend, a useful first pass is:

1. Open the frontend at `http://localhost:5173`.
2. Import or create students.
3. Create counselors.
4. Add counselor availability slots.
5. Create an appointment.
6. Review/edit the communication templates.
7. Configure SMTP if email delivery is required.
8. Start the email worker and send a test email.
9. Check the semester report export.

---

# Core functionality

## Student management

- Create, update, list, and delete students.
- Import student data from XLSX/XLS/CSV/PDF sources.
- Preview imported rows before confirming them.
- Track contact state such as not contacted, emailed, confirmed, or did not respond.
- Automatically update contact status after successful student email delivery and booking workflows while still allowing manual edits.
- Attach initial and final study-plan documents.
- Export the current semester as CSV.

## Counselors and availability

- Maintain persistent counselor records.
- Store multiple availability slots per counselor.
- Allow availability slots to overlap because they represent general availability, not bookings.
- Compute free/taken segments from actual appointment times.
- Return appointments outside declared availability as uncovered appointments instead of hiding them.

## Appointments

- One counseling appointment per student.
- Assign a counselor and optionally associate a declared availability slot.
- Store `start_time + duration_minutes` rather than duplicating an authoritative end time.
- Reschedule by updating the existing appointment.
- Track appointment states including pending, booked, completed, cancelled, and missed.
- Only active appointments (`pending` and `booked`) occupy availability.
- Detect overlapping active appointments for the same counselor, with explicit override support where the workflow requires it.

## Templates and PDF generation

- Reusable templates are identified by purpose.
- Template rendering uses a restricted Jinja2 environment.
- Context schemas expose which variables are available for each template purpose.
- Markdown-based templates can be rendered into PDFs.
- Generated documents can be attached to email deliveries.

## Email workflow

The backend persists email work instead of sending directly inside the request/response cycle.

```text
Generate batch
    |
    v
Draft deliveries
    |
    v
Review / edit
    |
    v
Queue batch
    |
    v
Background worker
    |
    +--> Sent
    |
    +--> Retry --> Failed --> Manual resend
```

The mailing subsystem supports:

- Student, counselor, and external recipients.
- Draft/queued/sent/failed delivery states.
- Batch creation and status polling.
- Uploaded, existing, and generated attachments.
- Automatic retry for temporary failures.
- Manual resend of failed deliveries.
- Attachment cleanup after successful sending.
- Configurable SMTP sender identity.

## Semester lifecycle

Semester-specific records can be exported and cleaned without deleting reusable configuration.

Typical semester-specific data:

- Students
- Appointments
- Counselor availability slots
- Student study-plan documents
- Appointment minutes
- Semester email records/temporary files as applicable

Persistent data such as counselors and reusable templates remains available for the next semester.

---

# API and backend quality

## API documentation

The backend generates an OpenAPI schema automatically with `drf-spectacular`.

While the backend is running:

```text
Swagger: http://localhost:8000/api/docs/
ReDoc:   http://localhost:8000/api/redoc/
Schema:  http://localhost:8000/api/schema/
```

A static schema can also be generated with:

```bash
cd src/backend
python manage.py spectacular --color --file schema.yml
```

## Error handling and request tracing

DRF errors are normalized into a consistent response shape containing an error code, message, details, and request ID. Request IDs are also injected into logging context, making frontend-reported failures easier to trace in backend logs.

Example shape:

```json
{
  "error": {
    "code": "validation_error",
    "message": "The submitted data is invalid.",
    "details": {},
    "request_id": "..."
  }
}
```

## Tests

Run the complete backend suite from `src/backend`:

```bash
python manage.py test
```

Useful pre-commit checks:

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
```

Frontend checks from `src/frontend`:

```bash
npm run lint
npm run build
```

---

# Selected API endpoints

A few useful entry points are shown below; Swagger contains the complete API contract.

```text
GET/POST  /api/students/
POST      /api/students/import/preview/
POST      /api/students/import/confirm/
GET       /api/students/semester-report/
DELETE    /api/students/semester-cleanup/

GET/POST  /api/counselors/
GET       /api/counselors/slot-status/

GET       /api/appointments/
POST      /api/appointments/create-appointment/
PATCH     /api/appointments/{id}/

GET       /api/templates/
POST      /api/templates/{purpose}/render/

POST      /api/mailing/batches/
POST      /api/mailing/batches/{id}/send/
GET       /api/mailing/batches/{id}/status/
POST      /api/mailing/deliveries/{id}/resend/
```

# Design notes

A few decisions are especially important to understanding the codebase:

- **Availability is not a booking.** A counselor slot expresses general availability; appointments remain independent records and can exist outside declared slots when explicitly required.
- **Appointment end time is derived.** The model stores a start timestamp and duration to avoid maintaining two values that could become inconsistent.
- **Cancellation does not delete an appointment.** Its status changes to `cancelled`, preserving the record while releasing the period from active availability calculations.
- **Email sending is asynchronous from the UI workflow.** The request creates/queues persisted delivery records, while the worker handles SMTP interaction and retries.
- **Files have explicit lifecycle rules.** Persistent student/appointment documents are separated from temporary email attachments and generated files so cleanup does not accidentally delete source documents.
- **Semester cleanup is domain-aware.** Temporary semester data is removed while counselor identities and reusable templates remain.

# Development scope

This is an academic/internal administration project rather than a production SaaS product. The current development setup intentionally uses SQLite and local file storage and is designed around a small number of trusted administrative users. Production deployment would require environment-managed secrets, production-grade storage/database choices, authentication/authorization review, HTTPS, and deployment-specific hardening.

# Additional documentation

The backend contains more detailed developer/API notes in:

```text
src/backend/README.md
```

For the most accurate endpoint request/response definitions, run the backend and use the generated Swagger documentation.

## Docker / Dev Container note

A root `docker-compose.yml` is present and references a `.devcontainer/` build context used by the original development environment. The `.devcontainer/` directory is not included in this source snapshot, so the local setup above is the self-contained way to run this checkout. If the Dev Container files are restored, that workflow can be used to start the frontend, backend, and Supervisor-managed email worker together.
