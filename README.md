# pytest-junit-xray-xml
This plugin for [pytest](https://pytest.org) exports test results in an extended JUnit format for consumption by the [Xray plugin](https://www.getxray.app/)
 for [Jira](https://www.atlassian.com/software/jira).

This plugin aims to also be a drop-in replacement for `pytest`'s built-in JUnit support, so all non-Xray-related functionality will (hopefully soon) be supported.
## Rationale
The JUnit support in `pytest` does not allow for the following features:
- it is not possible to generate `<item>` elements as subnodes of a `<property>` tag (needed for storing test evidence)
- it is not possible to store `text` in a `property` tag

## Installation
This package is available on [pypi.org](https://pypi.org/project/pytest-junit-xray-xml/)
```shell
python -m pip install pytest-junit-xray-xml
```

## Usage
> [!NOTE]
> You need to explicitly import all fixtures that you want to use, e.g. `from pytest_junit_xray_xml import record_test_key`

To export the results as Xray-compatible JUnit, please start pytest with the parameter `--junit-xray-xml <filename.xml>`, e.g.
```shell
python -m pytest tests/examples.py --junit-xray-xml xray.xml
```
(All examples are available in [tests/examples.py](tests/examples.py) and can be run via the command above)

The following fixtures are supported.

### record_test_key
stores the test key in a property named `test_key`. Xray will attach the test results to the test case identified by this key.

> [!ALERT]
> Only a single test key is supported at the moment

#### example
```python
def test_record_test_key(record_test_key):
    record_test_key("JIRA-1234")
    assert True
```
#### output
```xml
<property name="test_key" value="JIRA-1234" />
```

### record_test_id
stores the test ID in a property named `test_id`. Xray will attach the test results to the test case identified by this key.

> [!ALERT]
> Only a single test key is supported at the moment

#### example
```python
def test_record_test_key(record_test_key):
    record_test_key("JIRA-1234")
    assert True
```
#### output
```xml
<property name="test_key" value="JIRA-1234" />
```

### record_test_description
stores the (potentially multi-line) test description as the `text` of a property named `test_description`. This cannot be accomplished with base `pytest` fixtures.
#### example
```python
def test_record_multiple_descriptions(record_test_description):
    record_test_description("This is my test description line 1")
    record_test_description("and line 2.")
    assert True
```
#### output
```xml
<property name="test_description">This is my test description line 1
and line 2.</property>
```

### record_test_evidence
stores the test evidence with base64 encoding inside the XML. Xray will attach this file to the corresponding Jira ticket.

Multiple files with evidence can be stored for a single test case (not shown in the example below).
#### example
```python
def test_store_test_evidence(record_test_evidence):
    with record_test_evidence("file1.txt", "w", encoding="UTF-8") as f:
        f.write("My file content is text")
    assert True
```
#### output
```xml
<property name="testrun_evidence">
                <item name="file1.txt">TXkgZmlsZSBjb250ZW50IGlzIHRleHQ=</item>
            </property>

```
#### example
```python
def test_store_test_evidence_xml(record_test_evidence):
    xml_content = ElementTree(Element("my_root", my_attribute="1"))
    with record_test_evidence("file1.xml", "wb") as f:
        xml_content.write(f)
    assert True
```
#### output
```xml
<property name="testrun_evidence">
    <item name="file1.xml">PG15X3Jvb3QgbXlfYXR0cmlidXRlPSIxIiAvPg==</item>
</property>
```

