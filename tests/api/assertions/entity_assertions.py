def assert_user_deleted(api_context, api_version_params, user_id, email):
    search_response = api_context.get(
        "/api/integrations/search",
        params={
            **api_version_params,
            "email": email,
        },
    )
    assert search_response.ok, search_response.text()
    search_result = search_response.json()
    assert search_result.get("userIdByEmail") is None

    users_response = api_context.get(
        "/api/integrations/users",
        params={
            **api_version_params,
            "ids": user_id,
        },
    )
    assert users_response.ok, users_response.text()
    users = users_response.json()
    assert all(user["id"] != user_id for user in users)


def assert_organization_exists(api_context, api_version_params, organization_id):
    organizations_response = api_context.get(
        "/api/integrations/organizations",
        params={
            **api_version_params,
            "ids": organization_id,
        },
    )
    assert organizations_response.ok, organizations_response.text()
    organizations = organizations_response.json()
    assert any(item["id"] == organization_id for item in organizations)
