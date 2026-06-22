from uuid import uuid4

import pytest

from tests.api.assertions import assert_no_internal_error
from tests.api.factories import AUTOTEST_RU_PREFIX, create_valid_inn
from tests.api.helpers import (
    create_organization,
    create_user_by_email,
    get_first_permission_id,
    get_organizations_by_ids,
)


# Проверяем повторное создание организации с тем же ИНН и КПП
@pytest.mark.extended
@pytest.mark.organizations_extended
def test_create_organization_with_same_inn_and_kpp(
    api_context,
    api_version_params,
):
    user_id, _ = create_user_by_email(api_context, api_version_params)
    permission_id = get_first_permission_id(api_context, api_version_params)
    _, inn, kpp = create_organization(
        api_context,
        api_version_params,
        user_id,
        permission_id,
    )

    response = api_context.post(
        "/api/integrations/organizations",
        params=api_version_params,
        data={
            "userId": user_id,
            "permissionIds": [permission_id],
            "organizationInfo": {
                "inn": inn,
                "kpp": kpp,
                "ogrn": "1027700132195",
                "name": f"{AUTOTEST_RU_PREFIX} организация дубль",
                "fullName": f"{AUTOTEST_RU_PREFIX} общество дубль",
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

    assert_no_internal_error(response)
    assert response.status in [200, 400], response.text()


# Проверяем создание двух организаций с одинаковым ИНН и разными КПП
@pytest.mark.extended
@pytest.mark.organizations_extended
def test_create_two_organizations_same_inn_different_kpp(
    api_context,
    api_version_params,
):
    user_id, _ = create_user_by_email(api_context, api_version_params)
    permission_id = get_first_permission_id(api_context, api_version_params)
    inn = create_valid_inn()

    first_organization_id, _, _ = create_organization(
        api_context,
        api_version_params,
        user_id,
        permission_id,
        inn=inn,
        kpp="770101001",
    )
    second_organization_id, _, _ = create_organization(
        api_context,
        api_version_params,
        user_id,
        permission_id,
        inn=inn,
        kpp="770201001",
    )

    assert first_organization_id != second_organization_id


# Проверяем создание организации с несуществующим userId создателя
@pytest.mark.extended
@pytest.mark.organizations_extended
def test_create_organization_with_unknown_creator(api_context, api_version_params):
    permission_id = get_first_permission_id(api_context, api_version_params)

    response = api_context.post(
        "/api/integrations/organizations",
        params=api_version_params,
        data={
            "userId": str(uuid4()),
            "permissionIds": [permission_id],
            "organizationInfo": {
                "inn": create_valid_inn(),
                "kpp": "770101001",
                "ogrn": "1027700132195",
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

    assert_no_internal_error(response)
    assert response.status in [400, 404], response.text()


# Проверяем получение нескольких организаций одним запросом
@pytest.mark.extended
@pytest.mark.organizations_extended
def test_get_organizations_with_multiple_ids(api_context, api_version_params):
    user_id, _ = create_user_by_email(api_context, api_version_params)
    permission_id = get_first_permission_id(api_context, api_version_params)
    first_organization_id, _, _ = create_organization(
        api_context,
        api_version_params,
        user_id,
        permission_id,
    )
    second_organization_id, _, _ = create_organization(
        api_context,
        api_version_params,
        user_id,
        permission_id,
    )

    response = api_context.get(
        "/api/integrations/organizations",
        params={
            **api_version_params,
            "ids": f"{first_organization_id},{second_organization_id}",
        },
    )

    assert response.ok, response.text()

    organization_ids = [organization["id"] for organization in response.json()]
    assert first_organization_id in organization_ids
    assert second_organization_id in organization_ids


# Проверяем получение организаций с valid + unknown id
@pytest.mark.extended
@pytest.mark.organizations_extended
def test_get_organizations_with_valid_and_unknown_id(
    api_context,
    api_version_params,
):
    user_id, _ = create_user_by_email(api_context, api_version_params)
    organization_id, _, _ = create_organization(
        api_context,
        api_version_params,
        user_id,
    )
    unknown_organization_id = str(uuid4())

    response = api_context.get(
        "/api/integrations/organizations",
        params={
            **api_version_params,
            "ids": f"{organization_id},{unknown_organization_id}",
        },
    )

    assert_no_internal_error(response)
    assert response.ok, response.text()

    organization_ids = [organization["id"] for organization in response.json()]
    assert organization_id in organization_ids
    assert unknown_organization_id not in organization_ids


# Проверяем, что дубли ids организаций не приводят к дублям в ответе
@pytest.mark.extended
@pytest.mark.organizations_extended
def test_get_organizations_with_duplicate_ids(api_context, api_version_params):
    user_id, _ = create_user_by_email(api_context, api_version_params)
    organization_id, _, _ = create_organization(
        api_context,
        api_version_params,
        user_id,
    )

    response = api_context.get(
        "/api/integrations/organizations",
        params={
            **api_version_params,
            "ids": f"{organization_id},{organization_id}",
        },
    )

    assert_no_internal_error(response)
    assert response.ok, response.text()

    organization_ids = [organization["id"] for organization in response.json()]
    assert organization_ids.count(organization_id) == 1


# Проверяем, что пустой ids организаций не приводит к 500
@pytest.mark.extended
@pytest.mark.organizations_extended
@pytest.mark.xfail(
    reason=(
        "Known API bug: empty organization ids query returns 500 "
        "NullReferenceException instead of 400 or 200 []"
    ),
    strict=True,
)
def test_get_organizations_with_empty_ids(api_context, api_version_params):
    response = api_context.get(
        "/api/integrations/organizations",
        params={
            **api_version_params,
            "ids": "",
        },
    )

    assert_no_internal_error(response)
    assert response.status == 400, response.text()


# Проверяем, что GET organizations без ids возвращает пустой список
@pytest.mark.extended
@pytest.mark.organizations_extended
def test_get_organizations_without_ids(api_context, api_version_params):
    response = api_context.get(
        "/api/integrations/organizations",
        params=api_version_params,
    )

    assert_no_internal_error(response)
    assert response.ok, response.text()
    assert response.json() == []


# Проверяем, что поиск только по ИНН не падает и возвращает список
@pytest.mark.extended
@pytest.mark.organizations_extended
def test_search_organization_by_inn_only(api_context, api_version_params):
    user_id, _ = create_user_by_email(api_context, api_version_params)
    organization_id, inn, _ = create_organization(
        api_context,
        api_version_params,
        user_id,
    )

    response = api_context.get(
        "/api/integrations/organizations/search",
        params={
            **api_version_params,
            "inn": inn,
        },
    )

    assert response.ok, response.text()
    assert isinstance(response.json(), list)


# Проверяем поиск организации по ИНН и КПП
@pytest.mark.extended
@pytest.mark.organizations_extended
def test_search_organization_by_inn_and_kpp(api_context, api_version_params):
    user_id, _ = create_user_by_email(api_context, api_version_params)
    organization_id, inn, kpp = create_organization(
        api_context,
        api_version_params,
        user_id,
    )

    response = api_context.get(
        "/api/integrations/organizations/search",
        params={
            **api_version_params,
            "inn": inn,
            "kpp": kpp,
        },
    )

    assert response.ok, response.text()
    assert any(item["id"] == organization_id for item in response.json())


# Проверяем поиск организации по ИНН с неверным КПП
@pytest.mark.extended
@pytest.mark.organizations_extended
def test_search_organization_by_inn_with_wrong_kpp(
    api_context,
    api_version_params,
):
    user_id, _ = create_user_by_email(api_context, api_version_params)
    organization_id, inn, _ = create_organization(
        api_context,
        api_version_params,
        user_id,
    )

    response = api_context.get(
        "/api/integrations/organizations/search",
        params={
            **api_version_params,
            "inn": inn,
            "kpp": "770999001",
        },
    )

    assert response.ok, response.text()
    assert all(item["id"] != organization_id for item in response.json())


# Проверяем поиск несуществующей организации
@pytest.mark.extended
@pytest.mark.organizations_extended
def test_search_unknown_organization(api_context, api_version_params):
    response = api_context.get(
        "/api/integrations/organizations/search",
        params={
            **api_version_params,
            "inn": create_valid_inn(),
        },
    )

    assert response.ok, response.text()
    assert response.json() == []


def create_organization_and_get_status(api_context, api_version_params):
    user_id, _ = create_user_by_email(api_context, api_version_params)
    organization_id, inn, kpp = create_organization(
        api_context,
        api_version_params,
        user_id,
    )
    organization = get_organizations_by_ids(
        api_context,
        api_version_params,
        [organization_id],
    )[0]

    return organization_id, inn, kpp, organization["status"]


# Проверяем поиск организации по ИНН и фактическому статусу
@pytest.mark.extended
@pytest.mark.organizations_extended
def test_search_organization_by_inn_and_actual_status(
    api_context,
    api_version_params,
):
    organization_id, inn, kpp, status = create_organization_and_get_status(
        api_context,
        api_version_params,
    )

    response = api_context.get(
        "/api/integrations/organizations/search",
        params={
            **api_version_params,
            "inn": inn,
            "kpp": kpp,
            "status": status,
        },
    )

    assert response.ok, response.text()
    assert any(item["id"] == organization_id for item in response.json())


# Проверяем поиск организации по ИНН, КПП и фактическому статусу
@pytest.mark.extended
@pytest.mark.organizations_extended
def test_search_organization_by_inn_kpp_and_actual_status(
    api_context,
    api_version_params,
):
    organization_id, inn, kpp, status = create_organization_and_get_status(
        api_context,
        api_version_params,
    )

    response = api_context.get(
        "/api/integrations/organizations/search",
        params={
            **api_version_params,
            "inn": inn,
            "kpp": kpp,
            "status": status,
        },
    )

    assert response.ok, response.text()
    assert any(item["id"] == organization_id for item in response.json())


# Проверяем поиск организации с неподходящим статусом
@pytest.mark.extended
@pytest.mark.organizations_extended
def test_search_organization_by_wrong_status_does_not_return_created_org(
    api_context,
    api_version_params,
):
    organization_id, inn, _, status = create_organization_and_get_status(
        api_context,
        api_version_params,
    )
    wrong_status = "Disabled" if status != "Disabled" else "Pending"

    response = api_context.get(
        "/api/integrations/organizations/search",
        params={
            **api_version_params,
            "inn": inn,
            "status": wrong_status,
        },
    )

    assert_no_internal_error(response)
    assert response.ok, response.text()
    assert all(item["id"] != organization_id for item in response.json())


# Проверяем invalid status в поиске организаций
@pytest.mark.extended
@pytest.mark.organizations_extended
def test_search_organization_with_invalid_status(api_context, api_version_params):
    response = api_context.get(
        "/api/integrations/organizations/search",
        params={
            **api_version_params,
            "inn": create_valid_inn(),
            "status": "WrongStatus",
        },
    )

    assert_no_internal_error(response)
    assert response.status == 400, response.text()


# Проверяем status в неправильном регистре
@pytest.mark.extended
@pytest.mark.organizations_extended
def test_search_organization_with_lowercase_status(api_context, api_version_params):
    response = api_context.get(
        "/api/integrations/organizations/search",
        params={
            **api_version_params,
            "inn": create_valid_inn(),
            "status": "confirmed",
        },
    )

    assert_no_internal_error(response)
    assert response.status in [200, 400], response.text()


# Проверяем Disabled status только при наличии безопасного способа подготовки данных
@pytest.mark.extended
@pytest.mark.organizations_extended
def test_search_disabled_organization_status_is_not_prepared():
    pytest.skip("No safe API flow to prepare Disabled organization on demo stand")
