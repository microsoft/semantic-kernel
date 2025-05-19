# Copyright (c) Microsoft. All rights reserved.

from _pytest.mark.structures import ParameterSet
from pytest import fixture, param

from semantic_kernel.exceptions.vector_store_exceptions import VectorStoreOperationException


@fixture()
def mongodb_atlas_unit_test_env(monkeypatch, exclude_list, override_env_param_dict):
    """Fixture to set environment variables for MongoDB Atlas Unit Tests."""
    if exclude_list is None:
        exclude_list = []

    if override_env_param_dict is None:
        override_env_param_dict = {}

    env_vars = {"MONGODB_ATLAS_CONNECTION_STRING": "mongodb://test", "MONGODB_ATLAS_DATABASE_NAME": "test-database"}

    env_vars.update(override_env_param_dict)

    for key, value in env_vars.items():
        if key not in exclude_list:
            monkeypatch.setenv(key, value)
        else:
            monkeypatch.delenv(key, raising=False)

    return env_vars


@fixture
def postgres_unit_test_env(monkeypatch, exclude_list, override_env_param_dict):
    """Fixture to set environment variables for Postgres connector."""
    if exclude_list is None:
        exclude_list = []

    if override_env_param_dict is None:
        override_env_param_dict = {}

    env_vars = {"POSTGRES_CONNECTION_STRING": "host=localhost port=5432 dbname=postgres user=testuser password=example"}

    env_vars.update(override_env_param_dict)

    for key, value in env_vars.items():
        if key not in exclude_list:
            monkeypatch.setenv(key, value)
        else:
            monkeypatch.delenv(key, raising=False)

    return env_vars


@fixture
def qdrant_unit_test_env(monkeypatch, exclude_list, override_env_param_dict):
    """Fixture to set environment variables for QdrantConnector."""
    if exclude_list is None:
        exclude_list = []

    if override_env_param_dict is None:
        override_env_param_dict = {}

    env_vars = {"QDRANT_LOCATION": "http://localhost:6333"}

    env_vars.update(override_env_param_dict)

    for key, value in env_vars.items():
        if key not in exclude_list:
            monkeypatch.setenv(key, value)
        else:
            monkeypatch.delenv(key, raising=False)

    return env_vars


@fixture
def redis_unit_test_env(monkeypatch, exclude_list, override_env_param_dict):
    """Fixture to set environment variables for Redis."""
    if exclude_list is None:
        exclude_list = []

    if override_env_param_dict is None:
        override_env_param_dict = {}

    env_vars = {"REDIS_CONNECTION_STRING": "redis://localhost:6379"}

    env_vars.update(override_env_param_dict)

    for key, value in env_vars.items():
        if key not in exclude_list:
            monkeypatch.setenv(key, value)
        else:
            monkeypatch.delenv(key, raising=False)

    return env_vars


@fixture
def pinecone_unit_test_env(monkeypatch, exclude_list, override_env_param_dict):
    """Fixture to set environment variables for Pinecone."""
    if exclude_list is None:
        exclude_list = []

    if override_env_param_dict is None:
        override_env_param_dict = {}

    env_vars = {"PINECONE_API_KEY": "test_key"}

    env_vars.update(override_env_param_dict)

    for key, value in env_vars.items():
        if key not in exclude_list:
            monkeypatch.setenv(key, value)
        else:
            monkeypatch.delenv(key, raising=False)

    return env_vars


@fixture
def sql_server_unit_test_env(monkeypatch, exclude_list, override_env_param_dict):
    """Fixture to set environment variables for SQL Server."""
    if exclude_list is None:
        exclude_list = []

    if override_env_param_dict is None:
        override_env_param_dict = {}

    env_vars = {
        "SQL_SERVER_CONNECTION_STRING": "Driver={ODBC Driver 18 for SQL Server};Server=localhost;Database=testdb;User Id=testuser;Password=example;"  # noqa: E501
    }

    env_vars.update(override_env_param_dict)

    for key, value in env_vars.items():
        if key not in exclude_list:
            monkeypatch.setenv(key, value)
        else:
            monkeypatch.delenv(key, raising=False)

    return env_vars


