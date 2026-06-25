import tomllib

import cellcheck


def test_package_exposes_version() -> None:
    assert hasattr(cellcheck, "__version__")
    assert isinstance(cellcheck.__version__, str)
    assert cellcheck.__version__ == "0.40.1"


def test_pyproject_version_matches_package_version() -> None:
    with open("pyproject.toml", "rb") as pyproject_file:
        pyproject = tomllib.load(pyproject_file)

    assert pyproject["project"]["version"] == "0.40.1"
    assert pyproject["project"]["version"] == cellcheck.__version__
