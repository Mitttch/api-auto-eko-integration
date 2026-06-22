from uuid import uuid4

import pytest

from tests.api.assertions import assert_no_internal_error
from tests.api.helpers import (
    ensure_employee_in_organization,
    get_organization_employees,
)


def prepare_seed_organization_with_employees(
    api_context,
    api_version_params,
    seed_org_1,
    seed_employee_1,
    seed_employee_2,
    seed_owner_2,
):
    organization_id = seed_org_1["organization_id"]
    employees = [
        {
            "user_id": seed_employee_1["user_id"],
            "email": seed_employee_1["email"],
        },
        {
            "user_id": seed_employee_2["user_id"],
            "email": seed_employee_2["email"],
        },
        {
            "user_id": seed_owner_2["user_id"],
            "email": seed_owner_2["email"],
        },
    ]

    for employee in employees:
        ensure_employee_in_organization(
            api_context,
            api_version_params,
            organization_id,
            employee["user_id"],
        )

    response = get_organization_employees(
        api_context,
        api_version_params,
        organization_id,
        offset=0,
        count=200,
    )
    employee_by_user_id = {item["userId"]: item for item in response["data"]}
    for employee in employees:
        employee["displayed_name"] = employee_by_user_id.get(
            employee["user_id"],
            {},
        ).get("displayedName", "")

    return organization_id, employees


def assert_employee_shape(employee, organization_id):
    assert employee["id"]
    assert employee["userId"]
    assert employee["organizationId"] == organization_id
    assert employee["status"]
    assert "email" in employee
    assert "employeePermissions" in employee


# Проверяем, что повторное добавление того же сотрудника не ломает setup и не дает 500
@pytest.mark.extended
@pytest.mark.employees_extended
def test_add_same_employee_twice(
    api_context,
    api_version_params,
    seed_org_1,
    seed_employee_1,
):
    organization_id = seed_org_1["organization_id"]
    ensure_employee_in_organization(
        api_context,
        api_version_params,
        organization_id,
        seed_employee_1["user_id"],
    )

    response = api_context.post(
        f"/api/integrations/organizations/{organization_id}/employees",
        params=api_version_params,
        data={
            "userId": seed_employee_1["user_id"],
            "permissionIds": [],
        },
    )

    assert_no_internal_error(response)
    assert response.status in [200, 400], response.text()


# Проверяем добавление нескольких seed-сотрудников в одну организацию
@pytest.mark.extended
@pytest.mark.employees_extended
def test_add_multiple_employees_to_organization(
    api_context,
    api_version_params,
    seed_org_1,
    seed_employee_1,
    seed_employee_2,
):
    organization_id = seed_org_1["organization_id"]

    ensure_employee_in_organization(
        api_context,
        api_version_params,
        organization_id,
        seed_employee_1["user_id"],
    )
    ensure_employee_in_organization(
        api_context,
        api_version_params,
        organization_id,
        seed_employee_2["user_id"],
    )

    employees = get_organization_employees(
        api_context,
        api_version_params,
        organization_id,
        offset=0,
        count=20,
    )
    employee_user_ids = [employee["userId"] for employee in employees["data"]]

    assert seed_employee_1["user_id"] in employee_user_ids
    assert seed_employee_2["user_id"] in employee_user_ids


# Проверяем добавление одного seed-пользователя в две разные организации
@pytest.mark.extended
@pytest.mark.employees_extended
def test_add_same_user_to_two_organizations(
    api_context,
    api_version_params,
    seed_org_1,
    seed_org_2,
    seed_employee_1,
):
    first_organization_id = seed_org_1["organization_id"]
    second_organization_id = seed_org_2["organization_id"]

    first_employee_record_id = ensure_employee_in_organization(
        api_context,
        api_version_params,
        first_organization_id,
        seed_employee_1["user_id"],
    )
    second_employee_record_id = ensure_employee_in_organization(
        api_context,
        api_version_params,
        second_organization_id,
        seed_employee_1["user_id"],
    )

    assert first_employee_record_id != second_employee_record_id


# Проверяем добавление несуществующего userId в существующую организацию
@pytest.mark.extended
@pytest.mark.employees_extended
def test_add_unknown_user_to_existing_organization(
    api_context,
    api_version_params,
    seed_org_1,
):
    organization_id = seed_org_1["organization_id"]

    response = api_context.post(
        f"/api/integrations/organizations/{organization_id}/employees",
        params=api_version_params,
        data={
            "userId": str(uuid4()),
            "permissionIds": [],
        },
    )

    assert_no_internal_error(response)
    assert response.status in [400, 404], response.text()


