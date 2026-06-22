from uuid import uuid4
from urllib.parse import urlencode

import pytest

from tests.api.assertions import assert_no_internal_error, assert_uuid
from tests.api.factories import (
    AUTOTEST_EMAIL_PREFIX,
    AUTOTEST_RU_PREFIX,
    build_email,
    unique_email,
    unique_phone,
)
from tests.api.helpers import (
    create_user_by_email,
    create_user_by_phone,
)


# Проверяем, что повторное precreate на тот же email не создает дубль пользователя
@pytest.mark.extended
@pytest.mark.users_extended
def test_precreate_same_email_returns_same_user_id(api_context, api_version_params):
    email = unique_email()
    first_user_id, _ = create_user_by_email(api_context, api_version_params, email)
    second_user_id, _ = create_user_by_email(api_context, api_version_params, email)

    assert second_user_id == first_user_id


# Проверяем, как API обрабатывает один email в разном регистре
@pytest.mark.extended
@pytest.mark.users_extended
def test_precreate_email_with_different_case(api_context, api_version_params):
    email = unique_email()
    upper_email = email.upper()

    first_user_id, _ = create_user_by_email(api_context, api_version_params, email)
    response = api_context.post(
        "/api/integrations/precreate",
        params=api_version_params,
        data={
            "email": upper_email,
            "password": "TestPassword123!",
        },
    )

    assert_no_internal_error(response)
    assert response.ok, response.text()
    assert response.json() == first_user_id


# Проверяем, что email с пробелами не принимается как валидный
@pytest.mark.extended
@pytest.mark.users_extended
def test_precreate_email_with_spaces(api_context, api_version_params):
    email = f" {unique_email()} "

    response = api_context.post(
        "/api/integrations/precreate",
        params=api_version_params,
        data={
            "email": email,
            "password": "TestPassword123!",
        },
    )

    assert_no_internal_error(response)
    assert response.status == 400, response.text()


# Проверяем, что email с допустимым спецсимволом плюс принимается
@pytest.mark.extended
@pytest.mark.users_extended
def test_precreate_email_with_plus_symbol(api_context, api_version_params):
    email = build_email(f"{AUTOTEST_EMAIL_PREFIX}+{uuid4().hex[:12]}")

    user_id, created_email = create_user_by_email(
        api_context,
        api_version_params,
        email,
    )

    assert_uuid(user_id)
    assert created_email == email


# Проверяем, что пользователей можно получить одним запросом по нескольким ids
@pytest.mark.extended
@pytest.mark.users_extended
def test_get_users_with_multiple_ids(api_context, api_version_params):
    first_user_id, _ = create_user_by_email(api_context, api_version_params)
    second_user_id, _ = create_user_by_email(api_context, api_version_params)

    response = api_context.get(
        "/api/integrations/users",
        params={
            **api_version_params,
            "ids": f"{first_user_id},{second_user_id}",
        },
    )

    assert response.ok, response.text()

    user_ids = [user["id"] for user in response.json()]
    assert first_user_id in user_ids
    assert second_user_id in user_ids


# Проверяем, что запрос valid + unknown id возвращает найденного пользователя без 500
@pytest.mark.extended
@pytest.mark.users_extended
def test_get_users_with_valid_and_unknown_id(api_context, api_version_params):
    user_id, _ = create_user_by_email(api_context, api_version_params)
    unknown_user_id = str(uuid4())

    response = api_context.get(
        "/api/integrations/users",
        params={
            **api_version_params,
            "ids": f"{user_id},{unknown_user_id}",
        },
    )

    assert_no_internal_error(response)
    assert response.ok, response.text()

    user_ids = [user["id"] for user in response.json()]
    assert user_id in user_ids
    assert unknown_user_id not in user_ids


