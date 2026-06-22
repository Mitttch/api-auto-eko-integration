from uuid import uuid4

import pytest

from tests.api.assertions import assert_no_internal_error_details
from tests.api.factories import AUTOTEST_RU_PREFIX


def assert_bad_request(response):
    assert response.status == 400, response.text()
    assert_no_internal_error_details(response)


def assert_auth_error(response):
    assert response.status in [401, 403], response.text()
    assert_no_internal_error_details(response)


def assert_client_error(response):
    assert response.status in [400, 404], response.text()
    assert_no_internal_error_details(response)


def make_fake_ids(count):
    return ",".join(str(uuid4()) for _ in range(count))


# Проверяем, что API не пускает запрос без access token
@pytest.mark.negative
def test_request_without_token_is_rejected(playwright_instance, settings):
    context = playwright_instance.request.new_context(
        base_url=settings["base_url"],
        extra_http_headers={"Accept": "application/json"},
    )

    response = context.get("/api/integrations/products")

    assert_auth_error(response)
    context.dispose()


# Проверяем, что API не пускает запрос с невалидным access token
@pytest.mark.negative
def test_request_with_invalid_token_is_rejected(playwright_instance, settings):
    context = playwright_instance.request.new_context(
        base_url=settings["base_url"],
        extra_http_headers={
            "Authorization": "Bearer invalid-token",
            "Accept": "application/json",
        },
    )

    response = context.get("/api/integrations/products")

    assert_auth_error(response)
    context.dispose()


# Проверяем, что нельзя проверить регистрацию почты с некорректным email
@pytest.mark.negative
def test_check_mail_register_with_invalid_email(api_context, api_version_params):
    response = api_context.get(
        "/api/integrations/checkmailregister/not-an-email",
        params=api_version_params,
    )

    assert_bad_request(response)


# Проверяем, что нельзя предсоздать пользователя с пустым email
@pytest.mark.negative
def test_precreate_user_with_empty_email(api_context, api_version_params):
    response = api_context.post(
        "/api/integrations/precreate",
        params=api_version_params,
        data={
            "email": "",
            "password": "TestPassword123!",
        },
    )

    assert_bad_request(response)


# Проверяем, что нельзя предсоздать пользователя с email неверного формата
@pytest.mark.negative
def test_precreate_user_with_invalid_email(api_context, api_version_params):
    response = api_context.post(
        "/api/integrations/precreate",
        params=api_version_params,
        data={
            "email": "wrong-email",
            "password": "TestPassword123!",
        },
    )

    assert_bad_request(response)


# Проверяем, что нельзя получить пользователя по невалидному id
@pytest.mark.negative
def test_get_users_with_invalid_id(api_context, api_version_params):
    response = api_context.get(
        "/api/integrations/users",
        params={
            **api_version_params,
            "ids": "wrong-user-id",
        },
    )

    assert_bad_request(response)


# Проверяем, что нельзя получить пользователей при превышении лимита ids
@pytest.mark.negative
def test_get_users_with_more_than_ten_ids(api_context, api_version_params):
    response = api_context.get(
        "/api/integrations/users",
        params={
            **api_version_params,
            "ids": make_fake_ids(11),
        },
    )

    assert_bad_request(response)


# Проверяем, что поиск пользователя без параметров не считается валидным запросом
@pytest.mark.negative
@pytest.mark.xfail(
    reason=(
        "Known API bug: search without params returns 400 with stackTrace "
        "and internal ApplicationLogicException details"
    ),
    strict=True,
)
def test_search_user_without_search_params(api_context, api_version_params):
    response = api_context.get(
        "/api/integrations/search",
        params=api_version_params,
    )

    assert_bad_request(response)


# Проверяем, что нельзя обновить ФИО пользователя с невалидным userId
@pytest.mark.negative
def test_update_user_fio_with_invalid_user_id(api_context, api_version_params):
    response = api_context.post(
        "/api/integrations/users/fio",
        params=api_version_params,
        data={
            "userId": "wrong-user-id",
            "surname": f"{AUTOTEST_RU_PREFIX}ов",
            "name": AUTOTEST_RU_PREFIX,
            "patronymic": "Тестович",
        },
    )

    assert_bad_request(response)


# Проверяем, что нельзя обновить телефон пользователя некорректным номером
@pytest.mark.negative
def test_update_user_phone_with_invalid_phone(api_context, api_version_params):
    response = api_context.post(
        "/api/integrations/users/phone",
        params=api_version_params,
        data={
            "userId": str(uuid4()),
            "phone": "+797195296465",
        },
    )

    assert_bad_request(response)


