# Copyright (c) Microsoft. All rights reserved.

import json
import sys
from dataclasses import dataclass
from typing import NamedTuple
from unittest.mock import AsyncMock, MagicMock, NonCallableMagicMock, patch

from pytest import fixture, mark, param, raises

from semantic_kernel.connectors.memory.sql_server import (
    QueryBuilder,
    SqlCommand,
    SqlServerCollection,
    SqlServerStore,
    _build_create_table_query,
    _build_delete_query,
    _build_delete_table_query,
    _build_merge_query,
    _build_search_query,
    _build_select_query,
    _build_select_table_names_query,
)
from semantic_kernel.data.const import DistanceFunction, IndexKind
from semantic_kernel.data.record_definition import (
    VectorStoreRecordDataField,
    VectorStoreRecordKeyField,
    VectorStoreRecordVectorField,
)
from semantic_kernel.data.vector_search import VectorSearchFilter, VectorSearchOptions
from semantic_kernel.exceptions.vector_store_exceptions import (
    VectorStoreInitializationException,
    VectorStoreOperationException,
)


class TestQueryBuilder:
    def test_query_builder_append(self):
        qb = QueryBuilder()
        qb.append("SELECT * FROM")
        qb.append(" table", suffix=";")
        result = str(qb).strip()
        assert result == "SELECT * FROM table;"

    def test_query_builder_append_list(self):
        qb = QueryBuilder()
        qb.append_list(["id", "name", "age"], sep=", ", suffix=";")
        result = str(qb).strip()
        assert result == "id, name, age;"

    def test_query_builder_append_table_name(self):
        qb = QueryBuilder()
        qb.append_table_name("dbo", "Users", prefix="SELECT * FROM", suffix=";", newline=False)
        result = str(qb).strip()
        assert result == "SELECT * FROM [dbo].[Users] ;"

    def test_query_builder_remove_last(self):
        qb = QueryBuilder("SELECT * FROM table;")
        qb.remove_last(1)  # remove trailing semicolon
        result = str(qb).strip()
        assert result == "SELECT * FROM table"

    def test_query_builder_in_parenthesis(self):
        qb = QueryBuilder("INSERT INTO table")
        with qb.in_parenthesis():
            qb.append("id, name, age")
        result = str(qb).strip()
        assert result == "INSERT INTO table (id, name, age)"

    def test_query_builder_in_parenthesis_with_prefix_suffix(self):
        qb = QueryBuilder()
        with qb.in_parenthesis(prefix="VALUES", suffix=";"):
            qb.append_list(["1", "'John'", "30"])
        result = str(qb).strip()
        assert result == "VALUES (1, 'John', 30) ;"

    def test_query_builder_in_logical_group(self):
        qb = QueryBuilder()
        with qb.in_logical_group():
            qb.append("UPDATE Users SET name = 'John'")
        result = str(qb).strip()
        lines = result.splitlines()
        assert lines[0] == "BEGIN"
        assert lines[1] == "UPDATE Users SET name = 'John'"
        assert lines[2] == "END"


class TestSqlCommand:
    def test_sql_command_initial_query(self):
        cmd = SqlCommand("SELECT 1")
        assert str(cmd.query) == "SELECT 1"

    def test_sql_command_add_parameter(self):
        cmd = SqlCommand("SELECT * FROM Test WHERE id = ?")
        cmd.add_parameter("42")
        assert cmd.parameters[0] == "42"

    def test_sql_command_add_parameters(self):
        cmd = SqlCommand("SELECT * FROM Test WHERE id = ?")
        cmd.add_parameters(["42", "43"])
        assert cmd.parameters[0] == "42"
        assert cmd.parameters[1] == "43"

    def test_parameter_limit(self):
        cmd = SqlCommand()
        cmd.add_parameters(["42"] * 2100)
        with raises(VectorStoreOperationException):
            cmd.add_parameter("43")
        with raises(VectorStoreOperationException):
            cmd.add_parameters(["43", "44"])


