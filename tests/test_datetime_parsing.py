import pytest
import em27_metadata


@pytest.mark.library
def test_datetime_parsing() -> None:
    assert em27_metadata.types.TimeSeriesElement.matches_datetime_regex(
        "2016-10-01T00:00:00+0000"
    )
    assert em27_metadata.types.TimeSeriesElement.matches_datetime_regex(
        "2016-10-01T23:00:00+0000"
    )
    assert em27_metadata.types.TimeSeriesElement.matches_datetime_regex(
        "2016-10-01T00:00:00+0100"
    )
    assert not em27_metadata.types.TimeSeriesElement.matches_datetime_regex(
        "2016-10-01T00:00:00+000"
    )
    assert not em27_metadata.types.TimeSeriesElement.matches_datetime_regex(
        "2016-10-01T00:00:00+3300"
    )


@pytest.mark.library
def test_time_series_element() -> None:
    tse1 = em27_metadata.types.TimeSeriesElement(
        from_datetime="2016-10-01T00:00:00+00:00",
        to_datetime="2016-10-01T23:00:00+02:00",
    )
    actual_dt_seconds = (tse1.to_datetime - tse1.from_datetime).total_seconds()
    expected_dt_seconds = 3600 * 21
    assert (
        actual_dt_seconds == expected_dt_seconds
    ), f"dt_seconds: {actual_dt_seconds} (actual) != {expected_dt_seconds} (expected)"

    tse2 = em27_metadata.types.TimeSeriesElement(
        from_datetime="2016-10-01T00:00:00+00:00",
        to_datetime="2016-10-03T13:24:35-05:30"
    )
    actual_dt_seconds = (tse2.to_datetime - tse2.from_datetime).total_seconds()
    expected_dt_seconds = 61 * 3600 + (24 * 60) + 35 + (5 * 3600) + (30 * 60)
    assert (
        actual_dt_seconds == expected_dt_seconds
    ), f"dt_seconds: {actual_dt_seconds} (actual) != {expected_dt_seconds} (expected)"
