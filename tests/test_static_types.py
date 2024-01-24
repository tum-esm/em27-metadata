import os
import sys
import pytest

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.mark.library
def test_static_types() -> None:
    print("removing old mypy cache")
    r1 = os.system(f"cd {PROJECT_DIR} && rm -rf .mypy_cache")
    assert r1 == 0, "command returned non-zero exit code"

    print("checking em27_metadata/")
    r2 = os.system(
        f"cd {PROJECT_DIR} && {sys.executable} -m mypy em27_metadata/"
    )
    assert r2 == 0, "command returned non-zero exit code"

    print("checking tests/")
    r3 = os.system(f"cd {PROJECT_DIR} && {sys.executable} -m mypy tests/")
    assert r3 == 0, "command returned non-zero exit code"
