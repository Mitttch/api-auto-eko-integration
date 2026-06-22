import pytest

from tests.api.cleanup import CleanupRegistry
from tests.api.seed_support import (
    collect_seed_protection,
    get_seed_organization,
    get_seed_organizations,
    get_seed_user,
    get_seed_users,
)


# Проверяем, что helper читает seed-пользователя из настроек, когда env заполнен
def test_get_seed_user_returns_expected_values():
    settings = {
        "target_env": "demo",
        "seed_owner_1_user_id": "user-1",
        "seed_owner_1_email": "seed-owner-1@example.com",
        "seed_owner_1_phone": "+79990000001",
    }

    seed_user = get_seed_user(settings, "seed_owner_1", pytest)

    assert seed_user["seed_owner_1_user_id"] == "user-1"
    assert seed_user["seed_owner_1_email"] == "seed-owner-1@example.com"
    assert seed_user["seed_owner_1_phone"] == "+79990000001"
    assert seed_user["user_id"] == "user-1"
    assert seed_user["email"] == "seed-owner-1@example.com"
    assert seed_user["phone"] == "+79990000001"
    assert seed_user["alias"] == "owner_1"
    assert seed_user["target_env"] == "demo"


# Проверяем, что helper пропускает seed-based сценарий с понятной причиной, если env не заполнен
def test_get_seed_user_skips_when_required_env_is_missing():
    settings = {
        "target_env": "integrity",
        "seed_owner_1_user_id": "",
        "seed_owner_1_email": "",
    }

    with pytest.raises(pytest.skip.Exception) as error:
        get_seed_user(settings, "seed_owner_1", pytest)

    assert "Seed user 'seed_owner_1' is not configured for environment 'integrity'" in str(error.value)
    assert "seed_owner_1_user_id" in str(error.value)
    assert "seed_owner_1_email" in str(error.value)


# Проверяем, что helper читает seed-организацию из настроек, когда env заполнен
def test_get_seed_organization_returns_expected_values():
    settings = {
        "target_env": "demo",
        "seed_org_1_id": "org-1",
        "seed_org_1_inn": "7701234567",
        "seed_org_1_kpp": "770101001",
    }

    seed_organization = get_seed_organization(settings, "seed_org_1", pytest)

    assert seed_organization["seed_org_1_id"] == "org-1"
    assert seed_organization["seed_org_1_inn"] == "7701234567"
    assert seed_organization["seed_org_1_kpp"] == "770101001"
    assert seed_organization["organization_id"] == "org-1"
    assert seed_organization["inn"] == "7701234567"
    assert seed_organization["kpp"] == "770101001"
    assert seed_organization["alias"] == "org_1"
    assert seed_organization["target_env"] == "demo"


# Проверяем, что helper собирает каталог seed-пользователей для текущего стенда
def test_get_seed_users_returns_environment_specific_catalog():
    settings = {
        "target_env": "integrity",
        "seed_owner_1_user_id": "owner-1",
        "seed_owner_1_email": "owner-1@example.com",
        "seed_owner_2_user_id": "owner-2",
        "seed_owner_2_email": "owner-2@example.com",
        "seed_employee_1_user_id": "employee-1",
        "seed_employee_1_email": "employee-1@example.com",
        "seed_employee_2_user_id": "employee-2",
        "seed_employee_2_email": "employee-2@example.com",
    }

    seed_users = get_seed_users(settings, pytest)

    assert seed_users["seed_owner_1"]["user_id"] == "owner-1"
    assert seed_users["seed_owner_2"]["user_id"] == "owner-2"
    assert seed_users["seed_employee_1"]["user_id"] == "employee-1"
    assert seed_users["seed_employee_2"]["user_id"] == "employee-2"
    assert all(item["target_env"] == "integrity" for item in seed_users.values())


# Проверяем, что helper собирает каталог seed-организаций для текущего стенда
def test_get_seed_organizations_returns_environment_specific_catalog():
    settings = {
        "target_env": "integrity",
        "seed_org_1_id": "org-1",
        "seed_org_1_inn": "7701234567",
        "seed_org_1_kpp": "770101001",
        "seed_org_2_id": "org-2",
        "seed_org_2_inn": "7702234567",
        "seed_org_2_kpp": "770201001",
    }

    seed_organizations = get_seed_organizations(settings, pytest)

    assert seed_organizations["seed_org_1"]["organization_id"] == "org-1"
    assert seed_organizations["seed_org_2"]["organization_id"] == "org-2"
    assert all(
        item["target_env"] == "integrity"
        for item in seed_organizations.values()
    )


# Проверяем, что seed-сущности попадают в защитный список и не могут быть отправлены в cleanup
def test_cleanup_registry_protects_seed_entities():
    settings = {
        "seed_owner_1_user_id": "user-1",
        "seed_owner_1_email": "seed-owner-1@example.com",
        "seed_owner_1_phone": "+79990000001",
        "seed_org_1_id": "org-1",
        "seed_org_1_inn": "7701234567",
        "seed_org_1_kpp": "770101001",
    }

    protected = collect_seed_protection(settings)
    registry = CleanupRegistry(
        protected_emails=protected["emails"],
        protected_user_ids=protected["user_ids"],
        protected_organization_ids=protected["organization_ids"],
    )

    with pytest.raises(AssertionError, match="Seed account email"):
        registry.register_email("seed-owner-1@example.com")

    with pytest.raises(AssertionError, match="Seed user"):
        registry.register_user("user-1")

    with pytest.raises(AssertionError, match="Seed organization"):
        registry.register_organization("org-1")


# Проверяем, что pytest fixture для seed-пользователя импортируется из conftest
def test_seed_owner_1_fixture_is_available(seed_owner_1):
    assert "seed_owner_1_user_id" in seed_owner_1
    assert "seed_owner_1_email" in seed_owner_1
