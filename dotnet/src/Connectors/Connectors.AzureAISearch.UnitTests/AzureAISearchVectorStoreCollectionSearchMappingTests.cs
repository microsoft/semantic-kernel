// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.AzureAISearch;
using Xunit;

namespace SemanticKernel.Connectors.AzureAISearch.UnitTests;

#pragma warning disable CS0618 // VectorSearchFilter is obsolete

/// <summary>
/// Contains tests for the <see cref="AzureAISearchVectorStoreCollectionSearchMapping"/> class.
/// </summary>
public class AzureAISearchVectorStoreCollectionSearchMappingTests
{
    [Theory]
    [MemberData(nameof(DataTypeMappingOptions))]
    public void BuildFilterStringBuildsCorrectEqualityStringForEachFilterType(string fieldName, object? fieldValue, string expected)
    {
        // Arrange.
        var filter = new VectorSearchFilter().EqualTo(fieldName, fieldValue!);

        // Act.
        var actual = AzureAISearchVectorStoreCollectionSearchMapping.BuildLegacyFilterString(filter, new Dictionary<string, string> { { fieldName, "storage_" + fieldName } });

        // Assert.
        Assert.Equal(expected, actual);
    }

    [Fact]
    public void BuildFilterStringBuildsCorrectTagContainsString()
    {
        // Arrange.
        var filter = new VectorSearchFilter().AnyTagEqualTo("Tags", "mytag");

        // Act.
        var actual = AzureAISearchVectorStoreCollectionSearchMapping.BuildLegacyFilterString(filter, new Dictionary<string, string> { { "Tags", "storage_tags" } });

        // Assert.
        Assert.Equal("storage_tags/any(t: t eq 'mytag')", actual);
    }

    [Fact]
    public void BuildFilterStringCombinesFilterOptions()
    {
        // Arrange.
        var filter = new VectorSearchFilter().EqualTo("intField", 5).AnyTagEqualTo("Tags", "mytag");

        // Act.
        var actual = AzureAISearchVectorStoreCollectionSearchMapping.BuildLegacyFilterString(filter, new Dictionary<string, string> { { "Tags", "storage_tags" }, { "intField", "storage_intField" } });

        // Assert.
        Assert.Equal("storage_intField eq 5 and storage_tags/any(t: t eq 'mytag')", actual);
    }

    [Fact]
    public void BuildFilterStringThrowsForUnknownPropertyName()
    {
        // Act and assert.
        Assert.Throws<InvalidOperationException>(() => AzureAISearchVectorStoreCollectionSearchMapping.BuildLegacyFilterString(new VectorSearchFilter().EqualTo("unknown", "value"), new Dictionary<string, string>()));
        Assert.Throws<InvalidOperationException>(() => AzureAISearchVectorStoreCollectionSearchMapping.BuildLegacyFilterString(new VectorSearchFilter().AnyTagEqualTo("unknown", "value"), new Dictionary<string, string>()));
    }

    public static IEnumerable<object[]> DataTypeMappingOptions()
    {
        yield return new object[] { "stringField", "value", "storage_stringField eq 'value'" };
        yield return new object[] { "boolField", true, "storage_boolField eq true" };
        yield return new object[] { "intField", 5, "storage_intField eq 5" };
        yield return new object[] { "longField", 5L, "storage_longField eq 5" };
        yield return new object[] { "floatField", 5.5f, "storage_floatField eq 5.5" };
        yield return new object[] { "doubleField", 5.5d, "storage_doubleField eq 5.5" };
        yield return new object[] { "dateTimeOffSetField", new DateTimeOffset(2000, 10, 20, 5, 55, 55, TimeSpan.Zero), "storage_dateTimeOffSetField eq 2000-10-20T05:55:55.0000000Z" };
        yield return new object[] { "nullField", null!, "storage_nullField eq null" };
    }
}
