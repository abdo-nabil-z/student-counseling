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
