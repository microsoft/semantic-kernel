// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using Microsoft.Data.Sqlite;
using Microsoft.Extensions.VectorData;
using Microsoft.Extensions.VectorData.ProviderServices;
using Microsoft.SemanticKernel.Connectors.SqliteVec;
using Xunit;

namespace SemanticKernel.Connectors.SqliteVec.UnitTests;

/// <summary>
/// Unit tests for <see cref="SqliteCommandBuilder"/> class.
/// </summary>
public sealed class SqliteCommandBuilderTests : IDisposable
{
    private readonly SqliteCommand _command;
    private readonly SqliteConnection _connection;

    public SqliteCommandBuilderTests()
    {
        this._command = new() { Connection = this._connection };
        this._connection = new();
    }

    [Fact]
    public void ItBuildsTableCountCommand()
    {
        // Arrange
        const string TableName = "TestTable";

        // Act
        var command = SqliteCommandBuilder.BuildTableCountCommand(this._connection, TableName);

        // Assert
        Assert.Equal("SELECT count(*) FROM sqlite_master WHERE type='table' AND name=@tableName;", command.CommandText);
        Assert.Equal("@tableName", command.Parameters[0].ParameterName);
        Assert.Equal(TableName, command.Parameters[0].Value);
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public void ItBuildsCreateTableCommand(bool ifNotExists)
    {
        // Arrange
        const string TableName = "TestTable";

        var columns = new List<SqliteColumn>
        {
            new("Column1", "Type1", isPrimary: true),
            new("Column2", "Type2", isPrimary: false) { Configuration = new() { ["distance_metric"] = "l2" } },
        };

        // Act
        var command = SqliteCommandBuilder.BuildCreateTableCommand(this._connection, TableName, columns, ifNotExists);

        // Assert
        Assert.Contains("CREATE TABLE", command.CommandText);
        Assert.Contains(TableName, command.CommandText);

        Assert.Equal(ifNotExists, command.CommandText.Contains("IF NOT EXISTS"));

        Assert.Contains("\"Column1\" Type1 PRIMARY KEY", command.CommandText);
        Assert.Contains("\"Column2\" Type2 distance_metric=l2", command.CommandText);
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public void ItBuildsCreateVirtualTableCommand(bool ifNotExists)
    {
        // Arrange
        const string TableName = "TestTable";

        var columns = new List<SqliteColumn>
        {
            new("Column1", "Type1", isPrimary: true),
            new("Column2", "Type2", isPrimary: false) { Configuration = new() { ["distance_metric"] = "l2" } },
        };

        // Act
        var command = SqliteCommandBuilder.BuildCreateVirtualTableCommand(this._connection, TableName, columns, ifNotExists);

        // Assert
        Assert.Contains("CREATE VIRTUAL TABLE", command.CommandText);
        Assert.Contains(TableName, command.CommandText);
        Assert.Contains("USING vec0", command.CommandText);

        Assert.Equal(ifNotExists, command.CommandText.Contains("IF NOT EXISTS"));

        Assert.Contains("Column1 Type1 PRIMARY KEY", command.CommandText);
        Assert.Contains("Column2 Type2 distance_metric=l2", command.CommandText);
    }

    [Fact]
    public void ItBuildsDropTableCommand()
    {
        // Arrange
        const string TableName = "TestTable";

        // Act
        var command = SqliteCommandBuilder.BuildDropTableCommand(this._connection, TableName);

        // Assert
        Assert.Equal("DROP TABLE IF EXISTS \"TestTable\";", command.CommandText);
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public void ItBuildsInsertCommand(bool replaceIfExists)
    {
        // Arrange
        const string TableName = "TestTable";
        const string RowIdentifier = "Id";

        var model = BuildModel(
        [
            new VectorStoreKeyProperty("Id", typeof(string)),
            new VectorStoreDataProperty("Name", typeof(string)),
            new VectorStoreDataProperty("Age", typeof(string)),
            new VectorStoreDataProperty("Address", typeof(string)),
        ]);

        var records = new List<Dictionary<string, object?>>
        {
            new() { ["Id"] = "IdValue1", ["Name"] = "NameValue1", ["Age"] = "AgeValue1", ["Address"] = "AddressValue1" },
            new() { ["Id"] = "IdValue2", ["Name"] = "NameValue2", ["Age"] = "AgeValue2", ["Address"] = "AddressValue2" },
        };

        // Act
        var command = SqliteCommandBuilder.BuildInsertCommand(
            this._connection,
            TableName,
            RowIdentifier,
            model,
            records,
            generatedEmbeddings: null,
            data: true,
            replaceIfExists);

        // Assert
        Assert.Equal(replaceIfExists, command.CommandText.Contains("OR REPLACE"));

        Assert.Contains($"INTO \"{TableName}\" (\"Id\", \"Name\", \"Age\", \"Address\")", command.CommandText);
        Assert.Contains("VALUES (@Id0, @Name0, @Age0, @Address0)", command.CommandText);
        Assert.Contains("VALUES (@Id1, @Name1, @Age1, @Address1)", command.CommandText);
        Assert.Contains("RETURNING Id", command.CommandText);

        Assert.Equal("@Id0", command.Parameters[0].ParameterName);
        Assert.Equal("IdValue1", command.Parameters[0].Value);

        Assert.Equal("@Name0", command.Parameters[1].ParameterName);
        Assert.Equal("NameValue1", command.Parameters[1].Value);

        Assert.Equal("@Age0", command.Parameters[2].ParameterName);
        Assert.Equal("AgeValue1", command.Parameters[2].Value);

        Assert.Equal("@Address0", command.Parameters[3].ParameterName);
        Assert.Equal("AddressValue1", command.Parameters[3].Value);

        Assert.Equal("@Id1", command.Parameters[4].ParameterName);
        Assert.Equal("IdValue2", command.Parameters[4].Value);

        Assert.Equal("@Name1", command.Parameters[5].ParameterName);
        Assert.Equal("NameValue2", command.Parameters[5].Value);

        Assert.Equal("@Age1", command.Parameters[6].ParameterName);
        Assert.Equal("AgeValue2", command.Parameters[6].Value);

        Assert.Equal("@Address1", command.Parameters[7].ParameterName);
        Assert.Equal("AddressValue2", command.Parameters[7].Value);
    }

    [Theory]
    [InlineData(null)]
    [InlineData("")]
    [InlineData("Age")]
    public void ItBuildsSelectCommand(string? orderByPropertyName)
    {
        // Arrange
        const string TableName = "TestTable";

        var model = BuildModel(
        [
            new VectorStoreKeyProperty("Id", typeof(string)),
            new VectorStoreDataProperty("Name", typeof(string)),
            new VectorStoreDataProperty("Age", typeof(string)),
            new VectorStoreDataProperty("Address", typeof(string)),
        ]);
        var conditions = new List<SqliteWhereCondition>
        {
            new SqliteWhereEqualsCondition("Name", "NameValue"),
            new SqliteWhereInCondition("Age", [10, 20, 30]),
        };
        FilteredRecordRetrievalOptions<Dictionary<string, object?>> filterOptions = new();
        if (!string.IsNullOrWhiteSpace(orderByPropertyName))
        {
            filterOptions.OrderBy = orderBy => orderBy.Ascending(record => record[orderByPropertyName]);
        }

        // Act
        var command = SqliteCommandBuilder.BuildSelectDataCommand<Dictionary<string, object?>>(this._connection, TableName, model, conditions, filterOptions);

        // Assert
        Assert.Contains("SELECT \"Id\",\"Name\",\"Age\",\"Address\"", command.CommandText);
        Assert.Contains($"FROM \"{TableName}\"", command.CommandText);

        Assert.Contains("\"Name\" = @Name0", command.CommandText);
        Assert.Contains("\"Age\" IN (@Age0, @Age1, @Age2)", command.CommandText);

        Assert.Equal(!string.IsNullOrWhiteSpace(orderByPropertyName), command.CommandText.Contains($"ORDER BY \"{orderByPropertyName}\""));

        Assert.Equal("@Name0", command.Parameters[0].ParameterName);
        Assert.Equal("NameValue", command.Parameters[0].Value);

        Assert.Equal("@Age0", command.Parameters[1].ParameterName);
        Assert.Equal(10, command.Parameters[1].Value);

        Assert.Equal("@Age1", command.Parameters[2].ParameterName);
        Assert.Equal(20, command.Parameters[2].Value);

        Assert.Equal("@Age2", command.Parameters[3].ParameterName);
        Assert.Equal(30, command.Parameters[3].Value);
    }

    [Theory]
    [InlineData(null)]
    [InlineData("")]
    [InlineData("Age")]
    public void ItBuildsSelectInnerJoinCommand(string? orderByPropertyName)
    {
        // Arrange
        const string DataTable = "DataTable";
        const string VectorTable = "VectorTable";
        const string JoinColumnName = "Id";

        var model = BuildModel(
        [
            new VectorStoreKeyProperty("Id", typeof(string)),
            new VectorStoreDataProperty("Name", typeof(string)),
            new VectorStoreVectorProperty("Age", typeof(ReadOnlyMemory<float>), 10),
            new VectorStoreVectorProperty("Address", typeof(ReadOnlyMemory<float>), 10),
        ]);

        var conditions = new List<SqliteWhereCondition>
        {
            new SqliteWhereEqualsCondition("Name", "NameValue"),
            new SqliteWhereInCondition("Age", [10, 20, 30]),
        };
        FilteredRecordRetrievalOptions<Dictionary<string, object?>> filterOptions = new();
        if (!string.IsNullOrWhiteSpace(orderByPropertyName))
        {
            filterOptions.OrderBy = orderBy => orderBy.Ascending(record => record[orderByPropertyName]);
        }

        // Act
        var command = SqliteCommandBuilder.BuildSelectInnerJoinCommand(
            this._connection,
            VectorTable,
            DataTable,
            JoinColumnName,
            model,
            conditions,
            true,
            filterOptions);

        // Assert
        Assert.Contains("SELECT \"DataTable\".\"Id\",\"DataTable\".\"Name\",\"VectorTable\".\"Age\",\"VectorTable\".\"Address\"", command.CommandText);
        Assert.Contains("FROM \"VectorTable\"", command.CommandText);

        Assert.Contains("INNER JOIN \"DataTable\" ON \"VectorTable\".\"Id\" = \"DataTable\".\"Id\"", command.CommandText);

        Assert.Contains("\"Name\" = @Name0", command.CommandText);
        Assert.Contains("\"Age\" IN (@Age0, @Age1, @Age2)", command.CommandText);

        Assert.Equal(!string.IsNullOrWhiteSpace(orderByPropertyName), command.CommandText.Contains($"ORDER BY \"DataTable\".\"{orderByPropertyName}\""));

        Assert.Equal("@Name0", command.Parameters[0].ParameterName);
        Assert.Equal("NameValue", command.Parameters[0].Value);

        Assert.Equal("@Age0", command.Parameters[1].ParameterName);
        Assert.Equal(10, command.Parameters[1].Value);

        Assert.Equal("@Age1", command.Parameters[2].ParameterName);
        Assert.Equal(20, command.Parameters[2].Value);

        Assert.Equal("@Age2", command.Parameters[3].ParameterName);
        Assert.Equal(30, command.Parameters[3].Value);
    }

    [Fact]
    public void ItBuildsDeleteCommand()
    {
        // Arrange
        const string TableName = "TestTable";

        var conditions = new List<SqliteWhereCondition>
        {
            new SqliteWhereEqualsCondition("Name", "NameValue"),
            new SqliteWhereInCondition("Age", [10, 20, 30]),
        };

        // Act
        var command = SqliteCommandBuilder.BuildDeleteCommand(this._connection, TableName, conditions);

        // Assert
        Assert.Contains("DELETE FROM \"TestTable\"", command.CommandText);

        Assert.Contains("\"Name\" = @Name0", command.CommandText);
        Assert.Contains("\"Age\" IN (@Age0, @Age1, @Age2)", command.CommandText);

        Assert.Equal("@Name0", command.Parameters[0].ParameterName);
        Assert.Equal("NameValue", command.Parameters[0].Value);

        Assert.Equal("@Age0", command.Parameters[1].ParameterName);
        Assert.Equal(10, command.Parameters[1].Value);

        Assert.Equal("@Age1", command.Parameters[2].ParameterName);
        Assert.Equal(20, command.Parameters[2].Value);

        Assert.Equal("@Age2", command.Parameters[3].ParameterName);
        Assert.Equal(30, command.Parameters[3].Value);
    }

    public void Dispose()
    {
        this._command.Dispose();
        this._connection.Dispose();
    }

    private static CollectionModel BuildModel(List<VectorStoreProperty> properties)
        => new SqliteModelBuilder()
            .BuildDynamic(new() { Properties = properties }, defaultEmbeddingGenerator: null);
}