# Проверяем, что дубли ids в GET users не приводят к дублям в ответе
@pytest.mark.extended
@pytest.mark.users_extended
def test_get_users_with_duplicate_ids(api_context, api_version_params):
    user_id, _ = create_user_by_email(api_context, api_version_params)

    response = api_context.get(
        "/api/integrations/users",
        params={
            **api_version_params,
            "ids": f"{user_id},{user_id}",
        },
    )

    assert_no_internal_error(response)
    assert response.ok, response.text()

    user_ids = [user["id"] for user in response.json()]
    assert user_ids.count(user_id) == 1


# Проверяем, что пустой ids в GET users не приводит к 500
@pytest.mark.extended
@pytest.mark.users_extended
def test_get_users_with_empty_ids(api_context, api_version_params):
    response = api_context.get(
        "/api/integrations/users",
        params={
            **api_version_params,
            "ids": "",
        },
    )

    assert_no_internal_error(response)
    assert response.status == 400, response.text()


# Проверяем, что GET users без ids не приводит к 500
@pytest.mark.extended
@pytest.mark.users_extended
def test_get_users_without_ids(api_context, api_version_params):
    response = api_context.get(
        "/api/integrations/users",
        params=api_version_params,
    )

    assert_no_internal_error(response)
    assert response.status == 400, response.text()


# Проверяем, что поиск по email до создания пользователя возвращает пустой результат
@pytest.mark.extended
@pytest.mark.users_extended
def test_search_unknown_email(api_context, api_version_params):
    response = api_context.get(
        "/api/integrations/search",
        params={
            **api_version_params,
            "email": unique_email("unknown"),
        },
    )

    assert response.ok, response.text()

    search_result = response.json()
    assert search_result.get("userIdByEmail") is None


# Проверяем, что поиск по email после precreate возвращает созданного пользователя
@pytest.mark.extended
@pytest.mark.users_extended
def test_search_email_after_precreate(api_context, api_version_params):
    user_id, email = create_user_by_email(api_context, api_version_params)

    response = api_context.get(
        "/api/integrations/search",
        params={
            **api_version_params,
            "email": email,
        },
    )

    assert response.ok, response.text()
    assert response.json()["userIdByEmail"] == user_id


# Проверяем, что поиск по телефону после обновления телефона возвращает пользователя
@pytest.mark.extended
@pytest.mark.users_extended
def test_search_phone_after_update(api_context, api_version_params):
    user_id, _ = create_user_by_email(api_context, api_version_params)
    phone = unique_phone()

    update_response = api_context.post(
        "/api/integrations/users/phone",
        params=api_version_params,
        data={
            "userId": user_id,
            "phone": phone,
        },
    )
    assert update_response.ok, update_response.text()

    response = api_context.get(
        "/api/integrations/search",
        params={
            **api_version_params,
            "phone": phone,
        },
    )

    assert response.ok, response.text()
    assert response.json()["userIdByPhone"] == user_id


# Проверяем, что поиск по email и phone одного пользователя возвращает один userId
@pytest.mark.extended
@pytest.mark.users_extended
def test_search_same_user_by_email_and_phone(api_context, api_version_params):
    user_id, email = create_user_by_email(api_context, api_version_params)
    phone = unique_phone()

    update_response = api_context.post(
        "/api/integrations/users/phone",
        params=api_version_params,
        data={
            "userId": user_id,
            "phone": phone,
        },
    )
    assert update_response.ok, update_response.text()

    response = api_context.get(
        "/api/integrations/search",
        params={
            **api_version_params,
            "email": email,
            "phone": phone,
        },
    )

    assert response.ok, response.text()

    search_result = response.json()
    assert search_result["userIdByEmail"] == user_id
    assert search_result["userIdByPhone"] == user_id


# Проверяем поиск с email и phone от разных пользователей
@pytest.mark.extended
@pytest.mark.users_extended
def test_search_conflicting_email_and_phone(api_context, api_version_params):
    first_user_id, first_email = create_user_by_email(
        api_context,
        api_version_params,
    )
    second_user_id, _ = create_user_by_email(api_context, api_version_params)
    second_phone = unique_phone()

    update_response = api_context.post(
        "/api/integrations/users/phone",
        params=api_version_params,
        data={
            "userId": second_user_id,
            "phone": second_phone,
        },
    )
    assert update_response.ok, update_response.text()

    response = api_context.get(
        "/api/integrations/search",
        params={
            **api_version_params,
            "email": first_email,
            "phone": second_phone,
        },
    )

    assert response.ok, response.text()

    search_result = response.json()
    assert search_result["userIdByEmail"] == first_user_id
    assert search_result["userIdByPhone"] == second_user_id


