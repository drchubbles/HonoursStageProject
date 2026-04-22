# Honours Stage Project
This repository contains the code for my Honours Stage Project. The system has been designed as an internal auditing/review application for handling forms, submissions, dashboard reporting, account management, and related administrative processes. I have tried to keep the structure practical for real internal use.

It is intended to be run on an **internal server** within an organisation rather than exposed directly to the public internet. During development it can be run locally using `127.0.0.1:5000`, but the intended production-style use is from a dedicated internal machine/server on a private network.

## Progression
Below, I have noted down the main areas of the project and how they relate to the milestone structure.

Areas that have been completed are noted down with an **x**, areas that still need working on are marked with an **o**, and areas that are waiting on something before being able to progress are noted with a **-**.

|  | Overarching Goal | What This Covers (Summary) | Related Milestone(s) |
| - | -------- | -------- | -------- |
| x | **Project Planning & Research** | Defining the project scope, reviewing relevant literature, surveying available technologies, and selecting the final technology stack. | Milestone 1 – Project Initiation |
| x | **System & UX Design** | Designing the user experience and system architecture, including UI sketches, wireframes, database schema, personas, and stakeholder validation. | Milestone 2 – Early Prototyping |
| x | **Prototype Creation & Validation** | Creating interactive prototypes, defining form questions, generating mock/sample data, and validating designs with the Data Admin team. | Milestone 3 – Prototyping/Design |
| x | **Core Forms Functionality Development** | Building the database, forms UI, form-question integration, edit functionality, feedback system, and validating correct form behaviour. | Milestone 4 – Forms Section |
| x | **Authentication & Admin Controls** | Implementing login, role-based permissions, secure account handling, and restricting sensitive actions to authorised users. | Milestone 5 – Admin Profiles |
| x | **Dashboard & Data Visualisation** | Developing dashboards, charts, summary cards, and reporting tools to highlight recurring issues and submission trends. | Milestone 6 – Dashboard |
| x | **Enhancement & Polish (Optional)** | Adding additional quality-of-life features, usability improvements, and final refinements where time allowed. | Post-Milestone / Stretch Goals |

## Intended deployment
This application is intended to be hosted on an **internal server** for organisational use.

In practice, this means:
- the database should sit on an internal MySQL instance
- the Flask application should run on an internal workstation or server
- access should be limited to authrorised staff on the local/internal network
- the system should not be treated as a public-facing web application without further hardening and deployment work

For development and testing, the application can be run locally and opened through:

`http://127.0.0.1:5000/`

For internal deployment, the same codebase can be hosted on a dedicated machine and made available through an internal hostname or server address.

## Main technologies and libraries used
This project is built primarily in Python using Flask.

### Core backend libraries
- **Flask** – web framework used for routing, request handling, template rendering, sessions, redirects, flashing messages, and JSON responses
- **Flask-SQLAlchemy** – ORM integration between Flask and the database layer
- **SQLAlchemy** – model definitions and relational data handling
- **PyMySQL** – MySQL database driver used in the SQLAlchemy connection string
- **Werkzeug** – password hashing/checking and secure filename handling
- **Jinja templates** – server-side HTML rendering through Flask templates

### Python standard library features used
Examples include:
- `os` for enviroment/configuration handling
- `json` for state/config payloads
- `uuid` for generated keys and unique values
- `re` for text normalisation/validation
- `secrets` and `hashlib` for token/security-related logic
- `datetime` for expiry windows, timestamps, and date-based logic
- `collections` for counters and aggregated statistics

### Internal project modules
- `config.py` – central configuration values
- `email_delivery.py` – email delivery strategy handling
- `local_summary.py` – local submission summariser handling

### Front-end / UI
The application uses Flask-rendered HTML templates and associated static assets. It is intended to be lightweight and server-rendered rather than heavily client-framework based.

## Technical overview
This project is more than a simple form app. It has been structured to support changing forms, secure account handling, reporting, and audit-style traceability.

### Main technical aspects
- **Role-based access control** for admin, standard, and developer users
- **Versioned forms and questions**, allowing the structure of forms to change over time without losing historic submission integrity
- **Branching logic** so that questions can appear or change behaviour depending on previous answers
- **Submission storage** that links answers back to the correct form version
- **Dashboard/statistics processing** for identifying recurring themes, trends, and common issues
- **Built-in local summariser** that generates internal summaries without sending data to an external AI service
- **Email handling layer** that supports submission-related notifications through a delivery strategy
- **Self-checking database/schema logic** to help keep expected database structures in place
- **Security/account setup flows** including password hashing, one-time codes/tokens, and security-question-based recovery

The application also includes logic for form versioning, account control, submission summaries, and dashboard reporting, which helps show that the project is not just a simple single-form website. This is somtimes useful when explaining the technical depth of the work.

## Database and data structure
A relational MySQL database is used for the application.

The codebase is structured around entities such as:
- roles
- users
- forms
- form versions
- questions
- question versions
- form version questions
- branching rules
- submissions
- submission answers
- user setup tokens
- user security questions

