import pytest

from unittest.mock import MagicMock, patch

from utils.tools import TimeTools, WebTools


@pytest.fixture
def time_tools() -> TimeTools:
    return TimeTools()


@pytest.fixture
def web_tools() -> WebTools:
    return WebTools()


def test_time_tools_has_function(time_tools: TimeTools) -> None:
    assert time_tools.has_function("get_time")
    assert not time_tools.has_function("invalid_function")


@patch("utils.tools.datetime")
def test_get_time(mock_datetime: MagicMock, time_tools: TimeTools) -> None:
    mock_now = MagicMock()
    mock_datetime.datetime.now.return_value = mock_now
    mock_now.strftime.return_value = "10:30AM - January 01, 2023"

    result = time_tools.call_function("get_time", {"format": "%I:%M%p - %B %d, %Y"})
    assert result == "The current time is 10:30AM - January 01, 2023."

    time_tools.call_function("get_time", {"format": "%H:%M"})
    mock_now.strftime.assert_called_with("%H:%M")


def test_web_tools_has_function(web_tools: WebTools) -> None:
    assert web_tools.has_function("http_request")
    assert not web_tools.has_function("invalid_function")


@patch("utils.tools.requests.get")
def test_http_get_request(mock_get: MagicMock, web_tools: WebTools) -> None:
    mock_get.return_value = MagicMock(status_code=200, text='{"data": "test"}')

    result = web_tools.call_function(
        "http_request",
        {"method": "GET", "url": "https://example.com", "headers": {"Content-Type": "application/json"}},
    )

    assert "Response: 200" in result
    assert '{"data": "test"}' in result
    mock_get.assert_called_once_with("https://example.com", headers={"Content-Type": "application/json"})


@patch("utils.tools.requests.post")
def test_http_post_request(mock_post: MagicMock, web_tools: WebTools) -> None:
    mock_post.return_value = MagicMock(status_code=201, text='{"status": "created"}')

    result = web_tools.call_function(
        "http_request",
        {
            "method": "POST",
            "url": "https://example.com/create",
            "headers": {"Content-Type": "application/json"},
            "body": {"name": "test"},
        },
    )

    assert "Response: 201" in result
    assert '{"status": "created"}' in result
    mock_post.assert_called_once_with(
        "https://example.com/create",
        headers={"Content-Type": "application/json"},
        json={"name": "test"},
    )


def test_unsupported_http_method(web_tools: WebTools) -> None:
    result = web_tools.call_function(
        "http_request",
        {"method": "PUT", "url": "https://example.com", "headers": {}, "body": {}},
    )
    assert "Unsupported HTTP method" in result
