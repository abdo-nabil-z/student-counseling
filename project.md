# Project Description

### Introduction

Many students face challenging circumstances that can negatively affect their academic progress. The University of Rostock offers a range of support programs to assist these students. One such program is academic counseling, which helps students better structure and manage their studies.

Academic counseling is typically offered to students who have accumulated delays in their study progress. To be effective, counseling sessions should take place at the beginning of a semester, allowing sufficient time for improvements within that term.

The study office identifies students who require counseling. Based on the number of students, an appropriate number of professors are asked to provide counseling time slots within the first two to three weeks of the semester. Students are then contacted via email and invited to select a suitable time slot.

In addition, students are required to prepare a draft study plan for up to the next four semesters and submit it prior to the counseling session. Once a session is confirmed, the counselor receives the study plan, an optional transcript of records or a previous study plan, and a standardized form for documenting the session.

During the session, the counselor records the outcome, typically an adjusted study plan, using the provided form. Afterward, the completed minutes are collected and eventually submitted to the study office where they are added to the student's official record.


### Functional Requirements

The coordination and management of this process currently involve a significant amount of manual effort. The goal of this project is to provide automation and technical support. This should address the following aspects:

* Management of Counselors, Time Slots, and Students
  * Create and manage counseling time slots
  * Assign available time slots to students
  * List available and booked slots

* Email Communication
  * Send invitation emails to students with available time slots
  * Generate emails from predefined templates
  * Send reminder emails to students who have not selected a time slot

* PDF Generation for Counseling Minutes
  * Generate PDF documents from templates
  * Pre-fill PDFs with relevant data (date, time, student and counselor names)
  * Include interactive form fields (checkboxes, text inputs)
  * Support both digital completion and printing
  * Enable electronic signatures via Adobe Acrobat by one click!

* Event Management
  * Upload student study plans
  * Convert text input (for a study plan) into PDF format
  * Send calendar invitations to students and counselors
  * Distribute relevant documents (study plan, transcript, minutes form) to counselors

* Collection and Processing of Minutes
  * Upload completed counseling minutes
  * Compile and forward reports to the study office


### Technical Requirements

* Backend implemented in Python
* PDF generation with support for electronically signable forms (e.g., using AcroTeX)
* Containerization using Docker
* Logging and backup functionality
* Asynchronous processing for tasks such as email sending and PDF generation
* Deployment on a local environment (localhost)


### Project Tasks

#### Infrastructure and Collaboration

* Use the university Git service: https://git.informatik.uni-rostock.de/
  (A valid department account is required: https://www.informatik.uni-rostock.de/en/it-service/information/user-account/)
* Important: Work that is not committed and pushed to the repository is considered non-existent.
* Establish team communication channels. Available services include:
  * Email: https://email.uni-rostock.de
  * Chat: https://chatspace.uni-rostock.de
  * Video conferencing via BigBlueButton in Stud.IP
  * File sharing and collaborative office: https://unibox.uni-rostock.de
  * Collaborative LaTeX: https://overleaf.uni-rostock.de


#### Team Organization

* Define a clear team structure
* Assign a meeting speaker/moderator for each session
* Ensure every team member actively contributes and presents progress during the semester
* Possible approaches include rotating speakers or shared presentation responsibilities


#### Development Setup

* Familiarize yourselves with Docker: https://www.docker.com/
  * Build and run example containers
  * You may use WSL2 if working on Windows
* Set up your development environment:
  * Native Linux, virtual machine (e.g., https://www.virtualbox.org/), or WSL2
* Configure your IDE for local and remote development if needed
  * Example: Visual Studio Code Remote Development: https://code.visualstudio.com/docs/remote/remote-overview


#### Project Execution

* Agree on a common technology stack
  * Test it before making final decisions
* Develop a conceptual design of the application
* Make interviews to query missing information and document the results
* Define a detailed task breakdown and assign responsibilities to team members
* Clearly indicate which tasks are assigned to whom by the end of the lecture period


#### To be continued

* Don't be surprised if there are more tasks to come...