import logging

from lakeventory.logging_config import configure_logging


def test_configure_logging_debug():
    level = configure_logging("debug")
    assert level == logging.DEBUG


def test_configure_logging_verbose_maps_to_info():
    level = configure_logging("verbose")
    assert level == logging.INFO


def test_configure_logging_error():
    level = configure_logging("error")
    assert level == logging.ERROR