class TestQueryBuildFunctions:
    def test_build_create_table_query(self):
        schema = "dbo"
        table = "Test"
        key_field = VectorStoreRecordKeyField(name="id", property_type="str")
        data_fields = [
            VectorStoreRecordDataField(name="name", property_type="str"),
            VectorStoreRecordDataField(name="age", property_type="int"),
        ]
        vector_fields = [
            VectorStoreRecordVectorField(name="embedding", property_type="float", dimensions=1536),
        ]
        cmd = _build_create_table_query(schema, table, key_field, data_fields, vector_fields)
        assert not cmd.parameters
        cmd_str = str(cmd.query)
        assert (
            cmd_str
            == 'BEGIN\nCREATE TABLE [dbo].[Test] \n ("id" nvarchar(255) NOT NULL,\n"name" nvarchar(max) NULL,\n"age" '
            'int NULL,\n"embedding" VECTOR(1536) NULL,\nPRIMARY KEY (id) \n) ;\nEND\n'
        )

    def test_delete_table_query(self):
        schema = "dbo"
        table = "Test"
        cmd = _build_delete_table_query(schema, table)
        assert str(cmd.query) == f"DROP TABLE IF EXISTS [{schema}].[{table}] ;"

    @mark.parametrize("schema", ["dbo", None])
    def test_build_select_table_names_query(self, schema):
        cmd = _build_select_table_names_query(schema)
        if schema:
            assert cmd.parameters == [schema]
            assert str(cmd) == (
                "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES "
                "WHERE TABLE_TYPE = 'BASE TABLE' "
                "AND (@schema is NULL or TABLE_SCHEMA = ?);"
            )
        else:
            assert str(cmd) == "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE';"

    def test_build_merge_query(self):
        schema = "dbo"
        table = "Test"
        key_field = VectorStoreRecordKeyField(name="id", property_type="str")
        data_fields = [
            VectorStoreRecordDataField(name="name", property_type="str"),
            VectorStoreRecordDataField(name="age", property_type="int"),
        ]
        vector_fields = [
            VectorStoreRecordVectorField(name="embedding", property_type="float", dimensions=5),
        ]
        records = [
            {
                "id": "test",
                "name": "name",
                "age": 50,
                "embedding": [0.1, 0.2, 0.3, 0.4, 0.5],
            }
        ]
        cmd = _build_merge_query(schema, table, key_field, data_fields, vector_fields, records)
        assert cmd.parameters[0] == records[0]["id"]
        assert cmd.parameters[1] == records[0]["name"]
        assert cmd.parameters[2] == str(records[0]["age"])
        assert cmd.parameters[3] == json.dumps(records[0]["embedding"])
        str_cmd = str(cmd)
        assert str_cmd == (
            "DECLARE @UpsertedKeys TABLE (KeyColumn nvarchar(255));\nMERGE INTO [dbo].[Test] AS t\nUSING ( "
            "VALUES  (?, ?, ?, ?) ) AS s (id, name, age, embedding)  ON (t.id = s.id) \nWHEN MATCHED THEN\nUPDATE "
            "SET t.name = s.name, t.age = s.age, t.embedding = s.embedding\nWHEN NOT MATCHED THEN\nINSERT "
            "(id, name, age, embedding)  VALUES (s.id, s.name, s.age, s.embedding)  \nOUTPUT inserted.id "
            "INTO @UpsertedKeys (KeyColumn);\nSELECT KeyColumn FROM @UpsertedKeys;\n"
        )

    def test_build_select_query(self):
        schema = "dbo"
        table = "Test"
        key_field = VectorStoreRecordKeyField(name="id", property_type="str")
        data_fields = [
            VectorStoreRecordDataField(name="name", property_type="str"),
            VectorStoreRecordDataField(name="age", property_type="int"),
        ]
        vector_fields = [
            VectorStoreRecordVectorField(name="embedding", property_type="float", dimensions=5),
        ]
        keys = ["test"]
        cmd = _build_select_query(schema, table, key_field, data_fields, vector_fields, keys)
        assert cmd.parameters == ["test"]
        str_cmd = str(cmd)
        assert str_cmd == "SELECT\nid, name, age, embedding FROM [dbo].[Test] \nWHERE id IN\n (?) ;"

    def test_build_delete_query(self):
        schema = "dbo"
        table = "Test"
        key_field = VectorStoreRecordKeyField(name="id", property_type="str")
        keys = ["test"]
        cmd = _build_delete_query(schema, table, key_field, keys)
        str_cmd = str(cmd)
        assert cmd.parameters[0] == "test"
        assert str_cmd == "DELETE FROM [dbo].[Test] WHERE [id] IN (?) ;"

    def test_build_search_query(self):
        schema = "dbo"
        table = "Test"
        key_field = VectorStoreRecordKeyField(name="id", property_type="str")
        data_fields = [
            VectorStoreRecordDataField(name="name", property_type="str"),
            VectorStoreRecordDataField(name="age", property_type="int"),
        ]
        vector_fields = [
            VectorStoreRecordVectorField(
                name="embedding",
                property_type="float",
                dimensions=5,
                distance_function=DistanceFunction.COSINE_DISTANCE,
            ),
        ]
        vector = [0.1, 0.2, 0.3, 0.4, 0.5]
        options = VectorSearchOptions(
            vector_field_name="embedding",
            filter=VectorSearchFilter.equal_to("age", "30").any_tag_equal_to("name", "test"),
        )
        cmd = _build_search_query(schema, table, key_field, data_fields, vector_fields, vector, options)
        assert cmd.parameters[0] == json.dumps(vector)
        assert cmd.parameters[1] == "30"
        assert cmd.parameters[2] == "test"
        str_cmd = str(cmd)
        assert (
            str_cmd == "SELECT id, name, age, VECTOR_DISTANCE('cosine', embedding, CAST(? AS VECTOR(5))) as "
            "_vector_distance_value\n FROM [dbo].[Test] \nWHERE [age] = ? AND\n? IN [name] \nORDER BY "
            "_vector_distance_value ASC\nOFFSET 0 ROWS FETCH NEXT 3 ROWS ONLY;"
        )