# Проверяем, что повторное обновление ФИО не приводит к ошибке
@pytest.mark.extended
@pytest.mark.users_extended
def test_update_user_fio_twice(api_context, api_version_params):
    user_id, _ = create_user_by_email(api_context, api_version_params)

    first_response = api_context.post(
        "/api/integrations/users/fio",
        params=api_version_params,
        data={
            "userId": user_id,
            "surname": f"{AUTOTEST_RU_PREFIX}ов",
            "name": AUTOTEST_RU_PREFIX,
            "patronymic": "Тестович",
        },
    )
    second_response = api_context.post(
        "/api/integrations/users/fio",
        params=api_version_params,
        data={
            "userId": user_id,
            "surname": f"{AUTOTEST_RU_PREFIX}ов2",
            "name": f"{AUTOTEST_RU_PREFIX}2",
            "patronymic": "Тестович2",
        },
    )

    assert first_response.ok, first_response.text()
    assert_no_internal_error(second_response)


# Проверяем, что повторное обновление телефона не приводит к 500
@pytest.mark.extended
@pytest.mark.users_extended
def test_update_user_phone_twice(api_context, api_version_params):
    user_id, _ = create_user_by_email(api_context, api_version_params)

    first_response = api_context.post(
        "/api/integrations/users/phone",
        params=api_version_params,
        data={
            "userId": user_id,
            "phone": unique_phone(),
        },
    )
    second_response = api_context.post(
        "/api/integrations/users/phone",
        params=api_version_params,
        data={
            "userId": user_id,
            "phone": unique_phone(),
        },
    )

    assert first_response.ok, first_response.text()
    assert_no_internal_error(second_response)
    assert second_response.status in [200, 400], second_response.text()


# Проверяем, что один телефон нельзя назначить двум разным пользователям
@pytest.mark.extended
@pytest.mark.users_extended
def test_same_phone_for_two_users(api_context, api_version_params):
    first_user_id, _ = create_user_by_email(api_context, api_version_params)
    second_user_id, _ = create_user_by_email(api_context, api_version_params)
    phone = unique_phone()

    first_response = api_context.post(
        "/api/integrations/users/phone",
        params=api_version_params,
        data={
            "userId": first_user_id,
            "phone": phone,
        },
    )
    second_response = api_context.post(
        "/api/integrations/users/phone",
        params=api_version_params,
        data={
            "userId": second_user_id,
            "phone": phone,
        },
    )

    assert first_response.ok, first_response.text()
    assert_no_internal_error(second_response)
    assert second_response.status == 400, second_response.text()


# Проверяем несколько невалидных форматов телефона
@pytest.mark.extended
@pytest.mark.users_extended
@pytest.mark.parametrize(
    "phone",
    [
        "12345",
        "+1234567890",
        "+797195296465",
        "phone-number",
    ],
)
def test_invalid_phone_formats(api_context, api_version_params, phone):
    user_id, _ = create_user_by_email(api_context, api_version_params)

    response = api_context.post(
        "/api/integrations/users/phone",
        params=api_version_params,
        data={
            "userId": user_id,
            "phone": phone,
        },
    )

    assert_no_internal_error(response)
    assert response.status == 400, response.text()


# Проверяем, что POST users/email может добавить email пользователю без email
@pytest.mark.extended
@pytest.mark.users_extended
def test_add_email_to_user_without_email(api_context, api_version_params):
    user_id, _ = create_user_by_phone(api_context, api_version_params)
    email = unique_email()

    response = api_context.post(
        "/api/integrations/users/email",
        params=api_version_params,
        data={
            "userId": user_id,
            "email": email,
        },
    )

    assert_no_internal_error(response)
    assert response.ok, response.text()


