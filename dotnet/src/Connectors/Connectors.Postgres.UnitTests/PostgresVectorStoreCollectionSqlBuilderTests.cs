// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using Microsoft.Extensions.VectorData;
using Microsoft.Extensions.VectorData.ConnectorSupport;
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
        var recordDefinition = new VectorStoreRecordDefinition()
        {
            Properties = [
                new VectorStoreRecordKeyProperty("id", typeof(long)),
                new VectorStoreRecordDataProperty("name", typeof(string)),
                new VectorStoreRecordDataProperty("code", typeof(int)),
                new VectorStoreRecordDataProperty("rating", typeof(float?)),
                new VectorStoreRecordDataProperty("description", typeof(string)),
                new VectorStoreRecordDataProperty("parking_is_included", typeof(bool)) { StoragePropertyName = "free_parking" },
                new VectorStoreRecordDataProperty("tags", typeof(List<string>)),
                new VectorStoreRecordVectorProperty("embedding1", typeof(ReadOnlyMemory<float>), 10)
                {
                    Dimensions = 10,
                    IndexKind = "hnsw",
                },
                new VectorStoreRecordVectorProperty("embedding2", typeof(ReadOnlyMemory<float>?), 10)
                {
                    Dimensions = 10,
                    IndexKind = "hnsw",
                }
            ]
        };

        var model = new VectorStoreRecordModelBuilder(PostgresConstants.ModelBuildingOptions).Build(typeof(Dictionary<string, object?>), recordDefinition, defaultEmbeddingGenerator: null);

        var cmdInfo = PostgresSqlBuilder.BuildCreateTableCommand("public", "testcollection", model, ifNotExists: ifNotExists);

        // Check for expected properties; integration tests will validate the actual SQL.
        Assert.Contains("public.\"testcollection\" (", cmdInfo.CommandText);
        Assert.Contains("\"name\" TEXT", cmdInfo.CommandText);
        Assert.Contains("\"code\" INTEGER NOT NULL", cmdInfo.CommandText);
        Assert.Contains("\"rating\" REAL", cmdInfo.CommandText);
        Assert.Contains("\"description\" TEXT", cmdInfo.CommandText);
        Assert.Contains("\"free_parking\" BOOLEAN NOT NULL", cmdInfo.CommandText);
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

    [Theory]
    [InlineData(IndexKind.Hnsw, DistanceFunction.EuclideanDistance, true)]
    [InlineData(IndexKind.Hnsw, DistanceFunction.EuclideanDistance, false)]
    [InlineData(IndexKind.IvfFlat, DistanceFunction.DotProductSimilarity, true)]
    [InlineData(IndexKind.IvfFlat, DistanceFunction.DotProductSimilarity, false)]
    [InlineData(IndexKind.Hnsw, DistanceFunction.CosineDistance, true)]
    [InlineData(IndexKind.Hnsw, DistanceFunction.CosineDistance, false)]
    public void TestBuildCreateIndexCommand(string indexKind, string distanceFunction, bool ifNotExists)
    {
        var vectorColumn = "embedding1";

        if (indexKind != IndexKind.Hnsw)
        {
            Assert.Throws<NotSupportedException>(() => PostgresSqlBuilder.BuildCreateIndexCommand("public", "testcollection", vectorColumn, indexKind, distanceFunction, true, ifNotExists));
            Assert.Throws<NotSupportedException>(() => PostgresSqlBuilder.BuildCreateIndexCommand("public", "testcollection", vectorColumn, indexKind, distanceFunction, true, ifNotExists));
            return;
        }

        var cmdInfo = PostgresSqlBuilder.BuildCreateIndexCommand("public", "1testcollection", vectorColumn, indexKind, distanceFunction, true, ifNotExists);

        // Check for expected properties; integration tests will validate the actual SQL.
        Assert.Contains("CREATE INDEX ", cmdInfo.CommandText);
        // Make sure ifNotExists is respected
        if (ifNotExists)
        {
            Assert.Contains("CREATE INDEX IF NOT EXISTS", cmdInfo.CommandText);
        }
        else
        {
            Assert.DoesNotContain("CREATE INDEX IF NOT EXISTS", cmdInfo.CommandText);
        }
        // Make sure the name is escaped, so names starting with a digit are OK.
        Assert.Contains($"\"1testcollection_{vectorColumn}_index\"", cmdInfo.CommandText);

        Assert.Contains("ON public.\"1testcollection\" USING hnsw (\"embedding1\" ", cmdInfo.CommandText);
        if (distanceFunction == null)
        {
            // Check for distance function defaults to cosine distance
            Assert.Contains("vector_cosine_ops)", cmdInfo.CommandText);
        }
        else if (distanceFunction == DistanceFunction.CosineDistance)
        {
            Assert.Contains("vector_cosine_ops)", cmdInfo.CommandText);
        }
        else if (distanceFunction == DistanceFunction.EuclideanDistance)
        {
            Assert.Contains("vector_l2_ops)", cmdInfo.CommandText);
        }
        else
        {
            throw new NotImplementedException($"Test case for Distance function {distanceFunction} is not implemented.");
        }
        // Output
        this._output.WriteLine(cmdInfo.CommandText);
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public void TestBuildCreateNonVectorIndexCommand(bool ifNotExists)
    {
        var cmdInfo = PostgresSqlBuilder.BuildCreateIndexCommand("schema", "tableName", "columnName", indexKind: "", distanceFunction: "", isVector: false, ifNotExists);

        var expectedCommandText = ifNotExists
            ? "CREATE INDEX IF NOT EXISTS \"tableName_columnName_index\" ON schema.\"tableName\" (\"columnName\");"
            : "CREATE INDEX \"tableName_columnName_index\" ON schema.\"tableName\" (\"columnName\");";

        Assert.Equal(expectedCommandText, cmdInfo.CommandText);
    }

    [Fact]
    public void TestBuildDropTableCommand()
    {
        var cmdInfo = PostgresSqlBuilder.BuildDropTableCommand("public", "testcollection");

        // Check for expected properties; integration tests will validate the actual SQL.
        Assert.Contains("DROP TABLE IF EXISTS public.\"testcollection\"", cmdInfo.CommandText);

        // Output
        this._output.WriteLine(cmdInfo.CommandText);
    }

    [Fact]
    public void TestBuildUpsertCommand()
    {
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

        var cmdInfo = PostgresSqlBuilder.BuildUpsertCommand("public", "testcollection", keyColumn, row);

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

        var cmdInfo = PostgresSqlBuilder.BuildUpsertBatchCommand("public", "testcollection", keyColumn, rows);

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
        var recordDefinition = new VectorStoreRecordDefinition()
        {
            Properties = [
                new VectorStoreRecordKeyProperty("id", typeof(long)),
                new VectorStoreRecordDataProperty("name", typeof(string)),
                new VectorStoreRecordDataProperty("code", typeof(int)),
                new VectorStoreRecordDataProperty("rating", typeof(float?)),
                new VectorStoreRecordDataProperty("description", typeof(string)),
                new VectorStoreRecordDataProperty("parking_is_included", typeof(bool)) { StoragePropertyName = "free_parking" },
                new VectorStoreRecordDataProperty("tags", typeof(List<string>)),
                new VectorStoreRecordVectorProperty("embedding1", typeof(ReadOnlyMemory<float>), 10)
                {
                    IndexKind = "hnsw",
                },
                new VectorStoreRecordVectorProperty("embedding2", typeof(ReadOnlyMemory<float>?), 10)
                {
                    IndexKind = "hnsw",
                }
            ]
        };

        var model = new VectorStoreRecordModelBuilder(PostgresConstants.ModelBuildingOptions).Build(typeof(Dictionary<string, object?>), recordDefinition, defaultEmbeddingGenerator: null);

        var key = 123;

        // Act
        var cmdInfo = PostgresSqlBuilder.BuildGetCommand("public", "testcollection", model, key, includeVectors: true);

        // Assert
        Assert.Contains("SELECT", cmdInfo.CommandText);
        Assert.Contains("\"free_parking\"", cmdInfo.CommandText);
        Assert.Contains("\"embedding1\"", cmdInfo.CommandText);
        Assert.Contains("FROM public.\"testcollection\"", cmdInfo.CommandText);
        Assert.Contains("WHERE \"id\" = $1", cmdInfo.CommandText);

        // Output
        this._output.WriteLine(cmdInfo.CommandText);
    }

    [Fact]
    public void TestBuildGetBatchCommand()
    {
        // Arrange
        var recordDefinition = new VectorStoreRecordDefinition()
        {
            Properties = [
                new VectorStoreRecordKeyProperty("id", typeof(long)),
                new VectorStoreRecordDataProperty("name", typeof(string)),
                new VectorStoreRecordDataProperty("code", typeof(int)),
                new VectorStoreRecordDataProperty("rating", typeof(float?)),
                new VectorStoreRecordDataProperty("description", typeof(string)),
                new VectorStoreRecordDataProperty("parking_is_included", typeof(bool)) { StoragePropertyName = "free_parking" },
                new VectorStoreRecordDataProperty("tags", typeof(List<string>)),
                new VectorStoreRecordVectorProperty("embedding1", typeof(ReadOnlyMemory<float>), 10)
                {
                    IndexKind = "hnsw",
                },
                new VectorStoreRecordVectorProperty("embedding2", typeof(ReadOnlyMemory<float>?), 10)
                {
                    IndexKind = "hnsw",
                }
            ]
        };

        var keys = new List<long> { 123, 124 };

        var model = new VectorStoreRecordModelBuilder(PostgresConstants.ModelBuildingOptions).Build(typeof(Dictionary<string, object?>), recordDefinition, defaultEmbeddingGenerator: null);

        // Act
        var cmdInfo = PostgresSqlBuilder.BuildGetBatchCommand("public", "testcollection", model, keys, includeVectors: true);

        // Assert
        Assert.Contains("SELECT", cmdInfo.CommandText);
        Assert.Contains("\"code\"", cmdInfo.CommandText);
        Assert.Contains("\"free_parking\"", cmdInfo.CommandText);
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
        var key = 123;

        // Act
        var cmdInfo = PostgresSqlBuilder.BuildDeleteCommand("public", "testcollection", "id", key);

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
        var keys = new List<long> { 123, 124 };

        // Act
        var cmdInfo = PostgresSqlBuilder.BuildDeleteBatchCommand("public", "testcollection", "id", keys);

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
}
