// Copyright (c) Microsoft. All rights reserved.

using System.Text;
using Microsoft.Data.SqlClient;
using Microsoft.Extensions.VectorData;
using Microsoft.Extensions.VectorData.ConnectorSupport;
using Microsoft.SemanticKernel.Connectors.SqlServer;
using Xunit;

namespace SqlServerIntegrationTests;

public class SqlServerCommandBuilderTests
{
    [Theory]
    [InlineData("schema", "name", "[schema].[name]")]
    [InlineData(null, "name", "[name]")]
    [InlineData("schema", "[brackets]", "[schema].[[brackets]]]")]
    [InlineData(null, "[needsEscaping]", "[[needsEscaping]]]")]
    [InlineData("needs]escaping", "[brackets]", "[needs]]escaping].[[brackets]]]")]
    public void AppendTableName(string? schema, string table, string expectedFullName)
    {
        StringBuilder result = new();

        SqlServerCommandBuilder.AppendTableName(result, schema, table);

        Assert.Equal(expectedFullName, result.ToString());
    }

    [Theory]
    [InlineData("name", "@name_")] // typical name
    [InlineData("na me", "@na_")] // contains a whitespace, an illegal parameter name character
    [InlineData("123", "@_")] // starts with a digit, also not allowed
    [InlineData("ĄŻŚĆ_doesNotStartWithAscii", "@_")] // starts with a non-ASCII character
    public void AppendParameterName(string propertyName, string expectedPrefix)
    {
        StringBuilder builder = new();
        StringBuilder expectedBuilder = new();
        VectorStoreRecordKeyPropertyModel keyProperty = new(propertyName, typeof(string));

        int paramIndex = 0; // we need a dedicated variable to ensure that AppendParameterName increments the index
        for (int i = 0; i < 10; i++)
        {
            Assert.Equal(paramIndex, i);
            SqlServerCommandBuilder.AppendParameterName(builder, keyProperty, ref paramIndex, out string parameterName);
            Assert.Equal($"{expectedPrefix}{i}", parameterName);
            expectedBuilder.Append(parameterName);
        }

        Assert.Equal(expectedBuilder.ToString(), builder.ToString());
    }

    [Theory]
    [InlineData("schema", "simpleName", "[simpleName]")]
    [InlineData("schema", "[needsEscaping]", "[[needsEscaping]]]")]
    public void DropTable(string schema, string table, string expectedTable)
    {
        using SqlConnection connection = CreateConnection();

        using SqlCommand command = SqlServerCommandBuilder.DropTableIfExists(connection, schema, table);

        Assert.Equal($"DROP TABLE IF EXISTS [{schema}].{expectedTable}", command.CommandText);
    }

    [Theory]
    [InlineData("schema", "simpleName")]
    [InlineData("schema", "[needsEscaping]")]
    public void SelectTableName(string schema, string table)
    {
        using SqlConnection connection = CreateConnection();

        using SqlCommand command = SqlServerCommandBuilder.SelectTableName(connection, schema, table);

        Assert.Equal(
        """
        SELECT TABLE_NAME
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_TYPE = 'BASE TABLE'
            AND (@schema is NULL or TABLE_SCHEMA = @schema)
            AND TABLE_NAME = @tableName
        """
        , command.CommandText);
        Assert.Equal(schema, command.Parameters[0].Value);
        Assert.Equal(table, command.Parameters[1].Value);
    }

