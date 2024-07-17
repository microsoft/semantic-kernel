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
            new VectorStoreRecordKeyProperty("Key"),

            new VectorStoreRecordDataProperty("FilterableString") { PropertyType = typeof(string), IsFilterable = true },
            new VectorStoreRecordDataProperty("FilterableInt") { PropertyType = typeof(int), IsFilterable = true },
            new VectorStoreRecordDataProperty("FilterableNullableInt") { PropertyType = typeof(int?), IsFilterable = true },

            new VectorStoreRecordDataProperty("NonFilterableString") { PropertyType = typeof(string) },

            new VectorStoreRecordVectorProperty("VectorDefaultIndexingOptions") { Dimensions = 10 },
            new VectorStoreRecordVectorProperty("VectorSpecificIndexingOptions") { Dimensions = 20, IndexKind = IndexKind.Flat, DistanceFunction = DistanceFunction.EuclideanDistance },
        };

        // Act.
        var schema = RedisVectorStoreCollectionCreateMapping.MapToSchema(properties);

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
        VerifyFieldName(schema.Fields[4].FieldName, new List<object> { "$.VectorSpecificIndexingOptions", "AS", "VectorSpecificIndexingOptions" });

        Assert.Equal("10", ((VectorField)schema.Fields[3]).Attributes!["DIM"]);
        Assert.Equal("FLOAT32", ((VectorField)schema.Fields[3]).Attributes!["TYPE"]);
        Assert.Equal("COSINE", ((VectorField)schema.Fields[3]).Attributes!["DISTANCE_METRIC"]);

        Assert.Equal("20", ((VectorField)schema.Fields[4]).Attributes!["DIM"]);
        Assert.Equal("FLOAT32", ((VectorField)schema.Fields[4]).Attributes!["TYPE"]);
        Assert.Equal("L2", ((VectorField)schema.Fields[4]).Attributes!["DISTANCE_METRIC"]);
    }

    [Fact]
    public void MapToSchemaThrowsOnMissingPropertyType()
    {
        // Arrange.
        var properties = new VectorStoreRecordProperty[] { new VectorStoreRecordDataProperty("FilterableString") { IsFilterable = true } };

        // Act and assert.
        Assert.Throws<InvalidOperationException>(() => RedisVectorStoreCollectionCreateMapping.MapToSchema(properties));
    }

    [Theory]
    [InlineData(null)]
    [InlineData(0)]
    public void MapToSchemaThrowsOnInvalidVectorDimensions(int? dimensions)
    {
        // Arrange.
        var properties = new VectorStoreRecordProperty[] { new VectorStoreRecordVectorProperty("VectorProperty") { Dimensions = dimensions } };

        // Act and assert.
        Assert.Throws<InvalidOperationException>(() => RedisVectorStoreCollectionCreateMapping.MapToSchema(properties));
    }

    [Fact]
    public void GetSDKIndexKindThrowsOnUnsupportedIndexKind()
    {
        // Arrange.
        var vectorProperty = new VectorStoreRecordVectorProperty("VectorProperty") { IndexKind = "Unsupported" };

        // Act and assert.
        Assert.Throws<InvalidOperationException>(() => RedisVectorStoreCollectionCreateMapping.GetSDKIndexKind(vectorProperty));
    }

    [Fact]
    public void GetSDKDistanceAlgorithmThrowsOnUnsupportedDistanceFunction()
    {
        // Arrange.
        var vectorProperty = new VectorStoreRecordVectorProperty("VectorProperty") { DistanceFunction = "Unsupported" };

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
