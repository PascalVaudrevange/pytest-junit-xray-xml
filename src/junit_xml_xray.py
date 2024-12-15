import os.path
import pathlib
import platform
import time
from typing import TYPE_CHECKING
from xml.sax.saxutils import escape, quoteattr

from lxml import etree

from .exceptions import MoreThanOneTestDescriptionError

#if TYPE_CHECKING:
from _pytest.config import Config
from _pytest.config.argparsing import Parser
from _pytest.nodes import Item
from _pytest.reports import TestReport
from _pytest.runner import CallInfo

class Element(etree._Element):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class LogJunitXrayXml(object):
    def __init__(self, logfile: str, logging: str = "no", log_passing_tests: bool = True) -> None:
        """

        :param logfile: name of the XML file
        """
        xmlfile = os.path.expanduser(os.path.expandvars(logfile))
        self.xmlfile = os.path.normpath(os.path.abspath(xmlfile))
        self.logging = logging
        self.log_passing_tests = log_passing_tests
        self.suite_start_time = None
        self.suite_node_attributes = {}
        root = etree.XML('<?xml version="1.0"?><test_suite/>')
        self.element_tree = etree.ElementTree(root)
        #self._suite_node = etree.Element(
        #    "test_suite"
        #)
        self.test_result_node = None
    
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
        self.suite_node.set("failures", f"{self._get_number_of_failed_tests()}")
        self.suite_node.set("skipped", f"{self._get_number_of_skipped_tests()}")
        self.suite_node.set("tests", f"{self._get_number_of_tests()}")
        self.suite_node.set("errors", f"{self._get_number_of_errors()}")
        self.element_tree.write(self.xmlfile, pretty_print=True, doctype='<?xml version="1.0" encoding="UTF-8"?>')

    def pytest_runtest_logstart(self, nodeid: str, location: list) -> None:
        self.test_result_node = etree.Element(
            "testcase",
            classname="",
            name=location[2],
            file=pathlib.Path(location[0]).as_posix(),
            line=f'{location[1]}'
        )
        self.suite_node.append(self.test_result_node)

    def pytest_runtest_logreport(self, report: TestReport) -> None:
        self.test_result_node.attrib['duration'] = f'{report.duration}'
        if report.when == "call":
            if report.passed:
                pass
            elif report.failed:
                failure_node = etree.Element("failure")
                failure_node.text = escape(report.longreprtext)
                self.test_result_node.append(failure_node)
            elif report.skipped:
                skipped_node = etree.Element("skipped", message=quoteattr(report.longreprtext))
                self.test_result_node.append(skipped_node)
            _process_caplog_capstdout_capstderr(report, self.test_result_node, self.logging, self.log_passing_tests)
            _process_test_evidences(report.user_properties, self.test_result_node)
            _process_test_description(report.user_properties, self.test_result_node)
        else:
            _process_error(report, self.test_result_node)

def _find_items_from_user_properties(user_properties: list[tuple], name: str) -> list:
    result = [
        item_
        for name_, item_ in user_properties
        if name_ == name
    ]
    return result


def _process_test_evidences(user_properties: list[tuple[str, object]], test_result_node: etree.Element) -> None:
    test_evidences = _find_items_from_user_properties(user_properties, "test_evidence")
    if test_evidences:
        test_evidence_node = etree.Element(
            "property", name="testrun_evidence"
        )
        for test_evidence_ in test_evidences:
            test_evidence_node.append(test_evidence_)
        test_result_node.append(test_evidence_node)

def _process_test_description(user_properties: list[tuple[str, object]], test_result_node: etree.Element) -> None:
    test_descriptions = _find_items_from_user_properties(user_properties, "test_description")
    if test_descriptions:
        if len(test_descriptions) > 1:
            raise MoreThanOneTestDescriptionError(
                "Found %d test description: '%s'",
                len(test_descriptions), test_descriptions
            )
        property_node = etree.Element("property", test_descriptions=quoteattr(test_descriptions[0]))
        test_result_node.append(property_node)

def _process_error(report: TestReport, test_result_node: etree.Element) -> None:
    if report.failed:
        reprcrash = getattr(report.longrepr, "reprcrash", None)
        message = quoteattr(f"error during {report.when}: {reprcrash or str(report.longrepr)}")
        error_node = etree.Element("error", message=message)
        test_result_node.append(error_node)

def _process_caplog_capstdout_capstderr(report: TestReport, test_result_node: etree.Element, logging: str, log_passing_tests: str) -> None:
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
            stdout_node = etree.Element("system-out")
            stdout_node.text = stdout
            test_result_node.append(stdout_node)
        if report.capstderr and logging in ["system-err", "out-err", "all"]:
            stderr_node = etree.Element("system-err")
            stderr_node.text = _prepare_content(report.longreprtext, " Captured Err ")
            test_result_node.append(stderr_node)