# Проверяем список сотрудников после идемпотентного добавления нескольких seed-пользователей
@pytest.mark.extended
@pytest.mark.employees_extended
def test_employee_list_after_adding_multiple_users(
    api_context,
    api_version_params,
    seed_org_1,
    seed_employee_1,
    seed_employee_2,
    seed_owner_2,
):
    organization_id = seed_org_1["organization_id"]
    employee_ids = [
        seed_employee_1["user_id"],
        seed_employee_2["user_id"],
        seed_owner_2["user_id"],
    ]

    for employee_id in employee_ids:
        ensure_employee_in_organization(
            api_context,
            api_version_params,
            organization_id,
            employee_id,
        )

    employees = get_organization_employees(
        api_context,
        api_version_params,
        organization_id,
        offset=0,
        count=20,
    )
    employee_user_ids = [employee["userId"] for employee in employees["data"]]

    for employee_id in employee_ids:
        assert employee_id in employee_user_ids


# Проверяем, что повторное добавление сотрудника не создает дубль в списке
@pytest.mark.extended
@pytest.mark.employees_extended
def test_no_duplicate_employee_after_second_add(
    api_context,
    api_version_params,
    seed_org_1,
    seed_employee_1,
):
    organization_id = seed_org_1["organization_id"]
    ensure_employee_in_organization(
        api_context,
        api_version_params,
        organization_id,
        seed_employee_1["user_id"],
    )

    second_response = api_context.post(
        f"/api/integrations/organizations/{organization_id}/employees",
        params=api_version_params,
        data={
            "userId": seed_employee_1["user_id"],
            "permissionIds": [],
        },
    )
    assert_no_internal_error(second_response)

    employees = get_organization_employees(
        api_context,
        api_version_params,
        organization_id,
        offset=0,
        count=20,
    )
    employee_user_ids = [employee["userId"] for employee in employees["data"]]
    assert employee_user_ids.count(seed_employee_1["user_id"]) == 1


# Проверяем, что сотрудники несуществующей организации возвращаются пустым списком
@pytest.mark.extended
@pytest.mark.employees_extended
def test_get_employees_for_unknown_organization(api_context, api_version_params):
    response = api_context.get(
        f"/api/integrations/organizations/{uuid4()}/employees",
        params={
            **api_version_params,
            "offset": 0,
            "count": 20,
        },
    )

    assert_no_internal_error(response)
    assert response.ok, response.text()
    assert response.json()["data"] == []
    assert response.json()["meta"]["totalCount"] == 0


# Проверяем получение сотрудников с невалидным organizationId
@pytest.mark.extended
@pytest.mark.employees_extended
def test_get_employees_with_invalid_organization_id(
    api_context,
    api_version_params,
):
    response = api_context.get(
        "/api/integrations/organizations/wrong-organization-id/employees",
        params={
            **api_version_params,
            "offset": 0,
            "count": 20,
        },
    )

    assert_no_internal_error(response)
    assert response.status in [400, 404], response.text()


# Проверяем получение сотрудников без query params
@pytest.mark.extended
@pytest.mark.employees_extended
def test_get_employees_without_query_params(
    api_context,
    api_version_params,
    seed_org_1,
    seed_employee_1,
    seed_employee_2,
    seed_owner_2,
):
    organization_id, employees = prepare_seed_organization_with_employees(
        api_context,
        api_version_params,
        seed_org_1,
        seed_employee_1,
        seed_employee_2,
        seed_owner_2,
    )

    response = api_context.get(
        f"/api/integrations/organizations/{organization_id}/employees",
        params=api_version_params,
    )

    assert response.ok, response.text()
    body = response.json()
    assert "data" in body
    assert "meta" in body
    assert body["meta"]["totalCount"] >= len(employees)
    for employee in body["data"]:
        assert_employee_shape(employee, organization_id)


# Проверяем count=1 для списка сотрудников
@pytest.mark.extended
@pytest.mark.employees_extended
def test_get_employees_with_count_one(
    api_context,
    api_version_params,
    seed_org_1,
    seed_employee_1,
    seed_employee_2,
    seed_owner_2,
):
    organization_id, _ = prepare_seed_organization_with_employees(
        api_context,
        api_version_params,
        seed_org_1,
        seed_employee_1,
        seed_employee_2,
        seed_owner_2,
    )

    response = api_context.get(
        f"/api/integrations/organizations/{organization_id}/employees",
        params={
            **api_version_params,
            "offset": 0,
            "count": 1,
        },
    )

    assert response.ok, response.text()
    assert len(response.json()["data"]) <= 1


