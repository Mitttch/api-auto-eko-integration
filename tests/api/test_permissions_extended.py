from uuid import uuid4

import pytest

from tests.api.assertions import assert_no_internal_error
from tests.api.helpers import (
    check_user_permissions,
    ensure_employee_in_organization,
    get_active_permission_ids,
    get_first_permission_id,
    get_organization_permissions,
    get_user_permissions,
    get_user_permissions_filtered,
    get_user_permissions_for_organization,
    set_user_permissions,
)


def prepare_seed_organization_for_user(
    api_context,
    api_version_params,
    organization_id,
    owner_user_id,
    target_user_id=None,
    permission_ids=None,
):
    if target_user_id and target_user_id != owner_user_id:
        ensure_employee_in_organization(
            api_context,
            api_version_params,
            organization_id,
            target_user_id,
            permission_ids=permission_ids[:1] if permission_ids else None,
        )

    return organization_id


def prepare_user_with_two_seed_organizations(
    api_context,
    api_version_params,
    seed_org_1,
    seed_org_2,
    first_owner_user_id,
    second_owner_user_id,
    target_user_id,
    permission_ids,
):
    first_organization_id = prepare_seed_organization_for_user(
        api_context,
        api_version_params,
        seed_org_1["organization_id"],
        first_owner_user_id,
        target_user_id=target_user_id,
        permission_ids=permission_ids,
    )
    second_organization_id = prepare_seed_organization_for_user(
        api_context,
        api_version_params,
        seed_org_2["organization_id"],
        second_owner_user_id,
        target_user_id=target_user_id,
        permission_ids=permission_ids,
    )

    return first_organization_id, second_organization_id


# Проверяем, что список permissions продукта не пустой
@pytest.mark.extended
@pytest.mark.permissions_extended
def test_product_permissions_are_not_empty(api_context, api_version_params):
    response = api_context.get(
        "/api/integrations/products/permissions",
        params=api_version_params,
    )

    assert response.ok, response.text()
    assert len(response.json()) > 0


# Проверяем, что permission ids в справочнике продукта уникальны
@pytest.mark.extended
@pytest.mark.permissions_extended
def test_product_permission_ids_are_unique(api_context, api_version_params):
    response = api_context.get(
        "/api/integrations/products/permissions",
        params=api_version_params,
    )

    assert response.ok, response.text()
    permission_ids = [permission["id"] for permission in response.json()]
    assert len(permission_ids) == len(set(permission_ids))


# Проверяем, что у permissions есть обязательные поля
@pytest.mark.extended
@pytest.mark.permissions_extended
def test_product_permissions_have_required_fields(api_context, api_version_params):
    response = api_context.get(
        "/api/integrations/products/permissions",
        params=api_version_params,
    )

    assert response.ok, response.text()
    for permission in response.json():
        assert "id" in permission
        assert "name" in permission
        assert "isPermission" in permission
        assert "isDisabled" in permission


# Проверяем, что permission из справочника можно использовать при назначении прав
@pytest.mark.extended
@pytest.mark.permissions_extended
def test_product_permission_can_be_used_for_update(
    api_context,
    api_version_params,
    seed_owner_1,
    seed_org_1,
):
    permission_id = get_first_permission_id(api_context, api_version_params)
    organization_id = prepare_seed_organization_for_user(
        api_context,
        api_version_params,
        seed_org_1["organization_id"],
        seed_owner_1["user_id"],
    )

    assigned_permissions = set_user_permissions(
        api_context,
        api_version_params,
        organization_id,
        seed_owner_1["user_id"],
        [permission_id],
    )
    assert permission_id in assigned_permissions


# Проверяем назначение одного права пользователю
@pytest.mark.extended
@pytest.mark.permissions_extended
@pytest.mark.skip(
    reason=(
        "Waiting for manual confirmation of the real permissions contract for "
        "assigned and returned permissions."
    )
)
def test_assign_one_permission(
    api_context,
    api_version_params,
    seed_owner_1,
    seed_org_1,
):
    permission_id = get_first_permission_id(api_context, api_version_params)
    organization_id = prepare_seed_organization_for_user(
        api_context,
        api_version_params,
        seed_org_1["organization_id"],
        seed_owner_1["user_id"],
    )

    assigned_permissions = set_user_permissions(
        api_context,
        api_version_params,
        organization_id,
        seed_owner_1["user_id"],
        [permission_id],
    )
    assert assigned_permissions == [permission_id]


