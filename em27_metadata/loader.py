import json
from typing import Any, Callable, Literal, Optional
import tum_esm_utils
import em27_metadata

def load_from_github(
    github_repository: str,
    access_token: Optional[str] = None,
) -> em27_metadata.interfaces.EM27MetadataInterface:
    """Loads an EM27MetadataInterface from GitHub"""

    _req: Callable[[str], Any] = lambda t: json.loads(
        tum_esm_utils.github.request_github_file(
            github_repository=github_repository,
            filepath=f"data/{t}.json",
            access_token=access_token,
        )
    )
    return em27_metadata.interfaces.EM27MetadataInterface(
        locations=[em27_metadata.types.LocationMetadata(**l) for l in _req("locations")],
        sensors=[em27_metadata.types.SensorMetadata(**l) for l in _req("sensors")],
        campaigns=[em27_metadata.types.CampaignMetadata(**l) for l in _req("campaigns")],
    )


def _load_json_list(
    filepath: Optional[str], name: Literal["locations", "sensors", "campaigns"]
) -> list[dict[Any, Any]]:
    if filepath is None:
        return []
    try:
        with open(filepath) as f:
            output = json.load(f)
            assert isinstance(output, list[dict[Any, Any]])
            return output
    except FileNotFoundError:
        raise ValueError(f"{name} file at ({filepath}) does not exist")
    except json.JSONDecodeError:
        raise ValueError(f"{name} file at ({filepath}) is not a valid json file")
    except AssertionError:
        raise ValueError(f"{name} file at ({filepath}) is not a list")


def load_from_local_files(
    locations_path: str,
    sensors_path: str,
    campaigns_path: Optional[str] = None,
) -> em27_metadata.interfaces.EM27MetadataInterface:
    """loads an EM27MetadataInterface from local files"""

    locations = _load_json_list(locations_path, "locations")
    sensors = _load_json_list(sensors_path, "sensors")
    campaigns = _load_json_list(campaigns_path, "campaigns")

    return em27_metadata.interfaces.EM27MetadataInterface(
        locations=[em27_metadata.types.LocationMetadata(**l) for l in locations],
        sensors=[em27_metadata.types.SensorMetadata(**l) for l in sensors],
        campaigns=[em27_metadata.types.CampaignMetadata(**l) for l in campaigns],
    )
