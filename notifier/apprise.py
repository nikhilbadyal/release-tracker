import logging
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from apprise import Apprise, LogCapture, NotifyFormat

from notifier.base import Notifier


class AppriseNotifier(Notifier):
    def __init__(self, config: dict[str, Any]) -> None:
        self.apprise = Apprise()
        self.apprise.add(config["url"])

        # From my POV: Validate message format and fall back if unknown
        requested_format = str(config.get("format", NotifyFormat.TEXT)).lower()
        valid_formats = {
            "text": NotifyFormat.TEXT,
            "html": NotifyFormat.HTML,
            "markdown": NotifyFormat.MARKDOWN,
        }

        if requested_format not in valid_formats:
            print(f"⚠️ Unknown message format '{requested_format}', defaulting to 'text'")
        self.message_format = valid_formats.get(requested_format, NotifyFormat.TEXT)

    def send(self, title: str, body: str, attachments: Sequence[Path] | None = None) -> bool:
        str_attachments = [str(path) for path in attachments] if attachments else None

        # From my POV: Warn if attachments are not supported
        if str_attachments:
            for service in self.apprise.servers:  # type: ignore[attr-defined]
                if not service.attachment_support:
                    print(f"⚠️ Warning: {service.url()} does not support attachments. They will be ignored.")

        with LogCapture(level=logging.WARNING) as logs:  # type: ignore[no-untyped-call]
            success = self.apprise.notify(
                title=title,
                body=body,
                body_format=self.message_format,
                attach=str_attachments,  # type: ignore[arg-type]
            )

            log_output = logs.getvalue().strip()
            if log_output:
                print("📋 Apprise Logs:")
                print(log_output)

        return success