# Проверяем offset и count для следующей страницы списка сотрудников
@pytest.mark.extended
@pytest.mark.employees_extended
def test_get_employees_with_offset_and_count(
    api_context,
    api_version_params,
    seed_org_1,
    seed_employee_1,
    seed_employee_2,
    seed_owner_2,
):
    organization_id, _ = prepare_seed_organization_with_employees(
        api_context,
        api_version_params,
        seed_org_1,
        seed_employee_1,
        seed_employee_2,
        seed_owner_2,
    )

    first_response = api_context.get(
        f"/api/integrations/organizations/{organization_id}/employees",
        params={
            **api_version_params,
            "offset": 0,
            "count": 1,
        },
    )
    second_response = api_context.get(
        f"/api/integrations/organizations/{organization_id}/employees",
        params={
            **api_version_params,
            "offset": 1,
            "count": 1,
        },
    )

    assert first_response.ok, first_response.text()
    assert second_response.ok, second_response.text()
    first_data = first_response.json()["data"]
    second_data = second_response.json()["data"]
    if first_data and second_data:
        assert first_data[0]["userId"] != second_data[0]["userId"]


# Проверяем поиск сотрудника по email
@pytest.mark.extended
@pytest.mark.employees_extended
def test_search_employee_by_email(
    api_context,
    api_version_params,
    seed_org_1,
    seed_employee_1,
    seed_employee_2,
    seed_owner_2,
):
    organization_id, employees = prepare_seed_organization_with_employees(
        api_context,
        api_version_params,
        seed_org_1,
        seed_employee_1,
        seed_employee_2,
        seed_owner_2,
    )
    expected_employee = employees[0]

    response = api_context.get(
        f"/api/integrations/organizations/{organization_id}/employees",
        params={
            **api_version_params,
            "search": expected_employee["email"],
            "offset": 0,
            "count": 20,
        },
    )

    assert response.ok, response.text()
    assert any(
        item["userId"] == expected_employee["user_id"]
        for item in response.json()["data"]
    )


# Проверяем поиск сотрудника по отображаемому имени
@pytest.mark.extended
@pytest.mark.employees_extended
def test_search_employee_by_displayed_name(
    api_context,
    api_version_params,
    seed_org_1,
    seed_employee_1,
    seed_employee_2,
    seed_owner_2,
):
    organization_id, employees = prepare_seed_organization_with_employees(
        api_context,
        api_version_params,
        seed_org_1,
        seed_employee_1,
        seed_employee_2,
        seed_owner_2,
    )
    search_value = next(
        (
            employee["displayed_name"]
            for employee in employees
            if employee["displayed_name"]
        ),
        "",
    )
    if not search_value:
        pytest.skip("Seed employees do not have displayedName for employee search")

    response = api_context.get(
        f"/api/integrations/organizations/{organization_id}/employees",
        params={
            **api_version_params,
            "search": search_value,
            "offset": 0,
            "count": 20,
        },
    )

    assert response.ok, response.text()
    employee_ids = [item["userId"] for item in response.json()["data"]]
    assert any(employee["user_id"] in employee_ids for employee in employees)


# Проверяем confirmedOnly=true для списка сотрудников
@pytest.mark.extended
@pytest.mark.employees_extended
def test_get_employees_confirmed_only_true(
    api_context,
    api_version_params,
    seed_org_1,
    seed_employee_1,
    seed_employee_2,
    seed_owner_2,
):
    organization_id, _ = prepare_seed_organization_with_employees(
        api_context,
        api_version_params,
        seed_org_1,
        seed_employee_1,
        seed_employee_2,
        seed_owner_2,
    )

    response = api_context.get(
        f"/api/integrations/organizations/{organization_id}/employees",
        params={
            **api_version_params,
            "confirmedOnly": True,
            "offset": 0,
            "count": 20,
        },
    )

    assert_no_internal_error(response)
    assert response.ok, response.text()
    assert all(item["status"] == "Confirmed" for item in response.json()["data"])


# Проверяем confirmedOnly=false для списка сотрудников
@pytest.mark.extended
@pytest.mark.employees_extended
def test_get_employees_confirmed_only_false(
    api_context,
    api_version_params,
    seed_org_1,
    seed_employee_1,
    seed_employee_2,
    seed_owner_2,
):
    organization_id, employees = prepare_seed_organization_with_employees(
        api_context,
        api_version_params,
        seed_org_1,
        seed_employee_1,
        seed_employee_2,
        seed_owner_2,
    )

    response = api_context.get(
        f"/api/integrations/organizations/{organization_id}/employees",
        params={
            **api_version_params,
            "confirmedOnly": False,
            "offset": 0,
            "count": 20,
        },
    )

    assert_no_internal_error(response)
    assert response.ok, response.text()
    assert response.json()["meta"]["totalCount"] >= len(employees)


