import datetime
from typing import Optional
import pytest
import em27_metadata


@pytest.mark.library
def test_explosion() -> None:
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
    # fmt: off
    sensors = em27_metadata.types.SensorMetadataList(
        root=[
            em27_metadata.types.SensorMetadata(
                sensor_id="sid1",
                serial_number=51,
                setups=[
                    em27_metadata.types.SetupsListItem(
                        from_datetime="2020-02-01T01:00:00+0000",
                        to_datetime="2020-02-01T09:59:59+0000",
                        value=em27_metadata.types.Setup( # type: ignore
                            lid="lid1", pds="A", utc_offset=3.7, profile_lid="lid2"
                        ),
                    ),
                    em27_metadata.types.SetupsListItem(
                        from_datetime="2020-02-01T12:00:00+0000",
                        to_datetime="2020-02-01T21:59:59+0000",
                        value=em27_metadata.types.Setup(lid="lid1", pds="B"), # type: ignore
                    ),
                    em27_metadata.types.SetupsListItem(
                        from_datetime="2020-02-01T22:00:00+0000",
                        to_datetime="2020-02-03T22:59:59+0000",
                        value=em27_metadata.types.Setup(lid="lid1", pds="C"), # type: ignore
                    ),
                    em27_metadata.types.SetupsListItem(
                        from_datetime="2020-02-04T00:00:00+0000",
                        to_datetime="2020-02-04T20:59:59+0000",
                        value=em27_metadata.types.Setup(lid="lid1", pds="D"), # type: ignore
                    ),
                    em27_metadata.types.SetupsListItem(
                        from_datetime="2020-02-04T22:00:00+0000",
                        to_datetime="2020-02-04T23:59:59+0000",
                        value=em27_metadata.types.Setup(lid="lid1", pds="E"), # type: ignore
                    ),
                ]
            ),
        ]
    )
    # fmt: on

    metadata = em27_metadata.interfaces.EM27MetadataInterface(
        locations,
        sensors,
        campaigns=em27_metadata.types.CampaignMetadataList(root=[]),
    )

    # fmt: off
    data: list[tuple[datetime.datetime, Optional[str]]] = [
        (datetime.datetime(2020, 2, 1, 0, 0, 0, tzinfo=datetime.timezone.utc),   None),
        (datetime.datetime(2020, 2, 1, 0, 30, 0, tzinfo=datetime.timezone.utc),  None),
        (datetime.datetime(2020, 2, 1, 1, 0, 0, tzinfo=datetime.timezone.utc),   "A"),
        (datetime.datetime(2020, 2, 1, 4, 0, 0, tzinfo=datetime.timezone.utc),   "A"),
        (datetime.datetime(2020, 2, 1, 9, 0, 0, tzinfo=datetime.timezone.utc),   "A"),
        (datetime.datetime(2020, 2, 1, 10, 0, 0, tzinfo=datetime.timezone.utc),  None),
        (datetime.datetime(2020, 2, 1, 11, 0, 0, tzinfo=datetime.timezone.utc),  None),
        (datetime.datetime(2020, 2, 1, 22, 30, 0, tzinfo=datetime.timezone.utc), "C"),
        (datetime.datetime(2020, 2, 1, 22, 45, 0, tzinfo=datetime.timezone.utc), "C"),
        (datetime.datetime(2020, 2, 4, 12, 0, 0, tzinfo=datetime.timezone.utc),  "D"),
        (datetime.datetime(2020, 2, 4, 21, 0, 0, tzinfo=datetime.timezone.utc),  None),
        (datetime.datetime(2020, 2, 5, 20, 0, 0, tzinfo=datetime.timezone.utc),  None),
    ]
    # fmt: on

    result = metadata.explode_efficiently("sid1", [dt for dt, _ in data])
    print(result)
    for r, (dt, expected) in zip(result, data):
        if r is None:
            assert expected is None
        else:
            location, _, pds, _ = r
            assert location.location_id == "lid1"
            assert pds == expected