This allows the system to preserve previous versions of forms and still correctly display or analyse historic submissions against the version that was active at the time.

## Setup guide
To run the product successfully, a database management system is required. In this project, **MySQL Workbench** is used to manage the database and execute the SQL setup scripts.

### 1. Clone or copy the repository
Place the project onto the target machine/server.

### 2. Create the database
The recommended setup process is to first run:

`PyFlask Access.sql`

This creates the database and access user.

Then run:

`QuickSetUp.sql`

This removes any existing tables, creates the latest version of the schema, applies the bootstrap setup, and inserts the initial form data required by the application.

### 3. Alternative manual SQL order
If the database is being built manually rather than through the quick setup script, run the SQL files in this order:

1. `PyFlask Access.sql`
2. `Table Creation.sql`
3. `BootstrapAccounts.sql`
4. `SettingRoles.sql`
5. `MockFormForBuilding.sql`

### 4. Install Python dependencies
Install the Python libraries required by the project on the target machine/environment.

Typical libraries used by the application include:
- `flask`
- `flask-sqlalchemy`
- `pymysql`
- `werkzeug`

If a `requirements.txt` file is present, install from that. Otherwise install the required packages manually into the Python environment being used to run the application.

It is also good practice to keep the Python version and package versions consistent across development and deployment machines so that behaviour remains stable and easier to troubleshoot. I have also found this makes later maintenance much easier.

### 5. Configure environment values
Before running on a real internal machine/server, configure the database connection values so the application does not rely on local defaults.

The application reads:
- `DB_USER`
- `DB_PASS`
- `DB_HOST`
- `DB_PORT`
- `DB_NAME`

If email integration is being used, the Microsoft Graph related values must also be configured in the target environment/configuration.

### 6. Install any remaining dependancies
If the target machine has not been used for the project before, make sure all required libraries, drivers, and supporting packages are installed before starting the application.

### 7. Run the application
Once the database and environment are ready, run:

`Run_app.bat`

This starts the Flask application on the target machine.

### 8. Open the system
For local development, navigate to:

`http://127.0.0.1:5000/`

For internal-server use, open the internal hostname/address configured for the server.

## Email delivery
The system includes an email-delivery layer for submission-related notifications.

This is designed so that the application can still function even when live email credentials are not yet available. In development or marking scenarios, a mock/dummy email strategy can be used. In an internal deployment, the real delivery method should be configured through the application settings/environment.

## Local summariser
The project includes a built-in local summariser that generates a short submission summary inside the Flask application after a form is saved.

The summariser:
- only uses saved question/answer data already held within the application
- does not scrape the page
- does not send submission data to an external AI service
- stores the generated summary on the submission record so it can be shown later in the system

The summariser can be controlled with environment variables:
- `LOCAL_SUMMARY_MODE=rule_based` keeps the built-in local summariser enabled
- `LOCAL_SUMMARY_MODE=disabled` turns summary generation off
- `LOCAL_SUMMARY_MODEL_NAME` changes the stored model label
- `LOCAL_SUMMARY_MAX_DETAIL_CHARS` controls how much free-text detail is kept in the summary

## Security and operational notes
This project includes several security-related features, but it is still intended to be operated in a controlled internal environment.

Examples of implemented/security-relevant features include:
- password hashing
- role-based permissions
- token-based setup/reset flows
- security question recovery
- session-based access control
- controlled account creation and management

Even though the application is intended for internal use, normal good practice should still be followed:
- use strong database credentials
- avoid hard-coded production secrets
- restrict who can access teh server
- back up the database regularly
- test changes before deploying updates to the live internal system

## Maintenance guide
To maintain the project over time, the following areas are likely to need the most attention.

### Database maintenance
- keep SQL setup scripts aligned with the current application schema
- back up the database before applying major changes
- test schema updates before using them on a live internal copy

### Application maintenance
- review any changes to forms, questions, and branching rules carefully
- test role permissions after account-related changes
- test submission saving, summary generation, and email behaviour after updates
- keep configuration values appropriate for the target internal environment

### Server maintenance
- ensure Python and the required packages remain installed on the host machine
- keep the internal machine/server patched and access-restricted
- monitor logs/errors when updating the system

### Recommended testing after changes
After any meaningful update, it is recommended to test:
- login/logout
- account creation / setup flow
- password reset flow
- form completion and submission
- dashboard/statistics loading
- branching behaviour
- email preview / email sending behaviour
- summary generation
- role-restricted pages such as admin/developer features

## Suggested structure for future improvements
Potential future improvements could include:
- more formal server deployment documentation
- a full `requirements.txt` and version-pinned dependencies
- automated tests for key workflows
- stronger production deployment configuration
- reverse proxy / WSGI hosting documentation
- fuller audit logging and operational monitoring

This would also help reccomend a clearer long-term deployment and maintenance approach if the system were to continue being used beyond the project itself.
