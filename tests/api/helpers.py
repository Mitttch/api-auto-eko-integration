import time

from tests.api.assertions import assert_no_internal_error, assert_uuid
from tests.api.factories import (
    create_organization_payload,
    unique_email,
    unique_phone,
)


def create_user_by_email(api_context, api_version_params, email=None):
    user_email = email or unique_email()

    response = api_context.post(
        "/api/integrations/precreate",
        params=api_version_params,
        data={
            "email": user_email,
            "password": "TestPassword123!",
        },
    )

    assert response.ok, response.text()

    user_id = response.json()
    assert_uuid(user_id)

    return user_id, user_email


def create_user_by_phone(api_context, api_version_params, phone=None):
    user_phone = phone or unique_phone()

    response = api_context.post(
        "/api/integrations/precreate/byphone",
        params=api_version_params,
        data={
            "phoneNumber": user_phone,
            "password": "TestPassword123!",
        },
    )

    assert response.ok, response.text()

    user_id = response.json()
    assert_uuid(user_id)

    return user_id, user_phone


def get_first_permission_id(api_context, api_version_params):
    return get_active_permission_ids(api_context, api_version_params, limit=1)[0]


def get_active_permission_ids(api_context, api_version_params, limit=None):
    response = api_context.get(
        "/api/integrations/products/permissions",
        params=api_version_params,
    )

    assert response.ok, response.text()

    permissions = response.json()
    assert isinstance(permissions, list)
    assert len(permissions) > 0

    active_permission_ids = [
        permission["id"]
        for permission in permissions
        if permission["isPermission"] and not permission["isDisabled"]
    ]

    if not active_permission_ids:
        raise AssertionError("No active product permissions found")

    if limit:
        return active_permission_ids[:limit]

    return active_permission_ids


def create_organization(
    api_context,
    api_version_params,
    user_id,
    permission_id=None,
    inn=None,
    kpp=None,
):
    selected_permission_id = permission_id or get_first_permission_id(
        api_context,
        api_version_params,
    )
    organization_data = create_organization_payload(
        user_id=user_id,
        permission_id=selected_permission_id,
        inn=inn,
        kpp=kpp,
    )

    response = api_context.post(
        "/api/integrations/organizations",
        params=api_version_params,
        data=organization_data["payload"],
    )

    assert response.ok, response.text()

    organization_id = response.json()
    assert_uuid(organization_id)

    return organization_id, organization_data["inn"], organization_data["kpp"]


def add_employee(api_context, api_version_params, organization_id, user_id):
    permission_id = get_first_permission_id(api_context, api_version_params)

    response = api_context.post(
        f"/api/integrations/organizations/{organization_id}/employees",
        params=api_version_params,
        data={
            "userId": user_id,
            "permissionIds": [permission_id],
        },
    )

    assert response.ok, response.text()
    employee_id = response.json()
    assert_uuid(employee_id)

    return employee_id


def get_organization_employees(
    api_context,
    api_version_params,
    organization_id,
    **query_params,
):
    response = api_context.get(
        f"/api/integrations/organizations/{organization_id}/employees",
        params={
            **api_version_params,
            **query_params,
        },
    )

    assert response.ok, response.text()
    return response.json()


def find_employee_in_organization(
    api_context,
    api_version_params,
    organization_id,
    user_id,
):
    employees = get_organization_employees(
        api_context,
        api_version_params,
        organization_id,
        offset=0,
        count=200,
    )

    for employee in employees["data"]:
        if employee["userId"] == user_id:
            return employee

    return None


