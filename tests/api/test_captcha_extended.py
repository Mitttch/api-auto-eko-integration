import pytest

from tests.api.assertions import assert_no_internal_error


# Проверяем, что captcha/exclude с валидным токеном возвращает непустую строку
@pytest.mark.extended
@pytest.mark.captcha_extended
def test_captcha_exclude_returns_token(captcha_api_context, api_version_params):
    response = captcha_api_context.get(
        "/api/integrations/captcha/exclude",
        params=api_version_params,
    )

    assert_no_internal_error(response)
    assert response.ok, response.text()
    assert isinstance(response.json(), str)
    assert response.json()


# Проверяем, что captcha/exclude без токена отклоняется
@pytest.mark.extended
@pytest.mark.captcha_extended
def test_captcha_exclude_without_token_is_rejected(
    playwright_instance,
    settings,
    api_version_params,
):
    context = playwright_instance.request.new_context(base_url=settings["base_url"])
    response = context.get(
        "/api/integrations/captcha/exclude",
        params=api_version_params,
    )
    context.dispose()

    assert_no_internal_error(response)
    assert response.status in [401, 403], response.text()


# Проверяем, что captcha/exclude с битым токеном отклоняется
@pytest.mark.extended
@pytest.mark.captcha_extended
def test_captcha_exclude_with_invalid_token_is_rejected(
    playwright_instance,
    settings,
    api_version_params,
):
    context = playwright_instance.request.new_context(
        base_url=settings["base_url"],
        extra_http_headers={
            "Authorization": "Bearer wrong-token",
            "Accept": "application/json",
        },
    )
    response = context.get(
        "/api/integrations/captcha/exclude",
        params=api_version_params,
    )
    context.dispose()

    assert_no_internal_error(response)
    assert response.status in [401, 403], response.text()
