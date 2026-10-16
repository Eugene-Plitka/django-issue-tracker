# Django Issue Tracker — Project Guide

## 1. About the Project

Django Issue Tracker is a portfolio project that demonstrates how to build a practical issue tracking application with Django.

The application is inspired by tools such as Jira but intentionally keeps the scope smaller and focused on backend architecture, permissions, database design, testing, Docker, CI, and production preparation.

The application supports multiple Workspaces. Each Workspace contains Projects, and Projects contain Issues.

The project uses a custom user model where email is used for authentication instead of a username.

---

## 2. Main Features

### Authentication

The application supports:

- registration with email and password;
- login with email and password;
- logout;
- password reset;
- Google OAuth login;
- GitHub OAuth login;
- social account linking.

The custom user model uses:

```text
email
```

as the login identifier.

No username is required.

---

## 3. Workspaces

A Workspace is the top-level container of the application.

A user may belong to multiple Workspaces.

Each Workspace contains:

- members;
- roles;
- Projects.

A new Workspace creator becomes an Owner.

### Workspace roles

The application uses four roles:

- Owner
- Manager
- Developer
- Viewer

### Owner

Owner has full control of the Workspace.

Owner can:

- edit Workspace settings;
- manage Workspace members;
- assign roles;
- add other Owners;
- create and manage Projects;
- manage Project members;
- create, edit, and delete Issues;
- create Labels;
- add Comments.

The last Owner cannot be removed or demoted.

### Manager

Manager can:

- manage regular Workspace members;
- create and update Projects;
- manage Project members;
- create, edit, and delete Issues;
- create Labels;
- add Comments.

Manager cannot:

- edit Workspace settings;
- assign the Owner role;
- remove an Owner.

### Developer

Developer can access only Projects where a ProjectMembership exists.

Developer can:

- view accessible Projects;
- view Issues;
- create Issues;
- add Comments;
- update allowed Issue fields;
- assign an Issue to themselves.

Developer has more restricted editing permissions than Owner and Manager.

### Viewer

Viewer can access only Projects where a ProjectMembership exists.

Viewer can:

- view Projects;
- view Issues;
- view Labels;
- view Activity history;
- add Comments.

Viewer cannot:

- create Issues;
- edit Issues;
- delete Issues;
- manage Projects;
- manage members;
- create Labels.

---

## 4. Projects

Each Project belongs to one Workspace.

Project fields include:

- name;
- key;
- description;
- next issue number.

Project keys are unique inside a Workspace.

Example Project key:

```text
BACK
```

Issues in that Project may use identifiers such as:

```text
BACK-1
BACK-2
BACK-3
```

Owner and Manager automatically have access to all Projects in their Workspace.

Developer and Viewer require ProjectMembership.

---

## 5. Issues

Each Issue belongs to one Project.

Issue fields include:

- number;
- title;
- description;
- status;
- priority;
- reporter;
- assignee;
- labels;
- created timestamp;
- updated timestamp.

### Statuses

Available statuses:

```text
To Do
In Progress
Done
```

### Priorities

Available priorities:

```text
Low
Medium
High
Critical
```

### Issue numbering

Issue numbers are generated per Project.

The application stores the next number in:

```text
Project.next_issue_number
```

Issue creation uses a database transaction and row locking to safely generate the next number.

---

## 6. Labels

Labels belong to a Project.

Label names are unique inside each Project.

Owner and Manager can create Labels.

Users with Project access can view Labels.

---

## 7. Comments

Users with access to a Project can add Comments to its Issues.

This includes:

- Owner;
- Manager;
- Developer;
- Viewer.

Each Comment stores:

- Issue;
- author;
- body;
- created timestamp;
- updated timestamp.

Comment creation also produces an Activity record.

---

## 8. Activity History

The application stores Issue activity history.

Examples include:

- Issue created;
- status changed;
- priority changed;
- assignee changed;
- comment added.

Activity is visible to users who can access the Issue.

---

## 9. Filtering, Search, and Sorting

The Issue list supports filtering by:

- status;
- priority;
- assignee;
- label.

