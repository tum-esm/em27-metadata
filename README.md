# EM27 Metadata

## The purpose of this library

TODO: write

<br/>

## Library Usage

Install as a library

```bash
poetry add tum-esm-em27-metadata
# or
pip install tum-esm-em27-metadata
```

```python
import tum_esm_em27_metadata

em27_metadata = tum_esm_em27_metadata.load_from_github(
    github_repository="org-name/repo-name",
    access_token="your-github-access-token",
)

# or load it from local files
em27_metadata = tum_esm_em27_metadata.load_from_local_files(
    locations_path="location-data/locations.json",
    sensors_path="location-data/sensors.json",
    campaigns_path="location-data/campaigns.json",
)

metadata = em27_metadata.get(
    sensor_id = "ma", date = "20220601"
)  # is of type tum_esm_em27_metadata.types.SensorDataContext

print(metadata.dict())
```

prints out:

```json
{
    "sensor_id": "ma",
    "serial_number": 61,
    "utc_offset": 0,
    "pressure_data_source": "ma",
    "pressure_calibration_factor": 1,
    "date": "20220601",
    "location": {
        "location_id": "TUM_I",
        "details": "TUM Dach Innenstadt",
        "lon": 11.569,
        "lat": 48.151,
        "alt": 539
    }
}
```

<br/>

## Set up an EM27 Metadata Storage Directory

TODO: write
