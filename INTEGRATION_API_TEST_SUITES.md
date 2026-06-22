# Integration API Test Suites

Документ описывает текущую структуру pytest API-автотестов для Integration API Identity Server.

## Поддержка стендов

Проект поддерживает запуск на двух стендах:

- `demo`
- `integrity`

Код тестов общий. Отличаются только env-конфиги.

Стенд выбирается через `--env-file`.

## Подготовка

```powershell
python -m pip install -r requirements.txt
```

Создай локальный env-файл на основе одного из шаблонов:

- `.env.demo.example`
- `.env.integrity.example`

Например:

- `.env.demo`
- `.env.integrity`

## Примеры запуска

```powershell
python -m pytest --env-file=.env.demo -m positive_smoke -q
python -m pytest --env-file=.env.integrity -m positive_smoke -q

python -m pytest --env-file=.env.demo -q
python -m pytest --env-file=.env.integrity -q

python -m pytest --env-file=.env.integrity --collect-only -q
```

Если `--env-file` не передан, pytest использует `.env`.

## Отдельные suite-ы

```powershell
python -m pytest --env-file=.env.demo -m positive_smoke -q
python -m pytest --env-file=.env.demo -m negative -q
python -m pytest --env-file=.env.demo -m users_extended -q
python -m pytest --env-file=.env.demo -m organizations_extended -q
python -m pytest --env-file=.env.demo -m employees_extended -q
python -m pytest --env-file=.env.demo -m permissions_extended -q
python -m pytest --env-file=.env.demo -m consistency -q
python -m pytest --env-file=.env.demo -m mass_extended -q
python -m pytest --env-file=.env.demo -m auth_extended -q
python -m pytest --env-file=.env.demo -m security_extended -q
python -m pytest --env-file=.env.demo -m email_confirmation_extended -q
python -m pytest --env-file=.env.demo -m phone_mass_extended -q
python -m pytest --env-file=.env.demo -m captcha_extended -q
python -m pytest --env-file=.env.demo -m integrator_extended -q
```

Для `integrity` меняется только env-файл:

```powershell
python -m pytest --env-file=.env.integrity -m positive_smoke -q
```

## Positive Smoke Suite

Файл: `tests/api/test_positive_smoke.py`

Маркер: `positive_smoke`

Проверяет:

- `checkmailregister`
- `products`
- `products/permissions`
- `precreate`
- `users`
- `search`
- `users/fio`
- `users/phone`
- `organizations`
- `organizations/search`
- `employees`
- `permissions`
- `check-permissions`

## Negative Suite

Файл: `tests/api/test_negative.py`

Маркер: `negative`

Проверяет базовые client error сценарии и отсутствие лишних `500`.

## Extended Suite-ы

### `users_extended`

Файл: `tests/api/test_users_extended.py`

Проверяет расширенные сценарии по пользователям и поиску.

### `organizations_extended`

Файл: `tests/api/test_organizations_extended.py`

Проверяет расширенные сценарии по организациям.

### `employees_extended`

Файл: `tests/api/test_employees_extended.py`

Проверяет сценарии по сотрудникам организации.

### `permissions_extended`

Файл: `tests/api/test_permissions_extended.py`

Проверяет назначение, замену и проверку прав.

### `consistency`

Файл: `tests/api/test_consistency_flows.py`

Проверяет сквозную согласованность read/write flow.

### `mass_extended`

Файл: `tests/api/test_mass_extended.py`

Проверяет batch email сценарии:

- `precreatemass`
- `precreatemass/silent`

### `auth_extended`

Файл: `tests/api/test_auth_extended.py`

Проверяет token flow и `products`.

### `security_extended`

Файл: `tests/api/test_security_extended.py`

Проверяет, что API не уходит в лишние `500` на подозрительных входных данных.

### `email_confirmation_extended`

Файл: `tests/api/test_email_confirmation_extended.py`

Проверяет `precreate/byemail`, `resend` и негативные confirm-сценарии.

### `phone_mass_extended`

Файл: `tests/api/test_phone_mass_extended.py`

Проверяет `precreate/byphone`, `precreatemass/byphone`, `users/email`, `resend`.

### `captcha_extended`

