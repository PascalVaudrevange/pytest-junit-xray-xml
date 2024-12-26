import pytest

from . import junit_xml_xray

from _pytest.config import Config
from _pytest.config.argparsing import Parser


def pytest_addoption(parser: Parser) -> None:
    """Add pytest-junit-xray options"""
    group = parser.getgroup("junit_xray")
    group.addoption(
        "--junitxrayxml",
        "--junit-xray-xml",
        action="store",
        dest="junit_xray_xml_path",
        metavar="path",
        default=None,
        help=(
            "create Junit XML test reports with extra nodes for consumption"
            "by the Jira plugin Xray"
        )
    )
    parser.addini(
        "junit_suite_name",
        "Test suite name for JUnit report",
        default="pytest"
    )
    parser.addini(
        "junit_log_passing_tests",
        "Capture log information for passing tests to JUnit report.",
        type="bool",
        default=True
    )
    parser.addini(
        "junit_logging",
        "Write captured log messages to JUnit report: "
        "one of no|log|system-out|system-err|out-err|all",
        default="no"
    )


@pytest.hookimpl(trylast=True)
def pytest_configure(config: Config) -> None:
    xml_path = config.option.junit_xray_xml_path
    # prevent opening xml on work nodes (xdist)
    if xml_path and not hasattr(config, "workerinput"):
        config._junitxray = junit_xml_xray.LogJunitXrayXml(xml_path)
        config.pluginmanager.register(config._junitxray)


def pytest_unconfigure(config: Config) -> None:
    junitxray = getattr(config, "_junitxray", None)
    if junitxray is not None:
        del config._junitxray
        config.pluginmanager.unregister(junitxray)
