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
    public void GetSanitizedFullTableName(string schema, string table, string expectedFullName)
    {
        string result = SqlServerCommandBuilder.GetSanitizedFullTableName(schema, table);
        Assert.Equal(expectedFullName, result);
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

        if (OperatingSystem.IsWindows())
        {
            expectedCommand = expectedCommand.Replace("\n", "\r\n");
        }

        Assert.Equal(expectedCommand, command.CommandText);
    }

    // We create a connection using a fake connection string just to be able to create the SqlCommand.
    private static SqlConnection CreateConnection()
        => new("Server=localhost;Database=master;Integrated Security=True;");
}
