import cellcheck


def test_package_exposes_version() -> None:
    assert hasattr(cellcheck, "__version__")
    assert isinstance(cellcheck.__version__, str)
