from xml.etree.ElementTree import ElementTree, Element, canonicalize
from pytest_junit_xray_xml import (
    record_test_evidence,
    record_test_description,
    record_test_summary,
    record_test_key
)


def test_record_single_description(record_test_description):
    record_test_description("This is my test description")
    assert True


def test_record_multiple_descriptions(record_test_description):
    record_test_description("This is my test description line 1")
    record_test_description("and line 2.")
    assert True


def test_record_test_key(record_test_key):
    record_test_key("JIRA-1234")
    assert True


def test_record_summary(record_test_summary):
    record_test_summary("This is my test summary")
    assert True


def test_store_test_evidence(record_test_evidence):
    with record_test_evidence("file1.txt", "w", encoding="UTF-8") as f:
        f.write("My file content is text")
    assert True


def test_store_test_evidence_xml(record_test_evidence):
    xml_content = ElementTree(Element("my_root", my_attribute="1"))
    with record_test_evidence("file1.xml", "wb") as f:
        xml_content.write(f)
    assert True
