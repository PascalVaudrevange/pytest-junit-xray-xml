import base64
import io
import typing

import pytest

from _pytest.fixtures import FixtureRequest

from .exceptions import MoreThanOneItemError
from .utils import find_items_from_user_properties


def _record_single_item(user_properties, key: str, value: str):
    items = find_items_from_user_properties(user_properties, key)
    if items:
        raise MoreThanOneItemError(
            f"Found a '{key}' already: '{items}'"
        )
    else:
        user_properties.append(
            (key, value)
        )


@pytest.fixture
def record_test_evidence(request: FixtureRequest) -> typing.Callable[[dict],
                                                                     None]:
    class InMemoryFile(io.BytesIO):
        def __init__(self, filename: str, mode: str = "wb",
                     encoding: str = "UTF-8", *args, **kwargs):
            self.__filename = filename
            self.__mode = mode
            self.__encoding = encoding
            super().__init__()

        def __exit__(self, *args, **kwargs):
            item = self._get_test_evidence_encoded(
                self.__filename, self.getvalue()
            )
            request.node.user_properties.append(
                ("test_evidence", item)
            )
            super().__exit__()

        def _get_test_evidence_encoded(self, name: str, content: str) -> dict:
            result = {
                "filename": name,
                "content": base64.b64encode(content).decode("ascii")
            }
            return result

        def write(self, b, *args, **kwargs):
            if "b" in self.__mode:
                super().write(b)
            elif self.__encoding is None:
                raise ValueError(
                    f"Calling InMemoryFile(filename='{self.__filename}', "
                    f"mode='{self.__mode}', encoding='{self.__encoding}') "
                    "is not supported: if mode is not binary, you must "
                    "supply an encoding"
                )
            else:
                super().write(b.encode(self.__encoding), *args, **kwargs)

    return InMemoryFile


@pytest.fixture
def record_test_key(request: FixtureRequest) -> typing.Callable[[str], None]:
    def _record_test_key(test_key: str) -> None:
        _record_single_item(request.node.user_properties, "test_key", test_key)
    return _record_test_key


@pytest.fixture
def record_test_id(request: FixtureRequest) -> typing.Callable[[str], None]:
    def _record_test_id(test_id: str) -> None:
        _record_single_item(request.node.user_properties, "test_id", test_id)
    return _record_test_id


@pytest.fixture
def record_test_summary(request: FixtureRequest) -> typing.Callable[[str],
                                                                    None]:
    def _record_test_summary(test_summary: str) -> None:
        _record_single_item(
            request.node.user_properties,
            "test_summary",
            test_summary
        )
    return _record_test_summary


@pytest.fixture
def record_test_description(request: FixtureRequest) -> typing.Callable[[str],
                                                                        None]:
    def _record_test_description(test_description: str) -> None:
        request.node.user_properties.append(
            ("test_description", test_description)
        )
    return _record_test_description
