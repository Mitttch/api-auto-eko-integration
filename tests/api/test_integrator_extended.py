from uuid import uuid4

import pytest

from tests.api.assertions import assert_no_internal_error, assert_uuid
from tests.api.factories import unique_email, unique_external_user_id, unique_phone


def require_integrator_settings(settings):
    if not settings["integrator_id"]:
        pytest.skip("Set INTEGRATOR_ID to run integrator API tests")


def require_oidc_settings(settings):
    required_values = [
        settings["oidc_client_id"],
        settings["oidc_client_secret"],
        settings["oidc_redirect_uri"],
        settings["oidc_scope"],
    ]
    if not all(required_values):
        pytest.skip(
            "Set OIDC_CLIENT_ID, OIDC_CLIENT_SECRET, OIDC_REDIRECT_URI "
            "and OIDC_SCOPE to run /integrations/code tests"
        )


def create_integration_user(api_context, api_version_params, settings, external_id=None):
    require_integrator_settings(settings)
    payload = {
        "id": external_id or unique_external_user_id(),
        "integratorId": settings["integrator_id"],
        "email": unique_email("qa_autotest_integrator"),
        "phone": unique_phone(),
        "firstName": "qa_autotest_first",
        "lastName": "qa_autotest_last",
        "patronymic": "qa_autotest_middle",
    }

    response = api_context.post(
        "/api/integrations/integrateuser",
        params=api_version_params,
        data=payload,
    )

    assert response.ok, response.text()
    user_id = response.json()
    assert_uuid(user_id)
    return payload, user_id


def create_oidc_config(settings):
    return {
        "clientId": settings["oidc_client_id"],
        "clientSecret": settings["oidc_client_secret"],
        "redirectUri": settings["oidc_redirect_uri"],
        "postLogoutRedirectUris": [settings["oidc_redirect_uri"]],
        "scope": settings["oidc_scope"],
    }


# Проверяем регистрацию интеграционного пользователя
@pytest.mark.extended
@pytest.mark.integrator_extended
def test_integrate_user_with_valid_payload(api_context, api_version_params, settings):
    _, user_id = create_integration_user(api_context, api_version_params, settings)

    assert_uuid(user_id)


# Проверяем повторную регистрацию с тем же external id
@pytest.mark.extended
@pytest.mark.integrator_extended
def test_integrate_user_duplicate_external_id(api_context, api_version_params, settings):
    external_id = unique_external_user_id()
    _, first_user_id = create_integration_user(
        api_context,
        api_version_params,
        settings,
        external_id,
    )

    response = api_context.post(
        "/api/integrations/integrateuser",
        params=api_version_params,
        data={
            "id": external_id,
            "integratorId": settings["integrator_id"],
            "email": unique_email("qa_autotest_integrator"),
            "phone": unique_phone(),
            "firstName": "qa_autotest_first",
            "lastName": "qa_autotest_last",
            "patronymic": "qa_autotest_middle",
        },
    )

    assert_no_internal_error(response)
    assert response.status in [200, 400], response.text()
    if response.ok:
        assert response.json() == first_user_id


# Проверяем integrateuser без валидного integratorId
@pytest.mark.extended
@pytest.mark.integrator_extended
def test_integrate_user_with_invalid_integrator_id(api_context, api_version_params):
    response = api_context.post(
        "/api/integrations/integrateuser",
        params=api_version_params,
        data={
            "id": unique_external_user_id(),
            "integratorId": str(uuid4()),
            "email": unique_email("qa_autotest_integrator"),
            "phone": unique_phone(),
            "firstName": "qa_autotest_first",
            "lastName": "qa_autotest_last",
            "patronymic": "qa_autotest_middle",
        },
    )

    assert_no_internal_error(response)
    assert response.status in [400, 404], response.text()


# Проверяем integrateuser с невалидным email
@pytest.mark.extended
@pytest.mark.integrator_extended
def test_integrate_user_with_invalid_email(api_context, api_version_params, settings):
    require_integrator_settings(settings)

    response = api_context.post(
        "/api/integrations/integrateuser",
        params=api_version_params,
        data={
            "id": unique_external_user_id(),
            "integratorId": settings["integrator_id"],
            "email": "wrong-email",
            "phone": unique_phone(),
            "firstName": "qa_autotest_first",
            "lastName": "qa_autotest_last",
            "patronymic": "qa_autotest_middle",
        },
    )

    assert_no_internal_error(response)
    assert response.status == 400, response.text()


# Проверяем получение authorization code для интеграционного пользователя
@pytest.mark.extended
@pytest.mark.integrator_extended
def test_code_for_valid_integration_user(api_context, api_version_params, settings):
    require_oidc_settings(settings)
    integration_user, _ = create_integration_user(
        api_context,
        api_version_params,
        settings,
    )

    response = api_context.post(
        "/api/integrations/code",
        params=api_version_params,
        data={
            "userId": integration_user["id"],
            "integratorId": settings["integrator_id"],
            "oidcConfig": create_oidc_config(settings),
        },
    )

    assert_no_internal_error(response)
    assert response.ok, response.text()
    assert isinstance(response.json(), str)
    assert response.json()


# Проверяем code для unknown userId
@pytest.mark.extended
@pytest.mark.integrator_extended
def test_code_for_unknown_user_id(api_context, api_version_params, settings):
    require_integrator_settings(settings)
    require_oidc_settings(settings)

    response = api_context.post(
        "/api/integrations/code",
        params=api_version_params,
        data={
            "userId": unique_external_user_id(),
            "integratorId": settings["integrator_id"],
            "oidcConfig": create_oidc_config(settings),
        },
    )

    assert_no_internal_error(response)
    assert response.status in [400, 404], response.text()


# Проверяем code без oidcConfig
@pytest.mark.extended
@pytest.mark.integrator_extended
def test_code_without_oidc_config(api_context, api_version_params, settings):
    require_integrator_settings(settings)

    response = api_context.post(
        "/api/integrations/code",
        params=api_version_params,
        data={
            "userId": unique_external_user_id(),
            "integratorId": settings["integrator_id"],
        },
    )

    assert_no_internal_error(response)
    assert response.status == 400, response.text()