# Проверяем назначение нескольких прав пользователю
@pytest.mark.extended
@pytest.mark.permissions_extended
@pytest.mark.skip(
    reason=(
        "Waiting for manual confirmation of the real permissions contract for "
        "assigned and returned permissions."
    )
)
def test_assign_multiple_permissions(
    api_context,
    api_version_params,
    seed_owner_1,
    seed_org_1,
):
    permission_ids = get_active_permission_ids(api_context, api_version_params, limit=2)
    organization_id = prepare_seed_organization_for_user(
        api_context,
        api_version_params,
        seed_org_1["organization_id"],
        seed_owner_1["user_id"],
    )

    assigned_permissions = set_user_permissions(
        api_context,
        api_version_params,
        organization_id,
        seed_owner_1["user_id"],
        permission_ids,
    )
    assert set(assigned_permissions) == set(permission_ids)


# Проверяем назначение всех доступных прав продукта
@pytest.mark.extended
@pytest.mark.permissions_extended
@pytest.mark.skip(
    reason=(
        "Waiting for manual confirmation of the real permissions contract for "
        "assigned and returned permissions."
    )
)
def test_assign_all_available_permissions(
    api_context,
    api_version_params,
    seed_owner_1,
    seed_org_1,
):
    permission_ids = get_active_permission_ids(api_context, api_version_params)
    organization_id = prepare_seed_organization_for_user(
        api_context,
        api_version_params,
        seed_org_1["organization_id"],
        seed_owner_1["user_id"],
    )

    assigned_permissions = set_user_permissions(
        api_context,
        api_version_params,
        organization_id,
        seed_owner_1["user_id"],
        permission_ids,
    )
    assert set(assigned_permissions) == set(permission_ids)


# Проверяем назначение пустого списка permissions
@pytest.mark.extended
@pytest.mark.permissions_extended
def test_assign_empty_permissions_list(
    api_context,
    api_version_params,
    seed_owner_1,
    seed_org_1,
):
    permission_id = get_first_permission_id(api_context, api_version_params)
    organization_id = prepare_seed_organization_for_user(
        api_context,
        api_version_params,
        seed_org_1["organization_id"],
        seed_owner_1["user_id"],
    )

    assigned_permissions = set_user_permissions(
        api_context,
        api_version_params,
        organization_id,
        seed_owner_1["user_id"],
        [],
    )
    assert assigned_permissions == []


# Проверяем повторное назначение того же списка прав
@pytest.mark.extended
@pytest.mark.permissions_extended
def test_assign_same_permissions_twice(
    api_context,
    api_version_params,
    seed_owner_1,
    seed_org_1,
):
    permission_ids = get_active_permission_ids(api_context, api_version_params, limit=2)
    organization_id = prepare_seed_organization_for_user(
        api_context,
        api_version_params,
        seed_org_1["organization_id"],
        seed_owner_1["user_id"],
    )

    set_user_permissions(
        api_context,
        api_version_params,
        organization_id,
        seed_owner_1["user_id"],
        permission_ids,
    )
    assigned_permissions = set_user_permissions(
        api_context,
        api_version_params,
        organization_id,
        seed_owner_1["user_id"],
        permission_ids,
    )
    assert set(assigned_permissions) == set(permission_ids)


# Проверяем replace-логику при повторном обновлении permissions
@pytest.mark.extended
@pytest.mark.permissions_extended
@pytest.mark.skip(
    reason=(
        "Waiting for manual confirmation of replace-vs-merge behavior in the "
        "permissions contract."
    )
)
def test_update_permissions_replaces_previous_permissions(
    api_context,
    api_version_params,
    seed_owner_1,
    seed_org_1,
):
    permission_ids = get_active_permission_ids(api_context, api_version_params, limit=3)
    organization_id = prepare_seed_organization_for_user(
        api_context,
        api_version_params,
        seed_org_1["organization_id"],
        seed_owner_1["user_id"],
    )

    set_user_permissions(
        api_context,
        api_version_params,
        organization_id,
        seed_owner_1["user_id"],
        permission_ids[:2],
    )
    assigned_permissions = set_user_permissions(
        api_context,
        api_version_params,
        organization_id,
        seed_owner_1["user_id"],
        [permission_ids[-1]],
    )
    assert assigned_permissions == [permission_ids[-1]]


