import os
import pytest


@pytest.mark.ci
@pytest.mark.local
def test_static_types() -> None:
    print("removing old mypy cache")
    r1 = os.system("rm -rf .mypy_cache")
    assert r1 == 0, "command returned non-zero exit code"

    print("checking tum_esm_em27_metadata/")
    r2 = os.system(".venv/bin/python -m mypy tum_esm_em27_metadata/")
    assert r2 == 0, "command returned non-zero exit code"

    print("checking tests/")
    r3 = os.system(".venv/bin/python -m mypy tests/")
    assert r3 == 0, "command returned non-zero exit code"
