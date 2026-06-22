# Integration API Autotests

Проект с API-автотестами для Integration API Identity Server.

Тесты написаны на:

- Python
- pytest
- Playwright `APIRequestContext`

Проект поддерживает запуск на нескольких стендах:

- `demo`
- `integrity`

Код тестов общий. Отличаются только env-конфиги.

## Основные suite-ы

- `positive_smoke` - базовый позитивный smoke по основным API flow
- `negative` - негативные проверки и known bug сценарии
- `users_extended` - расширенные сценарии по пользователям
- `organizations_extended` - расширенные сценарии по организациям
- `employees_extended` - сценарии по сотрудникам организации
- `permissions_extended` - сценарии по правам в организации
- `consistency` - проверки связности и согласованности данных
- `mass_extended` - массовые сценарии по email-регистрации
- `phone_mass_extended` - массовые сценарии по phone-регистрации
- `auth_extended` - дополнительные проверки авторизации
- `security_extended` - проверки ошибок и защитных сценариев
- `email_confirmation_extended` - сценарии подтверждения по email
- `captcha_extended` - сценарии по captcha exclude
- `integrator_extended` - сценарии интеграторских методов
- `certificates_extended` - сценарии по сертификатам

## Подготовка

Установить зависимости:

```powershell
python -m pip install -r requirements.txt
```

Создать env-файл на основе шаблона:

- `.env.demo.example` -> `.env.demo`
- `.env.integrity.example` -> `.env.integrity`

Если `--env-file` не передан, pytest использует `.env`.

## Запуск через --env-file

Примеры для `demo`:

```powershell
python -m pytest --env-file=.env.demo -m positive_smoke -q
python -m pytest --env-file=.env.demo -m negative -q
python -m pytest --env-file=.env.demo -q
```

Примеры для `integrity`:

```powershell
python -m pytest --env-file=.env.integrity -m positive_smoke -q
python -m pytest --env-file=.env.integrity -m negative -q
python -m pytest --env-file=.env.integrity -q
```

Проверка коллекции:

```powershell
python -m pytest --env-file=.env.integrity --collect-only -q
```

## CI/CD

В проект добавлены отдельные конфиги для ручного запуска полного набора тестов по стендам.

GitHub Actions:

- `.github/workflows/api-tests-demo.yml`
- `.github/workflows/api-tests-integrity.yml`

Azure DevOps / TFS:

- `azure-pipelines-demo.yml`
- `azure-pipelines-integrity.yml`

Логика одинаковая:

- `demo` и `integrity` запускаются раздельно;
- тесты общие, отличается только env-файл;
- workflow или pipeline ожидает секрет или переменную `PYTEST_ENV_FILE` с полным содержимым env-файла для нужного стенда.

Пример настройки:

- для GitHub environment `demo` в secret `PYTEST_ENV_FILE` кладется содержимое `.env.demo`
- для GitHub environment `integrity` в secret `PYTEST_ENV_FILE` кладется содержимое `.env.integrity`
- для Azure DevOps / TFS в pipeline variable `PYTEST_ENV_FILE` кладется содержимое env-файла нужного стенда


