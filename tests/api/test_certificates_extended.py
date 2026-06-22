import time
from uuid import uuid4

import pytest

from tests.api.assertions import assert_no_internal_error, assert_uuid


def get_user_id_by_skid(api_context, api_version_params, skid):
    response = api_context.get(
        "/api/integrations/search",
        params={
            **api_version_params,
            "skid": skid,
        },
    )

    assert response.ok, response.text()
    return response.json().get("userIdBySkid")


def wait_user_id_by_skid(api_context, api_version_params, skid, expected_user_id):
    deadline = time.time() + 5
    actual_user_id = None

    while time.time() < deadline:
        actual_user_id = get_user_id_by_skid(api_context, api_version_params, skid)
        if actual_user_id == expected_user_id:
            return actual_user_id

        time.sleep(0.5)

    assert actual_user_id == expected_user_id
    return actual_user_id


def build_mutable_ip_certificate_payload(settings):
    required_fields = [
        "mutable_ip_cert_skid",
        "mutable_ip_cert_common_name",
        "mutable_ip_cert_name",
        "mutable_ip_cert_surname",
        "mutable_ip_cert_patronymic",
        "mutable_ip_cert_inn",
        "mutable_ip_cert_ogrn",
        "mutable_ip_cert_snils",
        "mutable_ip_cert_thumbprint",
        "mutable_ip_cert_not_before",
        "mutable_ip_cert_not_after",
        "mutable_ip_cert_organization",
        "mutable_ip_cert_authority",
    ]
    missing_fields = [field for field in required_fields if not settings[field]]
    if missing_fields:
        pytest.skip(
            "Set mutable IP certificate env variables: "
            + ", ".join(missing_fields)
        )

    return {
        "skid": settings["mutable_ip_cert_skid"],
        "commonName": settings["mutable_ip_cert_common_name"],
        "notBefore": settings["mutable_ip_cert_not_before"],
        "notAfter": settings["mutable_ip_cert_not_after"],
        "name": settings["mutable_ip_cert_name"],
        "surname": settings["mutable_ip_cert_surname"],
        "patronymic": settings["mutable_ip_cert_patronymic"],
        "organization": settings["mutable_ip_cert_organization"],
        "inn": settings["mutable_ip_cert_inn"],
        "ogrn": settings["mutable_ip_cert_ogrn"],
        "snils": settings["mutable_ip_cert_snils"],
        "authority": settings["mutable_ip_cert_authority"],
        "thumbprint": settings["mutable_ip_cert_thumbprint"],
    }


def post_certificate(api_context, api_version_params, user_id, payload):
    return api_context.post(
        f"/api/integrations/certificate/{user_id}",
        params=api_version_params,
        data=payload,
    )


def bind_mutable_ip_certificate(
    api_context,
    api_version_params,
    settings,
    user_id,
):
    response = post_certificate(
        api_context,
        api_version_params,
        user_id,
        build_mutable_ip_certificate_payload(settings),
    )

    assert response.ok, response.text()
    certificate_id = response.json()
    assert_uuid(certificate_id)
    return certificate_id


def reattach_certificate(api_context, api_version_params, skid, user_id):
    response = api_context.post(
        f"/api/integrations/certificate/reattach/{skid}/{user_id}",
        params=api_version_params,
    )

    assert response.ok, response.text()


def ensure_mutable_certificate_attached_to_user(
    api_context,
    api_version_params,
    settings,
    user_id,
):
    skid = settings["mutable_ip_cert_skid"]
    if not skid:
        pytest.skip("Set MUTABLE_IP_CERT_SKID to run mutable IP certificate tests")

    current_user_id = get_user_id_by_skid(api_context, api_version_params, skid)
    if current_user_id == user_id:
        return current_user_id

    if current_user_id:
        reattach_certificate(api_context, api_version_params, skid, user_id)
    else:
        bind_mutable_ip_certificate(api_context, api_version_params, settings, user_id)

    return wait_user_id_by_skid(api_context, api_version_params, skid, user_id)


# Проверяем, что стабильный ИП-сертификат Жуковой находится по skid и привязан к seed-пользователю
@pytest.mark.extended
@pytest.mark.certificates_extended
def test_stable_ip_certificate_is_found_by_skid(
    api_context,
    api_version_params,
    seed_ip_user,
):
    user_id = get_user_id_by_skid(
        api_context,
        api_version_params,
        seed_ip_user["seed_ip_cert_skid"],
    )

    assert user_id == seed_ip_user["seed_ip_user_id"]


