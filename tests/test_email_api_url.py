from types import SimpleNamespace

import pytest

from treg import email as email_module


class _Response:
    status_code = 200
    text = "ok"


class _AsyncClient:
    def __init__(self, *, timeout):
        self.timeout = timeout

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def post(self, url, **kwargs):
        self.url = url
        _AsyncClient.last_url = url
        return _Response()


@pytest.mark.parametrize(
    ("configured", "expected"),
    [
        (None, email_module.RESEND_URL),
        ("https://send.example.com/api/v1/emails", "https://send.example.com/api/v1/emails"),
    ],
)
async def test_transactional_email_api_url_can_be_overridden(monkeypatch, configured, expected):
    if configured is None:
        monkeypatch.delenv("TREG_EMAIL_API_URL", raising=False)
    else:
        monkeypatch.setenv("TREG_EMAIL_API_URL", configured)

    monkeypatch.setattr(
        email_module,
        "get_settings",
        lambda: SimpleNamespace(resend_api_key="test-key", email_from="treg@example.com"),
    )
    monkeypatch.setattr(email_module.httpx, "AsyncClient", _AsyncClient)

    assert await email_module._send("person@example.com", "subject", "<p>hello</p>", "hello")
    assert _AsyncClient.last_url == expected
