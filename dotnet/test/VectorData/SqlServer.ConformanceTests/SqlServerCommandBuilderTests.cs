// Copyright (c) Microsoft. All rights reserved.

using System.Text;
using Microsoft.Data.SqlClient;
using Microsoft.Data.SqlTypes;
using Microsoft.Extensions.VectorData;
using Microsoft.Extensions.VectorData.ProviderServices;
using Microsoft.SemanticKernel.Connectors.SqlServer;
using Xunit;

namespace SqlServer.ConformanceTests;

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
        KeyPropertyModel keyProperty = new(propertyName, typeof(string));

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
                new VectorStoreKeyProperty("id", typeof(long)),
                new VectorStoreDataProperty("simpleName", typeof(string)),
                new VectorStoreDataProperty("with space", typeof(int)) { IsIndexed = true },
                new VectorStoreVectorProperty("embedding", typeof(ReadOnlyMemory<float>), 10)
            ]);

        using SqlConnection connection = CreateConnection();

        var commands = SqlServerCommandBuilder.CreateTable(connection, "schema", "table", ifNotExists, model);

        var command = Assert.Single(commands);
        string expectedCommand =
        """
        BEGIN
        CREATE TABLE [schema].[table] (
        [id] BIGINT IDENTITY,
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
    public void CreateTable_WithDiskAnnIndex()
    {
        var model = BuildModel(
            [
                new VectorStoreKeyProperty("id", typeof(long)),
                new VectorStoreDataProperty("name", typeof(string)),
                new VectorStoreVectorProperty("embedding", typeof(ReadOnlyMemory<float>), 10)
                {
                    IndexKind = IndexKind.DiskAnn,
                    DistanceFunction = DistanceFunction.CosineDistance
                }
            ]);

        using SqlConnection connection = CreateConnection();

        var commands = SqlServerCommandBuilder.CreateTable(connection, "schema", "table", ifNotExists: false, model);

        Assert.Equal(3, commands.Count);
        Assert.Equal(
        """
        BEGIN
        CREATE TABLE [schema].[table] (
        [id] BIGINT IDENTITY,
        [name] NVARCHAR(MAX),
        [embedding] VECTOR(10),
        PRIMARY KEY ([id])
        );
        END;
        """, commands[0].CommandText, ignoreLineEndingDifferences: true);
        Assert.Equal("ALTER DATABASE SCOPED CONFIGURATION SET PREVIEW_FEATURES = ON;", commands[1].CommandText);
        Assert.Equal(
        """
        CREATE VECTOR INDEX index_table_embedding ON [schema].[table]([embedding]) WITH (METRIC = 'COSINE', TYPE = 'DISKANN');

        """, commands[2].CommandText, ignoreLineEndingDifferences: true);
    }

    [Fact]
    public void CreateTable_WithDiskAnnIndex_EuclideanDistance()
    {
        var model = BuildModel(
            [
                new VectorStoreKeyProperty("id", typeof(long)),
                new VectorStoreVectorProperty("embedding", typeof(ReadOnlyMemory<float>), 10)
                {
                    IndexKind = IndexKind.DiskAnn,
                    DistanceFunction = DistanceFunction.EuclideanDistance
                }
            ]);

        using SqlConnection connection = CreateConnection();

        var commands = SqlServerCommandBuilder.CreateTable(connection, "schema", "table", ifNotExists: false, model);

        Assert.Equal(3, commands.Count);
        Assert.Equal(
        """
        BEGIN
        CREATE TABLE [schema].[table] (
        [id] BIGINT IDENTITY,
        [embedding] VECTOR(10),
        PRIMARY KEY ([id])
        );
        END;
        """, commands[0].CommandText, ignoreLineEndingDifferences: true);
        Assert.Equal("ALTER DATABASE SCOPED CONFIGURATION SET PREVIEW_FEATURES = ON;", commands[1].CommandText);
        Assert.Equal(
        """
        CREATE VECTOR INDEX index_table_embedding ON [schema].[table]([embedding]) WITH (METRIC = 'EUCLIDEAN', TYPE = 'DISKANN');

        """, commands[2].CommandText, ignoreLineEndingDifferences: true);
    }

    [Fact]
    public void CreateTable_WithUnsupportedIndexKind_Throws()
    {
        Assert.Throws<NotSupportedException>(() =>
            BuildModel(
            [
                new VectorStoreKeyProperty("id", typeof(long)),
                new VectorStoreVectorProperty("embedding", typeof(ReadOnlyMemory<float>), 10)
                {
                    IndexKind = IndexKind.Hnsw
                }
            ]));
    }

    [Fact]
    public void SelectVector_WithDiskAnnIndex()
    {
        var model = BuildModel(
            [
                new VectorStoreKeyProperty("id", typeof(long)),
                new VectorStoreDataProperty("name", typeof(string)),
                new VectorStoreVectorProperty("embedding", typeof(ReadOnlyMemory<float>), 3)
                {
                    IndexKind = IndexKind.DiskAnn,
                    DistanceFunction = DistanceFunction.CosineDistance
                }
            ]);

        using SqlConnection connection = CreateConnection();

        var options = new VectorSearchOptions<Dictionary<string, object?>> { IncludeVectors = true };
        using SqlCommand command = SqlServerCommandBuilder.SelectVector(
            connection, "schema", "table",
            model.VectorProperties[0], model,
            top: 5, options,
            new SqlVector<float>(new float[] { 1f, 2f, 3f }));

        Assert.Equal(
        """
        SELECT t.[id],t.[name],t.[embedding],
        s.[distance] AS [score]
        FROM VECTOR_SEARCH(TABLE = [schema].[table] AS t, COLUMN = [embedding], SIMILAR_TO = @vector, METRIC = 'COSINE', TOP_N = 5) AS s
        ORDER BY [score] ASC
        OFFSET 0 ROWS FETCH NEXT 5 ROWS ONLY;
        """, command.CommandText, ignoreLineEndingDifferences: true);
    }

    [Fact]
    public void SelectVector_WithDiskAnnIndex_WithSkip()
    {
        var model = BuildModel(
            [
                new VectorStoreKeyProperty("id", typeof(long)),
                new VectorStoreDataProperty("name", typeof(string)),
                new VectorStoreVectorProperty("embedding", typeof(ReadOnlyMemory<float>), 3)
                {
                    IndexKind = IndexKind.DiskAnn,
                    DistanceFunction = DistanceFunction.CosineDistance
                }
            ]);

        using SqlConnection connection = CreateConnection();

        var options = new VectorSearchOptions<Dictionary<string, object?>> { IncludeVectors = false, Skip = 3 };
        using SqlCommand command = SqlServerCommandBuilder.SelectVector(
            connection, "schema", "table",
            model.VectorProperties[0], model,
            top: 5, options,
            new SqlVector<float>(new float[] { 1f, 2f, 3f }));

        Assert.Equal(
        """
        SELECT t.[id],t.[name],
        s.[distance] AS [score]
        FROM VECTOR_SEARCH(TABLE = [schema].[table] AS t, COLUMN = [embedding], SIMILAR_TO = @vector, METRIC = 'COSINE', TOP_N = 8) AS s
        ORDER BY [score] ASC
        OFFSET 3 ROWS FETCH NEXT 5 ROWS ONLY;
        """, command.CommandText, ignoreLineEndingDifferences: true);
    }

    [Fact]
    public void SelectVector_WithDiskAnnIndex_WithFilter_Throws()
    {
        var model = BuildModel(
            [
                new VectorStoreKeyProperty("id", typeof(long)),
                new VectorStoreDataProperty("name", typeof(string)),
                new VectorStoreVectorProperty("embedding", typeof(ReadOnlyMemory<float>), 3)
                {
                    IndexKind = IndexKind.DiskAnn,
                    DistanceFunction = DistanceFunction.CosineDistance
                }
            ]);

        using SqlConnection connection = CreateConnection();

        var options = new VectorSearchOptions<Dictionary<string, object?>>
        {
            Filter = d => (string)d["name"]! == "test"
        };

        Assert.Throws<NotSupportedException>(() =>
            SqlServerCommandBuilder.SelectVector(
                connection, "schema", "table",
                model.VectorProperties[0], model,
                top: 5, options,
                new SqlVector<float>(new float[] { 1f, 2f, 3f })));
    }

    [Fact]
    public void SelectVector_WithDiskAnnIndex_WithScoreThreshold()
    {
        var model = BuildModel(
            [
                new VectorStoreKeyProperty("id", typeof(long)),
                new VectorStoreDataProperty("name", typeof(string)),
                new VectorStoreVectorProperty("embedding", typeof(ReadOnlyMemory<float>), 3)
                {
                    IndexKind = IndexKind.DiskAnn,
                    DistanceFunction = DistanceFunction.CosineDistance
                }
            ]);

        using SqlConnection connection = CreateConnection();

        var options = new VectorSearchOptions<Dictionary<string, object?>>
        {
            IncludeVectors = true,
            ScoreThreshold = 0.5f
        };
        using SqlCommand command = SqlServerCommandBuilder.SelectVector(
            connection, "schema", "table",
            model.VectorProperties[0], model,
            top: 5, options,
            new SqlVector<float>(new float[] { 1f, 2f, 3f }));

        Assert.Equal(
        """
        SELECT t.[id],t.[name],t.[embedding],
        s.[distance] AS [score]
        FROM VECTOR_SEARCH(TABLE = [schema].[table] AS t, COLUMN = [embedding], SIMILAR_TO = @vector, METRIC = 'COSINE', TOP_N = 5) AS s
        WHERE s.[distance] <= @scoreThreshold
        ORDER BY [score] ASC
        OFFSET 0 ROWS FETCH NEXT 5 ROWS ONLY;
        """, command.CommandText, ignoreLineEndingDifferences: true);
    }

    [Fact]
    public void Upsert()
    {
        var model = BuildModel(
            [
                new VectorStoreKeyProperty("id", typeof(long)) { IsAutoGenerated = false },
                new VectorStoreDataProperty("simpleString", typeof(string)),
                new VectorStoreDataProperty("simpleInt", typeof(int)),
                new VectorStoreVectorProperty("embedding", typeof(ReadOnlyMemory<float>), 10)
            ]);

        Dictionary<string, object?>[] records =
        [
            new Dictionary<string, object?>
            {
                { "id", 0L },
                { "simpleString", "nameValue0" },
                { "simpleInt", 134 },
                { "embedding", new ReadOnlyMemory<float>([10.0f]) }
            },
            new Dictionary<string, object?>
            {
                { "id", 1L },
                { "simpleString", "nameValue1" },
                { "simpleInt", 135 },
                { "embedding", new ReadOnlyMemory<float>([11.0f]) }
            }
        ];

        using SqlConnection connection = CreateConnection();
        using SqlCommand command = connection.CreateCommand();

        Assert.True(SqlServerCommandBuilder.Upsert<long>(command, "schema", "table", model, records, firstRecordIndex: 0, generatedEmbeddings: null));

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

        MERGE INTO [schema].[table] AS t
        USING (VALUES (@id_4,@simpleString_5,@simpleInt_6,@embedding_7)) AS s ([id],[simpleString],[simpleInt],[embedding])
        ON (t.[id] = s.[id])
        WHEN MATCHED THEN
        UPDATE SET t.[simpleString] = s.[simpleString],t.[simpleInt] = s.[simpleInt],t.[embedding] = s.[embedding]
        WHEN NOT MATCHED THEN
        INSERT ([id],[simpleString],[simpleInt],[embedding])
        VALUES (s.[id],s.[simpleString],s.[simpleInt],s.[embedding])
        OUTPUT inserted.[id];


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
            var vector = Assert.IsType<SqlVector<float>>(command.Parameters[4 * i + 3].Value);
            Assert.Equal([10 + i], vector.Memory.ToArray());
        }
    }

    [Fact]
    public void DeleteSingle()
    {
        KeyPropertyModel keyProperty = new("id", typeof(long));
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
        KeyPropertyModel keyProperty = new("id", typeof(string));
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
                new VectorStoreKeyProperty("id", typeof(long)),
                new VectorStoreDataProperty("name", typeof(string)),
                new VectorStoreDataProperty("age", typeof(int)),
                new VectorStoreVectorProperty("embedding", typeof(ReadOnlyMemory<float>), 10)
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
            new VectorStoreKeyProperty("id", typeof(long)),
            new VectorStoreDataProperty("name", typeof(string)),
            new VectorStoreDataProperty("age", typeof(int)),
            new VectorStoreVectorProperty("embedding", typeof(ReadOnlyMemory<float>), 10)
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

    private static CollectionModel BuildModel(List<VectorStoreProperty> properties)
        => new SqlServerModelBuilder()
            .BuildDynamic(new() { Properties = properties }, defaultEmbeddingGenerator: null);
}