# Проверяем, что поиск по стабильному skid и email Жуковой возвращает одного seed-пользователя
@pytest.mark.extended
@pytest.mark.certificates_extended
def test_stable_ip_certificate_search_with_email_returns_same_user(
    api_context,
    api_version_params,
    seed_ip_user,
):
    response = api_context.get(
        "/api/integrations/search",
        params={
            **api_version_params,
            "skid": seed_ip_user["seed_ip_cert_skid"],
            "email": seed_ip_user["email"],
        },
    )

    assert response.ok, response.text()
    result = response.json()
    assert result["userIdBySkid"] == seed_ip_user["seed_ip_user_id"]
    assert result["userIdByEmail"] == seed_ip_user["seed_ip_user_id"]


# Проверяем, что поиск по стабильному skid и телефону Жуковой возвращает одного seed-пользователя
@pytest.mark.extended
@pytest.mark.certificates_extended
def test_stable_ip_certificate_search_with_phone_returns_same_user(
    api_context,
    api_version_params,
    seed_ip_user,
):
    response = api_context.get(
        "/api/integrations/search",
        params={
            **api_version_params,
            "skid": seed_ip_user["seed_ip_cert_skid"],
            "phone": seed_ip_user["phone"].lstrip("+"),
        },
    )

    assert response.ok, response.text()
    result = response.json()
    assert result["userIdBySkid"] == seed_ip_user["seed_ip_user_id"]
    assert result["userIdByPhone"] == seed_ip_user["seed_ip_user_id"]


# Проверяем, что seed-организация ИП Жуковой доступна по сохраненному organizationId
@pytest.mark.extended
@pytest.mark.certificates_extended
def test_stable_ip_certificate_seed_organization_exists(
    api_context,
    api_version_params,
    seed_ip_user,
):
    response = api_context.get(
        "/api/integrations/organizations",
        params={
            **api_version_params,
            "ids": seed_ip_user["seed_ip_org_id"],
        },
    )

    assert response.ok, response.text()
    organizations = response.json()
    assert len(organizations) == 1
    organization = organizations[0]
    assert organization["id"] == seed_ip_user["seed_ip_org_id"]
    assert organization["inn"]
    assert "Жукова" in organization["name"]


# Проверяем, что seed-организация ИП Жуковой содержит ожидаемые данные сертификата
@pytest.mark.extended
@pytest.mark.certificates_extended
def test_stable_ip_certificate_seed_organization_has_expected_data(
    api_context,
    api_version_params,
    seed_ip_user,
):
    response = api_context.get(
        "/api/integrations/organizations",
        params={
            **api_version_params,
            "ids": seed_ip_user["seed_ip_org_id"],
        },
    )

    assert response.ok, response.text()
    organization = response.json()[0]
    assert organization["inn"] == "966731644734"
    assert organization["ogrn"] == "311605180545133"
    assert organization["status"] == "Confirmed"


# Проверяем, что mutable ИП-сертификат Петровой можно привязать к seed-пользователю без создания организации
@pytest.mark.extended
@pytest.mark.certificates_extended
def test_mutable_ip_certificate_can_be_bound_to_seed_user(
    api_context,
    api_version_params,
    settings,
    seed_owner_2,
):
    user_id = ensure_mutable_certificate_attached_to_user(
        api_context,
        api_version_params,
        settings,
        seed_owner_2["seed_owner_2_user_id"],
    )

    assert user_id == seed_owner_2["seed_owner_2_user_id"]


# Проверяем, что повторная привязка mutable ИП-сертификата к тому же пользователю не дает 500
@pytest.mark.extended
@pytest.mark.certificates_extended
def test_mutable_ip_certificate_can_be_bound_to_same_user_twice(
    api_context,
    api_version_params,
    settings,
    seed_owner_2,
):
    ensure_mutable_certificate_attached_to_user(
        api_context,
        api_version_params,
        settings,
        seed_owner_2["seed_owner_2_user_id"],
    )

    response = post_certificate(
        api_context,
        api_version_params,
        seed_owner_2["seed_owner_2_user_id"],
        build_mutable_ip_certificate_payload(settings),
    )

    assert_no_internal_error(response)
    assert response.status in [200, 400], response.text()
    user_id = get_user_id_by_skid(
        api_context,
        api_version_params,
        settings["mutable_ip_cert_skid"],
    )
    assert user_id == seed_owner_2["seed_owner_2_user_id"]


