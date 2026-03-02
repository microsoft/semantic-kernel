// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using Microsoft.Extensions.VectorData;
using Microsoft.Extensions.VectorData.ProviderServices;
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

        var sql = PostgresSqlBuilder.BuildCreateTableSql(schema: null, "testcollection", model, pgVersion: new Version(18, 0), ifNotExists: ifNotExists);

        // Check for expected properties; integration tests will validate the actual SQL.
        Assert.Contains("\"testcollection\" (", sql);
        Assert.DoesNotContain("\"public\"", sql);
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

    [Fact]
    public void TestBuildCreateTableCommand_WithTimestampStoreType()
    {
        var recordDefinition = new VectorStoreCollectionDefinition()
        {
            Properties = [
                new VectorStoreKeyProperty("id", typeof(long)),
                new VectorStoreDataProperty("created_utc", typeof(DateTime)),
                new VectorStoreDataProperty("created_local", typeof(DateTime)).WithStoreType("timestamp"),
                new VectorStoreDataProperty("created_nullable", typeof(DateTime?)).WithStoreType("timestamp without time zone"),
                new VectorStoreVectorProperty("embedding", typeof(ReadOnlyMemory<float>), 10)
            ]
        };

        var model = new PostgresModelBuilder().BuildDynamic(recordDefinition, defaultEmbeddingGenerator: null);

        var sql = PostgresSqlBuilder.BuildCreateTableSql(schema: null, "testcollection", model, pgVersion: new Version(18, 0));

        Assert.Contains("\"created_utc\" TIMESTAMPTZ NOT NULL", sql);
        Assert.Contains("\"created_local\" TIMESTAMP NOT NULL", sql);
        Assert.Contains("\"created_nullable\" TIMESTAMP", sql);
        // Make sure it's TIMESTAMP (not TIMESTAMPTZ) for the nullable one
        var idx = sql.IndexOf("\"created_nullable\"", StringComparison.Ordinal);
        var fragment = sql.Substring(idx, sql.IndexOf('\n', idx) - idx);
        Assert.DoesNotContain("TIMESTAMPTZ", fragment);

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
            Assert.Throws<NotSupportedException>(() => PostgresSqlBuilder.BuildCreateIndexSql(schema: null, "testcollection", vectorColumn, indexKind, distanceFunction, isVector: true, isFullText: false, fullTextLanguage: null, ifNotExists));
            Assert.Throws<NotSupportedException>(() => PostgresSqlBuilder.BuildCreateIndexSql(schema: null, "testcollection", vectorColumn, indexKind, distanceFunction, isVector: true, isFullText: false, fullTextLanguage: null, ifNotExists));
            return;
        }

        var sql = PostgresSqlBuilder.BuildCreateIndexSql(schema: null, "1testcollection", vectorColumn, indexKind, distanceFunction, isVector: true, isFullText: false, fullTextLanguage: null, ifNotExists);

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

        Assert.Contains("ON \"1testcollection\" USING hnsw (\"embedding1\" ", sql);
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
        var sql = PostgresSqlBuilder.BuildCreateIndexSql("schema", "tableName", "columnName", indexKind: "", distanceFunction: "", isVector: false, isFullText: false, fullTextLanguage: null, ifNotExists);

        var expectedCommandText = ifNotExists
            ? "CREATE INDEX IF NOT EXISTS \"tableName_columnName_index\" ON \"schema\".\"tableName\" (\"columnName\")"
            : "CREATE INDEX \"tableName_columnName_index\" ON \"schema\".\"tableName\" (\"columnName\")";

        Assert.Equal(expectedCommandText, sql);
    }

    [Theory]
    [InlineData(null, "english")]  // Default language
    [InlineData("spanish", "spanish")]
    [InlineData("german", "german")]
    public void TestBuildCreateFullTextIndexCommand(string? configuredLanguage, string expectedLanguage)
    {
        var sql = PostgresSqlBuilder.BuildCreateIndexSql("schema", "tableName", "content", indexKind: "", distanceFunction: "", isVector: false, isFullText: true, fullTextLanguage: configuredLanguage, ifNotExists: true);

        var expectedCommandText = $"CREATE INDEX IF NOT EXISTS \"tableName_content_index\" ON \"schema\".\"tableName\" USING GIN (to_tsvector('{expectedLanguage}', \"content\"))";

        Assert.Equal(expectedCommandText, sql);
    }

    [Fact]
    public void TestBuildCreateFullTextIndexCommand_EscapesSingleQuotes()
    {
        // Verify that single quotes in the language name are properly escaped to prevent SQL injection
        var sql = PostgresSqlBuilder.BuildCreateIndexSql("schema", "tableName", "content", indexKind: "", distanceFunction: "", isVector: false, isFullText: true, fullTextLanguage: "test'injection", ifNotExists: true);

        var expectedCommandText = "CREATE INDEX IF NOT EXISTS \"tableName_content_index\" ON \"schema\".\"tableName\" USING GIN (to_tsvector('test''injection', \"content\"))";

        Assert.Equal(expectedCommandText, sql);
    }

    [Fact]
    public void TestBuildDropTableCommand()
    {
        using var command = new NpgsqlCommand();
        PostgresSqlBuilder.BuildDropTableCommand(command, schema: null, "testcollection");

        // Check for expected properties; integration tests will validate the actual SQL.
        Assert.Contains("DROP TABLE IF EXISTS \"testcollection\"", command.CommandText);
        Assert.DoesNotContain("\"public\"", command.CommandText);

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

        using var batch = new NpgsqlBatch();
        _ = PostgresSqlBuilder.BuildUpsertCommand<int>(batch, schema: null, "testcollection", model, [record], generatedEmbeddings: null);

        // Check for expected properties; integration tests will validate the actual SQL.
        Assert.Single(batch.BatchCommands);
        var command = batch.BatchCommands[0];
        Assert.Contains("INSERT INTO \"testcollection\" (", command.CommandText);
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
        PostgresSqlBuilder.BuildGetCommand(command, schema: null, "testcollection", model, key, includeVectors: true);

        // Assert
        Assert.Contains("SELECT", command.CommandText);
        Assert.Contains("\"free_parking\"", command.CommandText);
        Assert.Contains("\"embedding1\"", command.CommandText);
        Assert.Contains("FROM \"testcollection\"", command.CommandText);
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
        PostgresSqlBuilder.BuildGetBatchCommand(command, schema: null, "testcollection", model, keys, includeVectors: true);

        // Assert
        Assert.Contains("SELECT", command.CommandText);
        Assert.Contains("\"code\"", command.CommandText);
        Assert.Contains("\"free_parking\"", command.CommandText);
        Assert.Contains("FROM \"testcollection\"", command.CommandText);
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
        PostgresSqlBuilder.BuildDeleteCommand(command, schema: null, "testcollection", "id", key);

        // Assert
        Assert.Contains("DELETE", command.CommandText);
        Assert.Contains("FROM \"testcollection\"", command.CommandText);
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
        var keyProperty = new KeyPropertyModel("id", typeof(long));
        PostgresSqlBuilder.BuildDeleteBatchCommand(command, schema: null, "testcollection", keyProperty, keys);

        // Assert
        Assert.Contains("DELETE", command.CommandText);
        Assert.Contains("FROM \"testcollection\"", command.CommandText);
        Assert.Contains("WHERE \"id\" = ANY($1)", command.CommandText);
        Assert.NotNull(command.Parameters);
        Assert.Single(command.Parameters);
        Assert.Equal(keys, command.Parameters[0].Value);

        // Output
        this._output.WriteLine(command.CommandText);
    }

    #region Schema-specified tests

    [Theory]
    [InlineData(null, "public")]
    [InlineData("myschema", "myschema")]
    public void TestBuildDoesTableExistCommand(string? schema, string expectedSchema)
    {
        using var command = new NpgsqlCommand();
        PostgresSqlBuilder.BuildDoesTableExistCommand(command, schema, "testcollection");

        Assert.Contains("table_schema = $1", command.CommandText);
        Assert.Contains("table_name = $2", command.CommandText);
        Assert.Equal(2, command.Parameters.Count);
        Assert.Equal(expectedSchema, command.Parameters[0].Value);
        Assert.Equal("testcollection", command.Parameters[1].Value);

        this._output.WriteLine(command.CommandText);
    }

    [Theory]
    [InlineData(null, "public")]
    [InlineData("myschema", "myschema")]
    public void TestBuildGetTablesCommand(string? schema, string expectedSchema)
    {
        using var command = new NpgsqlCommand();
        PostgresSqlBuilder.BuildGetTablesCommand(command, schema);

        Assert.Contains("table_schema = $1", command.CommandText);
        Assert.Single(command.Parameters);
        Assert.Equal(expectedSchema, command.Parameters[0].Value);

        this._output.WriteLine(command.CommandText);
    }

    [Fact]
    public void TestBuildCreateTableCommand_WithSchema()
    {
        var recordDefinition = new VectorStoreCollectionDefinition()
        {
            Properties = [
                new VectorStoreKeyProperty("id", typeof(long)),
                new VectorStoreDataProperty("name", typeof(string)),
                new VectorStoreVectorProperty("embedding1", typeof(ReadOnlyMemory<float>), 10) { IndexKind = "hnsw" }
            ]
        };

        var model = new PostgresModelBuilder().BuildDynamic(recordDefinition, defaultEmbeddingGenerator: null);

        var sql = PostgresSqlBuilder.BuildCreateTableSql(schema: "myschema", "testcollection", model, pgVersion: new Version(18, 0));

        Assert.Contains("\"myschema\".\"testcollection\"", sql);

        this._output.WriteLine(sql);
    }

    [Fact]
    public void TestBuildCreateIndexCommand_WithSchema()
    {
        var sql = PostgresSqlBuilder.BuildCreateIndexSql("myschema", "testcollection", "embedding1", IndexKind.Hnsw, DistanceFunction.CosineDistance, isVector: true, isFullText: false, fullTextLanguage: null, ifNotExists: true);

        Assert.Contains("ON \"myschema\".\"testcollection\"", sql);

        this._output.WriteLine(sql);
    }

    [Fact]
    public void TestBuildDropTableCommand_WithSchema()
    {
        using var command = new NpgsqlCommand();
        PostgresSqlBuilder.BuildDropTableCommand(command, schema: "myschema", "testcollection");

        Assert.Contains("DROP TABLE IF EXISTS \"myschema\".\"testcollection\"", command.CommandText);

        this._output.WriteLine(command.CommandText);
    }

    [Fact]
    public void TestBuildUpsertCommand_WithSchema()
    {
        var recordDefinition = new VectorStoreCollectionDefinition()
        {
            Properties = [
                new VectorStoreKeyProperty("id", typeof(int)),
                new VectorStoreDataProperty("name", typeof(string)),
                new VectorStoreVectorProperty("embedding1", typeof(ReadOnlyMemory<float>), 10) { IndexKind = "hnsw" }
            ]
        };

        var model = new PostgresModelBuilder().BuildDynamic(recordDefinition, defaultEmbeddingGenerator: null);

        var record = new Dictionary<string, object?>
        {
            ["id"] = 1,
            ["name"] = "Test",
            ["embedding1"] = new ReadOnlyMemory<float>(s_vector),
        };

        using var batch = new NpgsqlBatch();
        _ = PostgresSqlBuilder.BuildUpsertCommand<int>(batch, schema: "myschema", "testcollection", model, [record], generatedEmbeddings: null);

        var command = batch.BatchCommands[0];
        Assert.Contains("INSERT INTO \"myschema\".\"testcollection\"", command.CommandText);

        this._output.WriteLine(command.CommandText);
    }

    [Fact]
    public void TestBuildGetCommand_WithSchema()
    {
        var recordDefinition = new VectorStoreCollectionDefinition()
        {
            Properties = [
                new VectorStoreKeyProperty("id", typeof(long)),
                new VectorStoreDataProperty("name", typeof(string)),
                new VectorStoreVectorProperty("embedding1", typeof(ReadOnlyMemory<float>), 10) { IndexKind = "hnsw" }
            ]
        };

        var model = new PostgresModelBuilder().BuildDynamic(recordDefinition, defaultEmbeddingGenerator: null);

        using var command = new NpgsqlCommand();
        PostgresSqlBuilder.BuildGetCommand(command, schema: "myschema", "testcollection", model, 123, includeVectors: true);

        Assert.Contains("FROM \"myschema\".\"testcollection\"", command.CommandText);

        this._output.WriteLine(command.CommandText);
    }

    [Fact]
    public void TestBuildGetBatchCommand_WithSchema()
    {
        var recordDefinition = new VectorStoreCollectionDefinition()
        {
            Properties = [
                new VectorStoreKeyProperty("id", typeof(long)),
                new VectorStoreDataProperty("name", typeof(string)),
                new VectorStoreVectorProperty("embedding1", typeof(ReadOnlyMemory<float>), 10) { IndexKind = "hnsw" }
            ]
        };

        var model = new PostgresModelBuilder().BuildDynamic(recordDefinition, defaultEmbeddingGenerator: null);

        using var command = new NpgsqlCommand();
        PostgresSqlBuilder.BuildGetBatchCommand(command, schema: "myschema", "testcollection", model, new List<long> { 1, 2 }, includeVectors: true);

        Assert.Contains("FROM \"myschema\".\"testcollection\"", command.CommandText);

        this._output.WriteLine(command.CommandText);
    }

    [Fact]
    public void TestBuildDeleteCommand_WithSchema()
    {
        using var command = new NpgsqlCommand();
        PostgresSqlBuilder.BuildDeleteCommand(command, schema: "myschema", "testcollection", "id", 123);

        Assert.Contains("FROM \"myschema\".\"testcollection\"", command.CommandText);

        this._output.WriteLine(command.CommandText);
    }

    [Fact]
    public void TestBuildDeleteBatchCommand_WithSchema()
    {
        using var command = new NpgsqlCommand();
        var keyProperty = new KeyPropertyModel("id", typeof(long));
        PostgresSqlBuilder.BuildDeleteBatchCommand(command, schema: "myschema", "testcollection", keyProperty, new List<long> { 1, 2 });

        Assert.Contains("FROM \"myschema\".\"testcollection\"", command.CommandText);

        this._output.WriteLine(command.CommandText);
    }

    #endregion
}
