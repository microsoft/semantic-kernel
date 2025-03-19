# Copyright (c) Microsoft. All rights reserved.

import json

from pytest import mark, skip

from semantic_kernel.data.const import DistanceFunction
from semantic_kernel.data.record_definition.vector_store_record_fields import (
    VectorStoreRecordDataField,
    VectorStoreRecordKeyField,
    VectorStoreRecordVectorField,
)
from semantic_kernel.data.vector_search.vector_search_filter import VectorSearchFilter
from semantic_kernel.data.vector_search.vector_search_options import VectorSearchOptions

try:
    from semantic_kernel.connectors.memory.sql_server import (
        QueryBuilder,
        SqlCommand,
        SqlServerStore,
        _build_create_table_query,
        _build_delete_query,
        _build_delete_table_query,
        _build_merge_query,
        _build_search_query,
        _build_select_query,
        _build_select_table_names_query,
    )
except ImportError:
    skip(
        reason="pyodbc or underlying drivers are not installed. Please install it to run SQL Server tests."
    )  # pragma: no cover


def test_query_builder_append():
    qb = QueryBuilder()
    qb.append("SELECT * FROM")
    qb.append(" table", suffix=";")
    result = str(qb).strip()
    assert result == "SELECT * FROM table;"


def test_query_builder_append_list():
    qb = QueryBuilder()
    qb.append_list(["id", "name", "age"], sep=", ", suffix=";")
    result = str(qb).strip()
    assert result == "id, name, age;"


def test_query_builder_append_table_name():
    qb = QueryBuilder()
    qb.append_table_name("dbo", "Users", prefix="SELECT * FROM", suffix=";", newline=False)
    result = str(qb).strip()
    assert result == "SELECT * FROM [dbo].[Users] ;"


def test_query_builder_remove_last():
    qb = QueryBuilder("SELECT * FROM table;")
    qb.remove_last(1)  # remove trailing semicolon
    result = str(qb).strip()
    assert result == "SELECT * FROM table"


def test_query_builder_in_parenthesis():
    qb = QueryBuilder("INSERT INTO table")
    with qb.in_parenthesis():
        qb.append("id, name, age")
    result = str(qb).strip()
    assert result == "INSERT INTO table (id, name, age)"


def test_query_builder_in_parenthesis_with_prefix_suffix():
    qb = QueryBuilder()
    with qb.in_parenthesis(prefix="VALUES", suffix=";"):
        qb.append_list(["1", "'John'", "30"])
    result = str(qb).strip()
    assert result == "VALUES (1, 'John', 30) ;"


def test_query_builder_in_logical_group():
    qb = QueryBuilder()
    with qb.in_logical_group():
        qb.append("UPDATE Users SET name = 'John'")
    result = str(qb).strip()
    lines = result.splitlines()
    assert lines[0] == "BEGIN"
    assert lines[1] == "UPDATE Users SET name = 'John'"
    assert lines[2] == "END"


def test_sql_command_initial_query():
    cmd = SqlCommand("SELECT 1")
    assert str(cmd.query) == "SELECT 1"


def test_sql_command_add_parameter():
    cmd = SqlCommand("SELECT * FROM Test WHERE id = ?")
    cmd.add_parameter("42")
    assert cmd.parameters[0] == "42"


def test_sql_command_add_many_parameter():
    cmd = SqlCommand("SELECT * FROM Test WHERE name = ?", execute_many=True)
    cmd.add_parameter("Alice")
    assert cmd.many_parameters[0] == ("Alice",)
    cmd.add_parameter("Bob")
    assert cmd.many_parameters[0] == (
        "Alice",
        "Bob",
    )


def test_sql_command_add_many_parameters():
    cmd = SqlCommand("SELECT * FROM Test WHERE name = ?", execute_many=True)
    cmd.add_parameters(("Alice",))
    assert cmd.many_parameters[0] == ("Alice",)
    cmd.add_parameter("Bob")
    assert cmd.many_parameters[0] == (
        "Alice",
        "Bob",
    )


def test_sql_command_add_many_parameters_twice():
    cmd = SqlCommand("SELECT * FROM Test WHERE name = ?", execute_many=True)
    cmd.add_parameters(("Alice",))
    assert cmd.many_parameters[0] == ("Alice",)
    cmd.add_parameters(("Bob",))
    assert cmd.many_parameters[0] == ("Alice",)
    assert cmd.many_parameters[1] == ("Bob",)
    cmd.add_parameter("Charlie")
    assert cmd.many_parameters[0] == (
        "Alice",
        "Charlie",
    )
    assert cmd.many_parameters[1] == (
        "Bob",
        "Charlie",
    )


def test_build_create_table_query():
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


def test_delete_table_query():
    schema = "dbo"
    table = "Test"
    cmd = _build_delete_table_query(schema, table)
    assert str(cmd.query) == f"DROP TABLE IF EXISTS [{schema}].[{table}] ;"


@mark.parametrize("schema", ["dbo", None])
def test_build_select_table_names_query(schema):
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


def test_build_merge_query():
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
        "SET t.name = s.name, t.age = s.age, t.embedding = s.embedding\nWHEN NOT MATCHED THEN\nINSERT (id, name, age, "
        "embedding)  VALUES (s.id, s.name, s.age, s.embedding)  \nOUTPUT inserted.id INTO @UpsertedKeys (KeyColumn);\n"
        "SELECT KeyColumn FROM @UpsertedKeys;\n"
    )


def test_build_select_query():
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


def test_build_delete_query():
    schema = "dbo"
    table = "Test"
    key_field = VectorStoreRecordKeyField(name="id", property_type="str")
    keys = ["test"]
    cmd = _build_delete_query(schema, table, key_field, keys)
    str_cmd = str(cmd)
    assert cmd.parameters[0] == "test"
    assert str_cmd == "DELETE FROM [dbo].[Test] WHERE [id] IN (?) ;"


def test_build_search_query():
    schema = "dbo"
    table = "Test"
    key_field = VectorStoreRecordKeyField(name="id", property_type="str")
    data_fields = [
        VectorStoreRecordDataField(name="name", property_type="str"),
        VectorStoreRecordDataField(name="age", property_type="int"),
    ]
    vector_fields = [
        VectorStoreRecordVectorField(
            name="embedding", property_type="float", dimensions=5, distance_function=DistanceFunction.COSINE_DISTANCE
        ),
    ]
    vector = [0.1, 0.2, 0.3, 0.4, 0.5]
    options = VectorSearchOptions(
        vector_field_name="embedding", filter=VectorSearchFilter.equal_to("age", "30").any_tag_equal_to("name", "test")
    )
    cmd = _build_search_query(schema, table, key_field, data_fields, vector_fields, vector, options)
    assert cmd.parameters[0] == json.dumps(vector)
    str_cmd = str(cmd)
    assert (
        str_cmd
        == "SELECT id, name, age, VECTOR_DISTANCE('cosine', embedding, CAST(? AS VECTOR(5))) as _vector_distance_value"
        "\n FROM [dbo].[Test] \nWHERE [age] = '30' AND\n'test' IN [name] \nORDER BY _vector_distance_value ASC\nOFFSET "
        "0 ROWS FETCH NEXT 3 ROWS ONLY;"
    )


def test_create_store(sql_server_unit_test_env):
    store = SqlServerStore()
    assert store is not None
    assert store.settings is not None
    assert store.settings.connection_string is not None


def test_create_collection(sql_server_unit_test_env, data_model_definition):
    store = SqlServerStore()
    collection = store.get_collection("test", data_model_type=dict, data_model_definition=data_model_definition)
    assert collection is not None