Файл: `tests/api/test_captcha_extended.py`

Проверяет `captcha/exclude`.

### `integrator_extended`

Файл: `tests/api/test_integrator_extended.py`

Проверяет `integrateuser` и `/code`, если заполнены integrator/OIDC env-переменные.

## Seed data

Seed-данные задаются отдельно для каждого стенда через env-файл текущего запуска.

Поддерживаются:

- `SEED_OWNER_1_*`
- `SEED_OWNER_2_*`
- `SEED_EMPLOYEE_1_*`
- `SEED_EMPLOYEE_2_*`
- `SEED_ORG_1_*`
- `SEED_ORG_2_*`

Seed users и seed organizations не удаляются cleanup helper-ом.

## Cleanup-safe users

Cleanup-safe email имеет вид:

```text
qa_autotest-cleanup-<target_env>-<random>@<TEST_EMAIL_DOMAIN>
```

Примеры:

```text
qa_autotest-cleanup-demo-abc123def456@gamebcs.com
qa_autotest-cleanup-integrity-abc123def456@gamebcs.com
```

Helper удаляет только email текущего стенда.

## Suite constraints

### Suite-ы, которым нужны seed data

Эти suite-ы опираются на seed users и/или seed organizations из env текущего стенда:

- `employees_extended`
- `permissions_extended`
- `consistency`
- `certificates_extended`

Дополнительно:

- `integrator_extended` требует не seed-данные, а заполненные `INTEGRATOR_ID` и OIDC env-переменные;
- `captcha_extended` требует отдельные captcha credentials;
- `email_confirmation_extended` и `phone_mass_extended` могут работать без seed users, но зависят от доступности соответствующих flow на стенде.

### Suite-ы, которые меняют persistent state

Эти suite-ы не read-only. Они создают или меняют данные на стенде:

- `positive_smoke`
- `users_extended`
- `organizations_extended`
- `employees_extended`
- `permissions_extended`
- `consistency`
- `mass_extended`
- `email_confirmation_extended`
- `phone_mass_extended`
- `integrator_extended`
- `certificates_extended`
- `security_extended`

Обычно они делают одно или несколько действий:

- создают новых пользователей;
- добавляют email/phone/FIO;
- создают организации;
- добавляют сотрудников;
- назначают permissions;
- меняют привязку сертификата;
- удаляют только cleanup-safe accounts через test-api.

Read-mostly suite-ы:

- `negative`
- `auth_extended`
- `captcha_extended`

### Suite-ы, которые создают новые организации

На текущий момент новые организации создают или могут создавать:

- `positive_smoke`
- `organizations_extended`

Исторически также создавали много новых организаций:

- `employees_extended`
- `permissions_extended`
- `consistency`

Сейчас эти три suite-а переведены на seed-organization подход там, где это безопасно. Если `SEED_ORG_1_*` и `SEED_ORG_2_*` не заполнены, сценарии не создают новые организации "про запас", а уходят в `skip` с понятной причиной.

### Постоянные skip-и и условия включения

Ниже перечислены не случайные skip-и, а осознанно отложенные сценарии.

#### `permissions_extended`

- `test_assign_one_permission`
- `test_assign_multiple_permissions`
- `test_assign_all_available_permissions`
- `test_update_permissions_replaces_previous_permissions`
- `test_user_permissions_do_not_mix_between_organizations`
- `test_check_unassigned_permission`
- `test_check_partially_assigned_permissions`
- `test_check_all_assigned_permissions`
- `test_get_organization_permissions_multiple_users`
- `test_get_user_permissions_with_organization_filter`

Что нужно, чтобы включить:

- вручную подтвердить фактический backend contract по:
  - assigned vs returned permissions;
  - replace vs merge behavior;
  - semantics `check-permissions`;
  - изоляции permissions между организациями;
  - фильтрации `organizationId` в user permissions.

#### `consistency`

- `test_user_data_consistency_flow`
- `test_permissions_isolation_between_organizations_flow`

Что нужно, чтобы включить:

- для `test_user_data_consistency_flow` нужен redesign без изменения stable seed-user;
- для `test_permissions_isolation_between_organizations_flow` нужно вручную подтвердить реальный permissions contract между двумя организациями.

