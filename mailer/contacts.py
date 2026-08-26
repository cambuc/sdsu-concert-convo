import csv
from pathlib import Path

REQUIRED_COLUMNS = {"School", "Name", "Position", "Email", "Status"}
MISSING_EMAIL_MARKERS = {"", "not publicly listed", "not listed", "n/a"}


class ContactsFile:
    def __init__(self, path: str):
        self.path = Path(path)
        with open(self.path, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            self.fieldnames = reader.fieldnames or []
            self.rows = [dict(row) for row in reader]

        missing = REQUIRED_COLUMNS - set(self.fieldnames)
        if missing:
            raise ValueError(
                f"{self.path} is missing required column(s): {', '.join(sorted(missing))}"
            )

    def save(self):
        with open(self.path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=self.fieldnames)
            writer.writeheader()
            writer.writerows(self.rows)

    def mark_status(self, row: dict, status: str):
        row["Status"] = status
        self.save()

    def eligible_rows(self) -> list[dict]:
        eligible = []
        for row in self.rows:
            status = (row.get("Status") or "").strip().lower()
            email = (row.get("Email") or "").strip().lower()
            if status.startswith("sent"):
                continue
            if email in MISSING_EMAIL_MARKERS:
                continue
            eligible.append(row)
        return eligible

    def skipped_no_email_rows(self) -> list[dict]:
        return [
            row
            for row in self.rows
            if (row.get("Email") or "").strip().lower() in MISSING_EMAIL_MARKERS
        ]

    def already_sent_rows(self) -> list[dict]:
        return [
            row
            for row in self.rows
            if (row.get("Status") or "").strip().lower().startswith("sent")
        ]
