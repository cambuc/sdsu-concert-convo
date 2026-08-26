# Concert and Convo Emailer

A reusable SMTP mail-merge tool: point it at a contacts CSV (School, Name, Position, Email, Status) and a template, and it personalizes + sends an email to each eligible contact over SMTP, tracking status back into the CSV so reruns never double-send.

## One-time setup

No external dependencies to install. Sending uses only Python's standard library (`smtplib`).

### 1. Generate a Gmail App Password
Google requires an "App Password" for SMTP login instead of your normal account password.
1. Go to your [Google Account > Security](https://myaccount.google.com/security) and enable **2-Step Verification** (if it isn't already on).
2. Go to **Security > App passwords**, create a new one (name it e.g. "Concert and Convo Emailer"), and copy the 16-character password it generates.

### 2. Store your credentials
Copy `.env.example` to `.env` and fill in your details:
```
SMTP_USERNAME=camcarbuc@gmail.com
SMTP_APP_PASSWORD=your16charapppassword
```
`.env` is gitignored. It will never be committed. Remove the spaces Google shows you when generating the app password.

### Using a different SMTP provider
`smtp_host` / `smtp_port` in `config.json` default to Gmail (`smtp.gmail.com` / `587`). To send through a different provider (e.g. a school or work SMTP server), just change those two values and put the matching credentials in `.env`.

## Usage

Edit `templates/default_template.txt` with your real subject/body copy before sending anything. Merge fields available: `{{Name}}`, `{{Position}}`, `{{School}}` (must match the CSV's column headers exactly).

Edit `config.json` to set your display name and the delay between sends.

**1. Dry run** renders every eligible email to `logs/dry_run_preview.txt`, sends nothing:
```
python send_emails.py --dry-run
```

**2. Send a test to yourself** sends one rendered email only to your own configured SMTP address:
```
python send_emails.py --send-test-to-self
```

**3. Staged rollout** send to just the first few real contacts before running the full list:
```
python send_emails.py --limit 3
```

**4. Full send:**
```
python send_emails.py
```

**Using a different school's CSV/template:**
```
python send_emails.py --csv path/to/OtherSchool_Contacts.csv --template templates/other_template.txt
```

## How status tracking works
- After every single send (success or failure), the `Status` column for that row is written back into the source CSV immediately — so if the script is interrupted, nothing already sent is lost or resent.
- Rows with `Status` starting with `Sent` are skipped on the next run.
- Rows with a blank or `Not publicly listed` email are always skipped and reported in the run summary. They need manual follow-up.
- Every run also writes a full audit log to `logs/send_log_<timestamp>.csv`.

## Required CSV columns
`School, Name, Position, Email, Status` Additional columns are ignored, but these five must be present with those exact header names.