#### `organizations_extended`

- `test_search_disabled_organization_status_is_not_prepared`

Что нужно, чтобы включить:

- безопасный и воспроизводимый способ подготовить organization со статусом `Disabled` без ручных действий и без грязного состояния.

#### `certificates_extended`

- `test_ul_certificate_scenarios_are_not_prepared_yet`

Что нужно, чтобы включить:

- стабильный UL seed user;
- стабильная UL organization;
- стабильный UL certificate skid;
- безопасный flow для UL certificate сценариев.

#### Conditional skip по env / credentials

Это не "отложенные навсегда" тесты, а тесты, которые пропускаются, если стенд не подготовлен:

- любой seed-based suite при отсутствии `SEED_OWNER_*`, `SEED_EMPLOYEE_*`, `SEED_ORG_*`, `SEED_IP_*`, `SEED_UL_*`;
- `captcha_extended` без `CAPTCHA_CLIENT_ID`, `CAPTCHA_CLIENT_SECRET`, `CAPTCHA_SCOPE`;
- `integrator_extended` без `INTEGRATOR_ID` и OIDC env-переменных;
- mutable certificate сценарии без `MUTABLE_IP_CERT_*`.

Правило: если тест уходит в `skip` из-за env, причина должна явно перечислять недостающие переменные.

## Явный состав suite-ов

Ниже зафиксирован текущий inventory в формате `suite -> file::test_name`.

### `positive_smoke` (4)

- `tests/api/test_positive_smoke.py::test_check_mail_register`
- `tests/api/test_positive_smoke.py::test_get_product`
- `tests/api/test_positive_smoke.py::test_get_product_permissions`
- `tests/api/test_positive_smoke.py::test_full_positive_smoke_flow_with_safe_cleanup`

### `negative` (16)

- `tests/api/test_negative.py::test_request_without_token_is_rejected`
- `tests/api/test_negative.py::test_request_with_invalid_token_is_rejected`
- `tests/api/test_negative.py::test_check_mail_register_with_invalid_email`
- `tests/api/test_negative.py::test_precreate_user_with_empty_email`
- `tests/api/test_negative.py::test_precreate_user_with_invalid_email`
- `tests/api/test_negative.py::test_get_users_with_invalid_id`
- `tests/api/test_negative.py::test_get_users_with_more_than_ten_ids`
- `tests/api/test_negative.py::test_search_user_without_search_params`
- `tests/api/test_negative.py::test_update_user_fio_with_invalid_user_id`
- `tests/api/test_negative.py::test_update_user_phone_with_invalid_phone`
- `tests/api/test_negative.py::test_create_organization_with_invalid_inn_and_ogrn`
- `tests/api/test_negative.py::test_create_organization_without_user_id`
- `tests/api/test_negative.py::test_get_organizations_with_more_than_ten_ids`
- `tests/api/test_negative.py::test_add_employee_to_unknown_organization`
- `tests/api/test_negative.py::test_update_permissions_for_unknown_organization`
- `tests/api/test_negative.py::test_check_permissions_with_empty_permissions`

### `users_extended` (25)

- `tests/api/test_users_extended.py::test_precreate_same_email_returns_same_user_id`
- `tests/api/test_users_extended.py::test_precreate_email_with_different_case`
- `tests/api/test_users_extended.py::test_precreate_email_with_spaces`
- `tests/api/test_users_extended.py::test_precreate_email_with_plus_symbol`
- `tests/api/test_users_extended.py::test_get_users_with_multiple_ids`
- `tests/api/test_users_extended.py::test_get_users_with_valid_and_unknown_id`
- `tests/api/test_users_extended.py::test_get_users_with_duplicate_ids`
- `tests/api/test_users_extended.py::test_get_users_with_empty_ids`
- `tests/api/test_users_extended.py::test_get_users_without_ids`
- `tests/api/test_users_extended.py::test_search_unknown_email`
- `tests/api/test_users_extended.py::test_search_email_after_precreate`
- `tests/api/test_users_extended.py::test_search_phone_after_update`
- `tests/api/test_users_extended.py::test_search_same_user_by_email_and_phone`
- `tests/api/test_users_extended.py::test_search_conflicting_email_and_phone`
- `tests/api/test_users_extended.py::test_update_user_fio_twice`
- `tests/api/test_users_extended.py::test_update_user_phone_twice`
- `tests/api/test_users_extended.py::test_same_phone_for_two_users`
- `tests/api/test_users_extended.py::test_invalid_phone_formats`
- `tests/api/test_users_extended.py::test_add_email_to_user_without_email`
- `tests/api/test_users_extended.py::test_get_users_with_repeated_query_params_format`
- `tests/api/test_users_extended.py::test_get_users_repeated_and_comma_formats_return_same_users`
- `tests/api/test_users_extended.py::test_get_users_with_exactly_ten_ids`
- `tests/api/test_users_extended.py::test_get_users_with_eleven_ids_returns_client_error`
- `tests/api/test_users_extended.py::test_get_users_with_valid_and_invalid_uuid`
- `tests/api/test_users_extended.py::test_get_users_with_duplicate_repeated_ids`

