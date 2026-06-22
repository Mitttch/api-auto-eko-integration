import pytest

from tests.api.assertions import assert_no_internal_error
from tests.api.factories import AUTOTEST_RU_PREFIX, build_email
from tests.api.helpers import create_user_by_email


# Проверяем SQL-like значение в search email
@pytest.mark.extended
@pytest.mark.security_extended
def test_search_with_sql_like_email(api_context, api_version_params):
    response = api_context.get(
        "/api/integrations/search",
        params={
            **api_version_params,
            "email": "' OR 1=1 --",
        },
    )

    assert_no_internal_error(response)
    assert response.status in [200, 400], response.text()


# Проверяем очень длинный query param в search
@pytest.mark.extended
@pytest.mark.security_extended
def test_search_with_very_long_email(api_context, api_version_params):
    response = api_context.get(
        "/api/integrations/search",
        params={
            **api_version_params,
            "email": build_email("a" * 500),
        },
    )

    assert_no_internal_error(response)
    assert response.status in [200, 400], response.text()


# Проверяем script-like строки в ФИО
@pytest.mark.extended
@pytest.mark.security_extended
def test_update_fio_with_script_like_values(api_context, api_version_params):
    user_id, _ = create_user_by_email(api_context, api_version_params)

    response = api_context.post(
        "/api/integrations/users/fio",
        params=api_version_params,
        data={
            "userId": user_id,
            "surname": "<script>alert(1)</script>",
            "name": "<b>test</b>",
            "patronymic": f"{AUTOTEST_RU_PREFIX}ович",
        },
    )

    assert_no_internal_error(response)
    assert response.status in [200, 400], response.text()


# Проверяем пустой JSON body для precreate
@pytest.mark.extended
@pytest.mark.security_extended
@pytest.mark.xfail(
    reason=(
        "Known API bug: empty precreate body returns 500 "
        "ArgumentNullException instead of 400"
    ),
    strict=True,
)
def test_precreate_with_empty_json_body(api_context, api_version_params):
    response = api_context.post(
        "/api/integrations/precreate",
        params=api_version_params,
        data={},
    )

    assert_no_internal_error(response)
    assert response.status == 400, response.text()


# Проверяем body с лишними полями для precreate
@pytest.mark.extended
@pytest.mark.security_extended
def test_precreate_with_extra_fields(api_context, api_version_params):
    response = api_context.post(
        "/api/integrations/precreate",
        params=api_version_params,
        data={
            "email": "wrong-email",
            "password": "TestPassword123!",
            "unexpectedField": "unexpected value",
        },
    )

    assert_no_internal_error(response)
    assert response.status == 400, response.text()


# Проверяем GET вместо POST для precreate
@pytest.mark.extended
@pytest.mark.security_extended
def test_get_method_for_post_endpoint(api_context, api_version_params):
    response = api_context.get(
        "/api/integrations/precreate",
        params=api_version_params,
    )

    assert_no_internal_error(response)
    assert response.status in [404, 405], response.text()
