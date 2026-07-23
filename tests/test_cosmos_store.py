from app.database.cosmos import CosmosStore


def test_memory_store_persists_users_and_scopes_reports_by_user() -> None:
    repository = CosmosStore()

    repository.create_user("analyst@example.com", "password-hash")
    repository.save_report("analyst@example.com", {"title": "Analyst report"})
    repository.save_report("other@example.com", {"title": "Other report"})

    assert repository.get_user("analyst@example.com")["password"] == "password-hash"
    assert [item["title"] for item in repository.list_reports("analyst@example.com")] == ["Analyst report"]
    assert [item["title"] for item in repository.list_reports("other@example.com")] == ["Other report"]


def test_memory_store_rejects_duplicate_users() -> None:
    repository = CosmosStore()
    repository.create_user("duplicate@example.com", "password-hash")

    try:
        repository.create_user("duplicate@example.com", "another-hash")
    except ValueError as exc:
        assert str(exc) == "User already exists"
    else:
        raise AssertionError("duplicate user was accepted")
