import os

import pytest
from dotenv import load_dotenv
from playwright.sync_api import Playwright, sync_playwright

from tests.api.cleanup import CleanupRegistry
from tests.api.seed_support import (
    collect_seed_protection,
    get_seed_organization,
    get_seed_organizations,
    get_seed_user,
    get_seed_users,
)


def _join_url(base_url, path):
    return f"{base_url.rstrip('/')}/{path.lstrip('/')}"


def _get_base_url():
    # BASE_URL оставлен как legacy fallback для старых env-файлов.
    return os.getenv("API_BASE_URL") or os.getenv("BASE_URL") or ""


def _get_auth_base_url():
    return os.getenv("AUTH_BASE_URL") or _get_base_url()


def _get_token_url():
    auth_base_url = _get_auth_base_url()
    return os.getenv("TOKEN_URL") or (
        _join_url(auth_base_url, "/connect/token") if auth_base_url else ""
    )


def pytest_addoption(parser):
    parser.addoption(
        "--env-file",
        action="store",
        default=".env",
        help="Path to env file that should be loaded before fixtures are created.",
    )


def pytest_configure(config):
    env_file = config.getoption("--env-file")
    load_dotenv(env_file, override=True)


@pytest.fixture(scope="session")
def settings():
    test_email_domain = os.getenv("TEST_EMAIL_DOMAIN", "gamebcs.com")

    return {
        "target_env": os.getenv("TARGET_ENV", ""),
        "base_url": _get_base_url(),
        "auth_base_url": _get_auth_base_url(),
        "token_url": _get_token_url(),
        "test_api_base_url": os.getenv("TEST_API_BASE_URL") or _get_base_url(),
        "client_id": os.getenv("CLIENT_ID", ""),
        "client_secret": os.getenv("CLIENT_SECRET", ""),
        "scope": os.getenv("SCOPE", ""),
        "captcha_client_id": os.getenv("CAPTCHA_CLIENT_ID", ""),
        "captcha_client_secret": os.getenv("CAPTCHA_CLIENT_SECRET", ""),
        "captcha_scope": os.getenv("CAPTCHA_SCOPE", ""),
        "api_version": os.getenv("API_VERSION", ""),
        "test_email_domain": test_email_domain,
        "check_email": os.getenv(
            "CHECK_EMAIL",
            f"autotest-check@{test_email_domain}",
        ),
        "seed_owner_1_email": os.getenv("SEED_OWNER_1_EMAIL", ""),
        "seed_owner_1_user_id": os.getenv("SEED_OWNER_1_USER_ID", ""),
        "seed_owner_1_phone": os.getenv("SEED_OWNER_1_PHONE", ""),
        "seed_org_1_id": os.getenv("SEED_ORG_1_ID", ""),
        "seed_org_1_inn": os.getenv("SEED_ORG_1_INN", ""),
        "seed_org_1_kpp": os.getenv("SEED_ORG_1_KPP", ""),
        "seed_owner_2_email": os.getenv("SEED_OWNER_2_EMAIL", ""),
        "seed_owner_2_user_id": os.getenv("SEED_OWNER_2_USER_ID", ""),
        "seed_owner_2_phone": os.getenv("SEED_OWNER_2_PHONE", ""),
        "seed_org_2_id": os.getenv("SEED_ORG_2_ID", ""),
        "seed_org_2_inn": os.getenv("SEED_ORG_2_INN", ""),
        "seed_org_2_kpp": os.getenv("SEED_ORG_2_KPP", ""),
        "seed_employee_1_email": os.getenv("SEED_EMPLOYEE_1_EMAIL", ""),
        "seed_employee_1_user_id": os.getenv("SEED_EMPLOYEE_1_USER_ID", ""),
        "seed_employee_1_phone": os.getenv("SEED_EMPLOYEE_1_PHONE", ""),
        "seed_employee_2_email": os.getenv("SEED_EMPLOYEE_2_EMAIL", ""),
        "seed_employee_2_user_id": os.getenv("SEED_EMPLOYEE_2_USER_ID", ""),
        "seed_employee_2_phone": os.getenv("SEED_EMPLOYEE_2_PHONE", ""),
        "seed_ip_user_email": os.getenv("SEED_IP_USER_EMAIL", ""),
        "seed_ip_user_id": os.getenv("SEED_IP_USER_ID", ""),
        "seed_ip_user_phone": os.getenv("SEED_IP_USER_PHONE", ""),
        "seed_ip_org_id": os.getenv("SEED_IP_ORG_ID", ""),
        "seed_ip_cert_skid": os.getenv("SEED_IP_CERT_SKID", ""),
        "mutable_ip_cert_skid": os.getenv("MUTABLE_IP_CERT_SKID", ""),
        "mutable_ip_cert_common_name": os.getenv("MUTABLE_IP_CERT_COMMON_NAME", ""),
        "mutable_ip_cert_name": os.getenv("MUTABLE_IP_CERT_NAME", ""),
        "mutable_ip_cert_surname": os.getenv("MUTABLE_IP_CERT_SURNAME", ""),
        "mutable_ip_cert_patronymic": os.getenv("MUTABLE_IP_CERT_PATRONYMIC", ""),
        "mutable_ip_cert_inn": os.getenv("MUTABLE_IP_CERT_INN", ""),
        "mutable_ip_cert_ogrn": os.getenv("MUTABLE_IP_CERT_OGRN", ""),
        "mutable_ip_cert_snils": os.getenv("MUTABLE_IP_CERT_SNILS", ""),
        "mutable_ip_cert_thumbprint": os.getenv("MUTABLE_IP_CERT_THUMBPRINT", ""),
        "mutable_ip_cert_not_before": os.getenv("MUTABLE_IP_CERT_NOT_BEFORE", ""),
        "mutable_ip_cert_not_after": os.getenv("MUTABLE_IP_CERT_NOT_AFTER", ""),
        "mutable_ip_cert_organization": os.getenv("MUTABLE_IP_CERT_ORGANIZATION", ""),
        "mutable_ip_cert_authority": os.getenv("MUTABLE_IP_CERT_AUTHORITY", ""),
        "seed_ul_user_email": os.getenv("SEED_UL_USER_EMAIL", ""),
        "seed_ul_user_id": os.getenv("SEED_UL_USER_ID", ""),
        "seed_ul_org_id": os.getenv("SEED_UL_ORG_ID", ""),
        "seed_ul_cert_skid": os.getenv("SEED_UL_CERT_SKID", ""),
        "integrator_id": os.getenv("INTEGRATOR_ID", ""),
        "oidc_client_id": os.getenv("OIDC_CLIENT_ID", ""),
        "oidc_client_secret": os.getenv("OIDC_CLIENT_SECRET", ""),
        "oidc_redirect_uri": os.getenv("OIDC_REDIRECT_URI", ""),
        "oidc_scope": os.getenv("OIDC_SCOPE", ""),
    }


