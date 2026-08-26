import argparse
import csv
import sys
import time
from datetime import datetime
from pathlib import Path

from mailer.config import load_config
from mailer.contacts import ContactsFile
from mailer.template import Template

LOGS_DIR = Path(__file__).resolve().parent / "logs"


def parse_args():
    parser = argparse.ArgumentParser(description="Reusable SMTP mail-merge tool.")
    parser.add_argument("--csv", help="Path to the contacts CSV.")
    parser.add_argument("--template", help="Path to the template file.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Render every eligible email to logs/dry_run_preview.txt without sending.",
    )
    parser.add_argument(
        "--send-test-to-self",
        action="store_true",
        help="Send one rendered email to your own configured SMTP address only.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Only process the first N eligible rows (staged rollout).",
    )
    return parser.parse_args()


def run_dry_run(rows, template, limit):
    LOGS_DIR.mkdir(exist_ok=True)
    preview_path = LOGS_DIR / "dry_run_preview.txt"
    targeted = rows[:limit] if limit else rows

    with open(preview_path, "w", encoding="utf-8") as f:
        for row in targeted:
            subject, body = template.render(row)
            f.write(f"To: {row['Name']} <{row['Email']}>\n")
            f.write(f"Subject: {subject}\n\n")
            f.write(body)
            f.write("\n" + ("-" * 60) + "\n\n")

    print(f"Dry run complete. Rendered {len(targeted)} email(s) to {preview_path}")


def run_send_test_to_self(rows, template, config):
    from mailer.smtp_client import SMTPClient

    if not rows:
        print("No eligible rows to render a test email from.")
        return

    client = SMTPClient(config["smtp_host"], config["smtp_port"])
    try:
        subject, body = template.render(rows[0])
        client.send(
            to_address=client.sender_address,
            subject=f"[TEST] {subject}",
            body=body,
            sender_name=config["sender_name"],
        )
        print(f"Test email sent to {client.sender_address} (rendered from '{rows[0]['Name']}').")
    finally:
        client.close()


def run_live_send(contacts: ContactsFile, rows, template, config, limit):
    from mailer.smtp_client import SMTPClient

    targeted = rows[:limit] if limit else rows
    if not targeted:
        print("No eligible rows to send to.")
        return

    LOGS_DIR.mkdir(exist_ok=True)
    log_path = LOGS_DIR / f"send_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

    client = SMTPClient(config["smtp_host"], config["smtp_port"])
    sent_count = 0
    failed_count = 0

    try:
        with open(log_path, "w", encoding="utf-8", newline="") as log_file:
            log_writer = csv.writer(log_file)
            log_writer.writerow(["timestamp", "name", "email", "result"])

            for i, row in enumerate(targeted):
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                try:
                    subject, body = template.render(row)
                    client.send(
                        to_address=row["Email"],
                        subject=subject,
                        body=body,
                        sender_name=config["sender_name"],
                    )
                    contacts.mark_status(row, f"Sent {timestamp}")
                    log_writer.writerow([timestamp, row["Name"], row["Email"], "sent"])
                    sent_count += 1
                    print(f"[{i + 1}/{len(targeted)}] Sent to {row['Name']} <{row['Email']}>")
                except Exception as exc:
                    reason = str(exc)[:200]
                    contacts.mark_status(row, f"Failed: {reason}")
                    log_writer.writerow([timestamp, row["Name"], row["Email"], f"failed: {reason}"])
                    failed_count += 1
                    print(f"[{i + 1}/{len(targeted)}] FAILED for {row['Name']} <{row['Email']}>: {reason}")

                log_file.flush()

                if i < len(targeted) - 1:
                    time.sleep(config["delay_seconds"])
    finally:
        client.close()

    print(f"\nDone. Sent: {sent_count}, Failed: {failed_count}. Log: {log_path}")


def main():
    args = parse_args()
    config = load_config()

    csv_path = args.csv or config["default_csv"]
    template_path = args.template or config["default_template"]

    try:
        contacts = ContactsFile(csv_path)
        template = Template.load(template_path)
    except (FileNotFoundError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    eligible = contacts.eligible_rows()
    skipped_no_email = contacts.skipped_no_email_rows()
    already_sent = contacts.already_sent_rows()

    print(
        f"Loaded {len(contacts.rows)} row(s) from {csv_path}: "
        f"{len(eligible)} eligible, {len(already_sent)} already sent, "
        f"{len(skipped_no_email)} skipped (no email on file)."
    )

    if args.dry_run:
        run_dry_run(eligible, template, args.limit)
        return

    try:
        if args.send_test_to_self:
            run_send_test_to_self(eligible, template, config)
            return

        run_live_send(contacts, eligible, template, config, args.limit)
    except (FileNotFoundError, KeyError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
