import os
import re
from urllib.parse import quote


SAFE_ACCOUNT_CLEANUP_EMAIL_PREFIX = "qa_autotest-cleanup"


def get_target_env():
    target_env = os.getenv("TARGET_ENV", "").strip().lower()
    assert target_env, "Set TARGET_ENV in environment variables"
    return target_env


def get_safe_account_cleanup_email_domain():
    return os.getenv("TEST_EMAIL_DOMAIN", "gamebcs.com").strip().lower()


def get_safe_account_cleanup_email_regex():
    target_env = re.escape(get_target_env())
    domain = re.escape(get_safe_account_cleanup_email_domain())
    return (
        rf"^qa_autotest\-cleanup\-{target_env}\-[a-z0-9][a-z0-9+\-]*"
        rf"@{domain}$"
    )


def is_current_env_cleanup_email(email):
    if not isinstance(email, str):
        return False

    normalized_email = email.strip().lower()
    return re.fullmatch(get_safe_account_cleanup_email_regex(), normalized_email) is not None


def get_protected_cleanup_emails():
    protected_names = [
        "CHECK_EMAIL",
        "SEED_OWNER_1_EMAIL",
        "SEED_OWNER_2_EMAIL",
        "SEED_EMPLOYEE_1_EMAIL",
        "SEED_EMPLOYEE_2_EMAIL",
        "SEED_IP_USER_EMAIL",
        "SEED_UL_USER_EMAIL",
    ]
    return {
        os.getenv(name, "").strip().lower()
        for name in protected_names
        if os.getenv(name, "").strip()
    }


def get_test_api_base_url():
    return (
        os.getenv("TEST_API_BASE_URL")
        or os.getenv("API_BASE_URL")
        or os.getenv("BASE_URL")
        or ""
    )


def assert_safe_account_cleanup_email(email):
    assert isinstance(email, str), "Cleanup delete expects email as string"

    normalized_email = email.strip().lower()
    assert normalized_email not in get_protected_cleanup_emails(), (
        "Cleanup delete is forbidden for seed, stable, or check users"
    )
    assert is_current_env_cleanup_email(normalized_email), (
        "Cleanup delete is allowed only for current environment emails matching "
        f"{get_safe_account_cleanup_email_regex()}"
    )


def delete_account_by_email(api_context, api_version_params, email):
    assert_safe_account_cleanup_email(email)

    test_api_base_url = get_test_api_base_url()
    assert test_api_base_url, (
        "Set TEST_API_BASE_URL or API_BASE_URL/BASE_URL in environment variables"
    )

    encoded_email = quote(email, safe="")
    return api_context.delete(
        f"{test_api_base_url.rstrip('/')}/test-api/account/email/{encoded_email}",
        params=api_version_params,
    )


def delete_created_accounts(api_context, api_version_params, emails, deleted_emails):
    for email in emails:
        if email in deleted_emails:
            continue

        response = delete_account_by_email(api_context, api_version_params, email)
        assert response.ok, response.text()
        deleted_emails.add(email)


class CleanupRegistry:
    """Safe placeholder for future DB/API cleanup of autotest data.

    Current Integration API does not provide delete endpoints, and DB schema is
    not documented in this project. For that reason cleanup is intentionally a
    no-op until a safe delete mechanism is provided.
    """

    def __init__(
        self,
        protected_emails=None,
        protected_user_ids=None,
        protected_organization_ids=None,
    ):
        self.created_user_ids = []
        self.created_organization_ids = []
        self.protected_emails = set(protected_emails or [])
        self.protected_user_ids = set(protected_user_ids or [])
        self.protected_organization_ids = set(protected_organization_ids or [])

    def ensure_not_seed_email(self, email):
        assert email not in self.protected_emails, (
            "Seed account email cannot be registered for cleanup"
        )

    def ensure_not_seed_user(self, user_id):
        assert user_id not in self.protected_user_ids, (
            "Seed user cannot be registered for cleanup"
        )

    def ensure_not_seed_organization(self, organization_id):
        assert organization_id not in self.protected_organization_ids, (
            "Seed organization cannot be registered for cleanup"
        )

    def register_email(self, email):
        self.ensure_not_seed_email(email)

    def register_user(self, user_id):
        self.ensure_not_seed_user(user_id)
        self.created_user_ids.append(user_id)

    def register_organization(self, organization_id):
        self.ensure_not_seed_organization(organization_id)
        self.created_organization_ids.append(organization_id)

    def cleanup(self):
        # TODO: connect safe cleanup after DB schema or delete API is available.
        # Cleanup must delete only records with the autotest prefix.
        return {
            "users": list(self.created_user_ids),
            "organizations": list(self.created_organization_ids),
        }
