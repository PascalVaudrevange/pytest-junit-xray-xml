from xml.etree import ElementTree

import pytest
from _pytest.pytester import Pytester


def btest_record_fail():
    assert False

def btest_skipped():
    pytest.skip()
    assert False


class bTestErrorDuringSetup():
    def setup_method(self, test_method):
        raise ValueError("Intentional error during setup")
    def test_pass(self):
        assert True


class TbestErrorDuringTeardown():
    def teardown_method(self, test_method):
        raise ValueError("Intentional error during teardown")
    def test_pass(self):
        assert True

def run_and_parse(pytester: Pytester, family: str| None = "xunit1") -> tuple:
    if family:
        args = ("-o", "junit_family=" + family, *args)
    xml_path = pytester.path.joinpath("xray.xml")
    result = pytester.runpytest(f"--junitxrayxml={xml_path}")
    if family == "xunit2":
        with xml_path.open(encoding="utf-8") as f:
            pass#schema.validate(f)
    xmldoc = ElementTree.parse(str(xml_path))
    return result, xmldoc.getroot()


def test_single_evidence(pytester: Pytester):
    pytester.makepyfile("""
    import pytest
    from pytest_junit_xray import record_test_evidence


    def test_record_pass(record_test_evidence):
        evidences = {
            "file1.txt": "My file content is text".encode("UTF-8")
        }
        record_test_evidence(evidences)
        assert True

    """)
    _, root_node = run_and_parse(pytester, None)
    actual_evidence = root_node.find("./testcase/properties/property[@name='testrun_evidence']/item[@name='file1.txt']")
    assert actual_evidence.text == "TXkgZmlsZSBjb250ZW50IGlzIHRleHQ="


def test_single_description(pytester: Pytester):
    expected_description = "This is my test description"
    pytester.makepyfile(f"""
    import pytest
    from pytest_junit_xray import record_test_description


    def test_record_pass(record_test_description):
        record_test_description("{expected_description}")
        assert True

    """)
    _, root_node = run_and_parse(pytester, None)
    actual_description = root_node.find("./testcase/properties/property[@name='test_description']")
    assert actual_description.text == expected_description


def test_single_summary(pytester: Pytester):
    expected_summary = "This is my test summary"
    pytester.makepyfile(f"""
    import pytest
    from pytest_junit_xray import record_test_summary


    def test_record_pass(record_test_summary):
        record_test_summary("{expected_summary}")
        assert True

    """)
    _, root_node = run_and_parse(pytester, None)
    actual_description = root_node.find("./testcase/properties/property[@name='test_summary']")
    assert actual_description.attrib["value"]== expected_summary


def test_single_key(pytester: Pytester):
    expected_key = "JIRA-1234"
    pytester.makepyfile(f"""
    import pytest
    from pytest_junit_xray import record_test_key


    def test_record_pass(record_test_key):
        record_test_key("{expected_key}")
        assert True

    """)
    _, root_node = run_and_parse(pytester, None)
    actual_key = root_node.find("./testcase/properties/property[@name='test_key']")
    assert actual_key.attrib["value"]== expected_key