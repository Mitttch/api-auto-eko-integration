INTERNAL_ERROR_MARKERS = [
    "NullReferenceException",
    "ArgumentNullException",
    "StackTrace",
    "stackTrace",
    " at ",
    "/src/",
    "/azp/",
]


def assert_uuid(value):
    assert isinstance(value, str)
    assert len(value) == 36


def assert_no_internal_error(response):
    assert response.status < 500, response.text()


def assert_no_internal_error_details(response):
    response_text = response.text()

    for marker in INTERNAL_ERROR_MARKERS:
        assert marker not in response_text, response_text
