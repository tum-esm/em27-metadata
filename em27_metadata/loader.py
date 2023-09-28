from typing import Optional, List
import requests
import em27_metadata


def _request_github_file(
    github_repository: str,
    filepath: str,
    access_token: Optional[str] = None,
) -> str:
    """Sends a request and returns the content of the response,
    as a string.

    Args:
        github_repository:  The repository to load the metadata from, e.g. passing
                            "em27/em27-metadata" would mean that the repository is
                            hosted at `github.com/em27/em27-metadata`.
        filepath:           The path to the file to load, e.g. "data/locations.json".
        access_token:       The access token to use for the request. This is only
                            required if the GitHub repository is private. You can
                            read about these tokens at https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens.
    
    Raises:
        requests.exceptions.HTTPError:  If the request to GitHub fails.
    """

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
    return response.text


def load_from_github(
    github_repository: str,
    access_token: Optional[str] = None,
) -> em27_metadata.interfaces.EM27MetadataInterface:
    """Loads an EM27MetadataInterface from GitHub
    
    Args:
        github_repository:  The repository to load the metadata from, e.g. passing
                            "em27/em27-metadata" would mean that the repository is
                            hosted at `github.com/em27/em27-metadata`.
        access_token:       The access token to use for the request. This is only
                            required if the GitHub repository is private. You can
                            read about these tokens at https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens.
    
    Returns:  An metadata object containing all the metadata that can now be queried
              locally using `metadata.get`.

    Raises:
        requests.exceptions.HTTPError:  If the request to GitHub fails.
        pydantic.ValidationError:       If the response is not in a valid format.
    """

    return em27_metadata.interfaces.EM27MetadataInterface(
        locations=em27_metadata.types.LocationMetadataList.model_validate_json(
            '{"locations": ' + _request_github_file(
                github_repository=github_repository,
                filepath=f"data/locations.json",
                access_token=access_token,
            ) + "}"
        ).locations,
        sensors=em27_metadata.types.SensorMetadataList.model_validate_json(
            '{"sensors": ' + _request_github_file(
                github_repository=github_repository,
                filepath=f"data/sensors.json",
                access_token=access_token,
            ) + "}"
        ).sensors,
        campaigns=em27_metadata.types.CampaignMetadataList.model_validate_json(
            '{"campaigns": ' + _request_github_file(
                github_repository=github_repository,
                filepath=f"data/campaigns.json",
                access_token=access_token,
            ) + "}"
        ).campaigns,
    )


def load_from_local_files(
    locations_path: str,
    sensors_path: str,
    campaigns_path: Optional[str] = None,
) -> em27_metadata.interfaces.EM27MetadataInterface:
    """Loads an EM27MetadataInterface from local files.
    
    Args:
        locations_path:  path to the locations file, e.g. "data/locations.json"
        sensors_path:    path to the sensors file, e.g. "data/sensors.json"
        campaigns_path:  path to the campaigns file, e.g. "data/campaigns.json" not
                         required for the profile download and the retrieval in the
                         EM27 Retrieval Pipeline
    
    Returns:  An metadata object containing all the metadata that can now be queried
              locally using `metadata.get`.
    
    Raises:
        FileNotFoundError:              If a file does not exist.
        pydantic.ValidationError:       If a file is not in a valid format.
    """

    with open(locations_path) as f:
        locations = em27_metadata.types.LocationMetadataList.model_validate_json(
            f.read()
        ).locations

    with open(sensors_path) as f:
        sensors = em27_metadata.types.SensorMetadataList.model_validate_json(
            f.read()
        ).sensors

    campaigns: List[em27_metadata.types.CampaignMetadata] = []
    if campaigns_path is not None:
        with open(campaigns_path) as f:
            campaigns = em27_metadata.types.CampaignMetadataList.model_validate_json(
                f.read()
            ).campaigns

    return em27_metadata.interfaces.EM27MetadataInterface(
        locations=locations, sensors=sensors, campaigns=campaigns
    )