# Проверяем sortOrder=Asc для списка сотрудников
@pytest.mark.extended
@pytest.mark.employees_extended
def test_get_employees_sort_order_asc(
    api_context,
    api_version_params,
    seed_org_1,
    seed_employee_1,
    seed_employee_2,
    seed_owner_2,
):
    organization_id, _ = prepare_seed_organization_with_employees(
        api_context,
        api_version_params,
        seed_org_1,
        seed_employee_1,
        seed_employee_2,
        seed_owner_2,
    )

    response = api_context.get(
        f"/api/integrations/organizations/{organization_id}/employees",
        params={
            **api_version_params,
            "sortField": "createdAt",
            "sortOrder": "Asc",
            "offset": 0,
            "count": 20,
        },
    )

    assert_no_internal_error(response)
    assert response.ok, response.text()


# Проверяем sortOrder=Desc для списка сотрудников
@pytest.mark.extended
@pytest.mark.employees_extended
def test_get_employees_sort_order_desc(
    api_context,
    api_version_params,
    seed_org_1,
    seed_employee_1,
    seed_employee_2,
    seed_owner_2,
):
    organization_id, _ = prepare_seed_organization_with_employees(
        api_context,
        api_version_params,
        seed_org_1,
        seed_employee_1,
        seed_employee_2,
        seed_owner_2,
    )

    response = api_context.get(
        f"/api/integrations/organizations/{organization_id}/employees",
        params={
            **api_version_params,
            "sortField": "createdAt",
            "sortOrder": "Desc",
            "offset": 0,
            "count": 20,
        },
    )

    assert_no_internal_error(response)
    assert response.ok, response.text()


# Проверяем invalid count для списка сотрудников
@pytest.mark.extended
@pytest.mark.employees_extended
def test_get_employees_with_invalid_count(
    api_context,
    api_version_params,
    seed_org_1,
    seed_employee_1,
    seed_employee_2,
    seed_owner_2,
):
    organization_id, _ = prepare_seed_organization_with_employees(
        api_context,
        api_version_params,
        seed_org_1,
        seed_employee_1,
        seed_employee_2,
        seed_owner_2,
    )

    response = api_context.get(
        f"/api/integrations/organizations/{organization_id}/employees",
        params={
            **api_version_params,
            "offset": 0,
            "count": -1,
        },
    )

    assert_no_internal_error(response)
    assert response.status in [200, 400], response.text()


# Проверяем invalid offset для списка сотрудников
@pytest.mark.extended
@pytest.mark.employees_extended
def test_get_employees_with_invalid_offset(
    api_context,
    api_version_params,
    seed_org_1,
    seed_employee_1,
    seed_employee_2,
    seed_owner_2,
):
    organization_id, _ = prepare_seed_organization_with_employees(
        api_context,
        api_version_params,
        seed_org_1,
        seed_employee_1,
        seed_employee_2,
        seed_owner_2,
    )

    response = api_context.get(
        f"/api/integrations/organizations/{organization_id}/employees",
        params={
            **api_version_params,
            "offset": -1,
            "count": 20,
        },
    )

    assert_no_internal_error(response)
    assert response.status in [200, 400], response.text()


# Проверяем invalid sortOrder для списка сотрудников
@pytest.mark.extended
@pytest.mark.employees_extended
def test_get_employees_with_invalid_sort_order(
    api_context,
    api_version_params,
    seed_org_1,
    seed_employee_1,
    seed_employee_2,
    seed_owner_2,
):
    organization_id, _ = prepare_seed_organization_with_employees(
        api_context,
        api_version_params,
        seed_org_1,
        seed_employee_1,
        seed_employee_2,
        seed_owner_2,
    )

    response = api_context.get(
        f"/api/integrations/organizations/{organization_id}/employees",
        params={
            **api_version_params,
            "sortOrder": "Wrong",
            "offset": 0,
            "count": 20,
        },
    )

    assert_no_internal_error(response)
    assert response.status == 400, response.text()


# Проверяем unknown sortField для списка сотрудников
@pytest.mark.extended
@pytest.mark.employees_extended
def test_get_employees_with_unknown_sort_field(
    api_context,
    api_version_params,
    seed_org_1,
    seed_employee_1,
    seed_employee_2,
    seed_owner_2,
):
    organization_id, _ = prepare_seed_organization_with_employees(
        api_context,
        api_version_params,
        seed_org_1,
        seed_employee_1,
        seed_employee_2,
        seed_owner_2,
    )

    response = api_context.get(
        f"/api/integrations/organizations/{organization_id}/employees",
        params={
            **api_version_params,
            "sortField": "unknownField",
            "sortOrder": "Asc",
            "offset": 0,
            "count": 20,
        },
    )

    assert_no_internal_error(response)
    assert response.status in [200, 400], response.text()
