# Alumni Portal

A Django-based alumni job network portal.

## Requirements
- Python 3.10+
- PostgreSQL (or use the SQLite quick-start below if you just want to try it out)

## Setup

```bash
# 1. Create & activate a virtual environment (recommended)
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Copy the env template and fill in your real values
cp .env.example .env            # Windows: copy .env.example .env

# 4. Set up your database — see "Database" section below

# 5. Apply migrations
python manage.py migrate

# 6. Run the dev server
python manage.py runserver
```

Visit **http://127.0.0.1:8000/**

`.env` is read automatically by every `manage.py` command — set values there
once instead of exporting environment variables in every new terminal
session (this is what caused the earlier "OTP not received" / "relation
does not exist" issues — the app was silently falling back to defaults
because the env vars weren't set in that particular session).

---

## Database

By default this project expects **PostgreSQL**, configured via your `.env` file:

| Variable      | Default            |
|---------------|--------------------|
| DB_NAME       | alumni_portal_db   |
| DB_USER       | postgres           |
| DB_PASSWORD   | password           |
| DB_HOST       | localhost          |
| DB_PORT       | 5432               |

Create the database first:
```bash
createdb alumni_portal_db
```
Or set the values in `.env` to point at an existing database/instance.

**Forgot to run migrations on a fresh DB?** That's the `relation
"accounts_customuser" does not exist` error — fix with `python manage.py migrate`.

### Quick local test without installing Postgres
For local testing only, set in `.env`:
```
USE_SQLITE=True
```
That's it — `migrate` will create a `db.sqlite3` file and everything works
the same way. Don't use this in production.

---

## Email / OTP Verification

New users must verify a 6-digit code emailed to them before they can log in.

**By default (no `.env` changes needed), emails print straight to your
terminal** (console backend) — register a user, then check the terminal
running `runserver` for the code.

**For real delivery**, uncomment and fill in the email block in `.env`
(see `.env.example` — it has a worked Gmail example with all the gotchas
explained: App Passwords, port 587 vs 465, etc).

### What's handled for you (edge cases)
- **Brute-force protection** — each code allows `OTP_MAX_ATTEMPTS` (default 5)
  wrong guesses before it's locked; a resend is required after that.
- **Expiry** — codes expire after `OTP_EXPIRY_MINUTES` (default 10).
- **Resend throttling** — one resend per `OTP_RESEND_COOLDOWN_SECONDS` (default 30).
- **Abandoned signups** — if someone registers but never verifies, the email
  isn't permanently stuck: registering again with the same address quietly
  replaces the old, unverified attempt instead of erroring with "already exists."
- **Already-verified emails** — registering with an email that has a real,
  verified account is correctly rejected ("please log in instead").
- **SMTP/network failures don't crash the page** — if the email genuinely
  can't be sent (bad credentials, blocked port, provider down), the user
  sees a friendly retry message instead of a Django error page, the failure
  is logged, and no half-created account is left behind.
- **Logging in before verifying** — if the password is correct but the
  account isn't verified yet, the user is automatically sent a fresh code
  and redirected to the verification page instead of seeing "invalid login."
- **Stale account cleanup** — run periodically (e.g. via cron / Windows Task
  Scheduler once deployed) to delete abandoned unverified signups:
  ```bash
  python manage.py purge_unverified_accounts --hours 24
  # add --dry-run first to preview what would be deleted
  ```

---

## Admin Accounts

Admins **don't self-register through the website** — there's no public sign-up
form for them anymore. You (the owner) create each admin directly:

```bash
python manage.py create_admin --username rose --name "Rose" --email rose@example.com
```

Leave off `--code` and a secure random one is generated and printed for you;
or pass `--code yourcode` to set it yourself. The command prints something like:

```
Admin "Rose" created.
  Username:    rose
  Access code: aB3xK9pQmZ7w
```

Give that **username + access code** to the admin directly — that's all
they need at `/accounts/admin-login/`. No email, no password, no OTP for
admins; that whole flow is for regular users only.

Each admin gets their own unique code (stored on their `AdminProfile`), not
one shared secret — so revoking or rotating one admin's access doesn't
affect anyone else. To rotate an existing admin's code, just re-run the
command with the same `--username` and a new `--code`.

`--email` is only kept for your own record-keeping (the database requires
a unique email per account) — it's never used to log in or send anything.

## Key Features
- Users can only see their own posted job openings and their own applications — never anyone else's
- Regular user registration requires real email ownership — OTP verification, see above
- Admin login is intentionally separate and simpler: unique username + access code, provisioned by you
- Admin dashboard at `/accounts/admin-dashboard/` — 3 tabs: Users / Job Openings / Applications
  - Users tab shows a Verified / Pending badge per account
  - Job Openings tab shows the poster's name, email, and mobile number
  - Click "View →" on any row to expand full details inline
- Built-in Django admin at `/admin/` (separate from the dashboard above) for raw model management

## Project Structure
```
alumni_portal/
├── accounts/               # users, auth, registration, OTP verification, admin dashboard
│   └── management/commands/
│       ├── create_admin.py
│       └── purge_unverified_accounts.py
├── jobs/                   # job openings & applications
├── alumni_portal_config/   # settings, root urls
├── templates/
│   └── accounts/email/     # HTML email templates (OTP code)
├── static/
├── media/                  # uploaded resumes
├── .env.example            # copy to .env and fill in
└── requirements.txt
```

---

## Before deploying for real

This project is dev-ready, not deployment-ready yet. When you're ready to
go live, also do:

- Set `DEBUG=False` and a real `SECRET_KEY` in `.env`
- Set `ALLOWED_HOSTS` to your actual domain (not `*`)
- Use a real transactional email provider (SendGrid / Mailgun / SES /
  Postmark) instead of raw Gmail SMTP — Gmail throttles and sometimes
  blocks automated/high-volume sending
- Serve static files properly (e.g. WhiteNoise or a CDN) — `DEBUG=False`
  stops Django from serving them itself
- Put the app behind HTTPS
- Consider IP-based rate limiting or a CAPTCHA on `/accounts/user-register/`
  to prevent mass fake-account creation / email-bombing abuse (not included —
  needs a cache backend like Redis or a package like `django-ratelimit`)
- Schedule `purge_unverified_accounts` to run daily

---

## Job Board — approval & expiry workflow

Job openings now go through an approval workflow before they're visible to
other alumni:

1. **Posting** — Any user can submit an opening ("I Have an Opening" on the
   dashboard). It's saved with status `Pending Review` and is only visible
   to the person who posted it (and admins).
2. **Admin review** — Admins see a **Pending Review** tab on the admin
   dashboard with **Publish** / **Reject** buttons for each submission.
3. **Published** — Once published, the opening appears as a card on the
   public **Job Board** (`/jobs/board/`) to every logged-in user. The
   card and detail page never show the company name or who posted it —
   only the role, job type, experience, package, skills and last date to
   apply.
4. **Applying** — A user clicks a card to see full details, then
   "I'm Interested — Apply". This shows a confirmation screen with the
   details already saved in their "Looking for a Job" profile (prompting
   them to complete it first if they haven't) and submits the application
   with one click — there's no separate form to fill in per job.
5. **Reviewing applicants** — The person who posted the job sees every
   applicant's profile on their "My Job Opening" detail page.
6. **Expiry & removal** — Once `last_date_to_apply` passes, the opening is
   automatically hidden from the public Job Board. It stays visible to its
   poster/admin (marked "Expired") for 5 days, then is permanently deleted.

   This clean-up (marking expired + deleting old postings) runs via a
   management command:

   ```bash
   python manage.py cleanup_jobs
   ```

   Schedule it to run once a day:

   - **Linux/macOS (cron):**
     ```
     0 1 * * *  cd /path/to/alumni_portal && venv/bin/python manage.py cleanup_jobs
     ```
   - **Windows (Task Scheduler):** create a daily task that runs
     `venv\Scripts\python.exe manage.py cleanup_jobs` with the project
     folder as the working directory.

   The public Job Board also filters out expired postings at request time,
   so nothing expired is ever shown even if the scheduled task hasn't run
   yet — the command is only required for the final permanent deletion.

## Icons

All emoji have been replaced with [Bootstrap Icons](https://icons.getbootstrap.com/)
(self-hosted under `static/vendor/bootstrap-icons/`, no external CDN
dependency) for a consistent, professional look.
