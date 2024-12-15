import base64
import typing
from xml.etree.ElementTree import Element

import pytest

from _pytest.fixtures import FixtureRequest


def __get_test_evidence_property_item(name: str, content: str) -> Element:
    result = Element("item", name=name)
    result.text = base64.b64encode(content).decode("ascii")
    return result


@pytest.fixture
def record_test_evidence(request: FixtureRequest) -> typing.Callable[dict, None]:
    """records test evidence for consumption by the Jira Xray plugin
    
    The evidence is attached to the test run object in Jira/Xray as files with"
    names by their keys 
    """
    def _record_test_evidence(evidences: dict) -> None:
        for name_, evidence_ in evidences.items():
            item_ = __get_test_evidence_property_item(name_, evidence_)
            request.node.user_properties.append(
                ("test_evidence", item_)
            )
    return _record_test_evidence


@pytest.fixture
def record_test_id(request: FixtureRequest) -> typing.Callable[str, None]:
    def _record_test_id(test_id: str) -> None:
        request.node.user_properties.append(
            ("test_id", test_id)
        )
    return _record_test_id


@pytest.fixture
def record_test_summary(request: FixtureRequest) -> typing.Callable[str, None]:
    def _record_test_summary(test_summary: str) -> None:
        request.node.user_properties.append(
            ("test_summary", test_summary)
        )
    return _record_test_summary


@pytest.fixture
def record_test_description(request: FixtureRequest) -> typing.Callable[str, None]:
    def _record_test_description(test_description: str) -> None:
        request.node.user_properties.append(
            ("test_description", test_description)
        )
    return _record_test_description
