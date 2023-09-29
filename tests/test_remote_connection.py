import os
import pytest
import em27_metadata
import dotenv


@pytest.mark.library
def test_remote_connection() -> None:
    dotenv.load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

    em27_metadata.load_from_github(
        "tum-esm/em27-metadata",
        access_token=os.getenv("GITHUB_ACCESS_TOKEN"),
    )
