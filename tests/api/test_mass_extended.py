import pytest

from tests.api.assertions import assert_no_internal_error, assert_user_deleted
from tests.api.cleanup import delete_created_accounts, is_current_env_cleanup_email
from tests.api.factories import unique_cleanup_email, unique_email
from tests.api.helpers import get_users_by_ids


def create_mass_payload(count, cleanup_safe=True, prefix="mass"):
    payload = []
    for _ in range(count):
        email = unique_cleanup_email(prefix) if cleanup_safe else unique_email(prefix)
        payload.append(
            {
                "email": email,
                "password": "TestPassword123!",
            }
        )

    return payload


def cleanup_created_mass_users(
    api_context,
    api_version_params,
    created_users,
    deleted_emails,
):
    cleanup_emails = [
        item["email"]
        for item in created_users
        if is_current_env_cleanup_email(item.get("email", ""))
    ]
    delete_created_accounts(
        api_context,
        api_version_params,
        cleanup_emails,
        deleted_emails,
    )

    for item in created_users:
        email = item.get("email")
        user_id = item.get("id") or item.get("userId")
        if email and user_id and is_current_env_cleanup_email(email):
            assert_user_deleted(api_context, api_version_params, user_id, email)


# Проверяем массовое создание нескольких пользователей по email с безопасным cleanup
@pytest.mark.extended
@pytest.mark.mass_extended
def test_precreate_mass_with_valid_users(api_context, api_version_params):
    payload = create_mass_payload(3, prefix="mass")
    created_users = []
    deleted_emails = set()

    try:
        response = api_context.post(
            "/api/integrations/precreatemass",
            params=api_version_params,
            data=payload,
        )

        assert response.ok, response.text()

        created_users = response.json()
        assert len(created_users) == 3
        assert all(item["id"] for item in created_users)
    finally:
        cleanup_created_mass_users(
            api_context,
            api_version_params,
            created_users,
            deleted_emails,
        )


# Проверяем, что пользователи из mass доступны через GET users и потом удаляются
@pytest.mark.extended
@pytest.mark.mass_extended
def test_precreate_mass_users_are_available_in_get_users(
    api_context,
    api_version_params,
):
    payload = create_mass_payload(2, prefix="mass-get-users")
    created_users = []
    deleted_emails = set()

    try:
        response = api_context.post(
            "/api/integrations/precreatemass",
            params=api_version_params,
            data=payload,
        )
        assert response.ok, response.text()

        created_users = response.json()
        user_ids = [item["id"] for item in created_users]
        users = get_users_by_ids(api_context, api_version_params, user_ids)

        assert len(users) == 2
        assert {user["id"] for user in users} == set(user_ids)
    finally:
        cleanup_created_mass_users(
            api_context,
            api_version_params,
            created_users,
            deleted_emails,
        )


# Проверяем, что пользователи из mass ищутся через search и потом удаляются
@pytest.mark.extended
@pytest.mark.mass_extended
def test_precreate_mass_users_are_available_in_search(
    api_context,
    api_version_params,
):
    payload = create_mass_payload(2, prefix="mass-search")
    created_users = []
    deleted_emails = set()

    try:
        response = api_context.post(
            "/api/integrations/precreatemass",
            params=api_version_params,
            data=payload,
        )
        assert response.ok, response.text()

        created_users = response.json()
        for created_user in created_users:
            search_response = api_context.get(
                "/api/integrations/search",
                params={
                    **api_version_params,
                    "email": created_user["email"],
                },
            )
            assert search_response.ok, search_response.text()
            assert search_response.json()["userIdByEmail"] == created_user["id"]
    finally:
        cleanup_created_mass_users(
            api_context,
            api_version_params,
            created_users,
            deleted_emails,
        )


# Проверяем массовое создание с пустым массивом
@pytest.mark.extended
@pytest.mark.mass_extended
def test_precreate_mass_with_empty_array(api_context, api_version_params):
    response = api_context.post(
        "/api/integrations/precreatemass",
        params=api_version_params,
        data=[],
    )

    assert_no_internal_error(response)
    assert response.status in [200, 400], response.text()


# Проверяем массовое создание с одним элементом и безопасным cleanup
@pytest.mark.extended
@pytest.mark.mass_extended
def test_precreate_mass_with_one_user(api_context, api_version_params):
    payload = create_mass_payload(1, prefix="mass-one")
    created_users = []
    deleted_emails = set()

    try:
        response = api_context.post(
            "/api/integrations/precreatemass",
            params=api_version_params,
            data=payload,
        )

        assert response.ok, response.text()
        created_users = response.json()
        assert len(created_users) == 1
    finally:
        cleanup_created_mass_users(
            api_context,
            api_version_params,
            created_users,
            deleted_emails,
        )


