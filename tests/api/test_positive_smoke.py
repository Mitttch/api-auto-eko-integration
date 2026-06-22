import pytest

from tests.api.assertions import (
    assert_organization_exists,
    assert_user_deleted,
    assert_uuid,
)
from tests.api.cleanup import delete_created_accounts
from tests.api.factories import AUTOTEST_RU_PREFIX, unique_cleanup_email
from tests.api.helpers import (
    add_employee,
    check_user_permissions,
    create_organization,
    create_user_by_email,
    get_first_permission_id,
    get_organization_permissions,
    get_user_permissions_for_organization,
    get_user_by_id,
)
from tests.api.factories import unique_phone


# Проверяем, что авторизация работает и API пускает запрос с access token
@pytest.mark.positive_smoke
def test_check_mail_register(api_context, api_version_params, settings):
    response = api_context.get(
        f"/api/integrations/checkmailregister/{settings['check_email']}",
        params=api_version_params,
    )

    assert response.ok, response.text()
    assert_uuid(response.json())


# Проверяем, что можно получить информацию о продукте по client_id
@pytest.mark.positive_smoke
def test_get_product(api_context, api_version_params, settings):
    response = api_context.get(
        "/api/integrations/products",
        params={
            **api_version_params,
            "clientId": settings["client_id"],
        },
    )

    assert response.ok, response.text()

    product = response.json()
    assert_uuid(product["productId"])
    assert product["productName"]


# Проверяем, что можно получить список доступных прав продукта
@pytest.mark.positive_smoke
def test_get_product_permissions(api_context, api_version_params):
    response = api_context.get(
        "/api/integrations/products/permissions",
        params=api_version_params,
    )

    assert response.ok, response.text()

    permissions = response.json()
    assert isinstance(permissions, list)
    assert len(permissions) > 0
    assert "id" in permissions[0]
    assert "name" in permissions[0]


# Проверяем полный позитивный smoke flow и безопасный cleanup созданных учеток
@pytest.mark.positive_smoke
def test_full_positive_smoke_flow_with_safe_cleanup(
    api_context,
    api_version_params,
):
    created_emails = []
    deleted_emails = set()

    try:
        owner_email = unique_cleanup_email("positive-smoke-owner")
        owner_id, _ = create_user_by_email(
            api_context,
            api_version_params,
            email=owner_email,
        )
        created_emails.append(owner_email)

        employee_email = unique_cleanup_email("positive-smoke-employee")
        employee_id, _ = create_user_by_email(
            api_context,
            api_version_params,
            email=employee_email,
        )
        created_emails.append(employee_email)

        owner_user = get_user_by_id(api_context, api_version_params, owner_id)
        assert owner_user["id"] == owner_id
        assert owner_user["email"] == owner_email

        search_owner_response = api_context.get(
            "/api/integrations/search",
            params={
                **api_version_params,
                "email": owner_email,
            },
        )
        assert search_owner_response.ok, search_owner_response.text()
        assert search_owner_response.json()["userIdByEmail"] == owner_id

        surname = f"{AUTOTEST_RU_PREFIX}ов"
        name = AUTOTEST_RU_PREFIX
        patronymic = "Тестович"
        fio_response = api_context.post(
            "/api/integrations/users/fio",
            params=api_version_params,
            data={
                "userId": owner_id,
                "surname": surname,
                "name": name,
                "patronymic": patronymic,
            },
        )
        assert fio_response.ok, fio_response.text()

        phone = unique_phone()
        phone_response = api_context.post(
            "/api/integrations/users/phone",
            params=api_version_params,
            data={
                "userId": owner_id,
                "phone": phone,
            },
        )
        assert phone_response.ok, phone_response.text()

        updated_owner = get_user_by_id(api_context, api_version_params, owner_id)
        assert updated_owner["fullName"]["surname"] == surname
        assert updated_owner["fullName"]["name"] == name
        assert updated_owner["fullName"]["patronymic"] == patronymic
        assert updated_owner["phone"] == phone

        phone_search_response = api_context.get(
            "/api/integrations/search",
            params={
                **api_version_params,
                "phone": phone,
            },
        )
        assert phone_search_response.ok, phone_search_response.text()
        assert phone_search_response.json()["userIdByPhone"] == owner_id

        permission_id = get_first_permission_id(api_context, api_version_params)
        organization_id, inn, kpp = create_organization(
            api_context,
            api_version_params,
            owner_id,
            permission_id,
        )

        organizations_response = api_context.get(
            "/api/integrations/organizations",
            params={
                **api_version_params,
                "ids": organization_id,
            },
        )
        assert organizations_response.ok, organizations_response.text()
        organizations = organizations_response.json()
        assert len(organizations) == 1
        assert organizations[0]["id"] == organization_id
        assert organizations[0]["inn"] == inn
        assert organizations[0]["kpp"] == kpp

        organization_search_response = api_context.get(
            "/api/integrations/organizations/search",
            params={
                **api_version_params,
                "inn": inn,
                "kpp": kpp,
            },
        )
        assert organization_search_response.ok, organization_search_response.text()
        assert any(
            item["id"] == organization_id
            for item in organization_search_response.json()
        )

        employee_relation_id = add_employee(
            api_context,
            api_version_params,
            organization_id,
            employee_id,
        )
        assert_uuid(employee_relation_id)

        employees_response = api_context.get(
            f"/api/integrations/organizations/{organization_id}/employees",
            params={
                **api_version_params,
                "offset": 0,
                "count": 20,
            },
        )
        assert employees_response.ok, employees_response.text()
        assert any(
            item["userId"] == employee_id
            for item in employees_response.json()["data"]
        )

        permissions_update_response = api_context.post(
            f"/api/integrations/organizations/{organization_id}/users/"
            f"{owner_id}/permissions",
            params=api_version_params,
            data=[permission_id],
        )
        assert permissions_update_response.ok, permissions_update_response.text()

        owner_permissions = get_user_permissions_for_organization(
            api_context,
            api_version_params,
            owner_id,
            organization_id,
        )
        assert permission_id in owner_permissions

        employee_permissions = get_user_permissions_for_organization(
            api_context,
            api_version_params,
            employee_id,
            organization_id,
        )
        assert permission_id in employee_permissions

        user_permissions_response = api_context.get(
            f"/api/integrations/users/{owner_id}/permissions",
            params=api_version_params,
        )
        assert user_permissions_response.ok, user_permissions_response.text()
        assert any(
            item["organizationId"] == organization_id
            for item in user_permissions_response.json()
        )

        assert check_user_permissions(
            api_context,
            api_version_params,
            owner_id,
            organization_id,
            [permission_id],
        ) is True

        organization_permissions = get_organization_permissions(
            api_context,
            api_version_params,
            organization_id,
        )
        assert any(item["userId"] == owner_id for item in organization_permissions)
        assert any(item["userId"] == employee_id for item in organization_permissions)

        delete_created_accounts(
            api_context,
            api_version_params,
            [owner_email, employee_email],
            deleted_emails,
        )

        assert_user_deleted(api_context, api_version_params, owner_id, owner_email)
        assert_user_deleted(
            api_context,
            api_version_params,
            employee_id,
            employee_email,
        )
        assert_organization_exists(
            api_context,
            api_version_params,
            organization_id,
        )
    finally:
        delete_created_accounts(
            api_context,
            api_version_params,
            created_emails,
            deleted_emails,
        )
