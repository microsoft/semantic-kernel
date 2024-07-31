// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using Microsoft.SemanticKernel.Data;
using NRedisStack.Search;
using Xunit;
using static NRedisStack.Search.Schema;

namespace Microsoft.SemanticKernel.Connectors.Redis.UnitTests;

/// <summary>
/// Contains tests for the <see cref="RedisVectorStoreCollectionCreateMapping"/> class.
/// </summary>
public class RedisVectorStoreCollectionCreateMappingTests
{
    [Fact]
    public void MapToSchemaCreatesSchema()
    {
        // Arrange.
        var properties = new VectorStoreRecordProperty[]
        {
            new VectorStoreRecordKeyProperty("Key", typeof(string)),

            new VectorStoreRecordDataProperty("FilterableString", typeof(string)) { IsFilterable = true },
            new VectorStoreRecordDataProperty("FilterableInt", typeof(int)) { IsFilterable = true },
            new VectorStoreRecordDataProperty("FilterableNullableInt", typeof(int)) { IsFilterable = true },

            new VectorStoreRecordDataProperty("NonFilterableString", typeof(string)),

            new VectorStoreRecordVectorProperty("VectorDefaultIndexingOptions", typeof(ReadOnlyMemory<float>)) { Dimensions = 10 },
            new VectorStoreRecordVectorProperty("VectorSpecificIndexingOptions", typeof(ReadOnlyMemory<float>)) { Dimensions = 20, IndexKind = IndexKind.Flat, DistanceFunction = DistanceFunction.EuclideanDistance },
        };

        var storagePropertyNames = new Dictionary<string, string>()
        {
            { "FilterableString", "FilterableString" },
            { "FilterableInt", "FilterableInt" },
            { "FilterableNullableInt", "FilterableNullableInt" },
            { "NonFilterableString", "NonFilterableString" },
            { "VectorDefaultIndexingOptions", "VectorDefaultIndexingOptions" },
            { "VectorSpecificIndexingOptions", "vector_specific_indexing_options" },
        };

        // Act.
        var schema = RedisVectorStoreCollectionCreateMapping.MapToSchema(properties, storagePropertyNames);

        // Assert.
        Assert.NotNull(schema);
        Assert.Equal(5, schema.Fields.Count);

        Assert.IsType<TextField>(schema.Fields[0]);
        Assert.IsType<NumericField>(schema.Fields[1]);
        Assert.IsType<NumericField>(schema.Fields[2]);
        Assert.IsType<VectorField>(schema.Fields[3]);
        Assert.IsType<VectorField>(schema.Fields[4]);

        VerifyFieldName(schema.Fields[0].FieldName, new List<object> { "$.FilterableString", "AS", "FilterableString" });
        VerifyFieldName(schema.Fields[1].FieldName, new List<object> { "$.FilterableInt", "AS", "FilterableInt" });
        VerifyFieldName(schema.Fields[2].FieldName, new List<object> { "$.FilterableNullableInt", "AS", "FilterableNullableInt" });

        VerifyFieldName(schema.Fields[3].FieldName, new List<object> { "$.VectorDefaultIndexingOptions", "AS", "VectorDefaultIndexingOptions" });
        VerifyFieldName(schema.Fields[4].FieldName, new List<object> { "$.vector_specific_indexing_options", "AS", "vector_specific_indexing_options" });

        Assert.Equal("10", ((VectorField)schema.Fields[3]).Attributes!["DIM"]);
        Assert.Equal("FLOAT32", ((VectorField)schema.Fields[3]).Attributes!["TYPE"]);
        Assert.Equal("COSINE", ((VectorField)schema.Fields[3]).Attributes!["DISTANCE_METRIC"]);

        Assert.Equal("20", ((VectorField)schema.Fields[4]).Attributes!["DIM"]);
        Assert.Equal("FLOAT32", ((VectorField)schema.Fields[4]).Attributes!["TYPE"]);
        Assert.Equal("L2", ((VectorField)schema.Fields[4]).Attributes!["DISTANCE_METRIC"]);
    }

    [Theory]
    [InlineData(null)]
    [InlineData(0)]
    public void MapToSchemaThrowsOnInvalidVectorDimensions(int? dimensions)
    {
        // Arrange.
        var properties = new VectorStoreRecordProperty[] { new VectorStoreRecordVectorProperty("VectorProperty", typeof(ReadOnlyMemory<float>)) { Dimensions = dimensions } };
        var storagePropertyNames = new Dictionary<string, string>() { { "VectorProperty", "VectorProperty" } };

        // Act and assert.
        Assert.Throws<InvalidOperationException>(() => RedisVectorStoreCollectionCreateMapping.MapToSchema(properties, storagePropertyNames));
    }

    [Fact]
    public void GetSDKIndexKindThrowsOnUnsupportedIndexKind()
    {
        // Arrange.
        var vectorProperty = new VectorStoreRecordVectorProperty("VectorProperty", typeof(ReadOnlyMemory<float>)) { IndexKind = "Unsupported" };

        // Act and assert.
        Assert.Throws<InvalidOperationException>(() => RedisVectorStoreCollectionCreateMapping.GetSDKIndexKind(vectorProperty));
    }

    [Fact]
    public void GetSDKDistanceAlgorithmThrowsOnUnsupportedDistanceFunction()
    {
        // Arrange.
        var vectorProperty = new VectorStoreRecordVectorProperty("VectorProperty", typeof(ReadOnlyMemory<float>)) { DistanceFunction = "Unsupported" };

        // Act and assert.
        Assert.Throws<InvalidOperationException>(() => RedisVectorStoreCollectionCreateMapping.GetSDKDistanceAlgorithm(vectorProperty));
    }

    private static void VerifyFieldName(FieldName fieldName, List<object> expected)
    {
        var args = new List<object>();
        fieldName.AddCommandArguments(args);
        Assert.Equal(expected, args);
    }
}
