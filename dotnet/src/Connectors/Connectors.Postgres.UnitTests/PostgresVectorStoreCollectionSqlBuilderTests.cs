﻿// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.Postgres;
using Pgvector;
using Xunit;
using Xunit.Abstractions;

namespace SemanticKernel.Connectors.Postgres.UnitTests;

public class PostgresVectorStoreCollectionSqlBuilderTests
{
    private readonly ITestOutputHelper _output;
    private static readonly float[] s_vector = new float[] { 1.0f, 2.0f, 3.0f };

    public PostgresVectorStoreCollectionSqlBuilderTests(ITestOutputHelper output)
    {
        this._output = output;
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public void TestBuildCreateTableCommand(bool ifNotExists)
    {
        var builder = new PostgresVectorStoreCollectionSqlBuilder();

        var recordDefinition = new VectorStoreRecordDefinition()
        {
            Properties = [
                new VectorStoreRecordKeyProperty("id", typeof(long)),
                new VectorStoreRecordDataProperty("name", typeof(string)),
                new VectorStoreRecordDataProperty("code", typeof(int)),
                new VectorStoreRecordDataProperty("rating", typeof(float?)),
                new VectorStoreRecordDataProperty("description", typeof(string)),
                new VectorStoreRecordDataProperty("parking_is_included", typeof(bool)),
                new VectorStoreRecordDataProperty("tags", typeof(List<string>)),
                new VectorStoreRecordVectorProperty("embedding1", typeof(ReadOnlyMemory<float>))
                {
                    Dimensions = 10,
                    IndexKind = "hnsw",
                },
                new VectorStoreRecordVectorProperty("embedding2", typeof(ReadOnlyMemory<float>?))
                {
                    Dimensions = 10,
                    IndexKind = "hnsw",
                }
            ]
        };

        var cmdInfo = builder.BuildCreateTableCommand("public", "testcollection", recordDefinition.Properties, ifNotExists: ifNotExists);

        // Check for expected properties; integration tests will validate the actual SQL.
        Assert.Contains("public.\"testcollection\" (", cmdInfo.CommandText);
        Assert.Contains("\"name\" TEXT", cmdInfo.CommandText);
        Assert.Contains("\"code\" INTEGER NOT NULL", cmdInfo.CommandText);
        Assert.Contains("\"rating\" REAL", cmdInfo.CommandText);
        Assert.Contains("\"description\" TEXT", cmdInfo.CommandText);
        Assert.Contains("\"parking_is_included\" BOOLEAN NOT NULL", cmdInfo.CommandText);
        Assert.Contains("\"tags\" TEXT[]", cmdInfo.CommandText);
        Assert.Contains("\"description\" TEXT", cmdInfo.CommandText);
        Assert.Contains("\"embedding1\" VECTOR(10) NOT NULL", cmdInfo.CommandText);
        Assert.Contains("\"embedding2\" VECTOR(10)", cmdInfo.CommandText);
        Assert.Contains("PRIMARY KEY (\"id\")", cmdInfo.CommandText);

        if (ifNotExists)
        {
            Assert.Contains("IF NOT EXISTS", cmdInfo.CommandText);
        }

        // Output
        this._output.WriteLine(cmdInfo.CommandText);
    }

    [Fact]
    public void TestBuildDropTableCommand()
    {
        var builder = new PostgresVectorStoreCollectionSqlBuilder();

        var cmdInfo = builder.BuildDropTableCommand("public", "testcollection");

        // Check for expected properties; integration tests will validate the actual SQL.
        Assert.Contains("DROP TABLE IF EXISTS public.\"testcollection\"", cmdInfo.CommandText);

        // Output
        this._output.WriteLine(cmdInfo.CommandText);
    }

    [Fact]
    public void TestBuildUpsertCommand()
    {
        var builder = new PostgresVectorStoreCollectionSqlBuilder();

        var row = new Dictionary<string, object?>()
        {
            ["id"] = 123,
            ["name"] = "Hotel",
            ["code"] = 456,
            ["rating"] = 4.5f,
            ["description"] = "Hotel description",
            ["parking_is_included"] = true,
            ["tags"] = new List<string> { "tag1", "tag2" },
            ["embedding1"] = new Vector(s_vector),
        };

        var keyColumn = "id";

        var cmdInfo = builder.BuildUpsertCommand("public", "testcollection", keyColumn, row);

        // Check for expected properties; integration tests will validate the actual SQL.
        Assert.Contains("INSERT INTO public.\"testcollection\" (", cmdInfo.CommandText);
        Assert.Contains("ON CONFLICT (\"id\")", cmdInfo.CommandText);
        Assert.Contains("DO UPDATE SET", cmdInfo.CommandText);
        Assert.NotNull(cmdInfo.Parameters);

        foreach (var (key, index) in row.Keys.Select((key, index) => (key, index)))
        {
            Assert.Equal(row[key], cmdInfo.Parameters[index].Value);
            // If the key is not the key column, it should be included in the update clause.
            if (key != keyColumn)
            {
                Assert.Contains($"\"{key}\"=${index + 1}", cmdInfo.CommandText);
            }
        }

        // Output
        this._output.WriteLine(cmdInfo.CommandText);
    }

    [Fact]
    public void TestBuildUpsertBatchCommand()
    {
        var builder = new PostgresVectorStoreCollectionSqlBuilder();

        var rows = new List<Dictionary<string, object?>>()
        {
            new()
            {
                ["id"] = 123,
                ["name"] = "Hotel",
                ["code"] = 456,
                ["rating"] = 4.5f,
                ["description"] = "Hotel description",
                ["parking_is_included"] = true,
                ["tags"] = new List<string> { "tag1", "tag2" },
                ["embedding1"] = new Vector(s_vector),
            },
            new()
            {
                ["id"] = 124,
                ["name"] = "Motel",
                ["code"] = 457,
                ["rating"] = 4.6f,
                ["description"] = "Motel description",
                ["parking_is_included"] = false,
                ["tags"] = new List<string> { "tag3", "tag4" },
                ["embedding1"] = new Vector(s_vector),
            },
        };

        var keyColumn = "id";
        var columnCount = rows.First().Count;

        var cmdInfo = builder.BuildUpsertBatchCommand("public", "testcollection", keyColumn, rows);

        // Check for expected properties; integration tests will validate the actual SQL.
        Assert.Contains("INSERT INTO public.\"testcollection\" (", cmdInfo.CommandText);
        Assert.Contains("ON CONFLICT (\"id\")", cmdInfo.CommandText);
        Assert.Contains("DO UPDATE SET", cmdInfo.CommandText);
        Assert.NotNull(cmdInfo.Parameters);

        foreach (var (row, rowIndex) in rows.Select((row, rowIndex) => (row, rowIndex)))
        {
            foreach (var (column, columnIndex) in row.Keys.Select((key, index) => (key, index)))
            {
                Assert.Equal(row[column], cmdInfo.Parameters[columnIndex + (rowIndex * columnCount)].Value);
                // If the key is not the key column, it should be included in the update clause.
                if (column != keyColumn)
                {
                    Assert.Contains($"\"{column}\" = EXCLUDED.\"{column}\"", cmdInfo.CommandText);
                }
            }
        }

        // Output
        this._output.WriteLine(cmdInfo.CommandText);
    }

    [Fact]
    public void TestBuildGetCommand()
    {
        // Arrange
        var builder = new PostgresVectorStoreCollectionSqlBuilder();

        var recordDefinition = new VectorStoreRecordDefinition()
        {
            Properties = [
                new VectorStoreRecordKeyProperty("id", typeof(long)),
                new VectorStoreRecordDataProperty("name", typeof(string)),
                new VectorStoreRecordDataProperty("code", typeof(int)),
                new VectorStoreRecordDataProperty("rating", typeof(float?)),
                new VectorStoreRecordDataProperty("description", typeof(string)),
                new VectorStoreRecordDataProperty("parking_is_included", typeof(bool)),
                new VectorStoreRecordDataProperty("tags", typeof(List<string>)),
                new VectorStoreRecordVectorProperty("embedding1", typeof(ReadOnlyMemory<float>))
                {
                    Dimensions = 10,
                    IndexKind = "hnsw",
                },
                new VectorStoreRecordVectorProperty("embedding2", typeof(ReadOnlyMemory<float>?))
                {
                    Dimensions = 10,
                    IndexKind = "hnsw",
                }
            ]
        };

        var key = 123;

        // Act
        var cmdInfo = builder.BuildGetCommand("public", "testcollection", recordDefinition.Properties, key, includeVectors: true);

        // Assert
        Assert.Contains("SELECT", cmdInfo.CommandText);
        Assert.Contains("FROM public.\"testcollection\"", cmdInfo.CommandText);
        Assert.Contains("WHERE \"id\" = $1", cmdInfo.CommandText);

        // Output
        this._output.WriteLine(cmdInfo.CommandText);
    }

    [Fact]
    public void TestBuildGetBatchCommand()
    {
        // Arrange
        var builder = new PostgresVectorStoreCollectionSqlBuilder();

        var recordDefinition = new VectorStoreRecordDefinition()
        {
            Properties = [
                new VectorStoreRecordKeyProperty("id", typeof(long)),
                new VectorStoreRecordDataProperty("name", typeof(string)),
                new VectorStoreRecordDataProperty("code", typeof(int)),
                new VectorStoreRecordDataProperty("rating", typeof(float?)),
                new VectorStoreRecordDataProperty("description", typeof(string)),
                new VectorStoreRecordDataProperty("parking_is_included", typeof(bool)),
                new VectorStoreRecordDataProperty("tags", typeof(List<string>)),
                new VectorStoreRecordVectorProperty("embedding1", typeof(ReadOnlyMemory<float>))
                {
                    Dimensions = 10,
                    IndexKind = "hnsw",
                },
                new VectorStoreRecordVectorProperty("embedding2", typeof(ReadOnlyMemory<float>?))
                {
                    Dimensions = 10,
                    IndexKind = "hnsw",
                }
            ]
        };

        var keys = new List<long> { 123, 124 };

        // Act
        var cmdInfo = builder.BuildGetBatchCommand("public", "testcollection", recordDefinition.Properties, keys, includeVectors: true);

        // Assert
        Assert.Contains("SELECT", cmdInfo.CommandText);
        Assert.Contains("FROM public.\"testcollection\"", cmdInfo.CommandText);
        Assert.Contains("WHERE \"id\" = ANY($1)", cmdInfo.CommandText);
        Assert.NotNull(cmdInfo.Parameters);
        Assert.Single(cmdInfo.Parameters);
        Assert.Equal(keys, cmdInfo.Parameters[0].Value);

        // Output
        this._output.WriteLine(cmdInfo.CommandText);
    }

    [Fact]
    public void TestBuildDeleteCommand()
    {
        // Arrange
        var builder = new PostgresVectorStoreCollectionSqlBuilder();

        var key = 123;

        // Act
        var cmdInfo = builder.BuildDeleteCommand("public", "testcollection", "id", key);

        // Assert
        Assert.Contains("DELETE", cmdInfo.CommandText);
        Assert.Contains("FROM public.\"testcollection\"", cmdInfo.CommandText);
        Assert.Contains("WHERE \"id\" = $1", cmdInfo.CommandText);

        // Output
        this._output.WriteLine(cmdInfo.CommandText);
    }

    [Fact]
    public void TestBuildDeleteBatchCommand()
    {
        // Arrange
        var builder = new PostgresVectorStoreCollectionSqlBuilder();

        var keys = new List<long> { 123, 124 };

        // Act
        var cmdInfo = builder.BuildDeleteBatchCommand("public", "testcollection", "id", keys);

        // Assert
        Assert.Contains("DELETE", cmdInfo.CommandText);
        Assert.Contains("FROM public.\"testcollection\"", cmdInfo.CommandText);
        Assert.Contains("WHERE \"id\" = ANY($1)", cmdInfo.CommandText);
        Assert.NotNull(cmdInfo.Parameters);
        Assert.Single(cmdInfo.Parameters);
        Assert.Equal(keys, cmdInfo.Parameters[0].Value);

        // Output
        this._output.WriteLine(cmdInfo.CommandText);
    }

    [Fact]
    public void TestBuildGetNearestMatchCommand()
    {
        // Arrange
        var builder = new PostgresVectorStoreCollectionSqlBuilder();

        var vectorProperty = new VectorStoreRecordVectorProperty("embedding1", typeof(ReadOnlyMemory<float>))
        {
            Dimensions = 10,
            IndexKind = "hnsw",
        };

        var recordDefinition = new VectorStoreRecordDefinition()
        {
            Properties = [
                new VectorStoreRecordKeyProperty("id", typeof(long)),
                new VectorStoreRecordDataProperty("name", typeof(string)),
                new VectorStoreRecordDataProperty("code", typeof(int)),
                new VectorStoreRecordDataProperty("rating", typeof(float?)),
                new VectorStoreRecordDataProperty("description", typeof(string)),
                new VectorStoreRecordDataProperty("parking_is_included", typeof(bool)),
                new VectorStoreRecordDataProperty("tags", typeof(List<string>)),
                vectorProperty,
                new VectorStoreRecordVectorProperty("embedding2", typeof(ReadOnlyMemory<float>?))
                {
                    Dimensions = 10,
                    IndexKind = "hnsw",
                }
            ]
        };

        var vector = new Vector(s_vector);

        // Act
        var cmdInfo = builder.BuildGetNearestMatchCommand("public", "testcollection",
            properties: recordDefinition.Properties,
            vectorProperty: vectorProperty,
            vectorValue: vector,
            filter: null,
            skip: null,
            withEmbeddings: true,
            limit: 10);

        // Assert
        Assert.Contains("SELECT", cmdInfo.CommandText);
        Assert.Contains("FROM public.\"testcollection\"", cmdInfo.CommandText);
        Assert.Contains("ORDER BY", cmdInfo.CommandText);
        Assert.Contains("LIMIT 10", cmdInfo.CommandText);

        // Output
        this._output.WriteLine(cmdInfo.CommandText);
    }
}