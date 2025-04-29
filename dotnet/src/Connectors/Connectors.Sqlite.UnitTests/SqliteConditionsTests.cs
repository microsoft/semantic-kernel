// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.SemanticKernel.Connectors.Sqlite;
using Xunit;

namespace SemanticKernel.Connectors.Sqlite.UnitTests;

/// <summary>
/// Unit tests for SQLite condition classes.
/// </summary>
public sealed class SqliteConditionsTests
{
    [Fact]
    public void SqliteWhereEqualsConditionWithoutParameterNamesThrowsException()
    {
        // Arrange
        var condition = new SqliteWhereEqualsCondition("Name", "Value");

        // Act & Assert
        Assert.Throws<ArgumentException>(() => condition.BuildQuery([]));
    }

    [Theory]
    [InlineData(null, "\"Name\" = @Name0")]
    [InlineData("", "\"Name\" = @Name0")]
    [InlineData("TableName", "\"TableName\".\"Name\" = @Name0")]
    public void SqliteWhereEqualsConditionBuildsValidQuery(string? tableName, string expectedQuery)
    {
        // Arrange
        var condition = new SqliteWhereEqualsCondition("Name", "Value") { TableName = tableName };

        // Act
        var query = condition.BuildQuery(["@Name0"]);

        // Assert
        Assert.Equal(expectedQuery, query);
    }

    [Fact]
    public void SqliteWhereInConditionWithoutParameterNamesThrowsException()
    {
        // Arrange
        var condition = new SqliteWhereInCondition("Name", ["Value1", "Value2"]);

        // Act & Assert
        Assert.Throws<ArgumentException>(() => condition.BuildQuery([]));
    }

    [Theory]
    [InlineData(null, "\"Name\" IN (@Name0, @Name1)")]
    [InlineData("", "\"Name\" IN (@Name0, @Name1)")]
    [InlineData("TableName", "\"TableName\".\"Name\" IN (@Name0, @Name1)")]
    public void SqliteWhereInConditionBuildsValidQuery(string? tableName, string expectedQuery)
    {
        // Arrange
        var condition = new SqliteWhereInCondition("Name", ["Value1", "Value2"]) { TableName = tableName };

        // Act
        var query = condition.BuildQuery(["@Name0", "@Name1"]);

        // Assert
        Assert.Equal(expectedQuery, query);
    }

    [Fact]
    public void SqliteWhereMatchConditionWithoutParameterNamesThrowsException()
    {
        // Arrange
        var condition = new SqliteWhereMatchCondition("Name", "Value");

        // Act & Assert
        Assert.Throws<ArgumentException>(() => condition.BuildQuery([]));
    }

    [Theory]
    [InlineData(null, "\"Name\" MATCH @Name0")]
    [InlineData("", "\"Name\" MATCH @Name0")]
    [InlineData("TableName", "\"TableName\".\"Name\" MATCH @Name0")]
    public void SqliteWhereMatchConditionBuildsValidQuery(string? tableName, string expectedQuery)
    {
        // Arrange
        var condition = new SqliteWhereMatchCondition("Name", "Value") { TableName = tableName };

        // Act
        var query = condition.BuildQuery(["@Name0"]);

        // Assert
        Assert.Equal(expectedQuery, query);
    }
}
