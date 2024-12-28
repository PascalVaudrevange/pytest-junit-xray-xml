import os.path
import pathlib
import platform
import time
from xml.etree.ElementTree import Element, ElementTree, indent
from xml.sax.saxutils import escape, quoteattr

from .exceptions import (
    MoreThanOneTestSummaryError,
    MoreThanOneTestIdError,
    MoreThanOneTestKeyError
)
from .utils import find_items_from_user_properties

from _pytest.reports import TestReport


class LogJunitXrayXml(object):
    def __init__(self, logfile: str, family: str, logging: str = "no",
                 log_passing_tests: bool = True) -> None:
        """

        :param family: determines the JUnit family
        :param logfile: name of the XML file
        :param log_passing_tests:
        """
        xmlfile = os.path.expanduser(os.path.expandvars(logfile))
        self.xmlfile = os.path.normpath(os.path.abspath(xmlfile))
        self.family = family
        self.logging = logging
        self.log_passing_tests = log_passing_tests
        self.suite_start_time = None
        self.element_tree = ElementTree(Element("test_suite"))

        if self.family == "legacy":
            self.family = "xunit1"

    @property
    def suite_node(self):
        result = self.element_tree.getroot()
        return result

    def _get_number_of_failed_tests(self) -> int:
        result = len(self.suite_node.findall("testcase/failure"))
        return result

    def _get_number_of_skipped_tests(self) -> int:
        result = len(self.suite_node.findall("testcase/skipped"))
        return result

    def _get_number_of_errors(self) -> int:
        result = len(self.suite_node.findall("testcase/error"))
        return result

    def _get_number_of_tests(self) -> int:
        result = len(self.suite_node.findall("testcase"))
        return result

    def pytest_sessionstart(self) -> None:
        self.suite_start_time = time.time()

    def pytest_sessionfinish(self) -> None:
        suite_stop_time = time.time()
        suite_time_delta = suite_stop_time - self.suite_start_time

        self.suite_node.set("name", "pytest")
        self.suite_node.set("tests", f"{len(self.suite_node)}")
        self.suite_node.set("time", f"{suite_time_delta:.3f}")
        self.suite_node.set("hostname", platform.node())
        self.suite_node.set(
            "failures",
            f"{self._get_number_of_failed_tests()}"
        )
        self.suite_node.set(
            "skipped",
            f"{self._get_number_of_skipped_tests()}"
        )
        self.suite_node.set("tests", f"{self._get_number_of_tests()}")
        self.suite_node.set("errors", f"{self._get_number_of_errors()}")
        indent(self.element_tree, space="    ", level=0)
        self.element_tree.write(
            self.xmlfile,
            xml_declaration='<?xml version="1.0" encoding="UTF-8"?>',
            encoding="UTF-8",
            method="xml"
        )

    def pytest_runtest_logstart(self, nodeid: str, location: list) -> None:
        self.location = location

    def pytest_runtest_logreport(self, report: TestReport) -> None:
        if report.when == "call" or report.failed:
            if self.family in ("xunit1", "xray"):
                test_result_node = Element(
                    "testcase",
                    classname="",
                    name=self.location[2],
                    file=pathlib.Path(self.location[0]).as_posix(),
                    line=f'{self.location[1]}',
                    duration=f'{report.duration}'
                )
            elif self.family == "xunit2":
                test_result_node = Element(
                    "testcase",
                    classname="",
                    name=self.location[2],
                    duration=f'{report.duration}'
                )
            else:
                raise NotImplementedError(
                    f"JUnit family '{self.family}' is not implemented. "
                    "Aborting."
                )
            self.suite_node.append(test_result_node)
            if report.when == "call":

                if report.passed:
                    pass
                elif report.failed:
                    failure_node = Element("failure")
                    failure_node.text = escape(report.longreprtext)
                    test_result_node.append(failure_node)
                elif report.skipped:
                    skipped_node = Element(
                        "skipped",
                        message=quoteattr(report.longreprtext)
                    )
                    test_result_node.append(skipped_node)
                _process_caplog_capstdout_capstderr(
                    report,
                    test_result_node,
                    self.logging,
                    self.log_passing_tests
                )
                if self.family == "xray":
                    properties_node = _get_properties_node(test_result_node)
                    _process_test_evidences(
                        report.user_properties,
                        properties_node
                    )
                    _process_test_description(
                        report.user_properties,
                        properties_node
                    )
                    _process_test_summary(
                        report.user_properties, properties_node
                    )
                    _process_test_key(report.user_properties, properties_node)
                    _process_test_id(report.user_properties, properties_node)

                    if len(properties_node) == 0:
                        test_result_node.remove(properties_node)
            elif report.failed:
                _process_error(report, test_result_node)


