import json
from typing import Any, Callable, Literal, Optional
import tum_esm_utils
from tum_esm_em27_metadata import types, interfaces


def load_from_github(
    github_repository: str,
    access_token: Optional[str] = None,
) -> interfaces.EM27MetadataInterface:
    """loads an EM27MetadataInterface from GitHub"""

    _req: Callable[[str], Any] = lambda t: json.loads(
        tum_esm_utils.github.request_github_file(
            github_repository=github_repository,
            filepath=f"data/{t}.json",
            access_token=access_token,
        )
    )

    return interfaces.EM27MetadataInterface(
        locations=[types.Location(**l) for l in _req("locations")],
        sensors=[types.Sensor(**l) for l in _req("sensors")],
        campaigns=[types.Campaign(**l) for l in _req("campaigns")],
    )

