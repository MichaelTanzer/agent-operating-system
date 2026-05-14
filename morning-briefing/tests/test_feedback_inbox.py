from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "feedback_inbox.py"


def load_feedback_module():
    spec = importlib.util.spec_from_file_location("feedback_inbox", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {SCRIPT_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class FeedbackInboxTest(unittest.TestCase):
    def setUp(self) -> None:
        self.feedback = load_feedback_module()

    def test_parse_reply_strips_quoted_email_and_labels_requested_change(self) -> None:
        message = {
            "id": "msg-1",
            "threadId": "thread-1",
            "from": "Michael Tanzer <michaelitanzer@gmail.com>",
            "subject": "Re: Morning Briefing — Overnight Ideas",
            "date": "Thu, 14 May 2026 06:41:50 -0400",
            "body": "Get started on:\r\n\r\n1- Create a personal feedback inbox for Morning Briefing replies that tags each comment by briefing item and requested change.\r\n\r\nGreat ideas!\r\n\r\nSent from my iPhone\r\n\r\n> On May 14, 2026, James Lafarge wrote:\r\n> prior briefing text",
        }

        item = self.feedback.parse_feedback_message(message)

        self.assertEqual(item.message_id, "msg-1")
        self.assertEqual(item.briefing_item, "Overnight Ideas")
        self.assertEqual(item.action_labels, ["requested_change", "positive_signal"])
        self.assertEqual(
            item.comment,
            "Get started on:\n\n1- Create a personal feedback inbox for Morning Briefing replies that tags each comment by briefing item and requested change.\n\nGreat ideas!",
        )
        self.assertNotIn("prior briefing text", item.comment)
        self.assertNotIn("Sent from my iPhone", item.comment)

    def test_write_daily_markdown_groups_by_briefing_item(self) -> None:
        messages = [
            {
                "id": "msg-1",
                "threadId": "thread-1",
                "from": "Michael Tanzer <michaelitanzer@gmail.com>",
                "subject": "Re: Morning Briefing — Overnight Ideas",
                "date": "Thu, 14 May 2026 06:41:50 -0400",
                "body": "Get started on parser.\n\nSent from my iPhone\n\n> quoted",
            },
            {
                "id": "msg-2",
                "threadId": "thread-2",
                "from": "Michael Tanzer <michaelitanzer@gmail.com>",
                "subject": "Re: Morning Briefing — Gratitude Prompt",
                "date": "Thu, 14 May 2026 06:39:52 -0400",
                "body": "I’m grateful for Charlie.\n\nSent from my iPhone\n\n> quoted",
            },
        ]
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = self.feedback.write_daily_markdown(
                [self.feedback.parse_feedback_message(message) for message in messages],
                output_dir=Path(tmpdir),
                day="2026-05-14",
            )
            content = output_path.read_text(encoding="utf-8")

        self.assertEqual(output_path.name, "2026-05-14.md")
        self.assertIn("# Morning Briefing feedback — 2026-05-14", content)
        self.assertIn("## Overnight Ideas", content)
        self.assertIn("- Labels: `requested_change`", content)
        self.assertIn("Get started on parser.", content)
        self.assertIn("## Gratitude Prompt", content)
        self.assertIn("I’m grateful for Charlie.", content)
        self.assertNotIn("> quoted", content)

    def test_cli_reads_gmail_json_and_writes_daily_markdown(self) -> None:
        messages = [
            {
                "id": "msg-1",
                "threadId": "thread-1",
                "from": "Michael Tanzer <michaelitanzer@gmail.com>",
                "subject": "Re: Morning Briefing — Overnight Ideas",
                "date": "Thu, 14 May 2026 06:41:50 -0400",
                "body": "Please add a parser.\n\n> quoted",
            }
        ]
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "gmail.json"
            input_path.write_text(json.dumps(messages), encoding="utf-8")
            exit_code = self.feedback.main([
                "--input-json",
                str(input_path),
                "--output-dir",
                tmpdir,
                "--date",
                "2026-05-14",
            ])
            output_path = Path(tmpdir) / "2026-05-14.md"

            self.assertEqual(exit_code, 0)
            self.assertTrue(output_path.exists())
            self.assertIn("Please add a parser.", output_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
