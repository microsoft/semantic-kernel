// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.Postgres;
using Pgvector;
using Xunit;
using Xunit.Abstractions;

namespace SemanticKernel.Connectors.UnitTests.Postgres;

public class PostgresVectorStoreCollectionSqlBuilderTests
{
    private readonly ITestOutputHelper _output;

    public PostgresVectorStoreCollectionSqlBuilderTests(ITestOutputHelper output)
    {
        this._output = output;
    }

    [Fact]
    public void TestBuildCreateTableCommand()
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

        var cmdInfo = builder.BuildCreateTableCommand("public", "testcollection", recordDefinition.Properties, ifNotExists: true);

        // Check for expected properties; integration tests will validate the actual SQL.
        Assert.Contains("public.\"testcollection\" (", cmdInfo.CommandText);
        Assert.Contains("IF NOT EXISTS", cmdInfo.CommandText);
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
            ["embedding1"] = new Vector(new float[] { 1.0f, 2.0f, 3.0f }),
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
}
