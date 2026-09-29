# Consultation Minutes

### Participants

{% textbox label="Student" lines=1 value=student.full_name %}
{% textbox label="Counselor" lines=1 value=counselor.full_name %}

### Appointment Details

| Name     | Value                                                     |
| -------- | --------------------------------------------------------- |
| Date     | {{ appointment.date }}                                    |
| Time     | {{ appointment.start_time }} - {{ appointment.end_time }} |
| Location | {{ appointment.location }}                                |

### Discussion Points

{% textbox label="Topics Discussed" lines=10 %}

### Agreed Next Steps

{% textbox label="Next Steps" lines=10 %}

{% vspace lines=3 %}

Date, Place {% textfield %}

{% signature label="Signature Student" %}
{% signature label="Signature Counselor" %}
