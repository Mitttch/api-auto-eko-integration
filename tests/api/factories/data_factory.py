import os
from uuid import uuid4


AUTOTEST_RU_PREFIX = os.getenv("AUTOTEST_RU_PREFIX", "Автотест")
AUTOTEST_EMAIL_PREFIX = os.getenv("AUTOTEST_EMAIL_PREFIX", "qa_autotest")


def get_test_email_domain():
    return os.getenv("TEST_EMAIL_DOMAIN", "gamebcs.com")


def get_target_env():
    target_env = os.getenv("TARGET_ENV", "").strip().lower()
    assert target_env, "Set TARGET_ENV in environment variables"
    return target_env


def short_id():
    return uuid4().hex[:12]


def build_email(local_part):
    return f"{local_part}@{get_test_email_domain()}"


def unique_email(prefix=AUTOTEST_EMAIL_PREFIX):
    return build_email(f"{prefix}-{short_id()}")


def unique_cleanup_email(prefix="positive-smoke"):
    return unique_email(f"qa_autotest-cleanup-{get_target_env()}-{prefix}")


def unique_phone():
    return f"+79{uuid4().int % 1_000_000_000:09d}"


def unique_external_user_id():
    return f"{AUTOTEST_EMAIL_PREFIX}_external_{short_id()}"


def create_email_precreate_payload(email=None):
    return {
        "email": email or unique_email(),
        "password": "TestPassword123!",
    }


def create_phone_precreate_payload(phone=None):
    return {
        "phoneNumber": phone or unique_phone(),
        "password": "TestPassword123!",
    }


def create_valid_inn():
    base_digits = [int(digit) for digit in f"77{uuid4().int % 10_000_000:08d}"]
    weights = [2, 4, 10, 3, 5, 9, 4, 6, 8]
    check_digit = sum(
        digit * weight for digit, weight in zip(base_digits[:9], weights)
    ) % 11 % 10

    return "".join(str(digit) for digit in base_digits[:9]) + str(check_digit)


def create_valid_ogrn():
    base_number = f"1{uuid4().int % 1_000_000_000_000:012d}"
    check_digit = int(base_number[:12]) % 11 % 10

    return base_number[:12] + str(check_digit)


def create_organization_payload(user_id, permission_id, inn=None, kpp=None):
    unique_number = uuid4().hex[:6]
    organization_inn = inn or create_valid_inn()
    organization_kpp = kpp or f"77{str(uuid4().int)[:2]}01001"

    return {
        "payload": {
            "userId": user_id,
            "permissionIds": [permission_id],
            "organizationInfo": {
                "inn": organization_inn,
                "kpp": organization_kpp,
                "ogrn": create_valid_ogrn(),
                "name": f"{AUTOTEST_RU_PREFIX} организация {unique_number}",
                "fullName": (
                    f"{AUTOTEST_RU_PREFIX} общество с ограниченной "
                    f"ответственностью {unique_number}"
                ),
                "legalAddress": f"{AUTOTEST_RU_PREFIX}, Москва, Тестовая улица, 1",
                "actualAddress": f"{AUTOTEST_RU_PREFIX}, Москва, Тестовая улица, 1",
                "leaderSurname": "Тестов",
                "leaderName": "Тест",
                "leaderPatronymic": "Тестович",
                "leaderPosition": f"{AUTOTEST_RU_PREFIX} директор",
                "legalDocument": f"{AUTOTEST_RU_PREFIX} устав",
            },
        },
        "inn": organization_inn,
        "kpp": organization_kpp,
    }
