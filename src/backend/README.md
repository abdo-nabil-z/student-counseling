# Backend

This project is created using [Django](https://github.com/django/django) version 6.0.4

## How to run

IF you are running from with in the container, from its terminal run:

```bash
python manage.py runserver 0.0.0.0:8000
```

if you are running from you device make sure the packages are installed

```bash
python -m django version
```

then to run the server, run:

```bash
python manage.py runserver 8000
```

or
then

```bash
python manage.py runserver
```

## checking the server

to check that the server is running properly open the browser and type:
for the pages:

```bash
http://localhost:8000/counselors/
```

and for the api Documentation:
in Swagger UI:

```bash
http://localhost:8000/api/docs/
```

in ReDoc

```bash
http://localhost:8000/api/redoc/
```

To export them to a YAML file for postman:

```bash
python manage.py spectacular --color --file schema.yml
```

the file schema.yml is created in the backend project

## API error handling

API errors raised through Django REST Framework use a consistent JSON structure:

```json
{
  "error": {
    "code": "validation_error",
    "message": "The submitted data is invalid.",
    "details": {
      "email": ["Enter a valid email address."]
    },
    "request_id": "e0d413a5-12dd-44c6-b67f-f2fe80db78ab"
  }
}
```

### Error response fields

- `code`: A machine-readable error identifier that the frontend can use when handling specific errors.
- `message`: A general human-readable description of the error.
- `details`: Additional information about the error. For validation errors, this normally contains errors grouped by field. It may be `null` when no additional information is available.
- `request_id`: A unique identifier for the request. Include this value when reporting an unexpected server error so the related backend log entry can be located.

The same request identifier is also returned in the response header:

```http
X-Request-ID: e0d413a5-12dd-44c6-b67f-f2fe80db78ab
```

### Validation error example

Status:

```http
400 Bad Request
```

Response:

```json
{
  "error": {
    "code": "validation_error",
    "message": "The submitted data is invalid.",
    "details": {
      "name": ["This field is required."]
    },
    "request_id": "e0d413a5-12dd-44c6-b67f-f2fe80db78ab"
  }
}
```

The frontend should display or map the field errors found inside `error.details`.

### Unknown API endpoint example

Status:

```http
404 Not Found
```

Response:

```json
{
  "error": {
    "code": "endpoint_not_found",
    "message": "The requested API endpoint was not found.",
    "details": null,
    "request_id": "e0d413a5-12dd-44c6-b67f-f2fe80db78ab"
  }
}
```

### Unexpected server error example

Status:

```http
500 Internal Server Error
```

Response:

```json
{
  "error": {
    "code": "internal_server_error",
    "message": "An unexpected server error occurred.",
    "details": null,
    "request_id": "e0d413a5-12dd-44c6-b67f-f2fe80db78ab"
  }
}
```

Internal exception details and stack traces are not returned to the frontend. They are written to the backend logs instead.

When reporting a `500` error, provide:

- The `request_id`
- The endpoint
- The HTTP method
- The approximate time of the request

### File uploads

The backend accepts uploaded files of any file type.

There is currently no application-level file-size limit. The hosting environment, reverse proxy, Docker configuration, available disk space, or web server may still impose external request or storage limits.

Student study plans and appointment minutes support an optional display name. If no display name is provided, the original uploaded filename is used.

Replacing an attached document is transaction-safe at the database level. If the replacement cannot be completed, the previous document remains attached and the unsuccessful new upload is cleaned from storage.

If a database document record exists but its physical file is missing, the download endpoint returns:

```http
404 Not Found
```


## Appointment and availability rules

The application uses the `Europe/Berlin` timezone so counseling times follow German local time, including daylight-saving changes.

Counselor availability is represented by `Slot` records. Availability slots themselves may overlap.

Appointments are independent for each counselor. Appointments belonging to different counselors may occur at the same time.

Only active appointments occupy counselor availability:

- `pending`
- `booked`

The following statuses do not consume availability:

- `cancelled`
- `missed`
- `completed`

When creating or rescheduling an active appointment, the backend checks for another active appointment belonging to the same counselor whose time overlaps.

If an overlap is detected, the API returns:

```http
409 Conflict
```

with error code:

```text
appointment_overlap_warning
```

The response includes the conflicting appointments and:

```json
{
  "can_override": true,
  "override_field": "allow_overlap"
}
```

If the user confirms the overlap, repeat the create/update request with:

```json
{
  "allow_overlap": true
}
```

The `slot` field on an appointment is optional. This allows forced appointments or appointments outside normal counselor availability.

If a slot is supplied:

- the slot must belong to the same counselor as the appointment
- the appointment must fit completely inside the selected slot

Use `"slot": null` for appointments intentionally scheduled outside counselor availability.

The counselor slot-status endpoints calculate free/taken segments from active appointments:

```text
GET /api/counselors/{counselor_id}/slot-status/
GET /api/counselors/slot-status/
```

Cancelled, missed, and completed appointments are not returned as occupied availability.



## Templates

Templates use [Jinja2](https://jinja.palletsprojects.com/) syntax.

Each template is identified by a unique `purpose`. The purpose determines which variables are available while rendering.

### List templates

```http
GET /api/templates/
```

### Get one template

```http
GET /api/templates/{purpose}/
````

Example response for `counselor_availability_request`:

```json
[
  {"path": "counselor.first_name", "type": "string"},
  {"path": "counselor.last_name",  "type": "string"},
  {"path": "counselor.full_name",  "type": "string"},
  {"path": "counselor.department", "type": "string"},
  {"path": "counselor.slots",        "type": "array"},
  {"path": "counselor.slots[].date",       "type": "date"},
  {"path": "counselor.slots[].start_time", "type": "time"},
  {"path": "counselor.slots[].end_time",   "type": "time"}
]
```


Example:

```http
GET /api/templates/student_invitation/
```

### Template syntax

**Insert a variable:**

```
{{ counselor.full_name }}
```


### Update a template

```http
PUT /api/templates/{purpose}/update/
Content-Type: text/plain
```

The request body is the raw template text, not JSON.

Example:

```text
Dear {{ counselor.full_name }},

Your currently available times are:

{% for slot in counselor.slots %}
{{ slot.date }} {{ slot.start_time }} - {{ slot.end_time }}
{% endfor %}
```

### Discover available template variables

```http
GET /api/templates/{purpose}/context-schema/
```

### End-to-end example with "counselor_availability_request"

**1. Create the template** (`PUT /api/templates/create/`): this doesnt exist anymore

```json
{
  "name": "Test Availability Mail",
  "content": "Dear {{ counselor.full_name }},\n\nYour available slots:\n{% for block in counselor.availability_blocks %}\n  - {{ block.date }}  {{ block.start_time }} – {{ block.end_time }}\n{% endfor %}\n\nBest regards",
  "purposes": ["counselor_availability_request"]
}
```

Example:

```http
GET /api/templates/testmail/context-schema/
```

The response contains variable paths, their types, ready-to-use Jinja directives, and usage descriptions.

Example:

```json
[
  {
    "path": "counselor.full_name",
    "type": "string",
    "directive": "{{counselor.full_name}}",
    "description": "Can be placed to be replaced by the actual value."
  },
  {
    "path": "counselor.slots",
    "type": "array",
    "directive": "{% for slot in counselor.slots %}\n\n{% endfor %}",
    "description": "Place to iterate over the List"
  }
]
```

`counselor.slots` contains the counselor's currently free availability segments after active (`pending` and `booked`) appointments have been removed.

### Render a testmail preview

```http
POST /api/templates/testmail/render/
Content-Type: application/json
```

Request:
**2. Render a preview** (`POST /api/templates/generate/counselor_availability_request/?template_id={id}`): this doesnt exist anymore

```json
{
  "counselor_id": 1
}
```

Response:

```json
{
  "rendered": "Dear Dr. Jane Smith..."
}
```

Other purposes have their equivalent render endpoint:

```text
POST /api/templates/student_invitation/render/
POST /api/templates/student_reminder/render/
POST /api/templates/forced_appointment_assignment/render/
POST /api/templates/appointment_invitation/render/
POST /api/templates/counselor_preparation_instruction/render/
POST /api/templates/appointment_cancellation/render/
POST /api/templates/counselor_availability_request/render/
POST /api/templates/counselor_appointments_summary/render/
POST /api/templates/general_mail/render/
```

PDF templates use:

```text
POST /api/templates/study_plan/render/
POST /api/templates/appointment_minutes/render/
```

and return an `application/pdf` response.

## Email generation and delivery

The backend generates personalized emails using the template system and stores them before delivery.

### Email records

`EmailBatch` represents one email operation for a particular purpose.

`EmailDelivery` represents one generated email and may target:

- a student
- a counselor
- an external email address

Each delivery stores a snapshot of:

- recipient email
- CC addresses
- subject
- rendered body
- status

Changing the original template or student/counselor information later does not modify an already-generated delivery.

### Creating an email batch

```http
POST /api/mailing/batches/
```

For student/counselor purposes, use `target_ids`.

Example:

```json
{
  "purpose": "student_invitation",
  "target_ids": [1, 2],
  "send_immediately": false,
  "generated_pdf_purposes": [],
  "existing_document_types": [],
  "uploaded_files": [],
  "external_recipients": []
}
```

`generated_pdf_purposes` may contain multiple PDF templates. Each selected PDF is generated and attached to every applicable delivery.

For a general email to addresses outside the database, use:

```json
{
  "purpose": "general_mail",
  "target_ids": [],
  "external_recipients": [
    "person@example.com",
    "another@example.com"
  ],
  "send_immediately": false,
  "generated_pdf_purposes": [],
  "existing_document_types": [],
  "uploaded_files": []
}
```

General external emails support uploaded files. Student/appointment documents and generated student PDFs are unavailable because an external recipient has no student context.

### Listing saved batches

```http
GET /api/mailing/batches/
```

This returns all stored batches newest first, including their deliveries, statuses, recipient information, and attachment information.

The frontend should use this endpoint to restore the email dashboard after refresh instead of storing batch IDs only in browser storage.

### Email workflow

Email deliveries use these statuses:

- `draft` — generated for preview/editing
- `queued` — waiting for the background worker
- `sent` — accepted successfully by the configured SMTP backend
- `failed` — sending failed permanently or retry attempts were exhausted

Draft and failed deliveries may be edited.

A reviewed draft batch can be queued using:

```http
POST /api/mailing/batches/{batch_id}/send/
```

A failed individual delivery can be queued again using:

```http
POST /api/mailing/deliveries/{delivery_id}/resend/
```

### Background email worker

Queued emails are processed by:

```bash
python manage.py process_email_queue
```

In the Dev Container, this worker is started automatically by Supervisor together with the backend and frontend.

Only one email worker should run with the current database-backed queue implementation.

For manual development/testing, one ready email can be processed and the command can then exit:

```bash
python manage.py process_email_queue --once
```

### Retry behavior

Each sending cycle permits two attempts by default.

Temporary SMTP/network failures are scheduled for automatic retry.

Permanent SMTP failures become `failed` immediately.

After retry attempts are exhausted, a delivery becomes `failed` and may be inspected, edited, and manually resent.

### Email account settings

SMTP credentials and visible sender information can be configured from the application settings page.

Backend endpoints:

```text
GET    /api/mailing/settings/
PUT    /api/mailing/settings/
DELETE /api/mailing/settings/
POST   /api/mailing/settings/test/
```

Example update:

```json
{
  "smtp_host": "email.uni-rostock.de",
  "smtp_port": 587,
  "use_tls": true,
  "smtp_username": "university-user-id",
  "password": "password",
  "from_name": "Prof. Jane Smith",
  "from_email": "jane.smith@uni-rostock.de",
  "persist_credentials": true
}
```

The password is write-only and is never returned through the API.

Instead, the settings response contains:

```json
{
  "password_configured": true
}
```

When `persist_credentials` is `true`, the credentials are stored persistently and the password is encrypted before storage.

When `persist_credentials` is `false`, they are kept in temporary container runtime storage rather than in the database.

The SMTP connection can be tested without sending an email:

```http
POST /api/mailing/settings/test/
```

Successful response:

```json
{
  "ok": true
}
```

### Email sender headers

Outgoing messages use the configured sender name and email address:

```text
From: Prof. Jane Smith <jane.smith@uni-rostock.de>
Reply-To: jane.smith@uni-rostock.de
```

The SMTP username is used for authentication and does not need to be the visible sender name.

The application uses Django's SMTP email backend by default.

### Frontend status polling

The frontend may poll:

```text
GET /api/mailing/batches/{batch_id}/status/
```

while a batch is being processed.

The response includes:

- total deliveries
- draft count
- queued count
- sent count
- failed count
- individual delivery statuses

Polling every few seconds while the mail page is open is sufficient. WebSockets are not required for the current application.