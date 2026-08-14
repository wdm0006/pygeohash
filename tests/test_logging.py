import io
import logging
from pathlib import Path
from typing import Iterator

import pytest

import pygeohash as pgh


@pytest.fixture(autouse=True)
def reset_pygeohash_logging() -> Iterator[None]:
    pgh.remove_all_handlers()
    pgh.set_log_level(logging.NOTSET)
    yield
    pgh.remove_all_handlers()
    pgh.set_log_level(logging.NOTSET)


def test_stream_handler_emits_debug_records() -> None:
    stream = io.StringIO()

    pgh.add_stream_handler(level=logging.DEBUG, stream=stream)
    pgh.get_adjacent("u4pruyd", "top")

    output = stream.getvalue()
    assert "Finding adjacent geohash for u4pruyd in direction top" in output
    assert "pygeohash.neighbor" in output
    assert "pygeohash.pygeohash" not in output


def test_stream_handler_default_emits_warning_records() -> None:
    stream = io.StringIO()

    pgh.add_stream_handler(stream=stream)
    pgh.mean([])

    assert "Empty geohash collection provided" in stream.getvalue()


def test_stream_handler_default_delivers_info_records() -> None:
    stream = io.StringIO()
    root_logger = logging.getLogger()
    original_root_level = root_logger.level
    root_logger.setLevel(logging.WARNING)

    try:
        pgh.add_stream_handler(stream=stream)
        pgh.logger.info("info level record")
    finally:
        root_logger.setLevel(original_root_level)

    assert "info level record" in stream.getvalue()


def test_file_handler_emits_records(tmp_path: Path) -> None:
    log_file = tmp_path / "pygeohash.log"

    pgh.add_file_handler(str(log_file), level=logging.DEBUG)
    pgh.get_adjacent("u4pruyd", "top")

    assert "Finding adjacent geohash for u4pruyd in direction top" in log_file.read_text()


def test_stream_handler_does_not_configure_root_logger() -> None:
    root_logger = logging.getLogger()
    original_handlers = list(root_logger.handlers)
    original_level = root_logger.level

    pgh.add_stream_handler(stream=io.StringIO())

    assert root_logger.handlers == original_handlers
    assert root_logger.level == original_level


def test_module_loggers_use_fully_qualified_names() -> None:
    import pygeohash.bounding_box  # noqa: F401
    import pygeohash.distances  # noqa: F401
    import pygeohash.geohash  # noqa: F401
    import pygeohash.neighbor  # noqa: F401
    import pygeohash.stats  # noqa: F401
    import pygeohash.types  # noqa: F401

    names = [name for name in logging.Logger.manager.loggerDict if name.startswith("pygeohash")]
    assert not any(name.startswith("pygeohash.pygeohash") for name in names)


def test_module_logger_handler_receives_neighbor_records() -> None:
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setLevel(logging.DEBUG)
    module_logger = logging.getLogger("pygeohash.neighbor")
    original_level = module_logger.level
    module_logger.setLevel(logging.DEBUG)
    module_logger.addHandler(handler)

    try:
        pgh.get_adjacent("u4pruyd", "top")
    finally:
        module_logger.removeHandler(handler)
        module_logger.setLevel(original_level)

    assert "Finding adjacent geohash for u4pruyd in direction top" in stream.getvalue()


def test_get_logger_preserves_bare_child_name() -> None:
    assert pgh.get_logger("myapp").name == "pygeohash.myapp"


def test_get_logger_returns_package_logger_for_package_name() -> None:
    assert pgh.get_logger("pygeohash") is pgh.logger


def test_remove_all_handlers_restores_only_null_handler() -> None:
    pgh.add_stream_handler(stream=io.StringIO())

    pgh.remove_all_handlers()

    assert len(pgh.logger.handlers) == 1
    assert isinstance(pgh.logger.handlers[0], logging.NullHandler)