def build_users_repeated_ids_path(api_version_params, user_ids):
    query_items = []
    if api_version_params.get("api-version"):
        query_items.append(("api-version", api_version_params["api-version"]))
    for user_id in user_ids:
        query_items.append(("ids", user_id))

    return f"/api/integrations/users?{urlencode(query_items)}"


# Проверяем repeated query params format для GET users
@pytest.mark.extended
@pytest.mark.users_extended
def test_get_users_with_repeated_query_params_format(api_context, api_version_params):
    first_user_id, _ = create_user_by_email(api_context, api_version_params)
    second_user_id, _ = create_user_by_email(api_context, api_version_params)

    response = api_context.get(
        build_users_repeated_ids_path(
            api_version_params,
            [first_user_id, second_user_id],
        ),
    )

    assert response.ok, response.text()
    assert {user["id"] for user in response.json()} == {first_user_id, second_user_id}


# Проверяем, что repeated и comma-separated ids возвращают один набор пользователей
@pytest.mark.extended
@pytest.mark.users_extended
def test_get_users_repeated_and_comma_formats_return_same_users(
    api_context,
    api_version_params,
):
    user_ids = [
        create_user_by_email(api_context, api_version_params)[0],
        create_user_by_email(api_context, api_version_params)[0],
    ]

    repeated_response = api_context.get(
        build_users_repeated_ids_path(api_version_params, user_ids),
    )
    comma_response = api_context.get(
        "/api/integrations/users",
        params={
            **api_version_params,
            "ids": ",".join(user_ids),
        },
    )

    assert repeated_response.ok, repeated_response.text()
    assert comma_response.ok, comma_response.text()
    assert {user["id"] for user in repeated_response.json()} == {
        user["id"] for user in comma_response.json()
    }


# Проверяем GET users с ровно 10 ids
@pytest.mark.extended
@pytest.mark.users_extended
def test_get_users_with_exactly_ten_ids(api_context, api_version_params):
    user_ids = [
        create_user_by_email(api_context, api_version_params)[0]
        for _ in range(10)
    ]

    response = api_context.get(
        "/api/integrations/users",
        params={
            **api_version_params,
            "ids": ",".join(user_ids),
        },
    )

    assert response.ok, response.text()
    assert {user["id"] for user in response.json()} == set(user_ids)


# Проверяем GET users с 11 ids
@pytest.mark.extended
@pytest.mark.users_extended
def test_get_users_with_eleven_ids_returns_client_error(api_context, api_version_params):
    user_ids = [str(uuid4()) for _ in range(11)]

    response = api_context.get(
        "/api/integrations/users",
        params={
            **api_version_params,
            "ids": ",".join(user_ids),
        },
    )

    assert_no_internal_error(response)
    assert response.status == 400, response.text()


# Проверяем GET users с valid + invalid uuid
@pytest.mark.extended
@pytest.mark.users_extended
def test_get_users_with_valid_and_invalid_uuid(api_context, api_version_params):
    user_id, _ = create_user_by_email(api_context, api_version_params)

    response = api_context.get(
        "/api/integrations/users",
        params={
            **api_version_params,
            "ids": f"{user_id},wrong-user-id",
        },
    )

    assert_no_internal_error(response)
    assert response.ok, response.text()
    user_ids = [user["id"] for user in response.json()]
    assert user_id in user_ids
    assert "wrong-user-id" not in user_ids


# Проверяем дубли ids в repeated params format
@pytest.mark.extended
@pytest.mark.users_extended
def test_get_users_with_duplicate_repeated_ids(api_context, api_version_params):
    user_id, _ = create_user_by_email(api_context, api_version_params)

    response = api_context.get(
        build_users_repeated_ids_path(api_version_params, [user_id, user_id]),
    )

    assert_no_internal_error(response)
    assert response.ok, response.text()
    assert [user["id"] for user in response.json()].count(user_id) == 1
