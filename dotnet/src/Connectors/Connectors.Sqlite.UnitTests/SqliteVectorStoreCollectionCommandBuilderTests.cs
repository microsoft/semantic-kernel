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
        var parameterCollection = new FakeDbParameterCollection();
        this._command = new(parameterCollection: parameterCollection);
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
            new("Column1", "Type1", IsPrimary: true),
            new("Column2", "Type2", IsPrimary: false, Configuration: new() { ["distance_metric"] = "l2" }),
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
            new("Column1", "Type1", IsPrimary: true),
            new("Column2", "Type2", IsPrimary: false, Configuration: new() { ["distance_metric"] = "l2" }),
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

    public void Dispose()
    {
        this._command.Dispose();
        this._connection.Dispose();
    }
}
