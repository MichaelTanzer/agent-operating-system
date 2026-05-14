#!/usr/bin/env python3
"""Convert Gmail Morning Briefing replies into daily markdown feedback files.

This first build step is intentionally offline and read-only: it accepts Gmail
message JSON that another process has fetched, strips quoted reply chains, tags
comments by briefing item and requested change, and writes a local markdown file.

Example:
    python3 morning-briefing/scripts/feedback_inbox.py \
        --input-json /tmp/morning-replies.json \
        --output-dir ~/.hermes/morning/feedback \
        --date 2026-05-14
"""

from __future__ import annotations

import argparse
import html
import json
import re
from dataclasses import dataclass
from datetime import datetime
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any, Iterable

DEFAULT_OUTPUT_DIR = Path("~/.hermes/morning/feedback").expanduser()
QUOTE_MARKERS = (
    "\n>",
    "\r\n>",
    "\nOn ",
    "\r\nOn ",
)
SIGNATURE_PATTERNS = (
    re.compile(r"\n\s*Sent from my iPhone\s*$", re.IGNORECASE),
    re.compile(r"\n\s*Sent from my iPad\s*$", re.IGNORECASE),
    re.compile(r"\n\s*Sent from my Android\s*$", re.IGNORECASE),
)
REQUEST_PATTERNS = (
    re.compile(r"\b(get started on|start|build|create|add|choose|specify|include|change|fix|remove|pause|enable|disable)\b", re.IGNORECASE),
)
POSITIVE_PATTERNS = (
    re.compile(r"\b(great ideas?|good|excellent|love|useful|helpful)\b", re.IGNORECASE),
)


@dataclass(frozen=True)
class FeedbackItem:
    message_id: str
    thread_id: str
    sender: str
    subject: str
    date: str
    briefing_item: str
    action_labels: list[str]
    comment: str


def normalize_body(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n").strip()


def html_to_text(text: str) -> str:
    """Convert simple Gmail HTML bodies to plain text before quote stripping."""
    if "<" not in text or ">" not in text:
        return text
    text = re.sub(r"(?is)<blockquote\b.*", "", text)
    text = re.sub(r"(?is)<(br|/p|/div|/tr|/li)\b[^>]*>", "\n", text)
    text = re.sub(r"(?is)<[^>]+>", "", text)
    text = html.unescape(text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)
    return text.strip()


def strip_quoted_reply(body: str) -> str:
    """Return only MT's newly-written reply text, not the quoted briefing."""
    text = normalize_body(html_to_text(body))
    cut_positions = [idx for marker in QUOTE_MARKERS if (idx := text.find(marker)) != -1]
    if cut_positions:
        text = text[: min(cut_positions)]
    for pattern in SIGNATURE_PATTERNS:
        text = pattern.sub("", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def briefing_item_from_subject(subject: str) -> str:
    cleaned = re.sub(r"^\s*(re|fwd?):\s*", "", subject, flags=re.IGNORECASE).strip()
    if "—" in cleaned:
        return cleaned.split("—", 1)[1].strip()
    if "-" in cleaned and cleaned.lower().startswith("morning briefing"):
        return cleaned.split("-", 1)[1].strip()
    return cleaned or "Unclassified"


def labels_for_comment(comment: str) -> list[str]:
    labels: list[str] = []
    if any(pattern.search(comment) for pattern in REQUEST_PATTERNS):
        labels.append("requested_change")
    if any(pattern.search(comment) for pattern in POSITIVE_PATTERNS):
        labels.append("positive_signal")
    if not labels:
        labels.append("comment")
    return labels


def parse_feedback_message(message: dict[str, Any]) -> FeedbackItem:
    subject = str(message.get("subject") or "")
    comment = strip_quoted_reply(str(message.get("body") or message.get("snippet") or ""))
    return FeedbackItem(
        message_id=str(message.get("id") or ""),
        thread_id=str(message.get("threadId") or ""),
        sender=str(message.get("from") or ""),
        subject=subject,
        date=str(message.get("date") or ""),
        briefing_item=briefing_item_from_subject(subject),
        action_labels=labels_for_comment(comment),
        comment=comment,
    )


def _sort_key(item: FeedbackItem) -> tuple[str, str, str]:
    try:
        parsed = parsedate_to_datetime(item.date)
        date_key = parsed.isoformat()
    except (TypeError, ValueError):
        date_key = item.date
    return (item.briefing_item.lower(), date_key, item.message_id)


def markdown_for_items(items: Iterable[FeedbackItem], *, day: str) -> str:
    grouped: dict[str, list[FeedbackItem]] = {}
    for item in sorted(items, key=_sort_key):
        if not item.comment:
            continue
        grouped.setdefault(item.briefing_item, []).append(item)

    lines = [f"# Morning Briefing feedback — {day}", ""]
    if not grouped:
        lines.extend(["No feedback captured.", ""])
        return "\n".join(lines)

    for briefing_item, group in grouped.items():
        lines.extend([f"## {briefing_item}", ""])
        for item in group:
            labels = ", ".join(f"`{label}`" for label in item.action_labels)
            lines.append(f"- Labels: {labels}")
            if item.message_id:
                lines.append(f"  Message: `{item.message_id}` / Thread: `{item.thread_id}`")
            if item.date:
                lines.append(f"  Date: {item.date}")
            if item.sender:
                lines.append(f"  From: {item.sender}")
            lines.append("  Comment:")
            for line in item.comment.splitlines() or [""]:
                lines.append(f"  > {line}" if line else "  >")
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def write_daily_markdown(items: Iterable[FeedbackItem], *, output_dir: Path, day: str) -> Path:
    output_dir = output_dir.expanduser()
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{day}.md"
    output_path.write_text(markdown_for_items(items, day=day), encoding="utf-8")
    return output_path


def load_messages(path: Path) -> list[dict[str, Any]]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(raw, dict):
        if "messages" in raw and isinstance(raw["messages"], list):
            return [dict(message) for message in raw["messages"]]
        return [raw]
    if isinstance(raw, list):
        return [dict(message) for message in raw]
    raise ValueError("input JSON must be a Gmail message object, a list, or {'messages': [...]} object")


def default_day() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-json", required=True, help="Path to Gmail message JSON from google_api.py gmail get/search enrichment")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR, help="Directory for YYYY-MM-DD.md feedback files")
    parser.add_argument("--date", default=default_day(), help="Feedback date for the markdown filename")
    parser.add_argument("--json", action="store_true", help="Print machine-readable result metadata")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    messages = load_messages(Path(args.input_json))
    items = [parse_feedback_message(message) for message in messages]
    output_path = write_daily_markdown(items, output_dir=args.output_dir, day=args.date)
    result = {
        "status": "written",
        "path": str(output_path),
        "messages": len(messages),
        "captured": sum(1 for item in items if item.comment),
    }
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"Wrote {result['captured']} feedback item(s) to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
