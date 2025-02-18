using System.Text;
using Microsoft.Data.SqlClient;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.SqlServer;
using Xunit;

namespace SqlServerIntegrationTests;

public class SqlServerCommandBuilderTests
{
    [Theory]
    [InlineData("schema", "name", "[schema].[name]")]
    [InlineData("schema", "[brackets]", "[schema].[[brackets]]]")]
    [InlineData("needs]escaping", "[brackets]", "[needs]]escaping].[[brackets]]]")]
    public void AppendTableName(string schema, string table, string expectedFullName)
    {
        StringBuilder result = new();

        SqlServerCommandBuilder.AppendTableName(result, schema, table);

        Assert.Equal(expectedFullName, result.ToString());
    }

    [Theory]
    [InlineData("schema", "simpleName", "[simpleName]")]
    [InlineData("schema", "[needsEscaping]", "[[needsEscaping]]]")]
    public void DropTable(string schema, string table, string expectedTable)
    {
        using SqlConnection connection = CreateConnection();

        using SqlCommand command = SqlServerCommandBuilder.DropTable(connection, schema, table);

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
            AND TABLE_SCHEMA = @schema
            AND TABLE_NAME = @tableName
        """
        , command.CommandText);
        Assert.Equal(schema, command.Parameters[0].Value);
        Assert.Equal(table, command.Parameters[1].Value);
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public void CreateTable(bool ifNotExists)
    {
        SqlServerVectorStoreOptions options = new()
        {
            Schema = "schema"
        };
        VectorStoreRecordKeyProperty keyProperty = new("id", typeof(long));
        VectorStoreRecordDataProperty[] dataProperties =
        [
            new VectorStoreRecordDataProperty("simpleName", typeof(string)),
            new VectorStoreRecordDataProperty("with space", typeof(int))
        ];
        VectorStoreRecordVectorProperty[] vectorProperties =
        [
            new VectorStoreRecordVectorProperty("embedding1", typeof(ReadOnlyMemory<float>))
            {
                Dimensions = 10
            }
        ];
        using SqlConnection connection = CreateConnection();

        using SqlCommand command = SqlServerCommandBuilder.CreateTable(connection, options, "table",
            ifNotExists, keyProperty, dataProperties, vectorProperties);

        string expectedCommand =
        """
        CREATE TABLE [schema].[table] (
        [id] BIGINT NOT NULL,
        [simpleName] NVARCHAR(255) COLLATE Latin1_General_100_BIN2,
        [with space] INT NOT NULL,
        [embedding1] VECTOR(10),
        PRIMARY KEY NONCLUSTERED ([id])
        )
        """;
        if (ifNotExists)
        {
            expectedCommand = "IF OBJECT_ID(N'[schema].[table]', N'U') IS NULL\n" + expectedCommand;
        }

        Assert.Equal(HandleNewLines(expectedCommand), command.CommandText);
    }

    [Fact]
    public void InsertInto()
    {
        SqlServerVectorStoreOptions options = new()
        {
            Schema = "schema"
        };
        VectorStoreRecordKeyProperty keyProperty = new("id", typeof(long));
        VectorStoreRecordDataProperty[] dataProperties =
        [
            new VectorStoreRecordDataProperty("simpleString", typeof(string)),
            new VectorStoreRecordDataProperty("simpleInt", typeof(int))
        ];
        VectorStoreRecordVectorProperty[] vectorProperties =
        [
            new VectorStoreRecordVectorProperty("embedding1", typeof(ReadOnlyMemory<float>))
            {
                Dimensions = 10
            }
        ];
        using SqlConnection connection = CreateConnection();

        using SqlCommand command = SqlServerCommandBuilder.InsertInto(connection, options, "table",
            keyProperty, dataProperties, vectorProperties,
            new Dictionary<string, object?>
            {
                { "id", null },
                { "simpleString", "nameValue" },
                { "simpleInt", 134 },
                { "embedding1", "{ 10.0 }" }
            });

        string expectedCommand =
        """
        INSERT INTO [schema].[table] ([simpleString],[simpleInt],[embedding1])
        OUTPUT inserted.[id]
        VALUES (@simpleString,@simpleInt,@embedding1);
        """;

        Assert.Equal(HandleNewLines(expectedCommand), command.CommandText);
        Assert.Equal("@simpleString", command.Parameters[0].ParameterName);
        Assert.Equal("nameValue", command.Parameters[0].Value);
        Assert.Equal("@simpleInt", command.Parameters[1].ParameterName);
        Assert.Equal(134, command.Parameters[1].Value);
        Assert.Equal("@embedding1", command.Parameters[2].ParameterName);
        Assert.Equal("{ 10.0 }", command.Parameters[2].Value);
    }

    [Fact]
    public void MergeIntoSingle()
    {
        SqlServerVectorStoreOptions options = new()
        {
            Schema = "schema"
        };
        VectorStoreRecordKeyProperty keyProperty = new("id", typeof(long));
        VectorStoreRecordProperty[] properties =
        [
            keyProperty,
            new VectorStoreRecordDataProperty("simpleString", typeof(string)),
            new VectorStoreRecordDataProperty("simpleInt", typeof(int)),
            new VectorStoreRecordVectorProperty("embedding1", typeof(ReadOnlyMemory<float>))
            {
                Dimensions = 10
            }
        ];

        using SqlConnection connection = CreateConnection();
        using SqlCommand command = SqlServerCommandBuilder.MergeIntoSingle(connection, options, "table",
            keyProperty, properties,
            new Dictionary<string, object?>
            {
                { "id", null },
                { "simpleString", "nameValue" },
                { "simpleInt", 134 },
                { "embedding1", "{ 10.0 }" }
            });

        string expectedCommand =
        """"
        MERGE INTO [schema].[table] AS t
        USING (VALUES (@id,@simpleString,@simpleInt,@embedding1)) AS s ([id],[simpleString],[simpleInt],[embedding1])
        ON (t.[id] = s.[id])
        WHEN MATCHED THEN
        UPDATE SET t.[simpleString] = s.[simpleString],t.[simpleInt] = s.[simpleInt],t.[embedding1] = s.[embedding1]
        WHEN NOT MATCHED THEN
        INSERT ([id],[simpleString],[simpleInt],[embedding1])
        VALUES (s.[id],s.[simpleString],s.[simpleInt],s.[embedding1]);
        """";

        Assert.Equal(HandleNewLines(expectedCommand), command.CommandText);
        Assert.Equal("@id", command.Parameters[0].ParameterName);
        Assert.Equal(DBNull.Value, command.Parameters[0].Value);
        Assert.Equal("@simpleString", command.Parameters[1].ParameterName);
        Assert.Equal("nameValue", command.Parameters[1].Value);
        Assert.Equal("@simpleInt", command.Parameters[2].ParameterName);
        Assert.Equal(134, command.Parameters[2].Value);
        Assert.Equal("@embedding1", command.Parameters[3].ParameterName);
        Assert.Equal("{ 10.0 }", command.Parameters[3].Value);
    }

    [Fact]
    public void MergeIntoMany()
    {
        SqlServerVectorStoreOptions options = new()
        {
            Schema = "schema"
        };
        VectorStoreRecordKeyProperty keyProperty = new("id", typeof(long));
        VectorStoreRecordProperty[] properties =
        [
            keyProperty,
            new VectorStoreRecordDataProperty("simpleString", typeof(string)),
            new VectorStoreRecordDataProperty("simpleInt", typeof(int)),
            new VectorStoreRecordVectorProperty("embedding", typeof(ReadOnlyMemory<float>))
            {
                Dimensions = 10
            }
        ];
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
        using SqlCommand command = SqlServerCommandBuilder.MergeIntoMany(connection, options, "table",
            keyProperty, properties, records);

        string expectedCommand =
        """"
        DECLARE @InsertedKeys TABLE (KeyColumn BIGINT);
        MERGE INTO [schema].[table] AS t
        USING (VALUES
        (@id_0,@simpleString_0,@simpleInt_0,@embedding_0),
        (@id_1,@simpleString_1,@simpleInt_1,@embedding_1)) AS s ([id],[simpleString],[simpleInt],[embedding])
        ON (t.[id] = s.[id])
        WHEN MATCHED THEN
        UPDATE SET t.[simpleString] = s.[simpleString],t.[simpleInt] = s.[simpleInt],t.[embedding] = s.[embedding]
        WHEN NOT MATCHED THEN
        INSERT ([id],[simpleString],[simpleInt],[embedding])
        VALUES (s.[id],s.[simpleString],s.[simpleInt],s.[embedding])
        OUTPUT inserted.[id] INTO @InsertedKeys (KeyColumn);
        SELECT KeyColumn FROM @InsertedKeys;
        """";

        Assert.Equal(expectedCommand, command.CommandText);

        for (int i = 0; i < records.Length; i++)
        {
            Assert.Equal($"@id_{i}", command.Parameters[4 * i].ParameterName);
            Assert.Equal((long)i, command.Parameters[4 * i].Value);
            Assert.Equal($"@simpleString_{i}", command.Parameters[4 * i + 1].ParameterName);
            Assert.Equal($"nameValue{i}", command.Parameters[4 * i + 1].Value);
            Assert.Equal($"@simpleInt_{i}", command.Parameters[4 * i + 2].ParameterName);
            Assert.Equal(134 + i, command.Parameters[4 * i + 2].Value);
            Assert.Equal($"@embedding_{i}", command.Parameters[4 * i + 3].ParameterName);
            Assert.Equal($"{{ 1{i}.0 }}", command.Parameters[4 * i + 3].Value);
        }
    }

    [Fact]
    public void DeleteSingle()
    {
        VectorStoreRecordKeyProperty keyProperty = new("id", typeof(long));
        using SqlConnection connection = CreateConnection();

        using SqlCommand command = SqlServerCommandBuilder.DeleteSingle(connection,
            "schema", "tableName", keyProperty, 123L);

        Assert.Equal("DELETE FROM [schema].[tableName] WHERE [id] = @id", command.CommandText);
        Assert.Equal(123L, command.Parameters[0].Value);
        Assert.Equal("@id", command.Parameters[0].ParameterName);
    }

    [Fact]
    public void DeleteMany()
    {
        string[] keys = ["key1", "key2"];
        VectorStoreRecordKeyProperty keyProperty = new("id", typeof(string));
        using SqlConnection connection = CreateConnection();

        using SqlCommand command = SqlServerCommandBuilder.DeleteMany(connection,
            "schema", "tableName", keyProperty, keys);

        Assert.Equal("DELETE FROM [schema].[tableName] WHERE [id] IN (@k0,@k1)", command.CommandText);
        for (int i = 0; i < keys.Length; i++)
        {
            Assert.Equal(keys[i], command.Parameters[i].Value);
            Assert.Equal($"@k{i}", command.Parameters[i].ParameterName);
        }
    }

    [Fact]
    public void SelectSingle()
    {
        VectorStoreRecordKeyProperty keyProperty = new("id", typeof(long));
        VectorStoreRecordProperty[] properties = [
            keyProperty,
            new VectorStoreRecordDataProperty("name", typeof(string)),
            new VectorStoreRecordDataProperty("age", typeof(int)),
            new VectorStoreRecordVectorProperty("embedding", typeof(ReadOnlyMemory<float>))
            {
                Dimensions = 10
            }
        ];
        using SqlConnection connection = CreateConnection();

        using SqlCommand command = SqlServerCommandBuilder.SelectSingle(connection,
            "schema", "tableName", keyProperty, properties, 123L);

        Assert.Equal(HandleNewLines(
        """""
        SELECT [id],[name],[age],[embedding]
        FROM [schema].[tableName]
        WHERE [id] = @id
        """""), command.CommandText);
        Assert.Equal(123L, command.Parameters[0].Value);
        Assert.Equal("@id", command.Parameters[0].ParameterName);
    }

    [Fact]
    public void SelectMany()
    {
        VectorStoreRecordKeyProperty keyProperty = new("id", typeof(long));
        VectorStoreRecordProperty[] properties = [
            keyProperty,
            new VectorStoreRecordDataProperty("name", typeof(string)),
            new VectorStoreRecordDataProperty("age", typeof(int)),
            new VectorStoreRecordVectorProperty("embedding", typeof(ReadOnlyMemory<float>))
            {
                Dimensions = 10
            }
        ];
        long[] keys = [123L, 456L, 789L];
        using SqlConnection connection = CreateConnection();

        using SqlCommand command = SqlServerCommandBuilder.SelectMany(connection,
            "schema", "tableName", keyProperty, properties, keys);

        Assert.Equal(HandleNewLines(
        """""
        SELECT [id],[name],[age],[embedding]
        FROM [schema].[tableName]
        WHERE [id] IN (@k0,@k1,@k2)
        """""), command.CommandText);
        for (int i = 0; i < keys.Length; i++)
        {
            Assert.Equal(keys[i], command.Parameters[i].Value);
            Assert.Equal($"@k{i}", command.Parameters[i].ParameterName);
        }
    }

    private static string HandleNewLines(string expectedCommand)
        => OperatingSystem.IsWindows()
            ? expectedCommand.Replace("\n", "\r\n")
            : expectedCommand;

    // We create a connection using a fake connection string just to be able to create the SqlCommand.
    private static SqlConnection CreateConnection()
        => new("Server=localhost;Database=master;Integrated Security=True;");
}
