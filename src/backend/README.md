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
      "email": [
        "Enter a valid email address."
      ]
    },
    "request_id": "e0d413a5-12dd-44c6-b67f-f2fe80db78ab"
  }
}
```

### Error response fields

* `code`: A machine-readable error identifier that the frontend can use when handling specific errors.
* `message`: A general human-readable description of the error.
* `details`: Additional information about the error. For validation errors, this normally contains errors grouped by field. It may be `null` when no additional information is available.
* `request_id`: A unique identifier for the request. Include this value when reporting an unexpected server error so the related backend log entry can be located.

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
      "name": [
        "This field is required."
      ]
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
    "code": "not_found",
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

* The `request_id`
* The endpoint
* The HTTP method
* The approximate time of the request


### File uploads

The backend accepts uploaded files of any file type.

There is currently no application-level file-size limit. The hosting environment, reverse proxy, Docker configuration, available disk space, or web server may still impose external request or storage limits.

Student study plans and appointment minutes support an optional display name. If no display name is provided, the original uploaded filename is used.

Replacing an attached document is transaction-safe at the database level. If the replacement cannot be completed, the previous document remains attached and the unsuccessful new upload is cleaned from storage.

If a database document record exists but its physical file is missing, the download endpoint returns:

```http
404 Not Found


## Templates

Templates use [Jinja2](https://jinja.palletsprojects.com/) syntax. Each template is linked to a **purpose**, which defines exactly which variables are available when the template is rendered.

### Discovering available variables

Before writing a template, fetch the flat variable list for the purpose:

```
GET /api/templates/purposes/{purpose}/context-schema/
```

Example response for `testmail`:

```json
[
  {"path": "counselor.first_name", "type": "string"},
  {"path": "counselor.last_name",  "type": "string"},
  {"path": "counselor.full_name",  "type": "string"},
  {"path": "counselor.department", "type": "string"},
  {"path": "counselor.availability_blocks",        "type": "array"},
  {"path": "counselor.availability_blocks[].date",       "type": "date"},
  {"path": "counselor.availability_blocks[].start_time", "type": "time"},
  {"path": "counselor.availability_blocks[].end_time",   "type": "time"}
]
```

### Template syntax

**Insert a variable:**

```
{{ counselor.full_name }}
```

**Conditional block:**

```
{% if counselor.availability_blocks %}
  ...
{% endif %}
```

**Loop over a list** — use any loop variable name; access its fields with dot notation:

```
{% for block in counselor.availability_blocks %}
  {{ block.date }}  {{ block.start_time }} – {{ block.end_time }}
{% endfor %}
```

### End-to-end example with "testmail"

**1. Create the template** (`PUT /api/templates/create/`):

```json
{
  "name": "Test Availability Mail",
  "content": "Dear {{ counselor.full_name }},\n\nYour available slots:\n{% for block in counselor.availability_blocks %}\n  - {{ block.date }}  {{ block.start_time }} – {{ block.end_time }}\n{% endfor %}\n\nBest regards",
  "purposes": ["testmail"]
}
```

Note the `id` in the response.

**2. Render a preview** (`POST /api/templates/generate/testmail/?template_id={id}`):

```json
{
  "counselor": 1
}
```

Response:

```json
{
  "rendered": "Dear Dr. Jane Smith,\n\nYour available slots:\n\n  - 2026-06-10  09:00:00 – 09:30:00\n  - 2026-06-10  10:00:00 – 10:30:00\n\nBest regards"
}
```