# Проверяем назначение прав пользователю, который не является сотрудником организации
@pytest.mark.extended
@pytest.mark.permissions_extended
def test_assign_permissions_to_user_who_is_not_employee(
    api_context,
    api_version_params,
    seed_owner_1,
    seed_owner_2,
    seed_org_1,
):
    permission_id = get_first_permission_id(api_context, api_version_params)
    organization_id = prepare_seed_organization_for_user(
        api_context,
        api_version_params,
        seed_org_1["organization_id"],
        seed_owner_1["user_id"],
    )

    response = api_context.post(
        f"/api/integrations/organizations/{organization_id}/users/"
        f"{seed_owner_2['user_id']}/permissions",
        params=api_version_params,
        data=[permission_id],
    )

    assert_no_internal_error(response)
    assert response.status in [200, 400, 404], response.text()


# Проверяем назначение прав несуществующему пользователю
@pytest.mark.extended
@pytest.mark.permissions_extended
def test_assign_permissions_to_unknown_user(
    api_context,
    api_version_params,
    seed_owner_1,
    seed_org_1,
):
    permission_id = get_first_permission_id(api_context, api_version_params)
    organization_id = prepare_seed_organization_for_user(
        api_context,
        api_version_params,
        seed_org_1["organization_id"],
        seed_owner_1["user_id"],
    )

    response = api_context.post(
        f"/api/integrations/organizations/{organization_id}/users/"
        f"{uuid4()}/permissions",
        params=api_version_params,
        data=[permission_id],
    )

    assert_no_internal_error(response)
    assert response.status in [400, 404], response.text()


# Проверяем назначение несуществующего permissionId
@pytest.mark.extended
@pytest.mark.permissions_extended
def test_assign_unknown_permission(
    api_context,
    api_version_params,
    seed_owner_1,
    seed_org_1,
):
    permission_id = get_first_permission_id(api_context, api_version_params)
    organization_id = prepare_seed_organization_for_user(
        api_context,
        api_version_params,
        seed_org_1["organization_id"],
        seed_owner_1["user_id"],
    )

    response = api_context.post(
        f"/api/integrations/organizations/{organization_id}/users/"
        f"{seed_owner_1['user_id']}/permissions",
        params=api_version_params,
        data=["unknown-permission"],
    )

    assert_no_internal_error(response)
    assert response.status in [400, 404], response.text()


# Проверяем передачу дублей permissionIds при назначении прав
@pytest.mark.extended
@pytest.mark.permissions_extended
def test_assign_duplicate_permission_ids(
    api_context,
    api_version_params,
    seed_owner_1,
    seed_org_1,
):
    permission_id = get_first_permission_id(api_context, api_version_params)
    organization_id = prepare_seed_organization_for_user(
        api_context,
        api_version_params,
        seed_org_1["organization_id"],
        seed_owner_1["user_id"],
    )

    response = api_context.post(
        f"/api/integrations/organizations/{organization_id}/users/"
        f"{seed_owner_1['user_id']}/permissions",
        params=api_version_params,
        data=[permission_id, permission_id],
    )

    assert_no_internal_error(response)
    assert response.ok, response.text()
    assigned_permissions = get_user_permissions_for_organization(
        api_context,
        api_version_params,
        seed_owner_1["user_id"],
        organization_id,
    )
    assert assigned_permissions.count(permission_id) == 1


# Проверяем назначение прав в несуществующей организации
@pytest.mark.extended
@pytest.mark.permissions_extended
@pytest.mark.skip(
    reason=(
        "Covered by focused xfail in negative suite: "
        "test_update_permissions_for_unknown_organization"
    )
)
def test_assign_permissions_to_unknown_organization(api_context, api_version_params):
    response = api_context.post(
        f"/api/integrations/organizations/{uuid4()}/users/{uuid4()}/permissions",
        params=api_version_params,
        data=["unknown-permission"],
    )

    assert_no_internal_error(response)
    assert response.status in [400, 404], response.text()


