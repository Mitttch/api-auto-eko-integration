import pytest

from tests.api.assertions import assert_no_internal_error, assert_user_deleted, assert_uuid
from tests.api.cleanup import delete_created_accounts
from tests.api.factories import unique_cleanup_email, unique_phone
from tests.api.helpers import (
    add_user_email,
    get_user_by_id,
    get_users_by_ids,
)


def create_phone_mass_payload(count):
    return [
        {
            "phoneNumber": unique_phone(),
            "password": "TestPassword123!",
        }
        for _ in range(count)
    ]


def assert_user_available_by_phone(api_context, api_version_params, user_id, phone):
    search_response = api_context.get(
        "/api/integrations/search",
        params={
            **api_version_params,
            "phone": phone,
        },
    )
    assert search_response.ok, search_response.text()
    assert search_response.json()["userIdByPhone"] == user_id

    user = get_user_by_id(api_context, api_version_params, user_id)
    assert user["phone"] == phone


def cleanup_phone_users_by_email(
    api_context,
    api_version_params,
    users,
):
    deleted_emails = set()
    created_cleanup_emails = []

    try:
        for user in users:
            email = add_user_email(
                api_context,
                api_version_params,
                user["user_id"],
                unique_cleanup_email("phone"),
            )
            created_cleanup_emails.append(
                {
                    "user_id": user["user_id"],
                    "email": email,
                }
            )

        delete_created_accounts(
            api_context,
            api_version_params,
            [item["email"] for item in created_cleanup_emails],
            deleted_emails,
        )

        for item in created_cleanup_emails:
            assert_user_deleted(
                api_context,
                api_version_params,
                item["user_id"],
                item["email"],
            )
    finally:
        delete_created_accounts(
            api_context,
            api_version_params,
            [item["email"] for item in created_cleanup_emails],
            deleted_emails,
        )


# Проверяем precreate/byphone с валидным уникальным телефоном
@pytest.mark.extended
@pytest.mark.phone_mass_extended
def test_precreate_byphone_returns_user_id(api_context, api_version_params):
    phone = unique_phone()

    response = api_context.post(
        "/api/integrations/precreate/byphone",
        params=api_version_params,
        data={
            "phoneNumber": phone,
            "password": "TestPassword123!",
        },
    )

    assert response.ok, response.text()
    user_id = response.json()
    assert_uuid(user_id)
    try:
        assert_user_available_by_phone(api_context, api_version_params, user_id, phone)
    finally:
        cleanup_phone_users_by_email(
            api_context,
            api_version_params,
            [{"user_id": user_id}],
        )


# Проверяем добавление email пользователю, созданному по телефону
@pytest.mark.extended
@pytest.mark.phone_mass_extended
def test_add_email_to_user_created_by_phone(api_context, api_version_params):
    phone = unique_phone()
    deleted_emails = set()
    create_response = api_context.post(
        "/api/integrations/precreate/byphone",
        params=api_version_params,
        data={
            "phoneNumber": phone,
            "password": "TestPassword123!",
        },
    )
    assert create_response.ok, create_response.text()
    user_id = create_response.json()
    email = add_user_email(
        api_context,
        api_version_params,
        user_id,
        unique_cleanup_email("phone"),
    )

    try:
        search_response = api_context.get(
            "/api/integrations/search",
            params={
                **api_version_params,
                "email": email,
            },
        )

        assert search_response.ok, search_response.text()
        assert search_response.json()["userIdByEmail"] == user_id
    finally:
        delete_created_accounts(
            api_context,
            api_version_params,
            [email],
            deleted_emails,
        )
        assert_user_deleted(api_context, api_version_params, user_id, email)


# Проверяем массовое создание пользователей по телефону
@pytest.mark.extended
@pytest.mark.phone_mass_extended
def test_precreate_mass_byphone_with_valid_phones(api_context, api_version_params):
    payload = create_phone_mass_payload(3)

    response = api_context.post(
        "/api/integrations/precreatemass/byphone",
        params=api_version_params,
        data=payload,
    )

    created_users = []
    try:
        assert response.ok, response.text()
        created_users = response.json()
        assert len(created_users) == 3

        for created_user in created_users:
            assert_uuid(created_user["id"])
            assert created_user["phoneNumber"]
            assert_user_available_by_phone(
                api_context,
                api_version_params,
                created_user["id"],
                created_user["phoneNumber"],
            )
    finally:
        cleanup_phone_users_by_email(
            api_context,
            api_version_params,
            [{"user_id": item["id"]} for item in created_users],
        )


# Проверяем массовое создание по телефону с одним элементом
@pytest.mark.extended
@pytest.mark.phone_mass_extended
def test_precreate_mass_byphone_with_one_phone(api_context, api_version_params):
    response = api_context.post(
        "/api/integrations/precreatemass/byphone",
        params=api_version_params,
        data=create_phone_mass_payload(1),
    )
    created_users = []

    try:
        assert response.ok, response.text()
        created_users = response.json()
        assert len(created_users) == 1
        assert_uuid(created_users[0]["id"])
    finally:
        cleanup_phone_users_by_email(
            api_context,
            api_version_params,
            [{"user_id": item["id"]} for item in created_users],
        )