@fixture
async def mock_connection(*args, **kwargs):
    return MagicMock()


@mark.parametrize(
    "connection_string",
    [
        param(
            "Driver={ODBC Driver 18 for SQL Server};Server=localhost;Database=testdb;uid=testuserLongAsMax=yes;",
            id="with uid",
        ),
        param(
            "Driver={ODBC Driver 18 for SQL Server};Server=localhost;Database=testdb;LongAsMax=yes;", id="credential"
        ),
    ],
)
async def test_get_mssql_connection(connection_string):
    mock_pyodbc = NonCallableMagicMock()
    sys.modules["pyodbc"] = mock_pyodbc

    with patch("pyodbc.connect") as patched_connection:
        from azure.identity.aio import DefaultAzureCredential

        from semantic_kernel.connectors.memory.sql_server import SqlSettings, _get_mssql_connection

        token = MagicMock()
        token.token.return_value = "test_token"
        token.token.encode.return_value = b"test_token"
        credential = AsyncMock(spec=DefaultAzureCredential)
        credential.__aenter__.return_value = credential
        credential.get_token.return_value = token

        settings = SqlSettings(connection_string=connection_string)
        with patch("semantic_kernel.connectors.memory.sql_server.DefaultAzureCredential", return_value=credential):
            connection = await _get_mssql_connection(settings)
            assert connection is not None
            assert isinstance(connection, MagicMock)
            if "uid" in connection_string:
                assert patched_connection.call_args.kwargs["attrs_before"] is None
            else:
                assert patched_connection.call_args.kwargs["attrs_before"] == {
                    1256: b"\n\x00\x00\x00test_token",
                }


class TestSqlServerStore:
    async def test_create_store(self, sql_server_unit_test_env):
        store = SqlServerStore()
        assert store is not None
        assert store.settings is not None
        assert store.settings.connection_string is not None
        assert "LongAsMax=yes;" in store.settings.connection_string.get_secret_value()

        with patch("semantic_kernel.connectors.memory.sql_server._get_mssql_connection") as mock_get_connection:
            mock_get_connection.return_value = AsyncMock()
            await store.__aenter__()
            assert store.connection is not None

    @mark.parametrize(
        "override_env_param_dict",
        [
            {
                "SQL_SERVER_CONNECTION_STRING": "Driver={ODBC Driver 18 for SQL Server};Server=localhost;Database=testdb;User Id=testuser;Password=example;LongAsMax=yes;"  # noqa: E501
            }
        ],
        indirect=True,
    )
    def test_create_store_with_long_as_max(self, sql_server_unit_test_env):
        store = SqlServerStore()
        assert store is not None
        assert store.settings is not None
        assert store.settings.connection_string is not None

    @mark.parametrize("exclude_list", ["SQL_SERVER_CONNECTION_STRING"], indirect=True)
    def test_create_without_connection_string(self, sql_server_unit_test_env):
        with raises(VectorStoreInitializationException):
            SqlServerStore(env_file_path="test.env")

    def test_get_collection(self, sql_server_unit_test_env, data_model_definition):
        store = SqlServerStore()
        collection = store.get_collection("test", data_model_type=dict, data_model_definition=data_model_definition)
        assert collection is not None

    async def test_list_collection_names(self, sql_server_unit_test_env, mock_connection):
        async with SqlServerStore(connection=mock_connection) as store:
            mock_connection.cursor.return_value.__enter__.return_value.fetchall.return_value = [
                ["Test1"],
                ["Test2"],
            ]
            collection_names = await store.list_collection_names()
            assert collection_names == ["Test1", "Test2"]

    async def test_no_connection(self, sql_server_unit_test_env):
        store = SqlServerStore()
        with raises(VectorStoreOperationException):
            await store.list_collection_names()


