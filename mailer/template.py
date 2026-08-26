import re
from pathlib import Path

PLACEHOLDER_RE = re.compile(r"\{\{(\w+)\}\}")


class Template:
    def __init__(self, subject: str, body: str):
        self.subject = subject
        self.body = body

    @classmethod
    def load(cls, path: str) -> "Template":
        text = Path(path).read_text(encoding="utf-8")
        if not text.startswith("Subject:"):
            raise ValueError(
                f"Template {path} must start with a 'Subject: ...' line, "
                "followed by a blank line and the body."
            )
        first_line, _, rest = text.partition("\n")
        subject = first_line[len("Subject:"):].strip()
        body = rest.lstrip("\n")
        return cls(subject=subject, body=body)

    def render(self, row: dict) -> tuple[str, str]:
        def substitute(text: str) -> str:
            def replace(match: re.Match) -> str:
                field = match.group(1)
                if field not in row:
                    available = ", ".join(sorted(row.keys()))
                    raise KeyError(
                        f"Template references '{{{{{field}}}}}' but the CSV has no "
                        f"'{field}' column. Available columns: {available}"
                    )
                return row[field]

            return PLACEHOLDER_RE.sub(replace, text)

        return substitute(self.subject), substitute(self.body)
