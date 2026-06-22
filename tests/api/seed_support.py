SEED_USER_CONFIGS = {
    "seed_owner_1": {
        "required": [
            "seed_owner_1_user_id",
            "seed_owner_1_email",
        ],
        "optional": [
            "seed_owner_1_phone",
        ],
    },
    "seed_owner_2": {
        "required": [
            "seed_owner_2_user_id",
            "seed_owner_2_email",
        ],
        "optional": [
            "seed_owner_2_phone",
        ],
    },
    "seed_employee_1": {
        "required": [
            "seed_employee_1_user_id",
            "seed_employee_1_email",
        ],
        "optional": [
            "seed_employee_1_phone",
        ],
    },
    "seed_employee_2": {
        "required": [
            "seed_employee_2_user_id",
            "seed_employee_2_email",
        ],
        "optional": [
            "seed_employee_2_phone",
        ],
    },
    "seed_ip_user": {
        "required": [
            "seed_ip_user_id",
            "seed_ip_user_email",
            "seed_ip_org_id",
            "seed_ip_cert_skid",
        ],
        "optional": [
            "seed_ip_user_phone",
        ],
    },
    "seed_ul_user": {
        "required": [
            "seed_ul_user_id",
            "seed_ul_user_email",
            "seed_ul_org_id",
            "seed_ul_cert_skid",
        ],
        "optional": [],
    },
}

SEED_ORGANIZATION_CONFIGS = {
    "seed_org_1": {
        "required": [
            "seed_org_1_id",
            "seed_org_1_inn",
            "seed_org_1_kpp",
        ],
        "optional": [],
    },
    "seed_org_2": {
        "required": [
            "seed_org_2_id",
            "seed_org_2_inn",
            "seed_org_2_kpp",
        ],
        "optional": [],
    },
}


def _get_target_env(settings):
    return settings.get("target_env", "")


def _extract_seed_alias_name(seed_name):
    if seed_name.startswith("seed_"):
        return seed_name[len("seed_"):]
    return seed_name


def _build_seed_entity(settings, seed_name, config, entity_type, pytest_module):
    missing_keys = [key for key in config["required"] if not settings.get(key)]
    if missing_keys:
        target_env = _get_target_env(settings) or "<unknown>"
        pytest_module.skip(
            f"Seed {entity_type} '{seed_name}' is not configured for environment "
            f"'{target_env}'. Fill env variables: {', '.join(missing_keys)}"
        )

    entity = {
        "seed_name": seed_name,
        "target_env": _get_target_env(settings),
    }
    for key in config["required"] + config["optional"]:
        value = settings.get(key, "")
        if value:
            entity[key] = value

    return entity


def _add_user_aliases(entity):
    seed_alias = _extract_seed_alias_name(entity["seed_name"])

    entity["alias"] = seed_alias
    entity["user_id"] = entity.get(f"{entity['seed_name']}_user_id", "")
    entity["email"] = entity.get(f"{entity['seed_name']}_email", "")
    entity["phone"] = entity.get(f"{entity['seed_name']}_phone", "")

    return entity


def _add_organization_aliases(entity):
    seed_alias = _extract_seed_alias_name(entity["seed_name"])

    entity["alias"] = seed_alias
    entity["organization_id"] = entity.get(f"{entity['seed_name']}_id", "")
    entity["inn"] = entity.get(f"{entity['seed_name']}_inn", "")
    entity["kpp"] = entity.get(f"{entity['seed_name']}_kpp", "")

    return entity


def get_seed_user(settings, seed_name, pytest_module):
    if seed_name not in SEED_USER_CONFIGS:
        raise KeyError(f"Unknown seed user: {seed_name}")

    entity = _build_seed_entity(
        settings=settings,
        seed_name=seed_name,
        config=SEED_USER_CONFIGS[seed_name],
        entity_type="user",
        pytest_module=pytest_module,
    )
    return _add_user_aliases(entity)


def get_seed_organization(settings, seed_name, pytest_module):
    if seed_name not in SEED_ORGANIZATION_CONFIGS:
        raise KeyError(f"Unknown seed organization: {seed_name}")

    entity = _build_seed_entity(
        settings=settings,
        seed_name=seed_name,
        config=SEED_ORGANIZATION_CONFIGS[seed_name],
        entity_type="organization",
        pytest_module=pytest_module,
    )
    return _add_organization_aliases(entity)


def get_seed_users(settings, pytest_module):
    return {
        seed_name: get_seed_user(settings, seed_name, pytest_module)
        for seed_name in (
            "seed_owner_1",
            "seed_owner_2",
            "seed_employee_1",
            "seed_employee_2",
        )
    }


def get_seed_organizations(settings, pytest_module):
    return {
        seed_name: get_seed_organization(settings, seed_name, pytest_module)
        for seed_name in (
            "seed_org_1",
            "seed_org_2",
        )
    }


def collect_seed_protection(settings):
    protected = {
        "emails": set(),
        "user_ids": set(),
        "organization_ids": set(),
    }

    for config in SEED_USER_CONFIGS.values():
        email_keys = [
            key for key in config["required"] + config["optional"] if key.endswith("_email")
        ]
        user_id_keys = [
            key for key in config["required"] + config["optional"] if key.endswith("_user_id")
        ]

        for key in email_keys:
            if settings.get(key):
                protected["emails"].add(settings[key])

        for key in user_id_keys:
            if settings.get(key):
                protected["user_ids"].add(settings[key])

    for config in SEED_ORGANIZATION_CONFIGS.values():
        organization_id_keys = [
            key for key in config["required"] + config["optional"] if key.endswith("_id")
        ]
        for key in organization_id_keys:
            if settings.get(key):
                protected["organization_ids"].add(settings[key])

    return protected