# Проверяем, что нельзя создать организацию с некорректным ИНН и ОГРН
@pytest.mark.negative
def test_create_organization_with_invalid_inn_and_ogrn(
    api_context,
    api_version_params,
):
    response = api_context.post(
        "/api/integrations/organizations",
        params=api_version_params,
        data={
            "userId": str(uuid4()),
            "permissionIds": ["organization management"],
            "organizationInfo": {
                "inn": "123",
                "kpp": "770101001",
                "ogrn": "123",
                "name": f"{AUTOTEST_RU_PREFIX} организация",
                "fullName": f"{AUTOTEST_RU_PREFIX} общество",
                "legalAddress": f"{AUTOTEST_RU_PREFIX}, Москва",
                "actualAddress": f"{AUTOTEST_RU_PREFIX}, Москва",
                "leaderSurname": f"{AUTOTEST_RU_PREFIX}ов",
                "leaderName": AUTOTEST_RU_PREFIX,
                "leaderPatronymic": "Тестович",
                "leaderPosition": f"{AUTOTEST_RU_PREFIX} директор",
                "legalDocument": f"{AUTOTEST_RU_PREFIX} устав",
            },
        },
    )

    assert_bad_request(response)


# Проверяем, что нельзя создать организацию без userId создателя
@pytest.mark.negative
def test_create_organization_without_user_id(api_context, api_version_params):
    response = api_context.post(
        "/api/integrations/organizations",
        params=api_version_params,
        data={
            "userId": None,
            "permissionIds": ["organization management"],
            "organizationInfo": {
                "inn": "123",
                "kpp": "770101001",
                "ogrn": "123",
                "name": f"{AUTOTEST_RU_PREFIX} организация",
                "fullName": f"{AUTOTEST_RU_PREFIX} общество",
                "legalAddress": f"{AUTOTEST_RU_PREFIX}, Москва",
                "actualAddress": f"{AUTOTEST_RU_PREFIX}, Москва",
                "leaderSurname": f"{AUTOTEST_RU_PREFIX}ов",
                "leaderName": AUTOTEST_RU_PREFIX,
                "leaderPatronymic": "Тестович",
                "leaderPosition": f"{AUTOTEST_RU_PREFIX} директор",
                "legalDocument": f"{AUTOTEST_RU_PREFIX} устав",
            },
        },
    )

    assert_bad_request(response)


# Проверяем, что нельзя получить организации при превышении лимита ids
@pytest.mark.negative
def test_get_organizations_with_more_than_ten_ids(api_context, api_version_params):
    response = api_context.get(
        "/api/integrations/organizations",
        params={
            **api_version_params,
            "ids": make_fake_ids(11),
        },
    )

    assert_bad_request(response)


# Проверяем, что нельзя добавить сотрудника в несуществующую организацию
@pytest.mark.negative
@pytest.mark.xfail(
    reason=(
        "Known API bug: adding employee with unknown ids returns 400 with "
        "stackTrace and internal ApplicationLogicException details"
    ),
    strict=True,
)
def test_add_employee_to_unknown_organization(api_context, api_version_params):
    response = api_context.post(
        f"/api/integrations/organizations/{uuid4()}/employees",
        params=api_version_params,
        data={
            "userId": str(uuid4()),
            "permissionIds": ["organization management"],
        },
    )

    assert_client_error(response)


# Проверяем, что нельзя обновить права для несуществующей организации
@pytest.mark.negative
@pytest.mark.xfail(
    reason=(
        "Known API bug: unknown organizationId returns 500 "
        "NullReferenceException instead of 400/404"
    ),
    strict=True,
)
def test_update_permissions_for_unknown_organization(
    api_context,
    api_version_params,
):
    response = api_context.post(
        f"/api/integrations/organizations/{uuid4()}/users/{uuid4()}/permissions",
        params=api_version_params,
        data=["unknown-permission"],
    )

    assert_client_error(response)


# Проверяем, что проверка прав с пустым списком permissions возвращает ошибку
@pytest.mark.negative
@pytest.mark.xfail(
    reason=(
        "Known API bug: empty permissionIds returns 500 "
        "NullReferenceException instead of 400"
    ),
    strict=True,
)
def test_check_permissions_with_empty_permissions(api_context, api_version_params):
    response = api_context.get(
        f"/api/integrations/users/{uuid4()}/organizations/"
        f"{uuid4()}/check-permissions",
        params={
            **api_version_params,
            "permissionIds": "",
        },
    )

    assert_bad_request(response)
