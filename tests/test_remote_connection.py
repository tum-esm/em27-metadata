import os
import pytest
from tum_esm_em27_metadata import interfaces


@pytest.mark.ci
@pytest.mark.action
def test_remote_connection() -> None:
    github_repository = os.getenv("GITHUB_REPOSITORY")
    access_token = os.getenv("GITHUB_ACCESS_TOKEN")

    assert github_repository is not None
    assert access_token is not None

    interfaces.load_from_github(github_repository, access_token)