def filter_lambda_list(store: str) -> list[ParameterSet]:
    """Fixture to provide a list of filter lambdas for testing."""
    sets = [
        (
            lambda x: x.content == "value",
            {
                "ai_search": "content eq 'value'",
            },
            "equal with string",
        ),
        (
            lambda x: x.id == 0,
            {
                "ai_search": "id eq 0",
            },
            "equal with int",
        ),
        (
            lambda x: x.content != "value",
            {
                "ai_search": "content ne 'value'",
            },
            "not equal",
        ),
        (
            lambda x: x.id > 0,
            {
                "ai_search": "id gt 0",
            },
            "greater than",
        ),
        (
            lambda x: x.id >= 0,
            {
                "ai_search": "id ge 0",
            },
            "greater than or equal",
        ),
        (
            lambda x: x.id == +0,
            {
                "ai_search": "id eq +0",
            },
            "equal with explicit positive",
        ),
        (
            lambda x: x.id < 0,
            {
                "ai_search": "id lt 0",
            },
            "less than",
        ),
        (
            lambda x: x.id <= 0,
            {
                "ai_search": "id le 0",
            },
            "less than or equal",
        ),
        (
            lambda x: -10 <= x.id <= 0,
            {
                "ai_search": "(-10 le id and id le 0)",
            },
            "between inclusive",
        ),
        (
            lambda x: -10 < x.id < 0,
            {
                "ai_search": "(-10 lt id and id lt 0)",
            },
            "between exclusive",
        ),
        (
            lambda x: x.content == "value" and x.id == 0,
            {
                "ai_search": "(content eq 'value' and id eq 0)",
            },
            "and",
        ),
        (
            lambda x: x.content == "value" or x.id == 0,
            {
                "ai_search": "(content eq 'value' or id eq 0)",
            },
            "or",
        ),
        (
            lambda x: not x.content,
            {
                "ai_search": "not content",
            },
            "not with truthy",
        ),
        (
            lambda x: not (x.content == "value"),  # noqa: SIM201
            {
                "ai_search": "not content eq 'value'",
            },
            "not with equal",
        ),
        (
            lambda x: not (x.content != "value"),  # noqa: SIM202
            {
                "ai_search": "not content ne 'value'",
            },
            "not with not equal",
        ),
        (
            lambda x: "value" in x.content,
            {
                "ai_search": "search.ismatch('value', 'content')",
            },
            "contains",
        ),
        (
            lambda x: "value" not in x.content,
            {
                "ai_search": "not search.ismatch('value', 'content')",
            },
            "not contains",
        ),
        (
            lambda x: (x.id > 0 and x.id < 3) or (x.id > 7 and x.id < 10),
            {
                "ai_search": "((id gt 0 and id lt 3) or (id gt 7 and id lt 10))",
            },
            "complex",
        ),
        (
            lambda x: x.unknown_field == "value",
            {
                "ai_search": VectorStoreOperationException,
            },
            "fail unknown field",
        ),
        (
            lambda x: any(x == "a" for x in x.content),
            {
                "ai_search": NotImplementedError,
            },
            "comprehension",
        ),
        (
            lambda x: ~x.id,
            {
                "ai_search": NotImplementedError,
            },
            "invert",
        ),
        (
            lambda x: constant,  # noqa: F821
            {
                "ai_search": NotImplementedError,
            },
            "constant",
        ),
        (
            lambda x: x.content.city == "Seattle",
            {
                "ai_search": "content/city eq 'Seattle'",
            },
            "nested property",
        ),
    ]
    return [param(s[0], s[1][store], id=s[2]) for s in sets if store in s[1]]
