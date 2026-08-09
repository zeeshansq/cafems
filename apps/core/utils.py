"""Core App – Utility Functions."""
import datetime
from zoneinfo import ZoneInfo
from django.conf import settings


PKT = ZoneInfo("Asia/Karachi")
CUTOFF_HOUR = 14  # 2:00 PM
CUTOFF_LEAD_DAYS = 1  # Request must be ≥1 day before start date


def is_before_cutoff(target_date: datetime.date) -> bool:
    """
    Return True if the current PKT datetime is before the cutoff
    for the given target_date.

    Rule (spec §5): Request must be submitted ≥1 day before date_range_start,
    by 2:00 PM Pakistan Standard Time.
    """
    now_pkt = datetime.datetime.now(PKT)
    cutoff_date = target_date - datetime.timedelta(days=CUTOFF_LEAD_DAYS)
    cutoff_dt = datetime.datetime(
        cutoff_date.year, cutoff_date.month, cutoff_date.day,
        CUTOFF_HOUR, 0, 0, tzinfo=PKT
    )
    return now_pkt < cutoff_dt


def get_today_pkt() -> datetime.date:
    """Return today's date in PKT."""
    return datetime.datetime.now(PKT).date()


def get_now_pkt() -> datetime.datetime:
    """Return current datetime in PKT."""
    return datetime.datetime.now(PKT)


def validate_file_upload(file, max_mb: float = 5.0, allowed_types=None):
    """Validate file size and content type for uploaded files."""
    if allowed_types is None:
        allowed_types = ["image/jpeg", "image/png", "image/webp", "image/gif"]

    if file.size > max_mb * 1024 * 1024:
        raise ValueError(f"File size must not exceed {max_mb}MB. Got {file.size / 1024 / 1024:.1f}MB.")

    content_type = getattr(file, "content_type", None)
    if content_type and content_type not in allowed_types:
        raise ValueError(f"File type '{content_type}' is not allowed. Accepted: {', '.join(allowed_types)}")

    return True