### `organizations_extended` (18)

- `tests/api/test_organizations_extended.py::test_create_organization_with_same_inn_and_kpp`
- `tests/api/test_organizations_extended.py::test_create_two_organizations_same_inn_different_kpp`
- `tests/api/test_organizations_extended.py::test_create_organization_with_unknown_creator`
- `tests/api/test_organizations_extended.py::test_get_organizations_with_multiple_ids`
- `tests/api/test_organizations_extended.py::test_get_organizations_with_valid_and_unknown_id`
- `tests/api/test_organizations_extended.py::test_get_organizations_with_duplicate_ids`
- `tests/api/test_organizations_extended.py::test_get_organizations_with_empty_ids`
- `tests/api/test_organizations_extended.py::test_get_organizations_without_ids`
- `tests/api/test_organizations_extended.py::test_search_organization_by_inn_only`
- `tests/api/test_organizations_extended.py::test_search_organization_by_inn_and_kpp`
- `tests/api/test_organizations_extended.py::test_search_organization_by_inn_with_wrong_kpp`
- `tests/api/test_organizations_extended.py::test_search_unknown_organization`
- `tests/api/test_organizations_extended.py::test_search_organization_by_inn_and_actual_status`
- `tests/api/test_organizations_extended.py::test_search_organization_by_inn_kpp_and_actual_status`
- `tests/api/test_organizations_extended.py::test_search_organization_by_wrong_status_does_not_return_created_org`
- `tests/api/test_organizations_extended.py::test_search_organization_with_invalid_status`
- `tests/api/test_organizations_extended.py::test_search_organization_with_lowercase_status`
- `tests/api/test_organizations_extended.py::test_search_disabled_organization_status_is_not_prepared`

### `employees_extended` (21)

- `tests/api/test_employees_extended.py::test_add_same_employee_twice`
- `tests/api/test_employees_extended.py::test_add_multiple_employees_to_organization`
- `tests/api/test_employees_extended.py::test_add_same_user_to_two_organizations`
- `tests/api/test_employees_extended.py::test_add_unknown_user_to_existing_organization`
- `tests/api/test_employees_extended.py::test_employee_list_after_adding_multiple_users`
- `tests/api/test_employees_extended.py::test_no_duplicate_employee_after_second_add`
- `tests/api/test_employees_extended.py::test_get_employees_for_unknown_organization`
- `tests/api/test_employees_extended.py::test_get_employees_with_invalid_organization_id`
- `tests/api/test_employees_extended.py::test_get_employees_without_query_params`
- `tests/api/test_employees_extended.py::test_get_employees_with_count_one`
- `tests/api/test_employees_extended.py::test_get_employees_with_offset_and_count`
- `tests/api/test_employees_extended.py::test_search_employee_by_email`
- `tests/api/test_employees_extended.py::test_search_employee_by_displayed_name`
- `tests/api/test_employees_extended.py::test_get_employees_confirmed_only_true`
- `tests/api/test_employees_extended.py::test_get_employees_confirmed_only_false`
- `tests/api/test_employees_extended.py::test_get_employees_sort_order_asc`
- `tests/api/test_employees_extended.py::test_get_employees_sort_order_desc`
- `tests/api/test_employees_extended.py::test_get_employees_with_invalid_count`
- `tests/api/test_employees_extended.py::test_get_employees_with_invalid_offset`
- `tests/api/test_employees_extended.py::test_get_employees_with_invalid_sort_order`
- `tests/api/test_employees_extended.py::test_get_employees_with_unknown_sort_field`

