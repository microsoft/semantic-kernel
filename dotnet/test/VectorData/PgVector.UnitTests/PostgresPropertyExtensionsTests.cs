// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.PgVector;
using Xunit;

namespace SemanticKernel.Connectors.PgVector.UnitTests;

public sealed class PostgresPropertyExtensionsTests
{
    [Theory]
    [InlineData("timestamp")]
    [InlineData("TIMESTAMP")]
    [InlineData("timestamp without time zone")]
    [InlineData("TIMESTAMP WITHOUT TIME ZONE")]
    public void WithStoreType_Timestamp_SetsAnnotation(string storeType)
    {
        var property = new VectorStoreDataProperty("test", typeof(DateTime));

        var result = property.WithStoreType(storeType);

        Assert.Same(property, result);
        Assert.Equal(storeType, property.GetStoreType());
    }

    [Theory]
    [InlineData("timestamptz")]
    [InlineData("timestamp with time zone")]
    [InlineData("integer")]
    [InlineData("text")]
    [InlineData("")]
    public void WithStoreType_UnsupportedType_Throws(string storeType)
    {
        var property = new VectorStoreDataProperty("test", typeof(DateTime));

        Assert.Throws<NotSupportedException>(() => property.WithStoreType(storeType));
    }

    [Fact]
    public void GetStoreType_NotSet_ReturnsNull()
    {
        var property = new VectorStoreDataProperty("test", typeof(DateTime));

        Assert.Null(property.GetStoreType());
    }

    [Fact]
    public void WithStoreType_OnlyAllowedOnDateTimeProperties()
    {
        // Setting the annotation on a non-DateTime property should succeed at the property level
        // (validation happens in the model builder), but building the model should throw.
        var definition = new VectorStoreCollectionDefinition
        {
            Properties =
            [
                new VectorStoreKeyProperty("id", typeof(Guid)),
                new VectorStoreDataProperty("name", typeof(string)).WithStoreType("timestamp"),
                new VectorStoreVectorProperty("embedding", typeof(ReadOnlyMemory<float>), 10)
            ]
        };

        Assert.Throws<NotSupportedException>(() =>
            new PostgresModelBuilder().BuildDynamic(definition, defaultEmbeddingGenerator: null));
    }

    [Fact]
    public void WithStoreType_AllowedOnDateTimeProperty()
    {
        var definition = new VectorStoreCollectionDefinition
        {
            Properties =
            [
                new VectorStoreKeyProperty("id", typeof(Guid)),
                new VectorStoreDataProperty("created", typeof(DateTime)).WithStoreType("timestamp"),
                new VectorStoreVectorProperty("embedding", typeof(ReadOnlyMemory<float>), 10)
            ]
        };

        // Should not throw
        var model = new PostgresModelBuilder().BuildDynamic(definition, defaultEmbeddingGenerator: null);
        Assert.NotNull(model);
    }

    [Fact]
    public void WithStoreType_AllowedOnKeyProperty()
    {
        var property = new VectorStoreKeyProperty("id", typeof(DateTime)).WithStoreType("timestamp");
        Assert.Equal("timestamp", property.GetStoreType());
    }

    [Fact]
    public void WithStoreType_OnKeyProperty_NonDateTime_Throws()
    {
        var definition = new VectorStoreCollectionDefinition
        {
            Properties =
            [
                new VectorStoreKeyProperty("id", typeof(Guid)).WithStoreType("timestamp"),
                new VectorStoreVectorProperty("embedding", typeof(ReadOnlyMemory<float>), 10)
            ]
        };

        Assert.Throws<NotSupportedException>(() =>
            new PostgresModelBuilder().BuildDynamic(definition, defaultEmbeddingGenerator: null));
    }

    [Fact]
    public void WithStoreType_AllowedOnNullableDateTimeProperty()
    {
        var definition = new VectorStoreCollectionDefinition
        {
            Properties =
            [
                new VectorStoreKeyProperty("id", typeof(Guid)),
                new VectorStoreDataProperty("created", typeof(DateTime?)).WithStoreType("timestamp"),
                new VectorStoreVectorProperty("embedding", typeof(ReadOnlyMemory<float>), 10)
            ]
        };

        // Should not throw
        var model = new PostgresModelBuilder().BuildDynamic(definition, defaultEmbeddingGenerator: null);
        Assert.NotNull(model);
    }
}
