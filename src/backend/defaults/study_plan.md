# Study Plan

### Student

{% textbox label="Name" lines=1 value=student.full_name %}
{% textbox label="Matriculation Number" lines=1 value=student.matriculation_number %}

#### Current Study Status

| Name                         | Value                                  |
| ---------------------------- | -------------------------------------- |
| Amount of absolved Semesters | {{student.current_study_semester - 1}} |
| Acquired Credit Points       | {{student.credit_points}}              |

### Planned Courses

In the following field, please enter the planned courses in the correct order, grouping by semester and annotated with obtained Credit Points.
{% textbox label="Planned Courses" lines=20 %}
{% vspace lines=5 %}
{% textbox label="Notes and Comments" lines=30 %}

{% vspace lines=5 %}

{% checkbox value=true %}This version of the plan is binding and not a draft.

Date, Place {% textfield %}

{% signature label="Signature Student" %}
