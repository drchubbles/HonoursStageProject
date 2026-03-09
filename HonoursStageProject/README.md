# Honours Stage Project
This Repository will be used to monitor the progress of my Honours Stage Project. It will have regular pushes to show the slow progression of code.

## Progression
Below, I have noted down my milestones and placed an X in the columns where they have been completed

Areas that have been completed are noted down with an **x**, areas that still need working on are marked with an **o** and areas that are waiting on somwthing before being able to progress are noted with a **-**

|  | Overarching Goal| What This Cover(Summary)| Related Milestone(s)|
| - | -------- | -------- | -------- |
| x | **Project Planning & Research**| Defining the project scope, reviewing relevant literature, surveying available technologies, and selecting the final technology stack. | Milestone 1 – Project Initiation|
| x | **System & UX Design**| Designing the user experience and system architecture, including UI sketches, wireframes, database schema, personas, and stakeholder validation. | Milestone 2 – Early Prototyping |
| x | **Prototype Creation & Validation** | Creating interactive prototypes, defining form questions, generating mock/sample data, and validating designs with the Data Admin team.| Milestone 3 – Prototyping/Design|
| x | **Core Forms Functionality Development** | Building the database, forms UI, form-question integration, edit functionality, feedback system, and validating correct form behavior.| Milestone 4 – Forms Section|
| x | **Authentication & Admin Controls**| Implementing admin login, role-based permissions, and restricting sensitive actions (e.g., editing questions) to administrators.| Milestone 5 – Admin Profiles|
| x | **Dashboard & Data Visualization**| Developing dashboards, visual data displays, charts, and systems to highlight recurring issues for staff.| Milestone 6 – Dashboard|
|  | **Enhancement & Polish (Optional)**| Adding “nice-to-have” features, usability improvements, and refinements if time allows.| Post-Milestone / Stretch Goals|

This code is done using PyFlare. To ensure it works properly, please clone the repository and then use the provided SQL scripts to create the database. Then ensure you have the packets necissary installed to run the code by running:

To run the product successfully, a database management system is required. In this project, **MySQL Workbench** is used to manage the database and execute the SQL setup scripts. These scripts must be run in the correct order so that the database structure, user accounts, roles, and initial form data are created properly.

The recommended setup process is to first run `PyFlask Access.sql`, which creates the database and access user, and then run `QuickSetUp.sql`, which removes any existing tables, creates the latest version of the schema, applies the bootstrap setup, and inserts the initial form data required by the application.

Alternatively, if the database is being built manually rather than through the quick setup script, the SQL files should be run in the following order: `PyFlask Access.sql`, `Table Creation.sql`, `BootstrapAccounts.sql`, `SettingRoles.sql`, and `MockFormForBuilding.sql`.

Once this setup is complete, the user should run the `Run_app.bat` file from the project folder to launch the product.

Then navigate to [here](http://127.0.0.1:5000/) (localhost) to see the system up and working. *Just to be clear, once this application is actually up and running it will be on its own dedicated server.*