Search supports Issue fields such as:

- Issue key;
- title;
- description;
- Project key.

Sorting supports:

- created time;
- updated time;
- status;
- priority.

The interface includes JavaScript for:

- automatic select-filter submission;
- debounced search.

---

## 10. Technology Stack

Main technologies:

- Python 3.14
- Django 6.1
- django-allauth
- PostgreSQL
- HTML
- CSS
- JavaScript
- Docker
- Docker Compose
- Gunicorn
- WhiteNoise
- Ruff
- GitHub Actions

---

## 11. Project Structure

```text
django-issue-tracker/
├── accounts/
├── config/
├── docs/
│   ├── screenshots/
│   └── PROJECT_GUIDE.md
├── issues/
├── projects/
├── static/
├── templates/
├── workspaces/
├── .env.example
├── .env.prod.example
├── compose.prod.yml
├── docker-compose.yml
├── Dockerfile
├── LICENSE
├── manage.py
├── pyproject.toml
├── README.md
└── requirements.txt
```

### Django applications

#### accounts

Responsible for:

- custom User model;
- authentication foundation.

#### workspaces

Responsible for:

- Workspace;
- WorkspaceMembership;
- Workspace permissions;
- member management.

#### projects

Responsible for:

- Project;
- ProjectMembership;
- Project permissions.

#### issues

Responsible for:

- Issue;
- Label;
- Comment;
- Activity;
- Issue services;
- Issue permissions.

---

## 12. Installation

### Requirements

You need:

- Docker;
- Docker Compose;
- Git.

Clone the repository and open the project directory.

### Step 1 — Create the development environment file

On Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

The development `.env` contains values for:

- Django secret key;
- debug mode;
- allowed hosts;
- PostgreSQL;
- email backend;
- Google OAuth;
- GitHub OAuth.

Real secrets must not be committed to Git.

### Step 2 — Build and start containers

```powershell
docker compose up --build
```

The application will be available at:

```text
http://localhost:8000
```

### Step 3 — Apply migrations

```powershell
docker compose exec web python manage.py migrate
```

### Step 4 — Create a superuser if needed

```powershell
docker compose exec web python manage.py createsuperuser
```

### Step 5 — Create portfolio demo data

```powershell
docker compose exec web python manage.py seed_demo
```

The command resets the demo database content and creates a portfolio-ready data set.

---

## 13. Demo Data

The demo seed command keeps or creates exactly these four demo users:

```text
owner@example.com
manager@example.com
developer@example.com
viewer@example.com
```

Password for all four accounts:

```text
test12345
```

The command removes other users and all existing Workspace-related demo data before rebuilding the sample application state.

### Demo Workspaces

The seed command creates:

```text
Northstar Commerce
Atlas Internal Platform
```

It also creates multiple Projects, Issues, Labels, Comments, Activity records, and different Issue statuses and priorities.

`owner@example.com` is Owner in both Workspaces.

The other users are assigned their matching roles:

```text
manager@example.com   -> Manager
developer@example.com -> Developer
viewer@example.com    -> Viewer
```

Project memberships are created so Developer and Viewer permissions can be demonstrated.

One Project intentionally excludes Viewer access to demonstrate Project-level restrictions.

### Important

The seed command is destructive for demo data.

Do not run it against a production database containing real user or business data.

---

## 14. Google OAuth Setup

The project uses `django-allauth`.

Add these variables to `.env`:

```env
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
```

Create a Google OAuth Web application.

For local development, configure a callback URL such as:

```text
http://localhost:8000/accounts/google/login/callback/
```

Use the same host in the browser and OAuth configuration.

Do not commit real OAuth secrets.

---

## 15. GitHub OAuth Setup

Add these variables to `.env`:

```env
GITHUB_CLIENT_ID=
GITHUB_CLIENT_SECRET=
```

Create a GitHub OAuth App.

For local development, use:

```text
http://localhost:8000/accounts/github/login/callback/
```

The callback URL must match the host used to open the application.

Do not commit real OAuth secrets.

---

## 16. Password Reset