    [Fact]
    public void SelectTableNames()
    {
        const string SchemaName = "theSchemaName";
        using SqlConnection connection = CreateConnection();

        using SqlCommand command = SqlServerCommandBuilder.SelectTableNames(connection, SchemaName);

        Assert.Equal(
        """
        SELECT TABLE_NAME
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_TYPE = 'BASE TABLE'
            AND (@schema is NULL or TABLE_SCHEMA = @schema)
        """
        , command.CommandText);
        Assert.Equal(SchemaName, command.Parameters[0].Value);
        Assert.Equal("@schema", command.Parameters[0].ParameterName);
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public void CreateTable(bool ifNotExists)
    {
        var model = BuildModel(
            [
                new VectorStoreRecordKeyProperty("id", typeof(long)),
                new VectorStoreRecordDataProperty("simpleName", typeof(string)),
                new VectorStoreRecordDataProperty("with space", typeof(int)) { IsIndexed = true },
                new VectorStoreRecordVectorProperty("embedding", typeof(ReadOnlyMemory<float>), 10)
            ]);

        using SqlConnection connection = CreateConnection();

        using SqlCommand command = SqlServerCommandBuilder.CreateTable(connection, "schema", "table", ifNotExists, model);

        string expectedCommand =
        """
        BEGIN
        CREATE TABLE [schema].[table] (
        [id] BIGINT NOT NULL,
        [simpleName] NVARCHAR(MAX),
        [with space] INT,
        [embedding] VECTOR(10),
        PRIMARY KEY ([id])
        );
        CREATE INDEX index_table_withspace ON [schema].[table]([with space]);
        END;
        """;
        if (ifNotExists)
        {
            expectedCommand = "IF OBJECT_ID(N'[schema].[table]', N'U') IS NULL" + Environment.NewLine + expectedCommand;
        }

        Assert.Equal(expectedCommand, command.CommandText, ignoreLineEndingDifferences: true);
    }

    [Fact]
    public void MergeIntoSingle()
    {
        var model = BuildModel(
            [
                new VectorStoreRecordKeyProperty("id", typeof(long)),
                new VectorStoreRecordDataProperty("simpleString", typeof(string)),
                new VectorStoreRecordDataProperty("simpleInt", typeof(int)),
                new VectorStoreRecordVectorProperty("embedding", typeof(ReadOnlyMemory<float>), 10)
            ]);

        using SqlConnection connection = CreateConnection();
        using SqlCommand command = SqlServerCommandBuilder.MergeIntoSingle(connection, "schema", "table", model,
            new Dictionary<string, object?>
            {
                { "id", null },
                { "simpleString", "nameValue" },
                { "simpleInt", 134 },
                { "embedding", "{ 10.0 }" }
            });

        string expectedCommand =
        """"
        MERGE INTO [schema].[table] AS t
        USING (VALUES (@id_0,@simpleString_1,@simpleInt_2,@embedding_3)) AS s ([id],[simpleString],[simpleInt],[embedding])
        ON (t.[id] = s.[id])
        WHEN MATCHED THEN
        UPDATE SET t.[simpleString] = s.[simpleString],t.[simpleInt] = s.[simpleInt],t.[embedding] = s.[embedding]
        WHEN NOT MATCHED THEN
        INSERT ([id],[simpleString],[simpleInt],[embedding])
        VALUES (s.[id],s.[simpleString],s.[simpleInt],s.[embedding])
        OUTPUT inserted.[id];
        """";

        Assert.Equal(expectedCommand, command.CommandText, ignoreLineEndingDifferences: true);
        Assert.Equal("@id_0", command.Parameters[0].ParameterName);
        Assert.Equal(DBNull.Value, command.Parameters[0].Value);
        Assert.Equal("@simpleString_1", command.Parameters[1].ParameterName);
        Assert.Equal("nameValue", command.Parameters[1].Value);
        Assert.Equal("@simpleInt_2", command.Parameters[2].ParameterName);
        Assert.Equal(134, command.Parameters[2].Value);
        Assert.Equal("@embedding_3", command.Parameters[3].ParameterName);
        Assert.Equal("{ 10.0 }", command.Parameters[3].Value);
    }

    [Fact]
    public void MergeIntoMany()
    {
        var model = BuildModel(
            [
                new VectorStoreRecordKeyProperty("id", typeof(long)),
                new VectorStoreRecordDataProperty("simpleString", typeof(string)),
                new VectorStoreRecordDataProperty("simpleInt", typeof(int)),
                new VectorStoreRecordVectorProperty("embedding", typeof(ReadOnlyMemory<float>), 10)
            ]);

        Dictionary<string, object?>[] records =
        [
            new Dictionary<string, object?>
            {
                { "id", 0L },
                { "simpleString", "nameValue0" },
                { "simpleInt", 134 },
                { "embedding", "{ 10.0 }" }
            },
            new Dictionary<string, object?>
            {
                { "id", 1L },
                { "simpleString", "nameValue1" },
                { "simpleInt", 135 },
                { "embedding", "{ 11.0 }" }
            }
        ];

        using SqlConnection connection = CreateConnection();
        using SqlCommand command = connection.CreateCommand();

        Assert.True(SqlServerCommandBuilder.MergeIntoMany(command, "schema", "table", model, records));

        string expectedCommand =
        """"
        DECLARE @InsertedKeys TABLE (KeyColumn BIGINT);
        MERGE INTO [schema].[table] AS t
        USING (VALUES
        (@id_0,@simpleString_1,@simpleInt_2,@embedding_3),
        (@id_4,@simpleString_5,@simpleInt_6,@embedding_7)) AS s ([id],[simpleString],[simpleInt],[embedding])
        ON (t.[id] = s.[id])
        WHEN MATCHED THEN
        UPDATE SET t.[simpleString] = s.[simpleString],t.[simpleInt] = s.[simpleInt],t.[embedding] = s.[embedding]
        WHEN NOT MATCHED THEN
        INSERT ([id],[simpleString],[simpleInt],[embedding])
        VALUES (s.[id],s.[simpleString],s.[simpleInt],s.[embedding])
        OUTPUT inserted.[id] INTO @InsertedKeys (KeyColumn);
        SELECT KeyColumn FROM @InsertedKeys;
        """";

        Assert.Equal(expectedCommand, command.CommandText, ignoreLineEndingDifferences: true);

        for (int i = 0; i < records.Length; i++)
        {
            Assert.Equal($"@id_{4 * i + 0}", command.Parameters[4 * i + 0].ParameterName);
            Assert.Equal((long)i, command.Parameters[4 * i + 0].Value);
            Assert.Equal($"@simpleString_{4 * i + 1}", command.Parameters[4 * i + 1].ParameterName);
            Assert.Equal($"nameValue{i}", command.Parameters[4 * i + 1].Value);
            Assert.Equal($"@simpleInt_{4 * i + 2}", command.Parameters[4 * i + 2].ParameterName);
            Assert.Equal(134 + i, command.Parameters[4 * i + 2].Value);
            Assert.Equal($"@embedding_{4 * i + 3}", command.Parameters[4 * i + 3].ParameterName);
            Assert.Equal($"{{ 1{i}.0 }}", command.Parameters[4 * i + 3].Value);
        }
    }

    [Fact]
    public void DeleteSingle()
    {
        VectorStoreRecordKeyPropertyModel keyProperty = new("id", typeof(long));
        using SqlConnection connection = CreateConnection();

        using SqlCommand command = SqlServerCommandBuilder.DeleteSingle(connection,
            "schema", "tableName", keyProperty, 123L);

        Assert.Equal("DELETE FROM [schema].[tableName] WHERE [id] = @id_0", command.CommandText);
        Assert.Equal(123L, command.Parameters[0].Value);
        Assert.Equal("@id_0", command.Parameters[0].ParameterName);
    }

    [Fact]
    public void DeleteMany()
    {
        string[] keys = ["key1", "key2"];
        VectorStoreRecordKeyPropertyModel keyProperty = new("id", typeof(string));
        using SqlConnection connection = CreateConnection();
        using SqlCommand command = connection.CreateCommand();

        Assert.True(SqlServerCommandBuilder.DeleteMany(command, "schema", "tableName", keyProperty, keys));

        Assert.Equal("DELETE FROM [schema].[tableName] WHERE [id] IN (@id_0,@id_1)", command.CommandText);
        for (int i = 0; i < keys.Length; i++)
        {
            Assert.Equal(keys[i], command.Parameters[i].Value);
            Assert.Equal($"@id_{i}", command.Parameters[i].ParameterName);
        }
    }

    [Fact]
    public void SelectSingle()
    {
        var model = BuildModel(
            [
                new VectorStoreRecordKeyProperty("id", typeof(long)),
                new VectorStoreRecordDataProperty("name", typeof(string)),
                new VectorStoreRecordDataProperty("age", typeof(int)),
                new VectorStoreRecordVectorProperty("embedding", typeof(ReadOnlyMemory<float>), 10)
            ]);

        using SqlConnection connection = CreateConnection();

        using SqlCommand command = SqlServerCommandBuilder.SelectSingle(connection, "schema", "tableName", model, 123L, includeVectors: true);

        Assert.Equal(
        """""
        SELECT [id],[name],[age],[embedding]
        FROM [schema].[tableName]
        WHERE [id] = @id_0
        """"", command.CommandText, ignoreLineEndingDifferences: true);
        Assert.Equal(123L, command.Parameters[0].Value);
        Assert.Equal("@id_0", command.Parameters[0].ParameterName);
    }

    [Fact]
    public void SelectMany()
    {
        var model = BuildModel(
        [
            new VectorStoreRecordKeyProperty("id", typeof(long)),
            new VectorStoreRecordDataProperty("name", typeof(string)),
            new VectorStoreRecordDataProperty("age", typeof(int)),
            new VectorStoreRecordVectorProperty("embedding", typeof(ReadOnlyMemory<float>), 10)
        ]);

        long[] keys = [123L, 456L, 789L];
        using SqlConnection connection = CreateConnection();
        using SqlCommand command = connection.CreateCommand();

        Assert.True(SqlServerCommandBuilder.SelectMany(command,
            "schema", "tableName", model, keys, includeVectors: true));

        Assert.Equal(
        """""
        SELECT [id],[name],[age],[embedding]
        FROM [schema].[tableName]
        WHERE [id] IN (@id_0,@id_1,@id_2)
        """"", command.CommandText, ignoreLineEndingDifferences: true);
        for (int i = 0; i < keys.Length; i++)
        {
            Assert.Equal(keys[i], command.Parameters[i].Value);
            Assert.Equal($"@id_{i}", command.Parameters[i].ParameterName);
        }
    }

    // We create a connection using a fake connection string just to be able to create the SqlCommand.
    private static SqlConnection CreateConnection()
        => new("Server=localhost;Database=master;Integrated Security=True;");

    private static VectorStoreRecordModel BuildModel(List<VectorStoreRecordProperty> properties)
        => new VectorStoreRecordModelBuilder(SqlServerConstants.ModelBuildingOptions)
            .Build(
                typeof(Dictionary<string, object?>),
                new() { Properties = properties },
                defaultEmbeddingGenerator: null);
}
