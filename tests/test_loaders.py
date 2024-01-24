import os
import pytest
import em27_metadata
import dotenv

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.mark.library
def test_remote_loader() -> None:
    dotenv.load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
    em27_metadata.load_from_github(
        "tum-esm/em27-metadata",
        access_token=os.getenv("GITHUB_ACCESS_TOKEN"),
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
