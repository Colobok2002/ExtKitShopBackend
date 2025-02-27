from ext_kit_shop import _version  # noqa: D104

__all__ = (
    "__appname__",
    "__version__",
)

__appname__ = "app_name"
__version__ = _version.get_versions()["version"]
