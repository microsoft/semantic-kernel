// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using Microsoft.Extensions.VectorData;
using Microsoft.Extensions.VectorData.ProviderServices;
using NRedisStack.Search;
using Xunit;
using static NRedisStack.Search.Schema;

namespace Microsoft.SemanticKernel.Connectors.Redis.UnitTests;

/// <summary>
/// Contains tests for the <see cref="RedisCollectionCreateMapping"/> class.
/// </summary>
public class RedisCollectionCreateMappingTests
{
    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public void MapToSchemaCreatesSchema(bool useDollarPrefix)
    {
        // Arrange.
        PropertyModel[] properties =
        [
            new KeyPropertyModel("Key", typeof(string)),

            new DataPropertyModel("FilterableString", typeof(string)) { IsIndexed = true },
            new DataPropertyModel("FullTextSearchableString", typeof(string)) { IsFullTextIndexed = true },
            new DataPropertyModel("FilterableStringEnumerable", typeof(string[])) { IsIndexed = true },
            new DataPropertyModel("FullTextSearchableStringEnumerable", typeof(string[])) { IsFullTextIndexed = true },

            new DataPropertyModel("FilterableInt", typeof(int)) { IsIndexed = true },
            new DataPropertyModel("FilterableNullableInt", typeof(int)) { IsIndexed = true },

            new DataPropertyModel("NonFilterableString", typeof(string)),

            new VectorPropertyModel("VectorDefaultIndexingOptions", typeof(ReadOnlyMemory<float>)) { Dimensions = 10, EmbeddingType = typeof(ReadOnlyMemory<float>) },
            new VectorPropertyModel("VectorSpecificIndexingOptions", typeof(ReadOnlyMemory<float>))
            {
                Dimensions = 20,
                IndexKind = IndexKind.Flat,
                DistanceFunction = DistanceFunction.EuclideanSquaredDistance,
                StorageName = "vector_specific_indexing_options",
                EmbeddingType = typeof(ReadOnlyMemory<float>)
            }
        ];

        // Act.
        var schema = RedisCollectionCreateMapping.MapToSchema(properties, useDollarPrefix);

        // Assert.
        Assert.NotNull(schema);
        Assert.Equal(8, schema.Fields.Count);

        Assert.IsType<TagField>(schema.Fields[0]);
        Assert.IsType<TextField>(schema.Fields[1]);
        Assert.IsType<TagField>(schema.Fields[2]);
        Assert.IsType<TextField>(schema.Fields[3]);
        Assert.IsType<NumericField>(schema.Fields[4]);
        Assert.IsType<NumericField>(schema.Fields[5]);
        Assert.IsType<VectorField>(schema.Fields[6]);
        Assert.IsType<VectorField>(schema.Fields[7]);

        if (useDollarPrefix)
        {
            VerifyFieldName(schema.Fields[0].FieldName, new List<object> { "$.FilterableString", "AS", "FilterableString" });
            VerifyFieldName(schema.Fields[1].FieldName, new List<object> { "$.FullTextSearchableString", "AS", "FullTextSearchableString" });
            VerifyFieldName(schema.Fields[2].FieldName, new List<object> { "$.FilterableStringEnumerable.*", "AS", "FilterableStringEnumerable" });
            VerifyFieldName(schema.Fields[3].FieldName, new List<object> { "$.FullTextSearchableStringEnumerable", "AS", "FullTextSearchableStringEnumerable" });

            VerifyFieldName(schema.Fields[4].FieldName, new List<object> { "$.FilterableInt", "AS", "FilterableInt" });
            VerifyFieldName(schema.Fields[5].FieldName, new List<object> { "$.FilterableNullableInt", "AS", "FilterableNullableInt" });

            VerifyFieldName(schema.Fields[6].FieldName, new List<object> { "$.VectorDefaultIndexingOptions", "AS", "VectorDefaultIndexingOptions" });
            VerifyFieldName(schema.Fields[7].FieldName, new List<object> { "$.vector_specific_indexing_options", "AS", "vector_specific_indexing_options" });
        }
        else
        {
            VerifyFieldName(schema.Fields[0].FieldName, new List<object> { "FilterableString", "AS", "FilterableString" });
            VerifyFieldName(schema.Fields[1].FieldName, new List<object> { "FullTextSearchableString", "AS", "FullTextSearchableString" });
            VerifyFieldName(schema.Fields[2].FieldName, new List<object> { "FilterableStringEnumerable.*", "AS", "FilterableStringEnumerable" });
            VerifyFieldName(schema.Fields[3].FieldName, new List<object> { "FullTextSearchableStringEnumerable", "AS", "FullTextSearchableStringEnumerable" });

            VerifyFieldName(schema.Fields[4].FieldName, new List<object> { "FilterableInt", "AS", "FilterableInt" });
            VerifyFieldName(schema.Fields[5].FieldName, new List<object> { "FilterableNullableInt", "AS", "FilterableNullableInt" });

            VerifyFieldName(schema.Fields[6].FieldName, new List<object> { "VectorDefaultIndexingOptions", "AS", "VectorDefaultIndexingOptions" });
            VerifyFieldName(schema.Fields[7].FieldName, new List<object> { "vector_specific_indexing_options", "AS", "vector_specific_indexing_options" });
        }

        Assert.Equal("10", ((VectorField)schema.Fields[6]).Attributes!["DIM"]);
        Assert.Equal("FLOAT32", ((VectorField)schema.Fields[6]).Attributes!["TYPE"]);
        Assert.Equal("COSINE", ((VectorField)schema.Fields[6]).Attributes!["DISTANCE_METRIC"]);

        Assert.Equal("20", ((VectorField)schema.Fields[7]).Attributes!["DIM"]);
        Assert.Equal("FLOAT32", ((VectorField)schema.Fields[7]).Attributes!["TYPE"]);
        Assert.Equal("L2", ((VectorField)schema.Fields[7]).Attributes!["DISTANCE_METRIC"]);
    }

    [Fact]
    public void GetSDKIndexKindThrowsOnUnsupportedIndexKind()
    {
        // Arrange.
        var vectorProperty = new VectorPropertyModel("VectorProperty", typeof(ReadOnlyMemory<float>)) { IndexKind = "Unsupported" };

        // Act and assert.
        Assert.Throws<InvalidOperationException>(() => RedisCollectionCreateMapping.GetSDKIndexKind(vectorProperty));
    }

    [Fact]
    public void GetSDKDistanceAlgorithmThrowsOnUnsupportedDistanceFunction()
    {
        // Arrange.
        var vectorProperty = new VectorPropertyModel("VectorProperty", typeof(ReadOnlyMemory<float>)) { DistanceFunction = "Unsupported" };

        // Act and assert.
        Assert.Throws<InvalidOperationException>(() => RedisCollectionCreateMapping.GetSDKDistanceAlgorithm(vectorProperty));
    }

    private static void VerifyFieldName(FieldName fieldName, List<object> expected)
    {
        var args = new List<object>();
        fieldName.AddCommandArguments(args);
        Assert.Equal(expected, args);
    }
}
