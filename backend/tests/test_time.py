from datetime import datetime, timedelta, timezone

from database import utcnow


def test_utcnow_is_naive_and_matches_utc():
    now = utcnow()
    assert now.tzinfo is None  # MySQL DATETIME columns are timezone-naive
    expected = datetime.now(timezone.utc).replace(tzinfo=None)
    assert abs(expected - now) < timedelta(seconds=5)