### `permissions_extended` (27)

- `tests/api/test_permissions_extended.py::test_product_permissions_are_not_empty`
- `tests/api/test_permissions_extended.py::test_product_permission_ids_are_unique`
- `tests/api/test_permissions_extended.py::test_product_permissions_have_required_fields`
- `tests/api/test_permissions_extended.py::test_product_permission_can_be_used_for_update`
- `tests/api/test_permissions_extended.py::test_assign_one_permission`
- `tests/api/test_permissions_extended.py::test_assign_multiple_permissions`
- `tests/api/test_permissions_extended.py::test_assign_all_available_permissions`
- `tests/api/test_permissions_extended.py::test_assign_empty_permissions_list`
- `tests/api/test_permissions_extended.py::test_assign_same_permissions_twice`
- `tests/api/test_permissions_extended.py::test_update_permissions_replaces_previous_permissions`
- `tests/api/test_permissions_extended.py::test_assign_permissions_to_user_who_is_not_employee`
- `tests/api/test_permissions_extended.py::test_assign_permissions_to_unknown_user`
- `tests/api/test_permissions_extended.py::test_assign_unknown_permission`
- `tests/api/test_permissions_extended.py::test_assign_duplicate_permission_ids`
- `tests/api/test_permissions_extended.py::test_assign_permissions_to_unknown_organization`
- `tests/api/test_permissions_extended.py::test_get_user_permissions_without_assigned_permissions`
- `tests/api/test_permissions_extended.py::test_user_permissions_do_not_mix_between_organizations`
- `tests/api/test_permissions_extended.py::test_check_one_assigned_permission`
- `tests/api/test_permissions_extended.py::test_check_unassigned_permission`
- `tests/api/test_permissions_extended.py::test_check_partially_assigned_permissions`
- `tests/api/test_permissions_extended.py::test_check_all_assigned_permissions`
- `tests/api/test_permissions_extended.py::test_check_permissions_with_empty_permission_ids`
- `tests/api/test_permissions_extended.py::test_get_organization_permissions_multiple_users`
- `tests/api/test_permissions_extended.py::test_organization_permissions_change_after_update`
- `tests/api/test_permissions_extended.py::test_organization_permissions_do_not_include_other_organization_users`
- `tests/api/test_permissions_extended.py::test_get_user_permissions_with_organization_filter`
- `tests/api/test_permissions_extended.py::test_get_user_permissions_with_unrelated_organization_filter`

### `consistency` (4)

- `tests/api/test_consistency_flows.py::test_user_data_consistency_flow`
- `tests/api/test_consistency_flows.py::test_organization_data_consistency_flow`
- `tests/api/test_consistency_flows.py::test_employee_and_permissions_consistency_flow`
- `tests/api/test_consistency_flows.py::test_permissions_isolation_between_organizations_flow`

### `mass_extended` (12)

- `tests/api/test_mass_extended.py::test_precreate_mass_with_valid_users`
- `tests/api/test_mass_extended.py::test_precreate_mass_users_are_available_in_get_users`
- `tests/api/test_mass_extended.py::test_precreate_mass_users_are_available_in_search`
- `tests/api/test_mass_extended.py::test_precreate_mass_with_empty_array`
- `tests/api/test_mass_extended.py::test_precreate_mass_with_one_user`
- `tests/api/test_mass_extended.py::test_precreate_mass_with_duplicate_emails`
- `tests/api/test_mass_extended.py::test_precreate_mass_with_valid_and_invalid_email`
- `tests/api/test_mass_extended.py::test_precreate_mass_silent_with_valid_users`
- `tests/api/test_mass_extended.py::test_precreate_mass_silent_same_emails_twice`
- `tests/api/test_mass_extended.py::test_precreate_mass_silent_with_empty_array`
- `tests/api/test_mass_extended.py::test_precreate_mass_silent_with_duplicate_emails`
- `tests/api/test_mass_extended.py::test_precreate_mass_silent_with_valid_and_invalid_email`

