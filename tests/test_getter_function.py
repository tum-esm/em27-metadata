import datetime
import pytest
import em27_metadata


@pytest.mark.library
def test_getter_function() -> None:
    locations = em27_metadata.types.LocationMetadataList(
        root=[
            em27_metadata.types.LocationMetadata(
                location_id="lid1",
                details="description of location 1",
                lon=10.5,
                lat=48.1,
                alt=500,
            ),
            em27_metadata.types.LocationMetadata(
                location_id="lid2",
                details="description of location 2",
                lon=11.3,
                lat=48.0,
                alt=600,
            ),
        ]
    )
    sensors = em27_metadata.types.SensorMetadataList(
        root=[
            em27_metadata.types.SensorMetadata(
                sensor_id="sid1",
                serial_number=51,
                setups=[
                    em27_metadata.types.SetupsListItem(
                        from_datetime="2020-02-01T01:00:00+0000",
                        to_datetime="2020-02-01T09:59:59+0000",
                        value=em27_metadata.types.Setup(
                            location_id="lid1",
                            pressure_data_source="another",
                            utc_offset=3.7,
                        ),
                    ),
                    em27_metadata.types.SetupsListItem(
                        from_datetime="2020-02-01T12:00:00+0000",
                        to_datetime="2020-02-01T21:59:59+0000",
                        value=em27_metadata.types.Setup(location_id="lid2", ),
                    ),
                    em27_metadata.types.SetupsListItem(
                        from_datetime="2020-02-01T22:00:00+0000",
                        to_datetime="2020-02-03T22:59:59+0000",
                        value=em27_metadata.types.Setup(
                            location_id="lid2",
                            atmospheric_profile_location_id="lid1"
                        ),
                    ),
                ]
            ),
        ]
    )

    metadata = em27_metadata.interfaces.EM27MetadataInterface(
        locations,
        sensors,
        campaigns=em27_metadata.types.CampaignMetadataList(root=[]),
    )

    from_datetime = datetime.datetime.fromisoformat("2020-02-01T00:00:00+00:00")
    to_datetime = datetime.datetime.fromisoformat("2020-02-02T23:59:59+00:00")

    chunks = metadata.get("sid1", from_datetime, to_datetime)
    # 1-10, 12-22, 22-24

    for c in chunks:
        print(c.model_dump_json(indent=4))
    assert len(chunks) == 3

    # check correct splitting

    from_datetimes = [c.from_datetime for c in chunks]
    assert from_datetimes == [
        datetime.datetime.fromisoformat("2020-02-01T01:00:00+00:00"),
        datetime.datetime.fromisoformat("2020-02-01T12:00:00+00:00"),
        datetime.datetime.fromisoformat("2020-02-01T22:00:00+00:00"),
    ]
    to_datetimes = [c.to_datetime for c in chunks]
    assert to_datetimes == [
        datetime.datetime.fromisoformat("2020-02-01T09:59:59+00:00"),
        datetime.datetime.fromisoformat("2020-02-01T21:59:59+00:00"),
        datetime.datetime.fromisoformat("2020-02-02T23:59:59+00:00"),
    ]

    location_ids = [c.location.location_id for c in chunks]
    assert location_ids == ["lid1", "lid2", "lid2"]

    atmospheric_profile_location_ids = [
        c.atmospheric_profile_location.location_id for c in chunks
    ]
    assert atmospheric_profile_location_ids == ["lid1", "lid2", "lid1"]

    utc_offsets = [c.utc_offset for c in chunks]
    assert utc_offsets == [3.7, 0, 0]

    pressure_data_sources = [c.pressure_data_source for c in chunks]
    assert pressure_data_sources == ["another", "sid1", "sid1"]