@pytest.fixture(scope="session")
def playwright_instance():
    with sync_playwright() as playwright:
        yield playwright


@pytest.fixture(scope="session")
def access_token(playwright_instance: Playwright, settings):
    if not settings["base_url"]:
        pytest.fail("Set API_BASE_URL or BASE_URL in environment variables or env file")

    if not settings["token_url"]:
        pytest.fail(
            "Set TOKEN_URL or AUTH_BASE_URL in environment variables or env file"
        )

    if not settings["client_id"] or not settings["client_secret"]:
        pytest.fail("Set CLIENT_ID and CLIENT_SECRET in environment variables or .env")

    request_context = playwright_instance.request.new_context()
    response = request_context.post(
        settings["token_url"],
        form={
            "grant_type": "client_credentials",
            "client_id": settings["client_id"],
            "client_secret": settings["client_secret"],
            "scope": settings["scope"],
        },
    )

    assert response.ok, response.text()

    token_data = response.json()
    request_context.dispose()

    return token_data["access_token"]


@pytest.fixture(scope="session")
def captcha_access_token(playwright_instance: Playwright, settings):
    if not settings["captcha_client_id"] or not settings["captcha_client_secret"]:
        pytest.skip(
            "Set CAPTCHA_CLIENT_ID and CAPTCHA_CLIENT_SECRET to run captcha API tests"
        )

    request_context = playwright_instance.request.new_context()
    response = request_context.post(
        settings["token_url"],
        form={
            "grant_type": "client_credentials",
            "client_id": settings["captcha_client_id"],
            "client_secret": settings["captcha_client_secret"],
            "scope": settings["captcha_scope"],
        },
    )

    assert response.ok, response.text()

    token_data = response.json()
    request_context.dispose()

    return token_data["access_token"]


@pytest.fixture()
def api_context(playwright_instance: Playwright, settings, access_token):
    context = playwright_instance.request.new_context(
        base_url=settings["base_url"],
        extra_http_headers={
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
        },
    )

    yield context

    context.dispose()


@pytest.fixture()
def captcha_api_context(playwright_instance: Playwright, settings, captcha_access_token):
    context = playwright_instance.request.new_context(
        base_url=settings["base_url"],
        extra_http_headers={
            "Authorization": f"Bearer {captcha_access_token}",
            "Accept": "application/json",
        },
    )

    yield context

    context.dispose()


@pytest.fixture()
def api_version_params(settings):
    if settings["api_version"]:
        return {"api-version": settings["api_version"]}

    return {}


@pytest.fixture()
def cleanup_registry():
    registry = CleanupRegistry()

    yield registry

    registry.cleanup()


@pytest.fixture(scope="session")
def seed_protection(settings):
    return collect_seed_protection(settings)


@pytest.fixture()
def protected_cleanup_registry(seed_protection):
    registry = CleanupRegistry(
        protected_emails=seed_protection["emails"],
        protected_user_ids=seed_protection["user_ids"],
        protected_organization_ids=seed_protection["organization_ids"],
    )

    yield registry

    registry.cleanup()


@pytest.fixture(scope="session")
def seed_owner_1(settings):
    return get_seed_user(settings, "seed_owner_1", pytest)


@pytest.fixture(scope="session")
def seed_owner_2(settings):
    return get_seed_user(settings, "seed_owner_2", pytest)


@pytest.fixture(scope="session")
def seed_employee_1(settings):
    return get_seed_user(settings, "seed_employee_1", pytest)


@pytest.fixture(scope="session")
def seed_employee_2(settings):
    return get_seed_user(settings, "seed_employee_2", pytest)


@pytest.fixture(scope="session")
def seed_ip_user(settings):
    return get_seed_user(settings, "seed_ip_user", pytest)


@pytest.fixture(scope="session")
def seed_ul_user(settings):
    return get_seed_user(settings, "seed_ul_user", pytest)


@pytest.fixture(scope="session")
def seed_org_1(settings):
    return get_seed_organization(settings, "seed_org_1", pytest)


@pytest.fixture(scope="session")
def seed_org_2(settings):
    return get_seed_organization(settings, "seed_org_2", pytest)


@pytest.fixture(scope="session")
def seed_users(settings):
    return get_seed_users(settings, pytest)


@pytest.fixture(scope="session")
def seed_organizations(settings):
    return get_seed_organizations(settings, pytest)
