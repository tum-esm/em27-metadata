import datetime
import pytest
import em27_metadata


@pytest.mark.library
def test_getter_function() -> None:
    locations = [
        em27_metadata.types.LocationMetadata(
            **{
                "location_id": "lid1",
                "details": "description of location 1",
                "lon": 10.5,
                "lat": 48.1,
                "alt": 500,
            }
        ),
        em27_metadata.types.LocationMetadata(
            **{
                "location_id": "lid2",
                "details": "description of location 2",
                "lon": 11.3,
                "lat": 48.0,
                "alt": 600,
            }
        ),
    ]
    sensors = [
        em27_metadata.types.SensorMetadata.model_validate({
            "sensor_id":
                "sid1",
            "serial_number":
                51,
            "different_utc_offsets": [
                {
                    "from_datetime": "2020-02-01T02:00:00+00:00",
                    "to_datetime": "2020-02-01T15:59:59+00:00",
                    "utc_offset": 1,
                },
                {
                    "from_datetime": "2020-02-01T16:00:00+00:00",
                    "to_datetime": "2020-02-01T21:59:59+00:00",
                    "utc_offset": 2,
                },
            ],
            "different_pressure_data_sources": [
                {
                    "from_datetime": "2020-02-01T02:00:00+00:00",
                    "to_datetime": "2020-02-01T14:59:59+00:00",
                    "source": "src1",
                },
                {
                    "from_datetime": "2020-02-01T15:00:00+00:00",
                    "to_datetime": "2020-02-01T21:59:59+00:00",
                    "source": "src2",
                },
            ],
            "different_calibration_factors": [
                {
                    "from_datetime": "2020-02-01T02:00:00+00:00",
                    "to_datetime": "2020-02-01T12:59:59+00:00",
                    "pressure": 1.001,
                    "xco2": {
                        "factors": [1.001, 0],
                        "scheme": "Ohyama2021",
                    },
                    "xch4": {
                        "factors": [1.002, 0],
                        "scheme": "Ohyama2021",
                    },
                    "xco": {
                        "factors": [1.003, 0],
                        "scheme": "Ohyama2021",
                    },
                },
                {
                    "from_datetime": "2020-02-01T13:00:00+00:00",
                    "to_datetime": "2020-02-01T13:59:59+00:00",
                    "pressure": 1.001,
                    "xco2": {
                        "factors": [1.004, 0],
                        "scheme": "Ohyama2021",
                    },
                    "xch4": {
                        "factors": [1.005, 0],
                        "scheme": "Ohyama2021",
                    },
                    "xco": {
                        "factors": [1.006, 0],
                        "scheme": "Ohyama2021",
                    },
                },
                {
                    "from_datetime": "2020-02-01T14:00:00+00:00",
                    "to_datetime": "2020-02-01T21:59:59+00:00",
                    "pressure": 1.002,
                    "xco2": {
                        "factors": [1.004, 0],
                        "scheme": "Ohyama2021",
                    },
                    "xch4": {
                        "factors": [1.005, 0],
                        "scheme": "Ohyama2021",
                    },
                    "xco": {
                        "factors": [1.006, 0],
                        "scheme": "Ohyama2021",
                    },
                },
            ],
            "locations": [
                {
                    "from_datetime": "2020-02-01T01:00:00+00:00",
                    "to_datetime": "2020-02-01T09:59:59+00:00",
                    "location_id": "lid1",
                },
                {
                    "from_datetime": "2020-02-01T12:00:00+00:00",
                    "to_datetime": "2020-02-01T22:59:59+00:00",
                    "location_id": "lid2",
                },
            ],
        }),
    ]

    location_data = em27_metadata.interfaces.EM27MetadataInterface(
        locations, sensors, campaigns=[]
    )

    from_datetime = datetime.datetime.fromisoformat("2020-02-01T00:00:00+00:00")
    to_datetime = datetime.datetime.fromisoformat("2020-02-01T23:59:59+00:00")

    chunks = location_data.get("sid1", from_datetime, to_datetime)

    assert len(chunks) == 8

    # check correct splitting

    from_datetimes = [c.from_datetime for c in chunks]
    assert from_datetimes == [
        datetime.datetime.fromisoformat("2020-02-01T01:00:00+00:00"),
        datetime.datetime.fromisoformat("2020-02-01T02:00:00+00:00"),
        datetime.datetime.fromisoformat("2020-02-01T12:00:00+00:00"),
        datetime.datetime.fromisoformat("2020-02-01T13:00:00+00:00"),
        datetime.datetime.fromisoformat("2020-02-01T14:00:00+00:00"),
        datetime.datetime.fromisoformat("2020-02-01T15:00:00+00:00"),
        datetime.datetime.fromisoformat("2020-02-01T16:00:00+00:00"),
        datetime.datetime.fromisoformat("2020-02-01T22:00:00+00:00"),
    ]
    to_datetimes = [c.to_datetime for c in chunks]
    assert to_datetimes == [
        datetime.datetime.fromisoformat("2020-02-01T01:59:59+00:00"),
        datetime.datetime.fromisoformat("2020-02-01T09:59:59+00:00"),
        datetime.datetime.fromisoformat("2020-02-01T12:59:59+00:00"),
        datetime.datetime.fromisoformat("2020-02-01T13:59:59+00:00"),
        datetime.datetime.fromisoformat("2020-02-01T14:59:59+00:00"),
        datetime.datetime.fromisoformat("2020-02-01T15:59:59+00:00"),
        datetime.datetime.fromisoformat("2020-02-01T21:59:59+00:00"),
        datetime.datetime.fromisoformat("2020-02-01T22:59:59+00:00"),
    ]

    utc_offsets = [c.utc_offset for c in chunks]
    assert utc_offsets == [0, 1, 1, 1, 1, 1, 2, 0]

    pressure_data_sources = [c.pressure_data_source for c in chunks]
    assert pressure_data_sources == [
        "sid1", "src1", "src1", "src1", "src1", "src2", "src2", "sid1"
    ]

    pressure_calibration_factors = [
        c.calibration_factors.pressure for c in chunks
    ]
    assert pressure_calibration_factors == [
        1.0, 1.001, 1.001, 1.001, 1.002, 1.002, 1.002, 1.0
    ]

    xco2_calibration_factors = [(
        None if (c.calibration_factors.xco2 is None) else
        c.calibration_factors.xco2.factors[0]
    ) for c in chunks]
    assert xco2_calibration_factors == [
        1, 1.001, 1.001, 1.004, 1.004, 1.004, 1.004, 1
    ]

    location_ids = [c.location.location_id for c in chunks]
    assert location_ids == [
        "lid1", "lid1", "lid2", "lid2", "lid2", "lid2", "lid2", "lid2"
    ]
