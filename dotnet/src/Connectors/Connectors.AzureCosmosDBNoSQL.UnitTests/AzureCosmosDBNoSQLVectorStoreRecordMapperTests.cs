// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using System.Text.Json.Nodes;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.AzureCosmosDBNoSQL;
using Xunit;

namespace SemanticKernel.Connectors.AzureCosmosDBNoSQL.UnitTests;

/// <summary>
/// Unit tests for <see cref="AzureCosmosDBNoSQLVectorStoreRecordMapper{TRecord}"/> class.
/// </summary>
public sealed class AzureCosmosDBNoSQLVectorStoreRecordMapperTests
{
    private readonly AzureCosmosDBNoSQLVectorStoreRecordMapper<AzureCosmosDBNoSQLHotel> _sut
        = new(
            new AzureCosmosDBNoSQLVectorStoreModelBuilder().Build(
                typeof(Dictionary<string, object?>),
                new()
                {
                    Properties =
                    [
                        new VectorStoreRecordKeyProperty("HotelId", typeof(string)),
                        new VectorStoreRecordVectorProperty("TestProperty1", typeof(ReadOnlyMemory<float>), 10) { StoragePropertyName = "test_property_1" },
                        new VectorStoreRecordDataProperty("TestProperty2", typeof(string)) { StoragePropertyName = "test_property_2" },
                        new VectorStoreRecordDataProperty("TestProperty3", typeof(string)) { StoragePropertyName = "test_property_3" }
                    ]
                },
                defaultEmbeddingGenerator: null,
                JsonSerializerOptions.Default),
            JsonSerializerOptions.Default);

    [Fact]
    public void MapFromDataToStorageModelReturnsValidObject()
    {
        // Arrange
        var hotel = new AzureCosmosDBNoSQLHotel("key")
        {
            HotelName = "Test Name",
            Tags = ["tag1", "tag2"],
            DescriptionEmbedding = new ReadOnlyMemory<float>([1f, 2f, 3f])
        };

        // Act
        var document = this._sut.MapFromDataToStorageModel(hotel, generatedEmbeddings: null);

        // Assert
        Assert.NotNull(document);

        Assert.Equal("key", document["id"]!.GetValue<string>());
        Assert.Equal("Test Name", document["HotelName"]!.GetValue<string>());
        Assert.Equal(["tag1", "tag2"], document["Tags"]!.AsArray().Select(l => l!.GetValue<string>()));
        Assert.Equal([1f, 2f, 3f], document["description_embedding"]!.AsArray().Select(l => l!.GetValue<float>()));
    }

    [Fact]
    public void MapFromStorageToDataModelReturnsValidObject()
    {
        // Arrange
        var document = new JsonObject
        {
            ["id"] = "key",
            ["HotelName"] = "Test Name",
            ["Tags"] = new JsonArray(new List<string> { "tag1", "tag2" }.Select(l => JsonValue.Create(l)).ToArray()),
            ["description_embedding"] = new JsonArray(new List<float> { 1f, 2f, 3f }.Select(l => JsonValue.Create(l)).ToArray()),
        };

        // Act
        var hotel = this._sut.MapFromStorageToDataModel(document, new());

        // Assert
        Assert.NotNull(hotel);

        Assert.Equal("key", hotel.HotelId);
        Assert.Equal("Test Name", hotel.HotelName);
        Assert.Equal(["tag1", "tag2"], hotel.Tags);
        Assert.True(new ReadOnlyMemory<float>([1f, 2f, 3f]).Span.SequenceEqual(hotel.DescriptionEmbedding!.Value.Span));
    }
}