class TestSqlServerCollection:
    @mark.parametrize("exclude_list", ["SQL_SERVER_CONNECTION_STRING"], indirect=True)
    def test_create_without_connection_string(self, sql_server_unit_test_env, data_model_definition):
        with raises(VectorStoreInitializationException):
            SqlServerCollection(
                collection_name="test",
                data_model_type=dict,
                data_model_definition=data_model_definition,
                env_file_path="test.env",
            )

    async def test_create(self, sql_server_unit_test_env, data_model_definition):
        collection = SqlServerCollection(
            collection_name="test", data_model_type=dict, data_model_definition=data_model_definition
        )
        assert collection is not None
        assert collection.collection_name == "test"
        assert collection.settings is not None
        assert collection.settings.connection_string is not None

        with patch("semantic_kernel.connectors.memory.sql_server._get_mssql_connection") as mock_get_connection:
            mock_get_connection.return_value = AsyncMock()
            await collection.__aenter__()
            assert collection.connection is not None

    async def test_upsert(
        self,
        sql_server_unit_test_env,
        mock_connection,
        data_model_definition,
    ):
        collection = SqlServerCollection(
            collection_name="test",
            data_model_type=dict,
            data_model_definition=data_model_definition,
            connection=mock_connection,
        )
        record = {"id": "1", "content": "test", "vector": [0.1, 0.2, 0.3, 0.4, 0.5]}
        mock_connection.cursor.return_value.__enter__.return_value.nextset.side_effect = [True, False]
        mock_connection.cursor.return_value.__enter__.return_value.fetchall.return_value = [
            ["1"],
        ]
        await collection.upsert(record)
        mock_connection.cursor.return_value.__enter__.return_value.execute.assert_called_with(
            (
                "DECLARE @UpsertedKeys TABLE (KeyColumn nvarchar(255));\nMERGE INTO [dbo].[test] AS t\nUSING ( VALUES"
                "  (?, ?, ?) ) AS s (id, content, vector)  ON (t.id = s.id) \nWHEN MATCHED THEN\nUPDATE SET t.content"
                " = s.content, t.vector = s.vector\nWHEN NOT MATCHED THEN\nINSERT (id, content, vector)  VALUES (s.id, "
                "s.content, s.vector)  \nOUTPUT inserted.id INTO @UpsertedKeys (KeyColumn);\nSELECT KeyColumn "
                "FROM @UpsertedKeys;\n"
            ),
            ("1", "test", json.dumps([0.1, 0.2, 0.3, 0.4, 0.5])),
        )

    async def test_get(
        self,
        sql_server_unit_test_env,
        mock_connection,
        data_model_definition,
    ):
        class MockRow(NamedTuple):
            id: str
            content: str
            vector: str

        mock_cursor = MagicMock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor

        collection = SqlServerCollection(
            collection_name="test",
            data_model_type=dict,
            data_model_definition=data_model_definition,
            connection=mock_connection,
        )
        key = "1"

        row = MockRow("1", "test", "[0.1, 0.2, 0.3, 0.4, 0.5]")
        mock_cursor.description = [["id"], ["content"], ["vector"]]

        mock_cursor.__iter__.return_value = [row]
        record = await collection.get(key)
        mock_cursor.execute.assert_called_with(
            "SELECT\nid, content, vector FROM [dbo].[test] \nWHERE id IN\n (?) ;", ("1",)
        )
        assert record["id"] == "1"
        assert record["content"] == "test"
        assert record["vector"] == [0.1, 0.2, 0.3, 0.4, 0.5]

    async def test_delete(
        self,
        sql_server_unit_test_env,
        mock_connection,
        data_model_definition,
    ):
        collection = SqlServerCollection(
            collection_name="test",
            data_model_type=dict,
            data_model_definition=data_model_definition,
            connection=mock_connection,
        )
        key = "1"
        await collection.delete(key)
        mock_connection.cursor.return_value.__enter__.return_value.execute.assert_called_with(
            "DELETE FROM [dbo].[test] WHERE [id] IN (?) ;", ("1",)
        )

    async def test_search(
        self,
        sql_server_unit_test_env,
        mock_connection,
        data_model_definition,
    ):
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        data_model_definition.fields["vector"].distance_function = DistanceFunction.COSINE_DISTANCE
        collection = SqlServerCollection(
            collection_name="test",
            data_model_type=dict,
            data_model_definition=data_model_definition,
            connection=mock_connection,
        )
        vector = [0.1, 0.2, 0.3, 0.4, 0.5]
        options = VectorSearchOptions(vector_field_name="vector", filter=VectorSearchFilter.equal_to("content", "test"))

        @dataclass
        class MockRow:
            id: str
            content: str
            _vector_distance_value: float

        row = MockRow("1", "test", 0.1)
        mock_cursor.description = [["id"], ["content"], ["_vector_distance_value"]]

        mock_cursor.__iter__.return_value = [row]
        search_result = await collection.vectorized_search(vector, options)
        async for record in search_result.results:
            assert record.record["id"] == "1"
            assert record.record["content"] == "test"
            assert record.score == 0.1
        mock_cursor.execute.assert_called_with(
            (
                "SELECT id, content, VECTOR_DISTANCE('cosine', vector, CAST(? AS VECTOR(5))) as "
                "_vector_distance_value\n FROM [dbo].[test] \nWHERE [content] = ? \nORDER BY _vector_distance_value "
                "ASC\nOFFSET 0 ROWS FETCH NEXT 3 ROWS ONLY;"
            ),
            (json.dumps(vector), "test"),
        )

    async def test_create_collection(
        self,
        sql_server_unit_test_env,
        mock_connection,
        data_model_definition,
    ):
        data_model_definition.fields["vector"].index_kind = IndexKind.FLAT
        collection = SqlServerCollection(
            collection_name="test",
            data_model_type=dict,
            data_model_definition=data_model_definition,
            connection=mock_connection,
        )
        await collection.create_collection()
        mock_connection.cursor.return_value.__enter__.return_value.execute.assert_called_with(
            (
                "IF OBJECT_ID(N' [dbo].[test] ', N'U') IS NULL\nBEGIN\nCREATE TABLE [dbo].[test] \n (\"id\" nvarchar"
                '(255) NOT NULL,\n"content" nvarchar(max) NULL,\n"vector" VECTOR(5) NULL,\nPRIMARY KEY (id) \n) ;'
                "\nEND\n"
            ),
            (),
        )

    async def test_delete_collection(
        self,
        sql_server_unit_test_env,
        mock_connection,
        data_model_definition,
    ):
        collection = SqlServerCollection(
            collection_name="test",
            data_model_type=dict,
            data_model_definition=data_model_definition,
            connection=mock_connection,
        )
        await collection.delete_collection()
        mock_connection.cursor.return_value.__enter__.return_value.execute.assert_called_with(
            "DROP TABLE IF EXISTS [dbo].[test] ;", ()
        )

    async def test_no_connection(self, sql_server_unit_test_env, data_model_definition):
        collection = SqlServerCollection(
            collection_name="test",
            data_model_type=dict,
            data_model_definition=data_model_definition,
        )
        with raises(VectorStoreOperationException):
            await collection.create_collection()
        with raises(VectorStoreOperationException):
            await collection.delete_collection()
        with raises(VectorStoreOperationException):
            await collection.does_collection_exist()
        with raises(VectorStoreOperationException):
            await collection.upsert({"id": "1", "content": "test", "vector": [0.1, 0.2, 0.3, 0.4, 0.5]})
        with raises(VectorStoreOperationException):
            await collection.get("1")
        with raises(VectorStoreOperationException):
            await collection.delete("1")
        with raises(VectorStoreOperationException):
            await collection.vectorized_search([0.1, 0.2, 0.3, 0.4, 0.5], VectorSearchOptions())
