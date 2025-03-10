// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using Microsoft.SemanticKernel.Connectors.Sqlite;
using Xunit;

namespace SemanticKernel.Connectors.Sqlite.UnitTests;

/// <summary>
/// Unit tests for <see cref="SqliteVectorStoreCollectionCommandBuilder"/> class.
/// </summary>
public sealed class SqliteVectorStoreCollectionCommandBuilderTests : IDisposable
{
    private readonly FakeDbCommand _command;
    private readonly FakeDBConnection _connection;
    private readonly SqliteVectorStoreCollectionCommandBuilder _commandBuilder;

    public SqliteVectorStoreCollectionCommandBuilderTests()
    {
        this._command = new();
        this._connection = new(this._command);
        this._commandBuilder = new(this._connection);
    }

    [Fact]
    public void ItBuildsTableCountCommand()
    {
        // Arrange
        const string TableName = "TestTable";

        // Act
        var command = this._commandBuilder.BuildTableCountCommand(TableName);

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
        var command = this._commandBuilder.BuildCreateTableCommand(TableName, columns, ifNotExists);

        // Assert
        Assert.Contains("CREATE TABLE", command.CommandText);
        Assert.Contains(TableName, command.CommandText);

        Assert.Equal(ifNotExists, command.CommandText.Contains("IF NOT EXISTS"));

        Assert.Contains("Column1 Type1 PRIMARY KEY", command.CommandText);
        Assert.Contains("Column2 Type2 distance_metric=l2", command.CommandText);
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public void ItBuildsCreateVirtualTableCommand(bool ifNotExists)
    {
        // Arrange
        const string TableName = "TestTable";
        const string ExtensionName = "TestExtension";

        var columns = new List<SqliteColumn>
        {
            new("Column1", "Type1", isPrimary: true),
            new("Column2", "Type2", isPrimary: false) { Configuration = new() { ["distance_metric"] = "l2" } },
        };

        // Act
        var command = this._commandBuilder.BuildCreateVirtualTableCommand(TableName, columns, ifNotExists, ExtensionName);

        // Assert
        Assert.Contains("CREATE VIRTUAL TABLE", command.CommandText);
        Assert.Contains(TableName, command.CommandText);
        Assert.Contains($"USING {ExtensionName}", command.CommandText);

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
        var command = this._commandBuilder.BuildDropTableCommand(TableName);

        // Assert
        Assert.Equal("DROP TABLE [TestTable];", command.CommandText);
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public void ItBuildsInsertCommand(bool replaceIfExists)
    {
        // Arrange
        const string TableName = "TestTable";
        const string RowIdentifier = "Id";

        var columnNames = new List<string> { "Id", "Name", "Age", "Address" };
        var records = new List<Dictionary<string, object?>>
        {
            new() { ["Id"] = "IdValue1", ["Name"] = "NameValue1", ["Age"] = "AgeValue1", ["Address"] = "AddressValue1" },
            new() { ["Id"] = "IdValue2", ["Name"] = "NameValue2", ["Age"] = "AgeValue2", ["Address"] = "AddressValue2" },
        };

        // Act
        var command = this._commandBuilder.BuildInsertCommand(
            TableName,
            RowIdentifier,
            columnNames,
            records,
            replaceIfExists);

        // Assert
        Assert.Equal(replaceIfExists, command.CommandText.Contains("OR REPLACE"));

        Assert.Contains($"INTO {TableName} (Id, Name, Age, Address)", command.CommandText);
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

        var columnNames = new List<string> { "Id", "Name", "Age", "Address" };
        var conditions = new List<SqliteWhereCondition>
        {
            new SqliteWhereEqualsCondition("Name", "NameValue"),
            new SqliteWhereInCondition("Age", [10, 20, 30]),
        };

        // Act
        var command = this._commandBuilder.BuildSelectCommand(TableName, columnNames, conditions, orderByPropertyName);

        // Assert
        Assert.Contains("SELECT Id, Name, Age, Address", command.CommandText);
        Assert.Contains($"FROM {TableName}", command.CommandText);

        Assert.Contains("Name = @Name0", command.CommandText);
        Assert.Contains("Age IN (@Age0, @Age1, @Age2)", command.CommandText);

        Assert.Equal(!string.IsNullOrWhiteSpace(orderByPropertyName), command.CommandText.Contains($"ORDER BY {orderByPropertyName}"));

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
    public void ItBuildsSelectLeftJoinCommand(string? orderByPropertyName)
    {
        // Arrange
        const string LeftTable = "LeftTable";
        const string RightTable = "RightTable";
        const string JoinColumnName = "Id";

        var leftTablePropertyNames = new List<string> { "Id", "Name" };
        var rightTablePropertyNames = new List<string> { "Age", "Address" };

        var conditions = new List<SqliteWhereCondition>
        {
            new SqliteWhereEqualsCondition("Name", "NameValue"),
            new SqliteWhereInCondition("Age", [10, 20, 30]),
        };

        // Act
        var command = this._commandBuilder.BuildSelectLeftJoinCommand(
            LeftTable,
            RightTable,
            JoinColumnName,
            leftTablePropertyNames,
            rightTablePropertyNames,
            conditions,
            extraWhereFilter: null,
            extraParameters: null,
            orderByPropertyName);

        // Assert
        Assert.Contains("SELECT LeftTable.Id, LeftTable.Name, RightTable.Age, RightTable.Address", command.CommandText);
        Assert.Contains("FROM LeftTable", command.CommandText);

        Assert.Contains("LEFT JOIN RightTable ON LeftTable.Id = RightTable.Id", command.CommandText);

        Assert.Contains("Name = @Name0", command.CommandText);
        Assert.Contains("Age IN (@Age0, @Age1, @Age2)", command.CommandText);

        Assert.Equal(!string.IsNullOrWhiteSpace(orderByPropertyName), command.CommandText.Contains($"ORDER BY {orderByPropertyName}"));

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
        var command = this._commandBuilder.BuildDeleteCommand(TableName, conditions);

        // Assert
        Assert.Contains("DELETE FROM [TestTable]", command.CommandText);

        Assert.Contains("Name = @Name0", command.CommandText);
        Assert.Contains("Age IN (@Age0, @Age1, @Age2)", command.CommandText);

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
}
