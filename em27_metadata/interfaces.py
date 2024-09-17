import datetime
import em27_metadata


class EM27MetadataInterface:
    def __init__(
        self,
        locations: em27_metadata.types.LocationMetadataList,
        sensors: em27_metadata.types.SensorMetadataList,
        campaigns: em27_metadata.types.CampaignMetadataList,
    ):
        """Create a new EM27MetadataInterface object.

        During the instantiation, the integrity of the metadata is checked by
        running the following tests:

            * Location IDs are unique
            * Sensor IDs are unique
            * Campaign IDs are unique
            * All location IDs referenced in sensors.json exist
            * All sensor IDs referenced in campaigns.json exist
            * All location IDs referenced in campaigns.json exist
            * All time series elements in sensors.json have from_datetime < to_datetime
            * The time series in sensors.json are sorted
            * The time series in sensors.json have no overlaps
        
        Args:
            locations:  A list of `LocationMetadata` objects.
            sensors:    A list of `SensorMetadata` objects.
            campaigns:  A list of `CampaignMetadata` objects.
        
        Returns:  An metadata object containing all the metadata that can now be queried
                  locally using `metadata.get`.
        
        Raises:
            pydantic.ValidationError:  If the metadata integrity checks fail.
        """

        self.locations = locations
        self.sensors = sensors
        self.campaigns = campaigns

        # reference existence in sensors.json
        for s1 in sensors.root:
            for l1 in s1.setups:
                assert l1.value.location_id in locations.location_ids, f"unknown location id {l1.value.location_id}"

        # reference existence in campaigns.json
        for c1 in campaigns.root:
            for _sid in c1.sensor_ids:
                assert _sid in sensors.sensor_ids, f"unknown sensor id {_sid}"
            for _lid in c1.location_ids:
                assert _lid in locations.location_ids, f"unknown location id {_lid}"

    def get(
        self,
        sensor_id: str,
        from_datetime: datetime.datetime,
        to_datetime: datetime.datetime,
    ) -> list[em27_metadata.types.SensorDataContext]:
        """For a given `sensor_id`, return the list of metadata contexts between
        `from_datetime` and `to_datetime`.
        
        Each "context" is a time period where the setup is constant. For example,
        when requesting a full 24 hour day, and the setup changed at noon, the
        returned list will contain two items: One context until noon, and one
        context after noon.
        
        Args:
            sensor_id:      The sensor ID.
            from_datetime:  The start of the requested time period.
            to_datetime:    The end of the requested time period.
        
        Returns:  A list of `SensorDataContext` objects.

        Raises:
            ValueError:      If the `sensor_id` is unknown or the `from_datetime` is
                             greater than the given `to_datetime`."""

        try:
            sensor = next(
                filter(lambda s: s.sensor_id == sensor_id, self.sensors.root)
            )
        except StopIteration:
            raise ValueError(f"Unknown sensor_id {sensor_id}")

        if from_datetime > to_datetime:
            raise ValueError(
                f"from_datetime ({from_datetime}) > to_datetime ({to_datetime})"
            )

        # find all relevant setups

        relevant_setups: list[em27_metadata.types.SetupsListItem] = []
        for setup in sensor.setups:
            if (from_datetime <= setup.from_datetime <= to_datetime
               ) or (from_datetime <= setup.to_datetime <= to_datetime):
                relevant_setups.append(setup)

        for s1, s2 in zip(relevant_setups[:-1], relevant_setups[1 :]):
            assert s1.to_datetime < s2.from_datetime, f"this should not happen, overlapping setups: {s1} and {s2}"

        # crop setups list to requested time period

        if relevant_setups[0].from_datetime < from_datetime:
            relevant_setups[0].from_datetime = from_datetime

        if relevant_setups[-1].to_datetime > to_datetime:
            relevant_setups[-1].to_datetime = to_datetime

        # create sensor data contexts

        sensor_data_contexts: list[em27_metadata.types.SensorDataContext] = []
        for setup in relevant_setups:
            if setup.from_datetime >= setup.to_datetime:
                continue

            location = next(
                filter(
                    lambda l: l.location_id == setup.value.location_id,
                    self.locations.root,
                )
            )
            atmospheric_profile_location: em27_metadata.types.LocationMetadata
            if setup.value.atmospheric_profile_location_id is not None:
                atmospheric_profile_location = next(
                    filter(
                        lambda l: l.location_id == setup.value.
                        atmospheric_profile_location_id,
                        self.locations.root,
                    )
                )
            else:
                atmospheric_profile_location = location

            sensor_data_contexts.append(
                em27_metadata.types.SensorDataContext(
                    sensor_id=sensor.sensor_id,
                    serial_number=sensor.serial_number,
                    from_datetime=setup.from_datetime,
                    to_datetime=setup.to_datetime,
                    location=location,
                    utc_offset=setup.value.utc_offset,
                    pressure_data_source=(
                        setup.value.pressure_data_source if
                        setup.value.pressure_data_source else sensor.sensor_id
                    ),
                    atmospheric_profile_location=atmospheric_profile_location,
                )
            )

        return sensor_data_contexts
