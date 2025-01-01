import base64
import logging
import xml.etree.ElementTree as ET

from _pytest.pytester import Pytester

logger = logging.getLogger(__name__)


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


def run_and_parse(pytester: Pytester, family: str = "xunit1") -> tuple:
    if family:
        args = ("-o", "junit_family=" + family)
    else:
        args = ()
    xml_path = pytester.path / "xray.xml"
    result = pytester.runpytest(f"--junitxrayxml={xml_path}", *args)
    if family == "xunit2":
        with xml_path.open(encoding="utf-8") as f:
            pass  # schema.validate(f)
    xmldoc = ET.parse(str(xml_path))
    return result, xmldoc.getroot()


def test_single_description(pytester: Pytester):
    expected_description = "This is my test description"
    pytester.makepyfile(f"""
    import pytest
    from pytest_junit_xray_xml import record_test_description


    def test_record_single_description(record_test_description):
        record_test_description("{expected_description}")
        assert True

    """)
    _, root_node = run_and_parse(pytester, None)
    actual_description = root_node.find(
        "./testcase/properties/property[@name='test_description']"
    )
    assert actual_description.text == expected_description


def test_multiple_descriptions(pytester: Pytester):
    expected_description = "This is my test description line 1\nand line 2."
    pytester.makepyfile("""
    import pytest
    from pytest_junit_xray_xml import record_test_description


    def test_record_multiple_descriptions(record_test_description):
        record_test_description("This is my test description line 1")
        record_test_description("and line 2.")
        assert True

    """)
    _, root_node = run_and_parse(pytester, None)
    actual_description = root_node.find(
        "./testcase/properties/property[@name='test_description']"
    )
    assert actual_description.text == expected_description


def test_single_summary(pytester: Pytester):
    expected_summary = "This is my test summary"
    pytester.makepyfile(f"""
    from pytest_junit_xray_xml import record_test_summary

    def test_record_pass(record_test_summary):
        record_test_summary("{expected_summary}")
        assert True

    """)
    _, root_node = run_and_parse(pytester, None)
    actual_description = root_node.find(
        "./testcase/properties/property[@name='test_summary']"
    )
    assert actual_description.attrib["value"] == expected_summary


def test_multiple_summaries(pytester: Pytester):
    pytester.makepyfile("""
    from pytest_junit_xray_xml import record_test_summary

    def test_record_pass(record_test_summary):
        record_test_summary("Summary 1")
        record_test_summary("Summary 2")
        assert True
    """)

    result, _ = run_and_parse(pytester, None)
    result.assert_outcomes(failed=1)
    result.stdout.fnmatch_lines(
        "* pytest_junit_xray_xml.exceptions.MoreThanOneItemError: Found a "
        "'test_summary' already: '['Summary 1'*"
    )


def test_single_key(pytester: Pytester):
    expected_key = "JIRA-1234"
    pytester.makepyfile(f"""
    from pytest_junit_xray_xml import record_test_key

    def test_record_test_key(record_test_key):
        record_test_key("{expected_key}")
        assert True

    """)
    _, root_node = run_and_parse(pytester, None)
    actual_key = root_node.find(
        "./testcase/properties/property[@name='test_key']"
    )
    assert actual_key.attrib["value"] == expected_key


def test_pass(pytester: Pytester):
    pytester.makepyfile("""
    def test_pass():
        assert True
    """)
    _, root_node = run_and_parse(pytester, None)
    node = root_node.find(
        "./testcase[@name='test_pass']"
    )
    assert len(node) == 0, ET.tostring(node)


def test_record_test_evidence_text(pytester: Pytester):
    encoding = "UTF-8"
    file_content = "My file content is text"
    pytester.makepyfile(f"""
    from pytest_junit_xray_xml import record_test_evidence

    def test_record_test_evidence(record_test_evidence):
        with record_test_evidence("file1.txt", "w", encoding="{encoding}") as f:
            f.write("{file_content}")
        assert True
    """)
    _, root_node = run_and_parse(pytester, None)
    actual_evidence = root_node.find(
        "./testcase/properties"
        "/property[@name='testrun_evidence']/item[@name='file1.txt']"
    ).text
    expected_evidence = base64.b64encode(file_content.encode(encoding)).decode("us-ascii")
    assert actual_evidence == expected_evidence


def test_record_test_evidence_xml(pytester: Pytester):
    pytester.makepyfile("""
    from xml.etree.ElementTree import ElementTree, Element, canonicalize
    from pytest_junit_xray_xml import record_test_evidence

    def test_record_test_evidence(record_test_evidence):
        xml_content = ElementTree(Element("my_root", my_attribute="1"))
        with record_test_evidence("file1.xml", "wb") as f:
            xml_content.write(f)

        assert True
    """)
    _, root_node = run_and_parse(pytester, None)
    test_evidence = (
        root_node.find(
            "./testcase/properties"
            "/property[@name='testrun_evidence']/item[@name='file1.xml']"
        )
        .text
        .encode("us-ascii")
    )
    actual_evidence = ET.canonicalize(base64.b64decode(test_evidence))
    xml_content = ET.Element("my_root", my_attribute="1")
    expected_evidence = ET.canonicalize(ET.tostring(xml_content))
    assert actual_evidence == expected_evidence