def _get_properties_node(test_result_node: Element) -> Element:
    properties_node = test_result_node.find("./properties")
    if properties_node:
        result = properties_node
    else:
        result = Element("properties")
        test_result_node.append(result)
    return result


def _process_test_evidences(user_properties: list[tuple[str, object]],
                            properties_node: Element) -> None:
    test_evidences = find_items_from_user_properties(
        user_properties,
        "test_evidence"
    )
    if test_evidences:
        test_evidence_node = Element(
            "property", name="testrun_evidence"
        )
        for test_evidence_ in test_evidences:
            item_node = Element("item", name=test_evidence_["filename"])
            item_node.text = test_evidence_["content"]
            test_evidence_node.append(item_node)
        properties_node.append(test_evidence_node)


def _process_test_description(user_properties: list[tuple[str, object]],
                              properties_node: Element) -> None:
    test_descriptions = find_items_from_user_properties(
        user_properties,
        "test_description"
    )
    if test_descriptions:
        test_description = "\n".join(test_descriptions)
        property_node = Element("property", name="test_description")
        property_node.text = escape(test_description)
        properties_node.append(property_node)


def _process_test_summary(user_properties: list[tuple[str, object]],
                          properties_node: Element) -> None:
    test_summary = find_items_from_user_properties(
        user_properties,
        "test_summary"
    )
    if test_summary:
        if len(test_summary) > 1:
            raise MoreThanOneTestSummaryError(
                f"Found {len(test_summary)} test summaries: '{test_summary}'",
            )
        property_node = Element(
            "property",
            name="test_summary",
            value=test_summary[0]
        )
        properties_node.append(property_node)


def _process_test_id(user_properties: list[tuple[str, object]],
                     properties_node: Element) -> None:
    test_id = find_items_from_user_properties(user_properties, "test_id")
    if test_id:
        if len(test_id) > 1:
            raise MoreThanOneTestIdError(
                f"Found {len(test_id)} test ids: 'test_id'"
            )
        property_node = Element("property", name="test_id", value=test_id[0])
        properties_node.append(property_node)


def _process_test_key(user_properties: list[tuple[str, object]],
                      properties_node: Element) -> None:
    test_keys = find_items_from_user_properties(user_properties, "test_key")
    if test_keys:
        if len(test_keys) > 1:
            raise MoreThanOneTestKeyError(
                f"Found {len(test_keys)} test keys: 'test_keys'",
            )
        property_node = Element(
            "property",
            name="test_key",
            value=test_keys[0]
        )
        properties_node.append(property_node)


def _process_error(report: TestReport, test_result_node: Element) -> None:
    reprcrash = getattr(report.longrepr, "reprcrash", None)
    message = quoteattr(
        f"error during {report.when}: {reprcrash or str(report.longrepr)}"
    )
    error_node = Element("error", message=message)
    test_result_node.append(error_node)


def _process_caplog_capstdout_capstderr(report: TestReport,
                                        test_result_node: Element,
                                        logging: str,
                                        log_passing_tests: str) -> None:
    def _prepare_content(self, content: str, header: str) -> str:
        return escape("\n".join([header.center(80, "-"), content, ""]))

    if report.passed and not log_passing_tests:
        pass
    else:
        stdout = ""
        if report.caplog and logging in ["all", "log"]:
            stdout += _prepare_content(report.longreprtext, " Captured Log ")
        if report.capstdout and logging in ["all", "log"]:
            stdout += _prepare_content(report.longreprtext, " Captured Out ")
        if stdout:
            stdout_node = Element("system-out")
            stdout_node.text = stdout
            test_result_node.append(stdout_node)
        if report.capstderr and logging in ["system-err", "out-err", "all"]:
            stderr_node = Element("system-err")
            stderr_node.text = _prepare_content(
                report.longreprtext,
                " Captured Err "
            )
            test_result_node.append(stderr_node)
