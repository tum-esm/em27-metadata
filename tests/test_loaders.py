import os
import pytest
import em27_metadata
import dotenv

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.mark.library
def test_remote_loader_public_repo() -> None:
    em27_metadata.load_from_github("tum-esm/em27-metadata")


@pytest.mark.library
def test_remote_loader_private_repo() -> None:
    env_file = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_file):
        dotenv.load_dotenv(env_file)
    access_token = os.getenv("TUM_ESM_GITHUB_ACCESS_TOKEN")
    assert access_token is not None
    assert access_token.startswith("github_pat_")
    em27_metadata.load_from_github(
        "tum-esm/em27-metadata-storage", access_token=access_token
    )


@pytest.mark.library
def test_local_loader() -> None:
    em27_metadata.load_from_local_files(
        locations_path=os.path.join(
            PROJECT_DIR, "em27_metadata", "sample-data", "locations.json"
        ),
        sensors_path=os.path.join(
            PROJECT_DIR, "em27_metadata", "sample-data", "sensors.json"
        ),
        campaigns_path=os.path.join(
            PROJECT_DIR, "em27_metadata", "sample-data", "campaigns.json"
        ),
    )
