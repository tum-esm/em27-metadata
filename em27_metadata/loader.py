from typing import Any, Callable, Literal, Optional, List, Dict
import json
import requests
import em27_metadata


def _request_github_file(
    github_repository: str,
    filepath: str,
    access_token: Optional[str] = None,
) -> List[Dict[Any, Any]]:
    """Sends a request and returns the content of the response,
    as a string. Raises an HTTPError if the response status code
    is not 200."""

    url = f"https://raw.githubusercontent.com/{github_repository}/main/{filepath}"
    response = requests.get(
        url,
        headers={
            "Authorization": f"token {access_token}",
            "Accept": "application/text",
        },
        timeout=10,
    )
    response.raise_for_status()
    try:
        response = json.loads(response.text)
        assert isinstance(response, List)
        assert all(isinstance(r, Dict) for r in response)
        return response
    except (json.JSONDecodeError, AssertionError):
        raise ValueError(f"file at '{url}' is not a valid json file")


def load_from_github(
    github_repository: str,
    access_token: Optional[str] = None,
) -> em27_metadata.interfaces.EM27MetadataInterface:
    """Loads an EM27MetadataInterface from GitHub"""

    _req: Callable[[str], List[Dict[Any,
                                    Any]]] = lambda t: _request_github_file(
                                        github_repository=github_repository,
                                        filepath=f"data/{t}.json",
                                        access_token=access_token,
                                    )
    return em27_metadata.interfaces.EM27MetadataInterface(
        locations=[
            em27_metadata.types.LocationMetadata(**l)
            for l in _req("locations")
        ],
        sensors=[
            em27_metadata.types.SensorMetadata(**l) for l in _req("sensors")
        ],
        campaigns=[
            em27_metadata.types.CampaignMetadata(**l)
            for l in _req("campaigns")
        ],
    )


def _load_json_list(
    filepath: Optional[str], name: Literal["locations", "sensors", "campaigns"]
) -> List[Dict[Any, Any]]:
    if filepath is None:
        return []
    try:
        with open(filepath) as f:
            response = json.load(f)
        assert isinstance(response, List)
        assert all(isinstance(r, Dict) for r in response)
        return response
    except FileNotFoundError:
        raise ValueError(f"{name} file at ({filepath}) does not exist")
    except json.JSONDecodeError:
        raise ValueError(
            f"{name} file at ({filepath}) is not a valid json file"
        )
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
        locations=[
            em27_metadata.types.LocationMetadata(**l) for l in locations
        ],
        sensors=[em27_metadata.types.SensorMetadata(**l) for l in sensors],
        campaigns=[
            em27_metadata.types.CampaignMetadata(**l) for l in campaigns
        ],
    )
