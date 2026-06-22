# Integration API Autotests Summary

## Что это за проект

Проект содержит API-автотесты для Integration API Identity Server.

Тестовый стек:

- Python
- pytest
- Playwright `APIRequestContext`
- python-dotenv

Авторизация идет через OAuth2 Client Credentials:

- `POST /connect/token`
- `grant_type=client_credentials`
- `client_id`
- `client_secret`
- `scope`

## Стенды

Проект поддерживает два стенда:

- `demo`
- `integrity`

Код тестов общий. Меняются только env-конфиги.

Стенд выбирается через `--env-file`.

Примеры:

```powershell
python -m pytest --env-file=.env.demo -m positive_smoke -q
python -m pytest --env-file=.env.integrity -m positive_smoke -q

python -m pytest --env-file=.env.demo -q
python -m pytest --env-file=.env.integrity -q

python -m pytest --env-file=.env.integrity --collect-only -q
```

Если `--env-file` не передан, pytest использует `.env`.

## Основные файлы проекта

```text
.
|-- .editorconfig
|-- .env.example
|-- .env.demo.example
|-- .env.integrity.example
|-- .github/workflows/
|   |-- api-tests-demo.yml
|   `-- api-tests-integrity.yml
|-- azure-pipelines-demo.yml
|-- azure-pipelines-integrity.yml
|-- README.md
|-- PROJECT_SUMMARY.md
|-- INTEGRATION_API_TEST_SUITES.md
|-- pytest.ini
|-- requirements.txt
`-- tests
    |-- conftest.py
    `-- api
        |-- assertions/
        |-- factories/
        |-- cleanup.py
        |-- helpers.py
        |-- seed_support.py
        `-- test_*.py
```

## Env-конфиг

Базовые переменные:

```env
TARGET_ENV=

API_BASE_URL=
AUTH_BASE_URL=
TOKEN_URL=
CLIENT_ID=
CLIENT_SECRET=
SCOPE=

TEST_API_BASE_URL=
TEST_EMAIL_DOMAIN=
API_VERSION=
CHECK_EMAIL=
AUTOTEST_RU_PREFIX=
AUTOTEST_EMAIL_PREFIX=
```

Дополнительно поддерживаются:

- seed users и seed organizations
- captcha credentials
- mutable certificate переменные
- integrator / OIDC переменные

`BASE_URL` пока оставлен как legacy fallback для старых env-файлов.

## Тестовые данные

Человекочитаемый префикс:

```text
Автотест
```

Email prefix:

```text
qa_autotest
```

Cleanup-safe email:

```text
qa_autotest-cleanup-<target_env>-<random>@<TEST_EMAIL_DOMAIN>
```

Примеры:

```text
qa_autotest-cleanup-demo-abc123def456@gamebcs.com
qa_autotest-cleanup-integrity-abc123def456@gamebcs.com
```

## Seed-данные

Seed-данные читаются из env текущего стенда.

Поддерживаются:

- `SEED_OWNER_1_*`
- `SEED_OWNER_2_*`
- `SEED_EMPLOYEE_1_*`
- `SEED_EMPLOYEE_2_*`
- `SEED_ORG_1_*`
- `SEED_ORG_2_*`
- `SEED_IP_*`
- `SEED_UL_*`

Основные seed fixtures:

- `seed_owner_1`
- `seed_owner_2`
- `seed_employee_1`
- `seed_employee_2`
- `seed_ip_user`
- `seed_ul_user`
- `seed_org_1`
- `seed_org_2`
- `seed_users`
- `seed_organizations`

Seed users и seed organizations не должны удаляться cleanup helper-ом.

## Cleanup

Тестовый delete endpoint:

```text
DELETE /test-api/account/email/{email}
```

Логика cleanup живет в:

- `tests/api/cleanup.py`

Что делает cleanup helper:

- удаляет только cleanup-safe email текущего стенда
- валидирует email строгим regex
- не удаляет seed users
- не удаляет stable/check users
- не удаляет внешние email

## Структура кода

Текущее разбиение по ролям:

- `tests/conftest.py` — source of truth для env/config и session fixtures
- `tests/api/helpers.py` — request/setup helper-ы
- `tests/api/assertions/` — assertion helper-ы
- `tests/api/factories/` — генерация тестовых данных и payload factory
- `tests/api/cleanup.py` — cleanup и safe-delete guard
- `tests/api/seed_support.py` — чтение и защита seed-данных

## Suite-ы

Основные маркеры:

- `positive_smoke`
- `negative`
- `users_extended`
- `organizations_extended`
- `employees_extended`
- `permissions_extended`
- `consistency`
- `mass_extended`
- `auth_extended`
- `security_extended`
- `email_confirmation_extended`
- `phone_mass_extended`
- `captcha_extended`
- `integrator_extended`
- `certificates_extended`

Подробный inventory suite-ов, список тестов, постоянные `skip`, `xfail` и условия включения вынесены в:

- `INTEGRATION_API_TEST_SUITES.md`

`README.md` используется как короткая входная точка.

## CI/CD

В проекте есть отдельные конфиги для запуска по стендам.

GitHub Actions:

- `.github/workflows/api-tests-demo.yml`
- `.github/workflows/api-tests-integrity.yml`

Azure DevOps / TFS:

- `azure-pipelines-demo.yml`
- `azure-pipelines-integrity.yml`

Логика одинаковая:

- `demo` и `integrity` запускаются раздельно
- тесты общие, отличается только env-файл
- workflow или pipeline ожидает секрет/переменную `PYTEST_ENV_FILE`
- в `PYTEST_ENV_FILE` кладется полное содержимое env-файла нужного стенда

## Кодировка и редактирование

Базовые правила:

- source files должны быть в UTF-8
- русские комментарии над тестами допустимы и ожидаемы
- правки по кодировке делаются только targeted-патчами
- не нужно массово переписывать файлы только ради “красоты”

## Что смотреть дальше

Если нужно быстро понять проект:

1. Сначала открыть `README.md`
2. Потом открыть `PROJECT_SUMMARY.md`
3. Для состава suite-ов и условий запуска открыть `INTEGRATION_API_TEST_SUITES.md`
