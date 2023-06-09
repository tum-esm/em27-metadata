import pytest
from tum_esm_em27_metadata.types import TimeSeriesElement


@pytest.mark.ci
@pytest.mark.action
@pytest.mark.local
def test_datetime_parsing() -> None:
    assert TimeSeriesElement.matches_datetime_regex("2016-10-01T00:00:00+00:00")
    assert TimeSeriesElement.matches_datetime_regex("2016-10-01T23:00:00+00:00")
    assert TimeSeriesElement.matches_datetime_regex("2016-10-01T00:00:00+01:00")
    assert not TimeSeriesElement.matches_datetime_regex("2016-10-01T00:00:00+00:0")


@pytest.mark.ci
@pytest.mark.action
@pytest.mark.local
def test_time_series_element() -> None:
    tse1 = TimeSeriesElement(
        from_datetime="2016-10-01T00:00:00+00:00",
        to_datetime="2016-10-01T23:00:00+02:00",
    )
    actual_dt_seconds = (tse1.to_datetime - tse1.from_datetime).as_timedelta().total_seconds()
    expected_dt_seconds = 3600 * 21
    assert (
        actual_dt_seconds == expected_dt_seconds
    ), f"dt_seconds: {actual_dt_seconds} (actual) != {expected_dt_seconds} (expected)"

    tse2 = TimeSeriesElement(
        from_datetime="2016-10-01T00:00:00+00:00", to_datetime="2016-10-03T13:24:35-05:30"
    )
    actual_dt_seconds = (tse2.to_datetime - tse2.from_datetime).as_timedelta().total_seconds()
    expected_dt_seconds = 61 * 3600 + (24 * 60) + 35 + (5 * 3600) + (30 * 60)
    assert (
        actual_dt_seconds == expected_dt_seconds
    ), f"dt_seconds: {actual_dt_seconds} (actual) != {expected_dt_seconds} (expected)"