# Проверяем, что mutable ИП-сертификат Петровой можно перепривязать к другому seed-пользователю
@pytest.mark.extended
@pytest.mark.certificates_extended
def test_mutable_ip_certificate_can_be_reattached_to_another_seed_user(
    api_context,
    api_version_params,
    settings,
    seed_employee_1,
):
    ensure_mutable_certificate_attached_to_user(
        api_context,
        api_version_params,
        settings,
        seed_employee_1["seed_employee_1_user_id"],
    )

    user_id = wait_user_id_by_skid(
        api_context,
        api_version_params,
        settings["mutable_ip_cert_skid"],
        seed_employee_1["seed_employee_1_user_id"],
    )

    assert user_id == seed_employee_1["seed_employee_1_user_id"]


# Проверяем, что mutable ИП-сертификат Петровой можно перепривязать обратно к исходному seed-пользователю
@pytest.mark.extended
@pytest.mark.certificates_extended
def test_mutable_ip_certificate_can_be_reattached_back_to_owner(
    api_context,
    api_version_params,
    settings,
    seed_owner_2,
    seed_employee_1,
):
    ensure_mutable_certificate_attached_to_user(
        api_context,
        api_version_params,
        settings,
        seed_employee_1["seed_employee_1_user_id"],
    )

    reattach_certificate(
        api_context,
        api_version_params,
        settings["mutable_ip_cert_skid"],
        seed_owner_2["seed_owner_2_user_id"],
    )
    user_id = wait_user_id_by_skid(
        api_context,
        api_version_params,
        settings["mutable_ip_cert_skid"],
        seed_owner_2["seed_owner_2_user_id"],
    )

    assert user_id == seed_owner_2["seed_owner_2_user_id"]


# Проверяем, что перепривязка неизвестного skid не уходит в 500
@pytest.mark.extended
@pytest.mark.certificates_extended
def test_reattach_unknown_certificate_skid_returns_client_error(
    api_context,
    api_version_params,
    seed_owner_2,
):
    unknown_skid = uuid4().hex
    response = api_context.post(
        f"/api/integrations/certificate/reattach/{unknown_skid}/"
        f"{seed_owner_2['seed_owner_2_user_id']}",
        params=api_version_params,
    )

    assert_no_internal_error(response)
    assert response.status in [400, 404], response.text()


# Проверяем, что перепривязка сертификата к неизвестному пользователю не уходит в 500
@pytest.mark.extended
@pytest.mark.certificates_extended
def test_reattach_certificate_to_unknown_user_returns_client_error(
    api_context,
    api_version_params,
    settings,
    seed_owner_2,
):
    ensure_mutable_certificate_attached_to_user(
        api_context,
        api_version_params,
        settings,
        seed_owner_2["seed_owner_2_user_id"],
    )
    unknown_user_id = str(uuid4())
    response = api_context.post(
        f"/api/integrations/certificate/reattach/"
        f"{settings['mutable_ip_cert_skid']}/{unknown_user_id}",
        params=api_version_params,
    )

    assert_no_internal_error(response)
    assert response.status in [400, 404], response.text()


# Проверяем, что привязка сертификата к неизвестному пользователю не уходит в 500
@pytest.mark.extended
@pytest.mark.certificates_extended
def test_bind_certificate_to_unknown_user_returns_client_error(
    api_context,
    api_version_params,
    settings,
):
    unknown_user_id = str(uuid4())
    response = post_certificate(
        api_context,
        api_version_params,
        unknown_user_id,
        build_mutable_ip_certificate_payload(settings),
    )

    assert_no_internal_error(response)
    assert response.status in [400, 404], response.text()


# Проверяем, что привязка сертификата с пустым skid не уходит в 500
@pytest.mark.extended
@pytest.mark.certificates_extended
def test_bind_certificate_with_empty_skid_returns_client_error(
    api_context,
    api_version_params,
    settings,
    seed_owner_2,
):
    payload = build_mutable_ip_certificate_payload(settings)
    payload["skid"] = ""

    response = post_certificate(
        api_context,
        api_version_params,
        seed_owner_2["seed_owner_2_user_id"],
        payload,
    )

    assert_no_internal_error(response)
    assert response.status == 400, response.text()


# Проверяем, что привязка сертификата с пустым body не уходит в 500
@pytest.mark.extended
@pytest.mark.certificates_extended
def test_bind_certificate_with_empty_body_returns_client_error(
    api_context,
    api_version_params,
    seed_owner_2,
):
    response = post_certificate(
        api_context,
        api_version_params,
        seed_owner_2["seed_owner_2_user_id"],
        {},
    )

    assert_no_internal_error(response)
    assert response.status == 400, response.text()


# Пропускаем ЮЛ-сертификаты: seed-данные и безопасный flow для ЮЛ будут добавлены позже
@pytest.mark.extended
@pytest.mark.certificates_extended
def test_ul_certificate_scenarios_are_not_prepared_yet():
    pytest.skip("UL certificate scenarios are postponed until stable UL seed data is ready")