# Проверяем массовое создание по телефону с пустым массивом
@pytest.mark.extended
@pytest.mark.phone_mass_extended
def test_precreate_mass_byphone_with_empty_array(api_context, api_version_params):
    response = api_context.post(
        "/api/integrations/precreatemass/byphone",
        params=api_version_params,
        data=[],
    )

    assert_no_internal_error(response)
    assert response.status in [200, 400], response.text()


# Проверяем массовое создание по телефону с дублями
@pytest.mark.extended
@pytest.mark.phone_mass_extended
def test_precreate_mass_byphone_with_duplicate_phones(api_context, api_version_params):
    phone = unique_phone()
    payload = [
        {
            "phoneNumber": phone,
            "password": "TestPassword123!",
        },
        {
            "phoneNumber": phone,
            "password": "TestPassword123!",
        },
    ]

    response = api_context.post(
        "/api/integrations/precreatemass/byphone",
        params=api_version_params,
        data=payload,
    )

    assert_no_internal_error(response)
    assert response.status in [200, 400], response.text()


# Проверяем массовое создание по телефону с valid + invalid phone
@pytest.mark.extended
@pytest.mark.phone_mass_extended
def test_precreate_mass_byphone_with_valid_and_invalid_phone(
    api_context,
    api_version_params,
):
    payload = [
        {
            "phoneNumber": unique_phone(),
            "password": "TestPassword123!",
        },
        {
            "phoneNumber": "wrong-phone",
            "password": "TestPassword123!",
        },
    ]

    response = api_context.post(
        "/api/integrations/precreatemass/byphone",
        params=api_version_params,
        data=payload,
    )

    assert_no_internal_error(response)
    assert response.status == 400, response.text()


# Проверяем невалидные форматы телефона для precreate/byphone
@pytest.mark.extended
@pytest.mark.phone_mass_extended
@pytest.mark.parametrize("phone", ["12345", "+1234567890", "phone-number"])
def test_precreate_byphone_invalid_formats(api_context, api_version_params, phone):
    response = api_context.post(
        "/api/integrations/precreate/byphone",
        params=api_version_params,
        data={
            "phoneNumber": phone,
            "password": "TestPassword123!",
        },
    )

    assert_no_internal_error(response)
    assert response.status == 400, response.text()


# Проверяем, что mass by phone пользователей можно получить одним GET users
@pytest.mark.extended
@pytest.mark.phone_mass_extended
def test_precreate_mass_byphone_users_are_available_in_get_users(
    api_context,
    api_version_params,
):
    response = api_context.post(
        "/api/integrations/precreatemass/byphone",
        params=api_version_params,
        data=create_phone_mass_payload(2),
    )
    created_users = []

    try:
        assert response.ok, response.text()

        created_users = response.json()
        user_ids = [item["id"] for item in created_users]
        users = get_users_by_ids(api_context, api_version_params, user_ids)

        assert {user["id"] for user in users} == set(user_ids)
    finally:
        cleanup_phone_users_by_email(
            api_context,
            api_version_params,
            [{"user_id": item["id"]} for item in created_users],
        )


# Проверяем resend для пользователя, созданного по телефону
@pytest.mark.extended
@pytest.mark.phone_mass_extended
def test_resend_for_user_created_by_phone(api_context, api_version_params):
    phone = unique_phone()
    create_response = api_context.post(
        "/api/integrations/precreate/byphone",
        params=api_version_params,
        data={
            "phoneNumber": phone,
            "password": "TestPassword123!",
        },
    )
    assert create_response.ok, create_response.text()

    user_id = create_response.json()

    try:
        response = api_context.post(
            f"/api/integrations/resend/{user_id}",
            params=api_version_params,
        )

        assert_no_internal_error(response)
        assert response.status in [200, 400], response.text()
    finally:
        cleanup_phone_users_by_email(
            api_context,
            api_version_params,
            [{"user_id": user_id}],
        )


# Проверяем несколько resend подряд без проверки доставки кода
@pytest.mark.extended
@pytest.mark.phone_mass_extended
def test_multiple_resend_calls_do_not_return_500(api_context, api_version_params):
    phone = unique_phone()
    create_response = api_context.post(
        "/api/integrations/precreate/byphone",
        params=api_version_params,
        data={
            "phoneNumber": phone,
            "password": "TestPassword123!",
        },
    )
    assert create_response.ok, create_response.text()
    user_id = create_response.json()

    try:
        first_response = api_context.post(
            f"/api/integrations/resend/{user_id}",
            params=api_version_params,
        )
        second_response = api_context.post(
            f"/api/integrations/resend/{user_id}",
            params=api_version_params,
        )

        assert_no_internal_error(first_response)
        assert_no_internal_error(second_response)
        assert first_response.status in [200, 400], first_response.text()
        assert second_response.status in [200, 400], second_response.text()
    finally:
        cleanup_phone_users_by_email(
            api_context,
            api_version_params,
            [{"user_id": user_id}],
        )