### `auth_extended` (11)

- `tests/api/test_auth_extended.py::test_token_with_invalid_client_secret`
- `tests/api/test_auth_extended.py::test_token_with_invalid_client_id`
- `tests/api/test_auth_extended.py::test_token_without_scope`
- `tests/api/test_auth_extended.py::test_token_with_invalid_scope`
- `tests/api/test_auth_extended.py::test_token_with_invalid_grant_type`
- `tests/api/test_auth_extended.py::test_products_matches_current_client_id`
- `tests/api/test_auth_extended.py::test_products_without_client_id`
- `tests/api/test_auth_extended.py::test_products_without_and_with_current_client_id_return_same_product`
- `tests/api/test_auth_extended.py::test_products_with_unknown_client_id`
- `tests/api/test_auth_extended.py::test_products_with_empty_client_id`
- `tests/api/test_auth_extended.py::test_products_with_garbage_client_id`

### `security_extended` (6)

- `tests/api/test_security_extended.py::test_search_with_sql_like_email`
- `tests/api/test_security_extended.py::test_search_with_very_long_email`
- `tests/api/test_security_extended.py::test_update_fio_with_script_like_values`
- `tests/api/test_security_extended.py::test_precreate_with_empty_json_body`
- `tests/api/test_security_extended.py::test_precreate_with_extra_fields`
- `tests/api/test_security_extended.py::test_get_method_for_post_endpoint`

### `email_confirmation_extended` (8)

- `tests/api/test_email_confirmation_extended.py::test_precreate_byemail_returns_user_id_and_url`
- `tests/api/test_email_confirmation_extended.py::test_confirm_token_from_precreate_byemail`
- `tests/api/test_email_confirmation_extended.py::test_confirm_same_token_twice_does_not_return_500`
- `tests/api/test_email_confirmation_extended.py::test_confirm_with_unknown_token_returns_client_error`
- `tests/api/test_email_confirmation_extended.py::test_confirm_with_short_token_returns_client_error`
- `tests/api/test_email_confirmation_extended.py::test_resend_for_precreated_byemail_user`
- `tests/api/test_email_confirmation_extended.py::test_resend_for_unknown_user_returns_client_error`
- `tests/api/test_email_confirmation_extended.py::test_resend_with_invalid_user_id_returns_client_error`

### `phone_mass_extended` (11)

- `tests/api/test_phone_mass_extended.py::test_precreate_byphone_returns_user_id`
- `tests/api/test_phone_mass_extended.py::test_add_email_to_user_created_by_phone`
- `tests/api/test_phone_mass_extended.py::test_precreate_mass_byphone_with_valid_phones`
- `tests/api/test_phone_mass_extended.py::test_precreate_mass_byphone_with_one_phone`
- `tests/api/test_phone_mass_extended.py::test_precreate_mass_byphone_with_empty_array`
- `tests/api/test_phone_mass_extended.py::test_precreate_mass_byphone_with_duplicate_phones`
- `tests/api/test_phone_mass_extended.py::test_precreate_mass_byphone_with_valid_and_invalid_phone`
- `tests/api/test_phone_mass_extended.py::test_precreate_byphone_invalid_formats`
- `tests/api/test_phone_mass_extended.py::test_precreate_mass_byphone_users_are_available_in_get_users`
- `tests/api/test_phone_mass_extended.py::test_resend_for_user_created_by_phone`
- `tests/api/test_phone_mass_extended.py::test_multiple_resend_calls_do_not_return_500`

### `captcha_extended` (3)

- `tests/api/test_captcha_extended.py::test_captcha_exclude_returns_token`
- `tests/api/test_captcha_extended.py::test_captcha_exclude_without_token_is_rejected`
- `tests/api/test_captcha_extended.py::test_captcha_exclude_with_invalid_token_is_rejected`

### `integrator_extended` (7)