# Проверяем получение прав пользователя после явного обнуления прав
@pytest.mark.extended
@pytest.mark.permissions_extended
def test_get_user_permissions_without_assigned_permissions(
    api_context,
    api_version_params,
    seed_owner_1,
    seed_org_1,
):
    organization_id = prepare_seed_organization_for_user(
        api_context,
        api_version_params,
        seed_org_1["organization_id"],
        seed_owner_1["user_id"],
    )

    set_user_permissions(
        api_context,
        api_version_params,
        organization_id,
        seed_owner_1["user_id"],
        [],
    )
    permissions = get_user_permissions(
        api_context,
        api_version_params,
        seed_owner_1["user_id"],
    )
    org_permissions = get_user_permissions_for_organization(
        api_context,
        api_version_params,
        seed_owner_1["user_id"],
        organization_id,
    )

    assert isinstance(permissions, list)
    assert org_permissions == []


# Проверяем, что права не смешиваются между организациями
@pytest.mark.extended
@pytest.mark.permissions_extended
@pytest.mark.skip(
    reason=(
        "Waiting for manual confirmation of how permissions are isolated "
        "between organizations for the same user."
    )
)
def test_user_permissions_do_not_mix_between_organizations(
    api_context,
    api_version_params,
    seed_owner_1,
    seed_owner_2,
    seed_employee_1,
    seed_org_1,
    seed_org_2,
):
    permission_ids = get_active_permission_ids(api_context, api_version_params, limit=2)
    first_organization_id, second_organization_id = (
        prepare_user_with_two_seed_organizations(
            api_context,
            api_version_params,
            seed_org_1,
            seed_org_2,
            seed_owner_1["user_id"],
            seed_owner_2["user_id"],
            seed_employee_1["user_id"],
            permission_ids,
        )
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

    first_permissions = get_user_permissions_for_organization(
        api_context,
        api_version_params,
        seed_employee_1["user_id"],
        first_organization_id,
    )
    second_permissions = get_user_permissions_for_organization(
        api_context,
        api_version_params,
        seed_employee_1["user_id"],
        second_organization_id,
    )

    assert first_permissions == [permission_ids[0]]
    assert second_permissions == [permission_ids[-1]]


# Проверяем check-permissions для назначенного права
@pytest.mark.extended
@pytest.mark.permissions_extended
def test_check_one_assigned_permission(
    api_context,
    api_version_params,
    seed_owner_1,
    seed_org_1,
):
    permission_id = get_first_permission_id(api_context, api_version_params)
    organization_id = prepare_seed_organization_for_user(
        api_context,
        api_version_params,
        seed_org_1["organization_id"],
        seed_owner_1["user_id"],
    )

    set_user_permissions(
        api_context,
        api_version_params,
        organization_id,
        seed_owner_1["user_id"],
        [permission_id],
    )
    result = check_user_permissions(
        api_context,
        api_version_params,
        seed_owner_1["user_id"],
        organization_id,
        [permission_id],
    )
    assert result is True


# Проверяем check-permissions для неназначенного права
@pytest.mark.extended
@pytest.mark.permissions_extended
@pytest.mark.skip(
    reason=(
        "Waiting for manual confirmation of effective permissions semantics in "
        "check-permissions."
    )
)
def test_check_unassigned_permission(
    api_context,
    api_version_params,
    seed_owner_1,
    seed_org_1,
):
    permission_ids = get_active_permission_ids(api_context, api_version_params, limit=2)
    organization_id = prepare_seed_organization_for_user(
        api_context,
        api_version_params,
        seed_org_1["organization_id"],
        seed_owner_1["user_id"],
    )

    set_user_permissions(
        api_context,
        api_version_params,
        organization_id,
        seed_owner_1["user_id"],
        [permission_ids[0]],
    )
    result = check_user_permissions(
        api_context,
        api_version_params,
        seed_owner_1["user_id"],
        organization_id,
        [permission_ids[-1]],
    )
    assert result is False


# Проверяем check-permissions для части назначенных прав
@pytest.mark.extended
@pytest.mark.permissions_extended
@pytest.mark.skip(
    reason=(
        "Waiting for manual confirmation of effective permissions semantics in "
        "check-permissions."
    )
)
def test_check_partially_assigned_permissions(
    api_context,
    api_version_params,
    seed_owner_1,
    seed_org_1,
):
    permission_ids = get_active_permission_ids(api_context, api_version_params, limit=2)
    organization_id = prepare_seed_organization_for_user(
        api_context,
        api_version_params,
        seed_org_1["organization_id"],
        seed_owner_1["user_id"],
    )

    set_user_permissions(
        api_context,
        api_version_params,
        organization_id,
        seed_owner_1["user_id"],
        [permission_ids[0]],
    )
    result = check_user_permissions(
        api_context,
        api_version_params,
        seed_owner_1["user_id"],
        organization_id,
        permission_ids,
    )
    assert result is False


# Проверяем check-permissions для всех назначенных прав
@pytest.mark.extended
@pytest.mark.permissions_extended
@pytest.mark.skip(
    reason=(
        "Waiting for manual confirmation of effective permissions semantics in "
        "check-permissions."
    )
)
def test_check_all_assigned_permissions(
    api_context,
    api_version_params,
    seed_owner_1,
    seed_org_1,
):
    permission_ids = get_active_permission_ids(api_context, api_version_params, limit=2)
    organization_id = prepare_seed_organization_for_user(
        api_context,
        api_version_params,
        seed_org_1["organization_id"],
        seed_owner_1["user_id"],
    )

    set_user_permissions(
        api_context,
        api_version_params,
        organization_id,
        seed_owner_1["user_id"],
        permission_ids,
    )
    result = check_user_permissions(
        api_context,
        api_version_params,
        seed_owner_1["user_id"],
        organization_id,
        permission_ids,
    )
    assert result is True


# Проверяем check-permissions с пустым списком permissionIds
@pytest.mark.extended
@pytest.mark.permissions_extended
@pytest.mark.skip(
    reason=(
        "Covered by focused xfail in negative suite: "
        "test_check_permissions_with_empty_permissions"
    )
)
def test_check_permissions_with_empty_permission_ids(
    api_context,
    api_version_params,
):
    response = api_context.get(
        f"/api/integrations/users/{uuid4()}/organizations/"
        f"{uuid4()}/check-permissions",
        params={
            **api_version_params,
            "permissionIds": "",
        },
    )

    assert_no_internal_error(response)
    assert response.status == 400, response.text()


# Проверяем права организации с несколькими пользователями
@pytest.mark.extended
@pytest.mark.permissions_extended
@pytest.mark.skip(
    reason=(
        "Waiting for manual confirmation of how organization permissions are "
        "returned for multiple users."
    )
)
def test_get_organization_permissions_multiple_users(
    api_context,
    api_version_params,
    seed_owner_1,
    seed_employee_1,
    seed_org_1,
):
    permission_ids = get_active_permission_ids(api_context, api_version_params, limit=2)
    organization_id = prepare_seed_organization_for_user(
        api_context,
        api_version_params,
        seed_org_1["organization_id"],
        seed_owner_1["user_id"],
        target_user_id=seed_employee_1["user_id"],
        permission_ids=permission_ids,
    )

    set_user_permissions(
        api_context,
        api_version_params,
        organization_id,
        seed_owner_1["user_id"],
        [permission_ids[0]],
    )
    set_user_permissions(
        api_context,
        api_version_params,
        organization_id,
        seed_employee_1["user_id"],
        [permission_ids[-1]],
    )
    permissions = get_organization_permissions(
        api_context,
        api_version_params,
        organization_id,
    )

    owner_item = next(
        item for item in permissions
        if item["userId"] == seed_owner_1["user_id"]
    )
    employee_item = next(
        item for item in permissions
        if item["userId"] == seed_employee_1["user_id"]
    )
    assert owner_item["permissionIds"] == [permission_ids[0]]
    assert employee_item["permissionIds"] == [permission_ids[-1]]


# Проверяем, что после изменения прав ответ организации обновляется
@pytest.mark.extended
@pytest.mark.permissions_extended
def test_organization_permissions_change_after_update(
    api_context,
    api_version_params,
    seed_owner_1,
    seed_org_1,
):
    permission_ids = get_active_permission_ids(api_context, api_version_params, limit=2)
    organization_id = prepare_seed_organization_for_user(
        api_context,
        api_version_params,
        seed_org_1["organization_id"],
        seed_owner_1["user_id"],
    )

    set_user_permissions(
        api_context,
        api_version_params,
        organization_id,
        seed_owner_1["user_id"],
        [permission_ids[0]],
    )
    set_user_permissions(
        api_context,
        api_version_params,
        organization_id,
        seed_owner_1["user_id"],
        [permission_ids[-1]],
    )
    permissions = get_organization_permissions(
        api_context,
        api_version_params,
        organization_id,
    )

    user_item = next(
        item for item in permissions
        if item["userId"] == seed_owner_1["user_id"]
    )
    assert user_item["permissionIds"] == [permission_ids[-1]]


# Проверяем, что в правах организации нет пользователей из другой организации
@pytest.mark.extended
@pytest.mark.permissions_extended
def test_organization_permissions_do_not_include_other_organization_users(
    api_context,
    api_version_params,
    seed_owner_1,
    seed_owner_2,
    seed_org_1,
    seed_org_2,
):
    first_permissions = get_organization_permissions(
        api_context,
        api_version_params,
        seed_org_1["organization_id"],
    )
    second_permissions = get_organization_permissions(
        api_context,
        api_version_params,
        seed_org_2["organization_id"],
    )

    assert all(
        item["userId"] != seed_owner_2["user_id"]
        for item in first_permissions
    )
    assert all(
        item["userId"] != seed_owner_1["user_id"]
        for item in second_permissions
    )


# Проверяем фильтр organizationId для прав пользователя
@pytest.mark.extended
@pytest.mark.permissions_extended
@pytest.mark.skip(
    reason=(
        "Waiting for manual confirmation of how organizationId filtering works "
        "for user permissions."
    )
)
def test_get_user_permissions_with_organization_filter(
    api_context,
    api_version_params,
    seed_owner_1,
    seed_owner_2,
    seed_employee_1,
    seed_org_1,
    seed_org_2,
):
    permission_ids = get_active_permission_ids(api_context, api_version_params, limit=2)
    first_organization_id, second_organization_id = (
        prepare_user_with_two_seed_organizations(
            api_context,
            api_version_params,
            seed_org_1,
            seed_org_2,
            seed_owner_1["user_id"],
            seed_owner_2["user_id"],
            seed_employee_1["user_id"],
            permission_ids,
        )
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

    all_permissions = get_user_permissions(
        api_context,
        api_version_params,
        seed_employee_1["user_id"],
    )
    first_permissions = get_user_permissions_filtered(
        api_context,
        api_version_params,
        seed_employee_1["user_id"],
        first_organization_id,
    )
    second_permissions = get_user_permissions_filtered(
        api_context,
        api_version_params,
        seed_employee_1["user_id"],
        second_organization_id,
    )

    assert {item["organizationId"] for item in all_permissions} >= {
        first_organization_id,
        second_organization_id,
    }
    assert [item["organizationId"] for item in first_permissions] == [
        first_organization_id,
    ]
    assert [item["organizationId"] for item in second_permissions] == [
        second_organization_id,
    ]
    assert first_permissions[0]["permissionIds"] == [permission_ids[0]]
    assert second_permissions[0]["permissionIds"] == [permission_ids[-1]]


# Проверяем фильтр organizationId для не связанной с пользователем организации
@pytest.mark.extended
@pytest.mark.permissions_extended
def test_get_user_permissions_with_unrelated_organization_filter(
    api_context,
    api_version_params,
    seed_owner_1,
    seed_org_2,
):
    response = api_context.get(
        f"/api/integrations/users/{seed_owner_1['user_id']}/permissions",
        params={
            **api_version_params,
            "organizationId": seed_org_2["organization_id"],
        },
    )

    assert_no_internal_error(response)
    assert response.status in [200, 400, 404], response.text()
    if response.ok:
        assert response.json() == []
