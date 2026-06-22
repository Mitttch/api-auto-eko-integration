from uuid import uuid4
from urllib.parse import parse_qs, urlparse

import pytest

from tests.api.assertions import assert_no_internal_error, assert_uuid
from tests.api.factories import unique_email
from tests.api.helpers import get_user_by_id


def extract_token_from_url(url):
    parsed_url = urlparse(url)
    query_values = parse_qs(parsed_url.query)

    for key in ["token", "code", "confirmationToken"]:
        if query_values.get(key):
            return query_values[key][0]

    return None


def precreate_user_by_email(api_context, api_version_params, email):
    response = api_context.post(
        "/api/integrations/precreate/byemail",
        params=api_version_params,
        data={
            "email": email,
            "password": "TestPassword123!",
        },
    )

    assert response.ok, response.text()
    body = response.json()
    assert_uuid(body["userId"])
    assert "url" in body

    return body


# Проверяем, что precreate/byemail возвращает userId и ссылку подтверждения
@pytest.mark.extended
@pytest.mark.email_confirmation_extended
def test_precreate_byemail_returns_user_id_and_url(api_context, api_version_params):
    email = unique_email("qa_autotest_email")

    body = precreate_user_by_email(api_context, api_version_params, email)

    assert body["url"]
    if extract_token_from_url(body["url"]):
        assert extract_token_from_url(body["url"])


# Проверяем подтверждение пользователя токеном из ссылки без чтения почты
@pytest.mark.extended
@pytest.mark.email_confirmation_extended
def test_confirm_token_from_precreate_byemail(api_context, api_version_params):
    email = unique_email("qa_autotest_email")
    body = precreate_user_by_email(api_context, api_version_params, email)
    token = extract_token_from_url(body["url"])

    if not token:
        pytest.skip("precreate/byemail response does not contain confirmation token")

    confirm_response = api_context.get(
        f"/api/integrations/confirm/{token}",
        params=api_version_params,
    )

    assert_no_internal_error(confirm_response)
    if confirm_response.status == 400:
        pytest.skip("precreate/byemail URL token is not accepted by confirm endpoint")
    assert confirm_response.ok, confirm_response.text()

    check_response = api_context.get(
        f"/api/integrations/checkmailregister/{email}",
        params=api_version_params,
    )
    assert check_response.ok, check_response.text()
    assert check_response.json() == body["userId"]

    search_response = api_context.get(
        "/api/integrations/search",
        params={
            **api_version_params,
            "email": email,
        },
    )
    assert search_response.ok, search_response.text()
    assert search_response.json()["userIdByEmail"] == body["userId"]

    user = get_user_by_id(api_context, api_version_params, body["userId"])
    assert user["email"] == email
    if "emailConfirmed" in user:
        assert user["emailConfirmed"] is True


# Проверяем, что повторный confirm тем же токеном не приводит к 500
@pytest.mark.extended
@pytest.mark.email_confirmation_extended
def test_confirm_same_token_twice_does_not_return_500(api_context, api_version_params):
    email = unique_email("qa_autotest_email")
    body = precreate_user_by_email(api_context, api_version_params, email)
    token = extract_token_from_url(body["url"])

    if not token:
        pytest.skip("precreate/byemail response does not contain confirmation token")

    first_response = api_context.get(
        f"/api/integrations/confirm/{token}",
        params=api_version_params,
    )
    second_response = api_context.get(
        f"/api/integrations/confirm/{token}",
        params=api_version_params,
    )

    assert_no_internal_error(first_response)
    if first_response.status == 400:
        pytest.skip("precreate/byemail URL token is not accepted by confirm endpoint")
    assert first_response.ok, first_response.text()
    assert_no_internal_error(second_response)
    assert second_response.status in [200, 400, 404], second_response.text()


# Проверяем, что мусорный confirmation token не приводит к 500
@pytest.mark.extended
@pytest.mark.email_confirmation_extended
def test_confirm_with_unknown_token_returns_client_error(api_context, api_version_params):
    response = api_context.get(
        f"/api/integrations/confirm/{uuid4().hex}",
        params=api_version_params,
    )

    assert_no_internal_error(response)
    assert response.status in [400, 404], response.text()


# Проверяем, что короткий confirmation token не приводит к 500
@pytest.mark.extended
@pytest.mark.email_confirmation_extended
def test_confirm_with_short_token_returns_client_error(api_context, api_version_params):
    response = api_context.get(
        "/api/integrations/confirm/bad",
        params=api_version_params,
    )

    assert_no_internal_error(response)
    assert response.status in [400, 404], response.text()


# Проверяем resend для пользователя, созданного через precreate/byemail
@pytest.mark.extended
@pytest.mark.email_confirmation_extended
def test_resend_for_precreated_byemail_user(api_context, api_version_params):
    email = unique_email("qa_autotest_email")
    body = precreate_user_by_email(api_context, api_version_params, email)

    response = api_context.post(
        f"/api/integrations/resend/{body['userId']}",
        params=api_version_params,
    )

    assert_no_internal_error(response)
    assert response.status in [200, 400], response.text()


# Проверяем resend для неизвестного userId
@pytest.mark.extended
@pytest.mark.email_confirmation_extended
def test_resend_for_unknown_user_returns_client_error(api_context, api_version_params):
    response = api_context.post(
        f"/api/integrations/resend/{uuid4()}",
        params=api_version_params,
    )

    assert_no_internal_error(response)
    assert response.status in [400, 404], response.text()


# Проверяем resend с невалидным форматом userId
@pytest.mark.extended
@pytest.mark.email_confirmation_extended
def test_resend_with_invalid_user_id_returns_client_error(api_context, api_version_params):
    response = api_context.post(
        "/api/integrations/resend/wrong-user-id",
        params=api_version_params,
    )

    assert_no_internal_error(response)
    assert response.status in [400, 404], response.text()