The application supports password reset through `django-allauth`.

In local development the default setup uses the console email backend.

Reset emails are therefore printed to container logs instead of being sent to a real mailbox.

Use:

```powershell
docker compose logs web --tail=300
```

to find the reset email.

Because console output may use quoted-printable encoding, a long URL can be split across lines. A trailing `=` at the end of a line means that the URL continues on the next line and the `=` itself is not part of the token.

---

## 17. Testing

Run the full Django test suite:

```powershell
docker compose exec web python manage.py test
```

Run Ruff:

```powershell
docker compose exec web ruff check .
```

Run Django checks:

```powershell
docker compose exec web python manage.py check
```

The test suite covers:

- models;
- permissions;
- Workspace access;
- Project access;
- Issue access;
- Issue creation and editing;
- Comments;
- labels;
- role restrictions;
- authentication;
- registration;
- login;
- password reset page availability;
- social login routes.

---

## 18. Continuous Integration

GitHub Actions runs automatically on pushes and pull requests.

The CI pipeline performs:

- dependency installation;
- Ruff checks;
- static file collection;
- Django tests using PostgreSQL.

---

## 19. Production Preparation

The repository contains production-oriented configuration for:

- Gunicorn;
- WhiteNoise;
- PostgreSQL;
- environment-based Django settings;
- Docker Compose production overrides;
- static file collection;
- secure cookie settings;
- HTTPS-related Django settings;
- HSTS settings;
- production email configuration;
- OAuth credentials through environment variables.

Production deployment is intentionally not performed until the final project stage.

---

## 20. Production Environment

The repository contains:

```text
.env.prod.example
compose.prod.yml
```

Create a private production environment file from `.env.prod.example`.

Production secrets must never be committed.

Typical production configuration includes:

- real `SECRET_KEY`;
- production domain in `ALLOWED_HOSTS`;
- `CSRF_TRUSTED_ORIGINS`;
- PostgreSQL credentials;
- SMTP credentials;
- Google OAuth credentials;
- GitHub OAuth credentials;
- HTTPS security settings.

---

## 21. Static Files

Static files are handled with WhiteNoise.

Production collection:

```powershell
docker compose exec web python manage.py collectstatic --noinput
```

`staticfiles/` is generated output and should not be committed.

---

## 22. Useful Commands

Start development environment:

```powershell
docker compose up
```

Rebuild:

```powershell
docker compose up --build
```

Stop containers:

```powershell
docker compose down
```

Run migrations:

```powershell
docker compose exec web python manage.py migrate
```

Run Django checks:

```powershell
docker compose exec web python manage.py check
```

Run tests:

```powershell
docker compose exec web python manage.py test
```

Run Ruff:

```powershell
docker compose exec web ruff check .
```

Create demo data:

```powershell
docker compose exec web python manage.py seed_demo
```

View logs:

```powershell
docker compose logs web --tail=200
```

---

## 23. Demo Login

For a portfolio demonstration, the easiest accounts to use are:

### Owner

```text
Email: owner@example.com
Password: test12345
```

Use this account to demonstrate:

- Workspace management;
- Project management;
- member management;
- Issue management;
- Labels;
- Comments;
- Activity.

### Manager

```text
Email: manager@example.com
Password: test12345
```

Use this account to demonstrate Manager restrictions.

### Developer

```text
Email: developer@example.com
Password: test12345
```

Use this account to demonstrate ProjectMembership-based access and restricted Issue editing.

### Viewer

```text
Email: viewer@example.com
Password: test12345
```

Use this account to demonstrate read-oriented access, comments, and Project-level access restrictions.

---

## 24. Notes About Data Safety

The following files should remain private:

```text
.env
.env.prod
.env.prod.local
```

Never commit:

- production secret keys;
- database passwords;
- SMTP passwords;
- Google client secrets;
- GitHub client secrets.

The demo password `test12345` is intended only for the generated portfolio demo accounts.

---

## 25. License

This project is intended to be distributed under the MIT License.

See the [`LICENSE`](../LICENSE) file for the full license text.
