import pytest

from tests.api.assertions import assert_no_internal_error


def request_token(playwright_instance, settings, form):
    context = playwright_instance.request.new_context()
    response = context.post(
        settings["token_url"],
        form=form,
    )
    context.dispose()
    return response


# Проверяем получение token с неверным client_secret
@pytest.mark.extended
@pytest.mark.auth_extended
def test_token_with_invalid_client_secret(playwright_instance, settings):
    response = request_token(
        playwright_instance,
        settings,
        {
            "grant_type": "client_credentials",
            "client_id": settings["client_id"],
            "client_secret": "wrong-secret",
            "scope": settings["scope"],
        },
    )

    assert response.status in [400, 401], response.text()


# Проверяем получение token с неверным client_id
@pytest.mark.extended
@pytest.mark.auth_extended
def test_token_with_invalid_client_id(playwright_instance, settings):
    response = request_token(
        playwright_instance,
        settings,
        {
            "grant_type": "client_credentials",
            "client_id": "wrong-client-id",
            "client_secret": settings["client_secret"],
            "scope": settings["scope"],
        },
    )

    assert response.status in [400, 401], response.text()


# Проверяем получение token без scope
@pytest.mark.extended
@pytest.mark.auth_extended
def test_token_without_scope(playwright_instance, settings):
    response = request_token(
        playwright_instance,
        settings,
        {
            "grant_type": "client_credentials",
            "client_id": settings["client_id"],
            "client_secret": settings["client_secret"],
        },
    )

    assert response.status in [200, 400], response.text()


# Проверяем получение token с неправильным scope
@pytest.mark.extended
@pytest.mark.auth_extended
def test_token_with_invalid_scope(playwright_instance, settings):
    response = request_token(
        playwright_instance,
        settings,
        {
            "grant_type": "client_credentials",
            "client_id": settings["client_id"],
            "client_secret": settings["client_secret"],
            "scope": "wrong_scope",
        },
    )

    assert response.status in [400, 401], response.text()


# Проверяем получение token с неправильным grant_type
@pytest.mark.extended
@pytest.mark.auth_extended
def test_token_with_invalid_grant_type(playwright_instance, settings):
    response = request_token(
        playwright_instance,
        settings,
        {
            "grant_type": "password",
            "client_id": settings["client_id"],
            "client_secret": settings["client_secret"],
            "scope": settings["scope"],
        },
    )

    assert response.status in [400, 401], response.text()


# Проверяем, что products возвращает продукт текущего client_id
@pytest.mark.extended
@pytest.mark.auth_extended
def test_products_matches_current_client_id(api_context, api_version_params, settings):
    response = api_context.get(
        "/api/integrations/products",
        params={
            **api_version_params,
            "clientId": settings["client_id"],
        },
    )

    assert response.ok, response.text()
    assert response.json()["productId"]
    assert response.json()["productName"]


# Проверяем products без clientId
@pytest.mark.extended
@pytest.mark.auth_extended
def test_products_without_client_id(api_context, api_version_params):
    response = api_context.get(
        "/api/integrations/products",
        params=api_version_params,
    )

    assert_no_internal_error(response)
    assert response.ok, response.text()
    assert response.json()["productId"]
    assert response.json()["productName"]


# Проверяем, что products без clientId и с текущим clientId возвращают тот же продукт
@pytest.mark.extended
@pytest.mark.auth_extended
def test_products_without_and_with_current_client_id_return_same_product(
    api_context,
    api_version_params,
    settings,
):
    without_client_response = api_context.get(
        "/api/integrations/products",
        params=api_version_params,
    )
    with_client_response = api_context.get(
        "/api/integrations/products",
        params={
            **api_version_params,
            "clientId": settings["client_id"],
        },
    )

    assert without_client_response.ok, without_client_response.text()
    assert with_client_response.ok, with_client_response.text()
    assert without_client_response.json()["productId"] == with_client_response.json()[
        "productId"
    ]
    assert without_client_response.json()["productName"] == with_client_response.json()[
        "productName"
    ]


# Проверяем products с чужим clientId
@pytest.mark.extended
@pytest.mark.auth_extended
def test_products_with_unknown_client_id(api_context, api_version_params):
    response = api_context.get(
        "/api/integrations/products",
        params={
            **api_version_params,
            "clientId": "unknown-client-id",
        },
    )

    assert_no_internal_error(response)
    assert response.status in [200, 400, 404], response.text()


# Проверяем products с пустым clientId
@pytest.mark.extended
@pytest.mark.auth_extended
def test_products_with_empty_client_id(api_context, api_version_params):
    response = api_context.get(
        "/api/integrations/products",
        params={
            **api_version_params,
            "clientId": "",
        },
    )

    assert_no_internal_error(response)
    assert response.status in [200, 400, 404], response.text()


# Проверяем products с мусорным clientId
@pytest.mark.extended
@pytest.mark.auth_extended
def test_products_with_garbage_client_id(api_context, api_version_params):
    response = api_context.get(
        "/api/integrations/products",
        params={
            **api_version_params,
            "clientId": "qa_autotest_%$#_client",
        },
    )

    assert_no_internal_error(response)
    assert response.status in [200, 400, 404], response.text()
