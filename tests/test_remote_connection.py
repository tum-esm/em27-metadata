import os
import pytest
import em27_metadata
import dotenv


@pytest.mark.ci
@pytest.mark.action
def test_remote_connection() -> None:

    dotenv.load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

    github_repository = os.getenv("GITHUB_REPOSITORY")
    access_token = os.getenv("GITHUB_ACCESS_TOKEN")

    assert github_repository is not None
    assert access_token is not None

    em27_metadata.load_from_github(github_repository, access_token)