- `tests/api/test_integrator_extended.py::test_integrate_user_with_valid_payload`
- `tests/api/test_integrator_extended.py::test_integrate_user_duplicate_external_id`
- `tests/api/test_integrator_extended.py::test_integrate_user_with_invalid_integrator_id`
- `tests/api/test_integrator_extended.py::test_integrate_user_with_invalid_email`
- `tests/api/test_integrator_extended.py::test_code_for_valid_integration_user`
- `tests/api/test_integrator_extended.py::test_code_for_unknown_user_id`
- `tests/api/test_integrator_extended.py::test_code_without_oidc_config`

### `certificates_extended` (15)

- `tests/api/test_certificates_extended.py::test_stable_ip_certificate_is_found_by_skid`
- `tests/api/test_certificates_extended.py::test_stable_ip_certificate_search_with_email_returns_same_user`
- `tests/api/test_certificates_extended.py::test_stable_ip_certificate_search_with_phone_returns_same_user`
- `tests/api/test_certificates_extended.py::test_stable_ip_certificate_seed_organization_exists`
- `tests/api/test_certificates_extended.py::test_stable_ip_certificate_seed_organization_has_expected_data`
- `tests/api/test_certificates_extended.py::test_mutable_ip_certificate_can_be_bound_to_seed_user`
- `tests/api/test_certificates_extended.py::test_mutable_ip_certificate_can_be_bound_to_same_user_twice`
- `tests/api/test_certificates_extended.py::test_mutable_ip_certificate_can_be_reattached_to_another_seed_user`
- `tests/api/test_certificates_extended.py::test_mutable_ip_certificate_can_be_reattached_back_to_owner`
- `tests/api/test_certificates_extended.py::test_reattach_unknown_certificate_skid_returns_client_error`
- `tests/api/test_certificates_extended.py::test_reattach_certificate_to_unknown_user_returns_client_error`
- `tests/api/test_certificates_extended.py::test_bind_certificate_to_unknown_user_returns_client_error`
- `tests/api/test_certificates_extended.py::test_bind_certificate_with_empty_skid_returns_client_error`
- `tests/api/test_certificates_extended.py::test_bind_certificate_with_empty_body_returns_client_error`
- `tests/api/test_certificates_extended.py::test_ul_certificate_scenarios_are_not_prepared_yet`

### Вспомогательные unmarked tests (7)

Это не продуктовые suite-ы, а служебные проверки внутреннего seed/helper слоя:

- `tests/api/test_seed_support.py::test_get_seed_user_returns_expected_values`
- `tests/api/test_seed_support.py::test_get_seed_user_skips_when_required_env_is_missing`
- `tests/api/test_seed_support.py::test_get_seed_organization_returns_expected_values`
- `tests/api/test_seed_support.py::test_get_seed_users_returns_environment_specific_catalog`
- `tests/api/test_seed_support.py::test_get_seed_organizations_returns_environment_specific_catalog`
- `tests/api/test_seed_support.py::test_cleanup_registry_protects_seed_entities`
- `tests/api/test_seed_support.py::test_seed_owner_1_fixture_is_available`

## Правило обновления inventory

Это обязательное правило сопровождения проекта.

Если добавляется, удаляется, переименовывается или переносится любой тест:

1. Обновить раздел `Явный состав suite-ов` в этом файле.
2. Если тест получил новый marker suite, обновить его список именно в этом разделе.
3. Если добавлен новый test-файл или новый suite-marker, сначала добавить marker в `pytest.ini`, потом описать suite в этом файле, затем вписать тесты в inventory.
4. Если тест служебный и не относится к продуктовым suite-ам, его нужно добавить в блок `Вспомогательные unmarked tests`.
5. Если добавлен новый `skip` или `xfail`, нужно обновить документацию:
   - добавить или обновить запись в блоке `Постоянные skip-и и условия включения`, если это осознанно отложенный сценарий;
   - либо явно зафиксировать, что skip условный и зависит от env / credentials;
   - для `xfail` кратко описать backend bug и ожидаемое поведение.

Мини-чек перед коммитом:

- test function добавлен в код
- у теста есть русский комментарий
- suite-marker указан корректно
- inventory в `INTEGRATION_API_TEST_SUITES.md` обновлен
- блоки `Suite-ы, которым нужны seed data`, `Suite-ы, которые меняют persistent state`, `Suite-ы, которые создают новые организации` актуальны
- для нового `skip`/`xfail` обновлена причина и условие активации в документации
