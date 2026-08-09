import datetime
import pytest
from apps.core.utils import is_before_cutoff, PKT, CUTOFF_HOUR


def test_is_before_cutoff():
    # Future date (5 days ahead) -> should be True
    future_date = datetime.date.today() + datetime.timedelta(days=5)
    assert is_before_cutoff(future_date) is True

    # Past date (yesterday) -> should be False
    past_date = datetime.date.today() - datetime.timedelta(days=1)
    assert is_before_cutoff(past_date) is False
