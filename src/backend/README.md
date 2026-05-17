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