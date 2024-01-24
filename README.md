# EM27 Metadata

## The purpose of this library

This repository is the single source of truth for our EM27 measurement logistics: "Where has each station been on each day of measurements?" We selected this format over putting it in a database due to various reasons:

- Easy to read, modify and extend by selective group members using GitHub permissions
- Changes to this are more evident here than in database logs
- Versioning (easy to revert mistakes)
- Automatic testing of the files integrities
- Easy import as a statically typed Python library

<br/>

## How it works

This repository only contains a Python library to interact with the metadata. The metadata itself is stored in local files or a GitHub repository. The library can load the metadata from both sources and provides a unified interface with static types to access it.

<br/>

## Library Usage

Install as a library:

```bash
poetry add em27_metadata
# or
pip install em27_metadata
```

```python
import datetime
import em27_metadata

em27_metadata_store = em27_metadata.load_from_github(
    github_repository="org-name/repo-name",
    access_token="your-github-access-token",
)

# or load it from local files
em27_metadata_store = em27_metadata.load_from_local_files(
    locations_path="location-data/locations.json",
    sensors_path="location-data/sensors.json",
    campaigns_path="location-data/campaigns.json",
)

metadata = location_data.get(
      sensor_id="sid1",
      from_datetime=datetime.datetime(
          2020, 8, 26, 0, 0, 0, tzinfo=datetime.timezone.utc
      ),
      to_datetime=datetime.datetime(
          2020, 8, 26, 23, 59, 59, tzinfo=datetime.timezone.utc
      ),
  )
  print(metadata)
```

Prints out something like this:

```json
[
  {
    "sensor_id": "sid1",
    "serial_number": 50,
    "from_datetime": "2020-08-26T00:00:00+0000",
    "to_datetime": "2020-08-26T23:59:59+0000",
    "location": {
      "location_id": "lid1",
      "details": "description of location 1",
      "lon": 10.5,
      "lat": 48.1,
      "alt": 500.0
    },
    "utc_offset": 2.0,
    "pressure_data_source": "LMU-MIM01-height-adjusted",
    "calibration_factors": {
      "pressure": 1.001,
      "xco2": {
        "factors": [1.001, 0.0007],
        "scheme": "Ohyama2021",
        "note": null
      },
      "xch4": {
        "factors": [1.002, 0.0008],
        "scheme": "Ohyama2021",
        "note": null
      },
      "xco": {
        "factors": [1.003, 0.0009],
        "scheme": "Ohyama2021",
        "note": null
      }
    },
    "atmospheric_profile_location": {
      "location_id": "lid1",
      "details": "description of location 1",
      "lon": 10.5,
      "lat": 48.1,
      "alt": 500.0
    }
  }
]
```

The object returned by `em27_metadata_store.get()` is of type `list[em27_metadata.types.SensorDataContext]`. It is a Pydantic model (https://docs.pydantic.dev/) but can be converted to a dictionary using `metadata.model_dump()`.

The list will contain one item per time period where the metadata properties are continuous (same setup, and same calibration factors). You can find dummy data in the `data/` folder.

<br/>

## Set up an EM27 Metadata Storage Directory

You can use the repository https://github.com/tum-esm/em27-metadata-storage-template to create your own repository for storing the metadata. It contains a GitHub Actions workflow that automatically validates the metadata on every commit in any branch.

<br/>

## For Developers

Run tests:

```bash
# used inside the GitHub CI for this repo
pytest -m "ci"

# used inside the GitHub Actions workflow for storage repos
pytest -m "action"

# can be used for local development (libe "ci", but skips pulling from GitHub)
pytest -m "local"
```

Publish the Package to PyPI:

```bash
poetry build
poetry publish
```