# Проверяем массовое создание с дублями email внутри запроса
@pytest.mark.extended
@pytest.mark.mass_extended
def test_precreate_mass_with_duplicate_emails(api_context, api_version_params):
    email = unique_cleanup_email("mass-duplicate")
    payload = [
        {
            "email": email,
            "password": "TestPassword123!",
        },
        {
            "email": email,
            "password": "TestPassword123!",
        },
    ]
    deleted_emails = set()

    response = api_context.post(
        "/api/integrations/precreatemass",
        params=api_version_params,
        data=payload,
    )

    assert_no_internal_error(response)
    assert response.status in [200, 400], response.text()

    if response.ok:
        cleanup_created_mass_users(
            api_context,
            api_version_params,
            response.json(),
            deleted_emails,
        )


# Проверяем массовое создание с одним валидным и одним невалидным email
@pytest.mark.extended
@pytest.mark.mass_extended
def test_precreate_mass_with_valid_and_invalid_email(
    api_context,
    api_version_params,
):
    payload = [
        {
            "email": unique_cleanup_email("mass-valid"),
            "password": "TestPassword123!",
        },
        {
            "email": "wrong-email",
            "password": "TestPassword123!",
        },
    ]

    response = api_context.post(
        "/api/integrations/precreatemass",
        params=api_version_params,
        data=payload,
    )

    assert_no_internal_error(response)
    assert response.status == 400, response.text()


# Проверяем silent mass создание нескольких пользователей с безопасным cleanup
@pytest.mark.extended
@pytest.mark.mass_extended
def test_precreate_mass_silent_with_valid_users(api_context, api_version_params):
    payload = create_mass_payload(2, prefix="mass-silent")
    created_users = []
    deleted_emails = set()

    try:
        response = api_context.post(
            "/api/integrations/precreatemass/silent",
            params=api_version_params,
            data=payload,
        )

        assert response.ok, response.text()

        created_users = response.json()
        assert len(created_users) == 2
        assert all(item["userId"] for item in created_users)
        assert all("url" in item for item in created_users)
    finally:
        cleanup_created_mass_users(
            api_context,
            api_version_params,
            created_users,
            deleted_emails,
        )


# Проверяем повторный silent mass на те же email
@pytest.mark.extended
@pytest.mark.mass_extended
def test_precreate_mass_silent_same_emails_twice(api_context, api_version_params):
    payload = create_mass_payload(2, prefix="mass-silent-repeat")
    deleted_emails = set()

    first_response = api_context.post(
        "/api/integrations/precreatemass/silent",
        params=api_version_params,
        data=payload,
    )
    second_response = api_context.post(
        "/api/integrations/precreatemass/silent",
        params=api_version_params,
        data=payload,
    )

    assert first_response.ok, first_response.text()
    assert_no_internal_error(second_response)
    assert second_response.status in [200, 400], second_response.text()

    cleanup_created_mass_users(
        api_context,
        api_version_params,
        first_response.json(),
        deleted_emails,
    )
    if second_response.ok:
        cleanup_created_mass_users(
            api_context,
            api_version_params,
            second_response.json(),
            deleted_emails,
        )


# Проверяем silent mass с пустым массивом
@pytest.mark.extended
@pytest.mark.mass_extended
def test_precreate_mass_silent_with_empty_array(api_context, api_version_params):
    response = api_context.post(
        "/api/integrations/precreatemass/silent",
        params=api_version_params,
        data=[],
    )

    assert_no_internal_error(response)
    assert response.status in [200, 400], response.text()


# Проверяем silent mass с дублями email
@pytest.mark.extended
@pytest.mark.mass_extended
def test_precreate_mass_silent_with_duplicate_emails(
    api_context,
    api_version_params,
):
    email = unique_cleanup_email("mass-silent-duplicate")
    payload = [
        {
            "email": email,
            "password": "TestPassword123!",
        },
        {
            "email": email,
            "password": "TestPassword123!",
        },
    ]
    deleted_emails = set()

    response = api_context.post(
        "/api/integrations/precreatemass/silent",
        params=api_version_params,
        data=payload,
    )

    assert_no_internal_error(response)
    assert response.status in [200, 400], response.text()

    if response.ok:
        cleanup_created_mass_users(
            api_context,
            api_version_params,
            response.json(),
            deleted_emails,
        )


# Проверяем silent mass с одним валидным и одним невалидным email
@pytest.mark.extended
@pytest.mark.mass_extended
def test_precreate_mass_silent_with_valid_and_invalid_email(
    api_context,
    api_version_params,
):
    payload = [
        {
            "email": unique_cleanup_email("mass-silent-valid"),
            "password": "TestPassword123!",
        },
        {
            "email": "wrong-email",
            "password": "TestPassword123!",
        },
    ]

    response = api_context.post(
        "/api/integrations/precreatemass/silent",
        params=api_version_params,
        data=payload,
    )

    assert_no_internal_error(response)
    assert response.status == 400, response.text()
