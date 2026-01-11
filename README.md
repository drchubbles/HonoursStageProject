# Honours Stage Project
This Repository will be used as a way to monitor the progression of my Honours Stage Project. It will have regular pushes to show the slow progression of code.

## Progression
Below I have noted down my milestones and places an X in the columns where they have been completed

Areas that have been completed are noted down with an **x**, areas that still need working on are marked with an **o** and areas that are waiting on somwthing before being able to progressed are noted with a **-**

|  | Overarching Goal| What This Cover(Summary)| Related Milestone(s)|
| - | -------- | -------- | -------- |
| x | **Project Planning & Research**| Defining the project scope, reviewing relevant literature, surveying available technologies, and selecting the final technology stack. | Milestone 1 – Project Initiation|
| x | **System & UX Design**| Designing the user experience and system architecture, including UI sketches, wireframes, database schema, personas, and stakeholder validation. | Milestone 2 – Early Prototyping |
| - | **Prototype Creation & Validation** | Creating interactive prototypes, defining form questions, generating mock/sample data, and validating designs with the Data Admin team.| Milestone 3 – Prototyping/Design|
| x | **Core Forms Functionality Development** | Building the database, forms UI, form-question integration, edit functionality, feedback system, and validating correct form behavior.| Milestone 4 – Forms Section|
| x | **Authentication & Admin Controls**| Implementing admin login, role-based permissions, and restricting sensitive actions (e.g., editing questions) to administrators.| Milestone 5 – Admin Profiles|
| o | **Dashboard & Data Visualization**| Developing dashboards, visual data displays, charts, and systems to highlight recurring issues for staff.| Milestone 6 – Dashboard|
|  | **Enhancement & Polish (Optional)**| Adding “nice-to-have” features, usability improvements, and refinements if time allows.| Post-Milestone / Stretch Goals|

This code is done using pylance. In order to ensure it works properly please clone the repositoy and following that, use the SQL scripts provided to create the database. Then ensure you have the packets necissary installed to run the code by running:

```
pip install flask flask-sqlalchemy werkzeug
```
In terminal on VS code then run **This is to set up the server and make it work as it stands  -I hope to develop a .bat or script to avoid these steps but as it is not yet developed I will include the required code below**
```
pip install virtualenv 

virtualenv env

.\env\Scripts\activate.bat

```

following this use cd to enter the correct folder where the code is and run python app.py

then navigate to [here](http://127.0.0.1:5000/) to see the sytem up and working. *Just to be clear, once this application is actually up and running it will be on its own dedicated server.