def ensure_employee_in_organization(
    api_context,
    api_version_params,
    organization_id,
    user_id,
    permission_ids=None,
):
    existing_employee = find_employee_in_organization(
        api_context,
        api_version_params,
        organization_id,
        user_id,
    )
    if existing_employee:
        return existing_employee["id"]

    selected_permission_ids = permission_ids
    if selected_permission_ids is None:
        selected_permission_ids = [get_first_permission_id(api_context, api_version_params)]

    response = api_context.post(
        f"/api/integrations/organizations/{organization_id}/employees",
        params=api_version_params,
        data={
            "userId": user_id,
            "permissionIds": selected_permission_ids,
        },
    )

    if response.ok:
        employee_id = response.json()
        assert_uuid(employee_id)
        return employee_id

    assert_no_internal_error(response)

    existing_employee = find_employee_in_organization(
        api_context,
        api_version_params,
        organization_id,
        user_id,
    )
    if existing_employee:
        return existing_employee["id"]

    raise AssertionError(response.text())


def update_user_permissions(
    api_context,
    api_version_params,
    organization_id,
    user_id,
    permission_ids,
):
    response = api_context.post(
        f"/api/integrations/organizations/{organization_id}/users/"
        f"{user_id}/permissions",
        params=api_version_params,
        data=permission_ids,
    )

    assert response.ok, response.text()


def set_user_permissions(
    api_context,
    api_version_params,
    organization_id,
    user_id,
    permission_ids,
):
    update_user_permissions(
        api_context,
        api_version_params,
        organization_id,
        user_id,
        permission_ids,
    )

    deadline = time.time() + 5
    assigned_permissions = []

    while time.time() < deadline:
        assigned_permissions = get_user_permissions_for_organization(
            api_context,
            api_version_params,
            user_id,
            organization_id,
        )
        if set(assigned_permissions) == set(permission_ids):
            return assigned_permissions

        time.sleep(0.5)

    assert set(assigned_permissions) == set(permission_ids)
    return assigned_permissions


def get_user_permissions(api_context, api_version_params, user_id):
    response = api_context.get(
        f"/api/integrations/users/{user_id}/permissions",
        params=api_version_params,
    )

    assert response.ok, response.text()
    return response.json()


def get_user_permissions_filtered(
    api_context,
    api_version_params,
    user_id,
    organization_id,
):
    response = api_context.get(
        f"/api/integrations/users/{user_id}/permissions",
        params={
            **api_version_params,
            "organizationId": organization_id,
        },
    )

    assert response.ok, response.text()
    return response.json()


def get_user_permissions_for_organization(
    api_context,
    api_version_params,
    user_id,
    organization_id,
):
    user_permissions = get_user_permissions(api_context, api_version_params, user_id)

    for item in user_permissions:
        if item["organizationId"] == organization_id:
            return item["permissionIds"] or []

    return []


def check_user_permissions(
    api_context,
    api_version_params,
    user_id,
    organization_id,
    permission_ids,
):
    response = api_context.get(
        f"/api/integrations/users/{user_id}/organizations/"
        f"{organization_id}/check-permissions",
        params={
            **api_version_params,
            "permissionIds": ",".join(permission_ids),
        },
    )

    assert response.ok, response.text()
    return response.json()


def get_organization_permissions(api_context, api_version_params, organization_id):
    response = api_context.get(
        f"/api/integrations/organizations/{organization_id}/permissions",
        params=api_version_params,
    )

    assert response.ok, response.text()
    return response.json()


def get_users_by_ids(api_context, api_version_params, user_ids):
    response = api_context.get(
        "/api/integrations/users",
        params={
            **api_version_params,
            "ids": ",".join(user_ids),
        },
    )

    assert response.ok, response.text()
    return response.json()


def get_user_by_id(api_context, api_version_params, user_id):
    users = get_users_by_ids(api_context, api_version_params, [user_id])

    assert len(users) == 1
    return users[0]


def add_user_email(api_context, api_version_params, user_id, email=None):
    user_email = email or unique_email()

    response = api_context.post(
        "/api/integrations/users/email",
        params=api_version_params,
        data={
            "userId": user_id,
            "email": user_email,
        },
    )

    assert response.ok, response.text()
    return user_email


def get_organizations_by_ids(api_context, api_version_params, organization_ids):
    response = api_context.get(
        "/api/integrations/organizations",
        params={
            **api_version_params,
            "ids": ",".join(organization_ids),
        },
    )

    assert response.ok, response.text()
    return response.json()
