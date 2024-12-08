import pytest
from pytest_junit_xray import record_test_evidence, record_test_description

def test_record_pass(record_test_evidence, record_test_description):
    evidences = {
        "file1": "My file content is text".encode("UTF-8")
    }
    record_test_description("This is my test description")
    record_test_evidence(evidences)
    assert True

def test_record_fail():
    assert False

def test_skipped():
    pytest.skip()
    assert False


class TestErrorDuringSetup():
    def setup_method(self, test_method):
        raise ValueError("Intentional error during setup")
    def test_pass(self):
        assert True


class TestErrorDuringTeardown():
    def teardown_method(self, test_method):
        raise ValueError("Intentional error during teardown")
    def test_pass(self):
        assert True