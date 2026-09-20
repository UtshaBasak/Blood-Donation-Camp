# Blood Donation Camp

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-5.1-092E20?logo=django&logoColor=white)](https://www.djangoproject.com/)
[![MySQL](https://img.shields.io/badge/MySQL-8.0-4479A1?logo=mysql&logoColor=white)](https://www.mysql.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A Django blood bank management system that connects donors, recipients and branch blood
banks across Dhaka. Members search live branch stock for the blood group they need and
reach volunteer donors directly; branch managers record every bag collected and issued
against an auditable ledger.

Built as a CSE370 (Database Systems) course project, with the relational schema — not the
framework — as the centrepiece.

---

## Table of contents

- [Features](#features)
- [Tech stack](#tech-stack)
- [Data model](#data-model)
- [Getting started](#getting-started)
- [First-run configuration](#first-run-configuration)
- [Running the tests](#running-the-tests)
- [URL reference](#url-reference)
- [Project structure](#project-structure)
- [Configuration reference](#configuration-reference)
- [Security notes](#security-notes)
- [Roadmap](#roadmap)
- [License](#license)

---

## Features

### For members

- **Registration and authentication** — sign up with an email address, validated against
  Django's password policy and a donor age range of 18–65.
- **Blood search** — pick a zone and a blood group and see immediately whether the branch
  holds enough bags for the request.
- **Volunteer donor directory** — searches also list opted-in donors of the matching blood
  group in the same zone, with their phone number and email.
- **Donor opt-in** — join or leave the volunteer list from your profile at any time.

### For branch managers

- **Dashboard** — stock across every branch at a glance, plus the active member count.
- **Blood entry** — record bags collected into the branch; stock increases atomically.
- **Blood issue** — hand bags out; the system refuses to let a blood group go negative.
- **Stock ledger** — every movement is written to an append-only table with the date,
  branch, blood group, signed quantity and the manager who recorded it.
- **Member roster** — review registered members and deactivate accounts without deleting
  the history attached to them.
- **Django admin** — full CRUD over profiles, branches and ledger records, with filters,
  search and grouped stock fieldsets.

---

## Tech stack

| Layer    | Choice                                                                           |
| -------- | -------------------------------------------------------------------------------- |
| Backend  | Python 3.10+, Django 5.1                                                         |
| Database | MySQL 8.0 (SQLite supported for a zero-setup local run)                          |
| Frontend | Django templates with a single shared stylesheet, no JavaScript                  |
| Auth     | Django's built-in `auth` app, extended by a profile model                        |
| Tests    | Django `TestCase` — 19 tests over stock maths, access control and the main flows |

---

## Data model

Three tables carry the domain, alongside Django's built-in `auth_user`.

```text
auth_user ──1:1──> UserProfile
                     · gender, age, phone, address
                     · zone         (member's Dhaka zone)
                     · blood        (blood group)
                     · is_donor     (volunteer opt-in)
                     · working_zone (branch managed, managers only)

BloodBankInfo  (one row per branch — branch_zone is UNIQUE)
     · a_positive … ab_negative   current bag count per blood group
     · address, phone, email

BloodBagInfo   (append-only ledger)
     · date, branch, blood_group
     · quantity     signed: positive = collected, negative = issued
     · recorded_by  ──FK──> auth_user
```

**Why the quantity is signed.** `BloodBankInfo` stores the *current* stock so a search is a
single-row read. `BloodBagInfo` stores *how it got there*, so any branch total can be
reconciled by summing its ledger rows. Both are written inside one transaction with
`SELECT … FOR UPDATE` on the branch, which keeps two concurrent managers from overwriting
each other's stock update.

**Roles.** Branch managers are Django superusers whose profile carries a `working_zone`;
that field decides which branch their stock entries apply to. Everyone else is a member.

---

## Getting started

### Prerequisites

- Python 3.10 or newer
- MySQL 8.0 (or use the SQLite fallback described below)
- A C build toolchain for `mysqlclient`, or a prebuilt wheel for your platform

### 1. Clone and create a virtual environment

```bash
git clone https://github.com/UtshaBasak/Blood-Donation-Camp.git
cd Blood-Donation-Camp

python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure the environment

```bash
cp .env.example .env           # Windows: copy .env.example .env
```

Generate a secret key and paste it into `.env` as `DJANGO_SECRET_KEY`:

```bash
python -c "from django.core.management.utils import get_random_secret_key as k; print(k())"
```

Then set your database credentials in the same file. `.env` is git-ignored and must never
be committed.

> **Prefer to skip MySQL?** Set `DB_ENGINE=django.db.backends.sqlite3` and
> `DB_NAME=db.sqlite3` in `.env` and the project runs with no database server at all.

### 4. Create the database

```sql
CREATE DATABASE bloodbank CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 5. Apply migrations and create an administrator

```bash
python manage.py migrate
python manage.py createsuperuser
```

### 6. Run the development server

```bash
python manage.py runserver
```

The site is at <http://127.0.0.1:8000/> and the admin at <http://127.0.0.1:8000/admin/>.

---

## First-run configuration

A fresh database has no branches, so two short steps in the Django admin bring the app to
life:

1. **Create the branches.** Under *Blood bank branches*, add one record for `North` and one
   for `South`, each with an address, phone number and email. Searches and the About page
   read these rows; stock entry fails without them.
2. **Give your superuser a profile and a working zone.** `createsuperuser` only creates an
   `auth_user` row. Under *User profiles*, add a profile for that account and set
   **Working zone** to the branch they manage — the blood entry and issue pages use it to
   decide which branch to update, and will tell you to do this if it is missing.

Members created through the public registration form need no manual setup.

---

## Running the tests

```bash
python manage.py test
```

The suite runs against a throwaway database. To run it without a MySQL server:

```bash
DB_ENGINE=django.db.backends.sqlite3 DB_NAME=db.sqlite3 python manage.py test
```

Coverage spans the stock arithmetic (including the refusal to go negative), the
manager/member/anonymous access boundaries, registration validation, both stock movement
flows, search results and the member roster actions.

---

## URL reference

| Path                              | Name                  | Access    | Purpose                                  |
| --------------------------------- | --------------------- | --------- | ---------------------------------------- |
| `/`                               | `home`                | Public    | Landing page                             |
| `/about/`                         | `about`               | Public    | Programme overview and branch contacts   |
| `/register/`                      | `register`            | Public    | Create a member account                  |
| `/login/`                         | `login`               | Public    | Sign in                                  |
| `/logout/`                        | `logout`              | Member    | Sign out (POST)                          |
| `/profile/`                       | `profile`             | Member    | View your profile                        |
| `/profile/donor-status/`          | `toggle_donor_status` | Member    | Join or leave the donor list (POST)      |
| `/search/`                        | `search`              | Member    | Check stock and find volunteer donors    |
| `/dashboard/`                     | `dashboard`           | Manager   | Manager landing page                     |
| `/stock/`                         | `blood_details`       | Manager   | Branch stock and recent ledger rows      |
| `/stock/entry/`                   | `blood_entry`         | Manager   | Record collected bags                    |
| `/stock/issue/`                   | `blood_issue`         | Manager   | Record issued bags                       |
| `/members/`                       | `user_list`           | Manager   | Active member roster                     |
| `/members/<id>/deactivate/`       | `deactivate_user`     | Manager   | Deactivate a member (POST)               |
| `/admin/`                         | —                     | Superuser | Django admin                             |

---

## Project structure

```text
Blood-Donation-Camp/
├── bloodbank/                 # The application
│   ├── migrations/            # Schema history (0001 … 0009)
│   ├── admin.py               # Admin registrations for all three models
│   ├── models.py              # UserProfile, BloodBankInfo, BloodBagInfo + shared choices
│   ├── tests.py               # Stock maths, access control and flow tests
│   ├── urls.py                # Application routes
│   └── views.py               # Request handlers
├── cse370/                    # Project configuration (named after the course)
│   ├── settings.py            # Environment-driven settings
│   ├── urls.py                # Root URL configuration
│   ├── asgi.py
│   └── wsgi.py
├── static/css/style.css       # Single shared stylesheet
├── templates/                 # base.html plus one template per page
├── .env.example               # Template for local configuration
├── manage.py
└── requirements.txt
```

---

## Configuration reference

Every setting is read from the environment, so the same code runs locally and in
production without edits. See `.env.example` for a ready-to-copy template.

| Variable                      | Default                       | Notes                                        |
| ----------------------------- | ----------------------------- | -------------------------------------------- |
| `DJANGO_SECRET_KEY`           | insecure development key      | **Set this in any deployed environment.**    |
| `DJANGO_DEBUG`                | `True`                        | Set to `False` outside development.          |
| `DJANGO_ALLOWED_HOSTS`        | `localhost,127.0.0.1`         | Comma-separated.                             |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | empty                         | Comma-separated origins including scheme.    |
| `DJANGO_TIME_ZONE`            | `Asia/Dhaka`                  |                                              |
| `DB_ENGINE`                   | `django.db.backends.mysql`    | Use `…sqlite3` for a zero-setup run.         |
| `DB_NAME`                     | `bloodbank`                   | Filename when the engine is SQLite.          |
| `DB_USER` / `DB_PASSWORD`     | `root` / empty                |                                              |
| `DB_HOST` / `DB_PORT`         | `127.0.0.1` / `3306`          |                                              |

With `DJANGO_DEBUG=False` the project automatically enables HTTPS redirects, secure
session and CSRF cookies, HSTS, `X-Frame-Options: DENY` and content-type sniffing
protection.

---

## Security notes

- Credentials and the secret key live in the environment, never in the repository.
- Members are ordinary users; only explicitly created superusers reach the manager area.
- Every state-changing action (logout, donor opt-in, member removal, stock movements) is
  POST-only and CSRF-protected, so nothing can be triggered by a link.
- Donor contact details are visible only to signed-in members.
- Removing a member deactivates the account rather than deleting it, preserving the
  integrity of the stock ledger.

---

## Roadmap

- Replace the hand-rolled `request.POST` parsing with Django `Form` / `ModelForm` classes.
- Create the `UserProfile` row for superusers automatically via a post-save signal.
- Add per-branch stock history charts and a low-stock alert threshold.
- Email notifications to matching volunteer donors when a request cannot be met from stock.
- Continuous integration running `manage.py test` on every push.

---

## License

Released under the [MIT License](LICENSE).
