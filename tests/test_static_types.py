import os
import sys
import pytest

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.mark.library
def test_with_mypy() -> None:
    print("removing old mypy cache")
    r1 = os.system(
        f"cd {PROJECT_DIR} && rm -rf .mypy_cache/3.*/em27_metadata && rm -rf .mypy_cache/3.*/tests"
    )
    assert r1 == 0, "command returned non-zero exit code"

    print("checking em27_metadata/")
    r2 = os.system(f"cd {PROJECT_DIR} && {sys.executable} -m mypy em27_metadata/")
    assert r2 == 0, "command returned non-zero exit code"

    print("checking tests/")
    r3 = os.system(f"cd {PROJECT_DIR} && {sys.executable} -m mypy tests/")
    assert r3 == 0, "command returned non-zero exit code"


@pytest.mark.library
def test_with_pyright() -> None:
    assert os.system(f"cd {PROJECT_DIR} && {sys.executable} -m pyright") == 0
