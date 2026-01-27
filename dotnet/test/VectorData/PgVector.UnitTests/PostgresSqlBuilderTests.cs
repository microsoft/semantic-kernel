// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.PgVector;
using Npgsql;
using Xunit;
using Xunit.Abstractions;

namespace SemanticKernel.Connectors.PgVector.UnitTests;

public class PostgresSqlBuilderTests
{
    private readonly ITestOutputHelper _output;
    private static readonly float[] s_vector = new float[] { 1.0f, 2.0f, 3.0f };

    public PostgresSqlBuilderTests(ITestOutputHelper output)
    {
        this._output = output;
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public void TestBuildCreateTableCommand(bool ifNotExists)
    {
        var recordDefinition = new VectorStoreCollectionDefinition()
        {
            Properties = [
                new VectorStoreKeyProperty("id", typeof(long)),
                new VectorStoreDataProperty("name", typeof(string)),
                new VectorStoreDataProperty("code", typeof(int)),
                new VectorStoreDataProperty("rating", typeof(float?)),
                new VectorStoreDataProperty("description", typeof(string)),
                new VectorStoreDataProperty("parking_is_included", typeof(bool)) { StorageName = "free_parking" },
                new VectorStoreDataProperty("tags", typeof(List<string>)),
                new VectorStoreVectorProperty("embedding1", typeof(ReadOnlyMemory<float>), 10)
                {
                    Dimensions = 10,
                    IndexKind = "hnsw",
                },
                new VectorStoreVectorProperty("embedding2", typeof(ReadOnlyMemory<float>?), 10)
                {
                    Dimensions = 10,
                    IndexKind = "hnsw",
                }
            ]
        };

        var model = new PostgresModelBuilder().BuildDynamic(recordDefinition, defaultEmbeddingGenerator: null);

        var sql = PostgresSqlBuilder.BuildCreateTableSql("public", "testcollection", model, ifNotExists: ifNotExists);

        // Check for expected properties; integration tests will validate the actual SQL.
        Assert.Contains("\"public\".\"testcollection\" (", sql);
        Assert.Contains("\"name\" TEXT", sql);
        Assert.Contains("\"code\" INTEGER NOT NULL", sql);
        Assert.Contains("\"rating\" REAL", sql);
        Assert.Contains("\"description\" TEXT", sql);
        Assert.Contains("\"free_parking\" BOOLEAN NOT NULL", sql);
        Assert.Contains("\"tags\" TEXT[]", sql);
        Assert.Contains("\"description\" TEXT", sql);
        Assert.Contains("\"embedding1\" VECTOR(10) NOT NULL", sql);
        Assert.Contains("\"embedding2\" VECTOR(10)", sql);
        Assert.Contains("PRIMARY KEY (\"id\")", sql);

        if (ifNotExists)
        {
            Assert.Contains("IF NOT EXISTS", sql);
        }

        // Output
        this._output.WriteLine(sql);
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
            Assert.Throws<NotSupportedException>(() => PostgresSqlBuilder.BuildCreateIndexSql("public", "testcollection", vectorColumn, indexKind, distanceFunction, true, ifNotExists));
            Assert.Throws<NotSupportedException>(() => PostgresSqlBuilder.BuildCreateIndexSql("public", "testcollection", vectorColumn, indexKind, distanceFunction, true, ifNotExists));
            return;
        }

        var sql = PostgresSqlBuilder.BuildCreateIndexSql("public", "1testcollection", vectorColumn, indexKind, distanceFunction, true, ifNotExists);

        // Check for expected properties; integration tests will validate the actual SQL.
        Assert.Contains("CREATE INDEX ", sql);
        // Make sure ifNotExists is respected
        if (ifNotExists)
        {
            Assert.Contains("CREATE INDEX IF NOT EXISTS", sql);
        }
        else
        {
            Assert.DoesNotContain("CREATE INDEX IF NOT EXISTS", sql);
        }
        // Make sure the name is escaped, so names starting with a digit are OK.
        Assert.Contains($"\"1testcollection_{vectorColumn}_index\"", sql);

        Assert.Contains("ON \"public\".\"1testcollection\" USING hnsw (\"embedding1\" ", sql);
        if (distanceFunction == null)
        {
            // Check for distance function defaults to cosine distance
            Assert.Contains("vector_cosine_ops)", sql);
        }
        else if (distanceFunction == DistanceFunction.CosineDistance)
        {
            Assert.Contains("vector_cosine_ops)", sql);
        }
        else if (distanceFunction == DistanceFunction.EuclideanDistance)
        {
            Assert.Contains("vector_l2_ops)", sql);
        }
        else
        {
            throw new NotImplementedException($"Test case for Distance function {distanceFunction} is not implemented.");
        }
        // Output
        this._output.WriteLine(sql);
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public void TestBuildCreateNonVectorIndexCommand(bool ifNotExists)
    {
        var sql = PostgresSqlBuilder.BuildCreateIndexSql("schema", "tableName", "columnName", indexKind: "", distanceFunction: "", isVector: false, ifNotExists);

        var expectedCommandText = ifNotExists
            ? "CREATE INDEX IF NOT EXISTS \"tableName_columnName_index\" ON \"schema\".\"tableName\" (\"columnName\")"
            : "CREATE INDEX \"tableName_columnName_index\" ON \"schema\".\"tableName\" (\"columnName\")";

        Assert.Equal(expectedCommandText, sql);
    }

    [Fact]
    public void TestBuildDropTableCommand()
    {
        using var command = new NpgsqlCommand();
        PostgresSqlBuilder.BuildDropTableCommand(command, "public", "testcollection");

        // Check for expected properties; integration tests will validate the actual SQL.
        Assert.Contains("DROP TABLE IF EXISTS \"public\".\"testcollection\"", command.CommandText);

        // Output
        this._output.WriteLine(command.CommandText);
    }

    [Fact]
    public void TestBuildUpsertCommand()
    {
        var recordDefinition = new VectorStoreCollectionDefinition()
        {
            Properties = [
                new VectorStoreKeyProperty("id", typeof(int)),
                new VectorStoreDataProperty("name", typeof(string)),
                new VectorStoreDataProperty("code", typeof(int)),
                new VectorStoreDataProperty("rating", typeof(float?)),
                new VectorStoreDataProperty("description", typeof(string)),
                new VectorStoreDataProperty("parking_is_included", typeof(bool)) { StorageName = "free_parking" },
                new VectorStoreDataProperty("tags", typeof(List<string>)),
                new VectorStoreVectorProperty("embedding1", typeof(ReadOnlyMemory<float>), 10)
                {
                    Dimensions = 10,
                    IndexKind = "hnsw",
                },
                new VectorStoreVectorProperty("embedding2", typeof(ReadOnlyMemory<float>?), 10)
                {
                    Dimensions = 10,
                    IndexKind = "hnsw",
                }
            ]
        };

        var model = new PostgresModelBuilder().BuildDynamic(recordDefinition, defaultEmbeddingGenerator: null);

        var record = new Dictionary<string, object?>
        {
            ["id"] = 123,
            ["name"] = "Hotel",
            ["code"] = 456,
            ["rating"] = 4.5f,
            ["description"] = "Hotel description",
            ["parking_is_included"] = true,
            ["tags"] = new List<string> { "tag1", "tag2" },
            ["embedding1"] = new ReadOnlyMemory<float>(s_vector),
        };

        using var command = new NpgsqlCommand();
        var cmdInfo = PostgresSqlBuilder.BuildUpsertCommand(command, "public", "testcollection", model, [record], generatedEmbeddings: null);

        // Check for expected properties; integration tests will validate the actual SQL.
        Assert.Contains("INSERT INTO \"public\".\"testcollection\" (", command.CommandText);
        Assert.Contains("ON CONFLICT (\"id\")", command.CommandText);
        Assert.Contains("DO UPDATE SET", command.CommandText);
        Assert.NotNull(command.Parameters);

        foreach (var (column, index) in record.Keys.Select((key, index) => (key, index)))
        {
            var expectedValue = column is "embedding1"
                ? PostgresPropertyMapping.MapVectorForStorageModel((ReadOnlyMemory<float>)record[column]!)
                : record[column];
            Assert.Equal(expectedValue, command.Parameters[index].Value);

            // If the key is not the key column, it should be included in the update clause.
            if (column is "id")
            {
                continue;
            }

            var storageName = column is "parking_is_included" ? "free_parking" : column;

            Assert.Contains($"\"{storageName}\" = EXCLUDED.\"{storageName}\"", command.CommandText);
        }

        // Output
        this._output.WriteLine(command.CommandText);
    }

    [Fact]
    public void TestBuildGetCommand()
    {
        // Arrange
        var recordDefinition = new VectorStoreCollectionDefinition()
        {
            Properties = [
                new VectorStoreKeyProperty("id", typeof(long)),
                new VectorStoreDataProperty("name", typeof(string)),
                new VectorStoreDataProperty("code", typeof(int)),
                new VectorStoreDataProperty("rating", typeof(float?)),
                new VectorStoreDataProperty("description", typeof(string)),
                new VectorStoreDataProperty("parking_is_included", typeof(bool)) { StorageName = "free_parking" },
                new VectorStoreDataProperty("tags", typeof(List<string>)),
                new VectorStoreVectorProperty("embedding1", typeof(ReadOnlyMemory<float>), 10)
                {
                    IndexKind = "hnsw",
                },
                new VectorStoreVectorProperty("embedding2", typeof(ReadOnlyMemory<float>?), 10)
                {
                    IndexKind = "hnsw",
                }
            ]
        };

        var model = new PostgresModelBuilder().BuildDynamic(recordDefinition, defaultEmbeddingGenerator: null);

        var key = 123;

        // Act
        using var command = new NpgsqlCommand();
        PostgresSqlBuilder.BuildGetCommand(command, "public", "testcollection", model, key, includeVectors: true);

        // Assert
        Assert.Contains("SELECT", command.CommandText);
        Assert.Contains("\"free_parking\"", command.CommandText);
        Assert.Contains("\"embedding1\"", command.CommandText);
        Assert.Contains("FROM \"public\".\"testcollection\"", command.CommandText);
        Assert.Contains("WHERE \"id\" = $1", command.CommandText);

        // Output
        this._output.WriteLine(command.CommandText);
    }

    [Fact]
    public void TestBuildGetBatchCommand()
    {
        // Arrange
        var recordDefinition = new VectorStoreCollectionDefinition()
        {
            Properties = [
                new VectorStoreKeyProperty("id", typeof(long)),
                new VectorStoreDataProperty("name", typeof(string)),
                new VectorStoreDataProperty("code", typeof(int)),
                new VectorStoreDataProperty("rating", typeof(float?)),
                new VectorStoreDataProperty("description", typeof(string)),
                new VectorStoreDataProperty("parking_is_included", typeof(bool)) { StorageName = "free_parking" },
                new VectorStoreDataProperty("tags", typeof(List<string>)),
                new VectorStoreVectorProperty("embedding1", typeof(ReadOnlyMemory<float>), 10)
                {
                    IndexKind = "hnsw",
                },
                new VectorStoreVectorProperty("embedding2", typeof(ReadOnlyMemory<float>?), 10)
                {
                    IndexKind = "hnsw",
                }
            ]
        };

        var keys = new List<long> { 123, 124 };

        var model = new PostgresModelBuilder().BuildDynamic(recordDefinition, defaultEmbeddingGenerator: null);

        // Act
        using var command = new NpgsqlCommand();
        PostgresSqlBuilder.BuildGetBatchCommand(command, "public", "testcollection", model, keys, includeVectors: true);

        // Assert
        Assert.Contains("SELECT", command.CommandText);
        Assert.Contains("\"code\"", command.CommandText);
        Assert.Contains("\"free_parking\"", command.CommandText);
        Assert.Contains("FROM \"public\".\"testcollection\"", command.CommandText);
        Assert.Contains("WHERE \"id\" = ANY($1)", command.CommandText);
        Assert.NotNull(command.Parameters);
        Assert.Single(command.Parameters);
        Assert.Equal(keys, command.Parameters[0].Value);

        // Output
        this._output.WriteLine(command.CommandText);
    }

    [Fact]
    public void TestBuildDeleteCommand()
    {
        // Arrange
        var key = 123;

        // Act
        using var command = new NpgsqlCommand();
        PostgresSqlBuilder.BuildDeleteCommand(command, "public", "testcollection", "id", key);

        // Assert
        Assert.Contains("DELETE", command.CommandText);
        Assert.Contains("FROM \"public\".\"testcollection\"", command.CommandText);
        Assert.Contains("WHERE \"id\" = $1", command.CommandText);

        // Output
        this._output.WriteLine(command.CommandText);
    }

    [Fact]
    public void TestBuildDeleteBatchCommand()
    {
        // Arrange
        var keys = new List<long> { 123, 124 };

        // Act
        using var command = new NpgsqlCommand();
        PostgresSqlBuilder.BuildDeleteBatchCommand(command, "public", "testcollection", "id", keys);

        // Assert
        Assert.Contains("DELETE", command.CommandText);
        Assert.Contains("FROM \"public\".\"testcollection\"", command.CommandText);
        Assert.Contains("WHERE \"id\" = ANY($1)", command.CommandText);
        Assert.NotNull(command.Parameters);
        Assert.Single(command.Parameters);
        Assert.Equal(keys, command.Parameters[0].Value);

        // Output
        this._output.WriteLine(command.CommandText);
    }
}
