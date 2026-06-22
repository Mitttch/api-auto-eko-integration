import pytest

from tests.api.factories import AUTOTEST_RU_PREFIX, unique_phone
from tests.api.helpers import (
    check_user_permissions,
    ensure_employee_in_organization,
    get_active_permission_ids,
    get_organization_employees,
    get_organization_permissions,
    get_organizations_by_ids,
    get_user_permissions_for_organization,
    get_users_by_ids,
    set_user_permissions,
)


# Проверяем согласованность данных пользователя в users и search после обновлений
@pytest.mark.extended
@pytest.mark.consistency
@pytest.mark.skip(
    reason=(
        "Seed users must stay immutable. This scenario changes phone for a seed "
        "account and must be redesigned to avoid updating stable seed data."
    )
)
def test_user_data_consistency_flow(api_context, api_version_params, seed_owner_1):
    user_id = seed_owner_1["seed_owner_1_user_id"]
    email = seed_owner_1["seed_owner_1_email"]
    phone = unique_phone()

    user_response = get_users_by_ids(api_context, api_version_params, [user_id])
    search_response = api_context.get(
        "/api/integrations/search",
        params={
            **api_version_params,
            "email": email,
        },
    )
    assert search_response.ok, search_response.text()

    fio_response = api_context.post(
        "/api/integrations/users/fio",
        params=api_version_params,
        data={
            "userId": user_id,
            "surname": f"{AUTOTEST_RU_PREFIX}ов",
            "name": AUTOTEST_RU_PREFIX,
            "patronymic": "Тестович",
        },
    )
    phone_response = api_context.post(
        "/api/integrations/users/phone",
        params=api_version_params,
        data={
            "userId": user_id,
            "phone": phone,
        },
    )

    updated_user = get_users_by_ids(api_context, api_version_params, [user_id])[0]
    phone_search = api_context.get(
        "/api/integrations/search",
        params={
            **api_version_params,
            "phone": phone,
        },
    )

    assert user_response[0]["id"] == user_id
    assert search_response.json()["userIdByEmail"] == user_id
    assert fio_response.ok, fio_response.text()
    assert phone_response.ok, phone_response.text()
    assert updated_user["id"] == user_id
    assert updated_user["phone"] == phone
    assert phone_search.ok, phone_search.text()
    assert phone_search.json()["userIdByPhone"] == user_id


# Проверяем согласованность данных организации в get organizations и search
@pytest.mark.extended
@pytest.mark.consistency
def test_organization_data_consistency_flow(
    api_context,
    api_version_params,
    seed_org_1,
):
    organization_id = seed_org_1["organization_id"]
    inn = seed_org_1["inn"]
    kpp = seed_org_1["kpp"]

    organizations = get_organizations_by_ids(
        api_context,
        api_version_params,
        [organization_id],
    )
    search_by_inn = api_context.get(
        "/api/integrations/organizations/search",
        params={
            **api_version_params,
            "inn": inn,
        },
    )
    search_by_inn_and_kpp = api_context.get(
        "/api/integrations/organizations/search",
        params={
            **api_version_params,
            "inn": inn,
            "kpp": kpp,
        },
    )

    assert organizations[0]["id"] == organization_id
    assert organizations[0]["inn"] == inn
    assert organizations[0]["kpp"] == kpp
    assert search_by_inn.ok, search_by_inn.text()
    assert isinstance(search_by_inn.json(), list)
    assert search_by_inn_and_kpp.ok, search_by_inn_and_kpp.text()
    assert any(item["id"] == organization_id for item in search_by_inn_and_kpp.json())


# Проверяем согласованность сотрудников и прав во всех read-методах
@pytest.mark.extended
@pytest.mark.consistency
def test_employee_and_permissions_consistency_flow(
    api_context,
    api_version_params,
    seed_org_1,
    seed_owner_1,
    seed_employee_1,
):
    permission_ids = get_active_permission_ids(api_context, api_version_params, limit=2)
    organization_id = seed_org_1["organization_id"]

    ensure_employee_in_organization(
        api_context,
        api_version_params,
        organization_id,
        seed_employee_1["user_id"],
        permission_ids=permission_ids[:1],
    )
    set_user_permissions(
        api_context,
        api_version_params,
        organization_id,
        seed_employee_1["user_id"],
        permission_ids,
    )
    set_user_permissions(
        api_context,
        api_version_params,
        organization_id,
        seed_owner_1["user_id"],
        permission_ids[:1],
    )

    employees_response = get_organization_employees(
        api_context,
        api_version_params,
        organization_id,
        offset=0,
        count=20,
    )
    user_permissions = get_user_permissions_for_organization(
        api_context,
        api_version_params,
        seed_employee_1["user_id"],
        organization_id,
    )
    organization_permissions = get_organization_permissions(
        api_context,
        api_version_params,
        organization_id,
    )
    check_result = check_user_permissions(
        api_context,
        api_version_params,
        seed_employee_1["user_id"],
        organization_id,
        permission_ids,
    )

    organization_user_item = next(
        item
        for item in organization_permissions
        if item["userId"] == seed_employee_1["user_id"]
    )
    assert any(
        item["userId"] == seed_employee_1["user_id"]
        for item in employees_response["data"]
    )
    assert set(user_permissions) == set(permission_ids)
    assert set(organization_user_item["permissionIds"]) == set(permission_ids)
    assert check_result is True


# Проверяем изоляцию permissions между двумя организациями одного пользователя
@pytest.mark.extended
@pytest.mark.consistency
@pytest.mark.skip(
    reason=(
        "Waiting for manual confirmation of the real permissions contract: "
        "seed-based isolation expectations are not confirmed yet."
    )
)
def test_permissions_isolation_between_organizations_flow(
    api_context,
    api_version_params,
    seed_org_1,
    seed_org_2,
    seed_employee_1,
):
    permission_ids = get_active_permission_ids(api_context, api_version_params, limit=2)
    first_organization_id = seed_org_1["organization_id"]
    second_organization_id = seed_org_2["organization_id"]

    ensure_employee_in_organization(
        api_context,
        api_version_params,
        first_organization_id,
        seed_employee_1["user_id"],
        permission_ids=permission_ids[:1],
    )
    ensure_employee_in_organization(
        api_context,
        api_version_params,
        second_organization_id,
        seed_employee_1["user_id"],
        permission_ids=permission_ids[-1:],
    )

    set_user_permissions(
        api_context,
        api_version_params,
        first_organization_id,
        seed_employee_1["user_id"],
        [permission_ids[0]],
    )
    set_user_permissions(
        api_context,
        api_version_params,
        second_organization_id,
        seed_employee_1["user_id"],
        [permission_ids[-1]],
    )

    assert check_user_permissions(
        api_context,
        api_version_params,
        seed_employee_1["user_id"],
        first_organization_id,
        [permission_ids[0]],
    ) is True
    assert check_user_permissions(
        api_context,
        api_version_params,
        seed_employee_1["user_id"],
        first_organization_id,
        [permission_ids[-1]],
    ) is False
    assert check_user_permissions(
        api_context,
        api_version_params,
        seed_employee_1["user_id"],
        second_organization_id,
        [permission_ids[-1]],
    ) is True
    assert check_user_permissions(
        api_context,
        api_version_params,
        seed_employee_1["user_id"],
        second_organization_id,
        [permission_ids[0]],
    ) is False
