from pathlib import Path

tests_path = Path(__file__).parent


# This method will be used by the mock to replace requests.get
def mocked_requests_get(*args, **kwargs):
    class MockResponse:
        def __init__(self, content, status_code):
            self.content = content
            self.status_code = status_code

        def json(self):
            return self.json_data

    if "GetRecordsByInstanceId" in args[0] and "jdd" in args[0]:
        with open(tests_path / "files" / "jdd.xml", "rb") as f:
            return MockResponse(f.read(), 200)
    elif "GetRecordsByInstanceId" in args[0]:
        with open(tests_path / "files" / "af.xml", "rb") as f:
            return MockResponse(f.read(), 200)
    return MockResponse(None, 404)
