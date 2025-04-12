// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Net;
using System.Net.Http;
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Threading.Tasks;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.Weaviate;
using Xunit;

namespace SemanticKernel.Connectors.Weaviate.UnitTests;

/// <summary>
/// Unit tests for <see cref="WeaviateVectorStoreRecordCollection{TKey, TRecord}"/> class.
/// </summary>
public sealed class WeaviateVectorStoreRecordCollectionTests : IDisposable
{
    private readonly HttpMessageHandlerStub _messageHandlerStub = new();
    private readonly HttpClient _mockHttpClient;

    public WeaviateVectorStoreRecordCollectionTests()
    {
        this._mockHttpClient = new(this._messageHandlerStub, false) { BaseAddress = new Uri("http://default-endpoint") };
    }

    [Fact]
    public void ConstructorForModelWithoutKeyThrowsException()
    {
        // Act & Assert
        var exception = Assert.Throws<NotSupportedException>(() => new WeaviateVectorStoreRecordCollection<Guid, object>(this._mockHttpClient, "Collection"));
        Assert.Contains("No key property found", exception.Message);
    }

    [Fact]
    public void ConstructorWithoutEndpointThrowsException()
    {
        // Arrange
        using var httpClient = new HttpClient();

        // Act & Assert
        var exception = Assert.Throws<ArgumentException>(() => new WeaviateVectorStoreRecordCollection<Guid, WeaviateHotel>(httpClient, "Collection"));
        Assert.Contains("Weaviate endpoint should be provided", exception.Message);
    }

    [Fact]
    public void ConstructorWithDeclarativeModelInitializesCollection()
    {
        // Act & Assert
        var collection = new WeaviateVectorStoreRecordCollection<Guid, WeaviateHotel>(
            this._mockHttpClient,
            "Collection");

        Assert.NotNull(collection);
    }

    [Fact]
    public void ConstructorWithImperativeModelInitializesCollection()
    {
        // Arrange
        var definition = new VectorStoreRecordDefinition
        {
            Properties = [new VectorStoreRecordKeyProperty("Id", typeof(Guid))]
        };

        // Act
        var collection = new WeaviateVectorStoreRecordCollection<Guid, TestModel>(
            this._mockHttpClient,
            "Collection",
            new() { VectorStoreRecordDefinition = definition });

        // Assert
        Assert.NotNull(collection);
    }

    [Theory]
    [MemberData(nameof(CollectionExistsData))]
    public async Task CollectionExistsReturnsValidResultAsync(HttpResponseMessage responseMessage, bool expectedResult)
    {
        // Arrange
        this._messageHandlerStub.ResponseToReturn = responseMessage;

        var sut = new WeaviateVectorStoreRecordCollection<Guid, WeaviateHotel>(this._mockHttpClient, "Collection");

        // Act
        var actualResult = await sut.CollectionExistsAsync();

        // Assert
        Assert.Equal(expectedResult, actualResult);
    }

    [Theory]
    [InlineData("notStartingWithCapitalLetter")]
    [InlineData("0startingWithDigit")]
    [InlineData("contains spaces")]
    [InlineData("contains-dashes")]
    [InlineData("contains_underscores")]
    [InlineData("contains$specialCharacters")]
    [InlineData("contains!specialCharacters")]
    [InlineData("contains@specialCharacters")]
    [InlineData("contains#specialCharacters")]
    [InlineData("contains%specialCharacters")]
    [InlineData("contains^specialCharacters")]
    [InlineData("contains&specialCharacters")]
    [InlineData("contains*specialCharacters")]
    [InlineData("contains(specialCharacters")]
    [InlineData("contains)specialCharacters")]
    [InlineData("containsNonAsciiĄ")]
    [InlineData("containsNonAsciią")]
    public void CollectionCtorRejectsInvalidNames(string collectionName)
    {
        ArgumentException argumentException = Assert.Throws<ArgumentException>(() => new WeaviateVectorStoreRecordCollection<Guid, WeaviateHotel>(this._mockHttpClient, collectionName));
        Assert.Equal("collectionName", argumentException.ParamName);
    }

    [Fact]
    public async Task CreateCollectionUsesValidCollectionSchemaAsync()
    {
        // Arrange
        const string CollectionName = "Collection";
        var sut = new WeaviateVectorStoreRecordCollection<Guid, WeaviateHotel>(this._mockHttpClient, CollectionName);

        // Act
        await sut.CreateCollectionAsync();

        // Assert
        var schemaRequest = JsonSerializer.Deserialize<WeaviateCreateCollectionSchemaRequest>(this._messageHandlerStub.RequestContent);

        Assert.NotNull(schemaRequest);

        Assert.Equal(CollectionName, schemaRequest.CollectionName);

        Assert.NotNull(schemaRequest.VectorConfigurations);
        Assert.Equal("descriptionEmbedding", schemaRequest.VectorConfigurations.Keys.First());

        var vectorConfiguration = schemaRequest.VectorConfigurations["descriptionEmbedding"];

        Assert.Equal("cosine", vectorConfiguration.VectorIndexConfig?.Distance);
        Assert.Equal("hnsw", vectorConfiguration.VectorIndexType);

        Assert.NotNull(schemaRequest.Properties);

        this.AssertSchemaProperty(schemaRequest.Properties[0], "hotelName", "text", true, false);
        this.AssertSchemaProperty(schemaRequest.Properties[1], "hotelCode", "int", false, false);
        this.AssertSchemaProperty(schemaRequest.Properties[2], "hotelRating", "number", false, false);
        this.AssertSchemaProperty(schemaRequest.Properties[3], "parking_is_included", "boolean", false, false);
        this.AssertSchemaProperty(schemaRequest.Properties[4], "tags", "text[]", false, false);
        this.AssertSchemaProperty(schemaRequest.Properties[5], "description", "text", false, true);
        this.AssertSchemaProperty(schemaRequest.Properties[6], "timestamp", "date", false, false);
    }

    [Fact]
    public async Task DeleteCollectionSendsValidRequestAsync()
    {
        // Arrange
        const string CollectionName = "Collection";
        var sut = new WeaviateVectorStoreRecordCollection<Guid, WeaviateHotel>(this._mockHttpClient, CollectionName);

        // Act
        await sut.DeleteCollectionAsync();

        // Assert
        Assert.Equal("http://default-endpoint/schema/Collection", this._messageHandlerStub.RequestUri?.AbsoluteUri);
        Assert.Equal(HttpMethod.Delete, this._messageHandlerStub.Method);
    }

    [Fact]
    public async Task DeleteSendsValidRequestAsync()
    {
        // Arrange
        const string CollectionName = "Collection";
        var id = new Guid("55555555-5555-5555-5555-555555555555");

        var sut = new WeaviateVectorStoreRecordCollection<Guid, WeaviateHotel>(this._mockHttpClient, CollectionName);

        // Act
        await sut.DeleteAsync(id);

        // Assert
        Assert.Equal("http://default-endpoint/objects/Collection/55555555-5555-5555-5555-555555555555", this._messageHandlerStub.RequestUri?.AbsoluteUri);
        Assert.Equal(HttpMethod.Delete, this._messageHandlerStub.Method);
    }

    [Fact]
    public async Task DeleteBatchUsesValidQueryMatchAsync()
    {
        // Arrange
        const string CollectionName = "Collection";
        List<Guid> ids = [new Guid("11111111-1111-1111-1111-111111111111"), new Guid("22222222-2222-2222-2222-222222222222")];

        var sut = new WeaviateVectorStoreRecordCollection<Guid, WeaviateHotel>(this._mockHttpClient, CollectionName);

        // Act
        await sut.DeleteAsync(ids);

        // Assert
        var request = JsonSerializer.Deserialize<WeaviateDeleteObjectBatchRequest>(this._messageHandlerStub.RequestContent);

        Assert.NotNull(request?.Match);

        Assert.Equal(CollectionName, request.Match.CollectionName);

        Assert.NotNull(request.Match.WhereClause);

        var clause = request.Match.WhereClause;

        Assert.Equal("ContainsAny", clause.Operator);
        Assert.Equal(["id"], clause.Path);
        Assert.Equal(["11111111-1111-1111-1111-111111111111", "22222222-2222-2222-2222-222222222222"], clause.Values);
    }

    [Fact]
    public async Task GetExistingRecordReturnsValidRecordAsync()
    {
        // Arrange
        var id = new Guid("55555555-5555-5555-5555-555555555555");

        var jsonObject = new JsonObject { ["id"] = id.ToString(), ["properties"] = new JsonObject() };

        jsonObject["properties"]!["hotelName"] = "Test Name";

        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StringContent(JsonSerializer.Serialize(jsonObject))
        };

        var sut = new WeaviateVectorStoreRecordCollection<Guid, WeaviateHotel>(this._mockHttpClient, "Collection");

        // Act
        var result = await sut.GetAsync(id);

        // Assert
        Assert.NotNull(result);
        Assert.Equal(id, result.HotelId);
        Assert.Equal("Test Name", result.HotelName);
    }

    [Fact]
    public async Task GetExistingBatchRecordsReturnsValidRecordsAsync()
    {
        // Arrange
        var id1 = new Guid("11111111-1111-1111-1111-111111111111");
        var id2 = new Guid("22222222-2222-2222-2222-222222222222");

        var jsonObject1 = new JsonObject { ["id"] = id1.ToString(), ["properties"] = new JsonObject() };
        var jsonObject2 = new JsonObject { ["id"] = id2.ToString(), ["properties"] = new JsonObject() };

        jsonObject1["properties"]!["hotelName"] = "Test Name 1";
        jsonObject2["properties"]!["hotelName"] = "Test Name 2";

        using var response1 = new HttpResponseMessage(HttpStatusCode.OK) { Content = new StringContent(JsonSerializer.Serialize(jsonObject1)) };
        using var response2 = new HttpResponseMessage(HttpStatusCode.OK) { Content = new StringContent(JsonSerializer.Serialize(jsonObject2)) };

        this._messageHandlerStub.ResponseQueue.Enqueue(response1);
        this._messageHandlerStub.ResponseQueue.Enqueue(response2);

        var sut = new WeaviateVectorStoreRecordCollection<Guid, WeaviateHotel>(this._mockHttpClient, "Collection");

        // Act
        var results = await sut.GetAsync([id1, id2]).ToListAsync();

        // Assert
        Assert.NotNull(results[0]);
        Assert.Equal(id1, results[0].HotelId);
        Assert.Equal("Test Name 1", results[0].HotelName);

        Assert.NotNull(results[1]);
        Assert.Equal(id2, results[1].HotelId);
        Assert.Equal("Test Name 2", results[1].HotelName);
    }

    [Fact]
    public async Task UpsertReturnsRecordKeyAsync()
    {
        // Arrange
        var id = new Guid("11111111-1111-1111-1111-111111111111");
        var hotel = new WeaviateHotel { HotelId = id, HotelName = "Test Name" };

        var batchResponse = new List<WeaviateUpsertCollectionObjectBatchResponse> { new() { Id = id, Result = new() { Status = "Success" } } };

        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StringContent(JsonSerializer.Serialize(batchResponse)),
        };

        var sut = new WeaviateVectorStoreRecordCollection<Guid, WeaviateHotel>(this._mockHttpClient, "Collection");

        // Act
        var result = await sut.UpsertAsync(hotel);

        // Assert
        Assert.Equal(id, result);

        var request = JsonSerializer.Deserialize<WeaviateUpsertCollectionObjectBatchRequest>(this._messageHandlerStub.RequestContent);

        Assert.NotNull(request?.CollectionObjects);

        var jsonObject = request.CollectionObjects[0];

        Assert.Equal("11111111-1111-1111-1111-111111111111", jsonObject["id"]?.GetValue<string>());
        Assert.Equal("Test Name", jsonObject["properties"]?["hotelName"]?.GetValue<string>());
    }

    [Fact]
    public async Task UpsertReturnsRecordKeysAsync()
    {
        // Arrange
        var id1 = new Guid("11111111-1111-1111-1111-111111111111");
        var id2 = new Guid("22222222-2222-2222-2222-222222222222");

        var hotel1 = new WeaviateHotel { HotelId = id1, HotelName = "Test Name 1" };
        var hotel2 = new WeaviateHotel { HotelId = id2, HotelName = "Test Name 2" };

        var batchResponse = new List<WeaviateUpsertCollectionObjectBatchResponse>
        {
            new() { Id = id1, Result = new() { Status = "Success" } },
            new() { Id = id2, Result = new() { Status = "Success" } }
        };

        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StringContent(JsonSerializer.Serialize(batchResponse)),
        };

        var sut = new WeaviateVectorStoreRecordCollection<Guid, WeaviateHotel>(this._mockHttpClient, "Collection");

        // Act
        var results = await sut.UpsertAsync([hotel1, hotel2]);

        // Assert
        Assert.Contains(id1, results);
        Assert.Contains(id2, results);

        var request = JsonSerializer.Deserialize<WeaviateUpsertCollectionObjectBatchRequest>(this._messageHandlerStub.RequestContent);

        Assert.NotNull(request?.CollectionObjects);

        var jsonObject1 = request.CollectionObjects[0];
        var jsonObject2 = request.CollectionObjects[1];

        Assert.Equal("11111111-1111-1111-1111-111111111111", jsonObject1["id"]?.GetValue<string>());
        Assert.Equal("Test Name 1", jsonObject1["properties"]?["hotelName"]?.GetValue<string>());

        Assert.Equal("22222222-2222-2222-2222-222222222222", jsonObject2["id"]?.GetValue<string>());
        Assert.Equal("Test Name 2", jsonObject2["properties"]?["hotelName"]?.GetValue<string>());
    }

    [Theory]
    [InlineData(true, "http://test-endpoint/schema", "Bearer fake-key")]
    [InlineData(false, "http://default-endpoint/schema", null)]
    public async Task ItUsesHttpClientParametersAsync(bool initializeOptions, string expectedEndpoint, string? expectedHeader)
    {
        // Arrange
        const string CollectionName = "Collection";

        var options = initializeOptions ?
            new WeaviateVectorStoreRecordCollectionOptions<WeaviateHotel>() { Endpoint = new Uri("http://test-endpoint"), ApiKey = "fake-key" } :
            null;

        var sut = new WeaviateVectorStoreRecordCollection<Guid, WeaviateHotel>(this._mockHttpClient, CollectionName, options);

        // Act
        await sut.CreateCollectionAsync();

        var headers = this._messageHandlerStub.RequestHeaders;
        var endpoint = this._messageHandlerStub.RequestUri;

        // Assert
        Assert.Equal(expectedEndpoint, endpoint?.AbsoluteUri);
        Assert.Equal(expectedHeader, headers?.Authorization?.ToString());
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public async Task SearchEmbeddingReturnsValidRecordAsync(bool includeVectors)
    {
        // Arrange
        const string CollectionName = "SearchEmbeddingCollection";
        var id = new Guid("55555555-5555-5555-5555-555555555555");
        var vector = new ReadOnlyMemory<float>([30f, 31f, 32f, 33f]);

        var jsonObject = new JsonObject
        {
            ["data"] = new JsonObject
            {
                ["Get"] = new JsonObject
                {
                    [CollectionName] = new JsonArray
                    {
                        new JsonObject
                        {
                            ["_additional"] = new JsonObject
                            {
                                ["distance"] = 0.5,
                                ["id"] = id.ToString(),
                                ["vectors"] = new JsonObject
                                {
                                    ["descriptionEmbedding"] = new JsonArray(new List<float> {30, 31, 32, 33}.Select(l => (JsonNode)l).ToArray())
                                }
                            },
                            ["description"] = "This is a great hotel.",
                            ["hotelCode"] = 42,
                            ["hotelName"] = "My Hotel",
                            ["hotelRating"] = 4.5,
                            ["parking_is_included"] = true,
                            ["tags"] = new JsonArray(new List<string> { "t1", "t2" }.Select(l => (JsonNode)l).ToArray()),
                            ["timestamp"] = "2024-08-28T10:11:12-07:00"
                        }
                    }
                }
            }
        };

        this._messageHandlerStub.ResponseToReturn = new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StringContent(JsonSerializer.Serialize(jsonObject))
        };

        var sut = new WeaviateVectorStoreRecordCollection<Guid, WeaviateHotel>(this._mockHttpClient, CollectionName);

        // Act
        var results = await sut.SearchEmbeddingAsync(vector, top: 3, new()
        {
            IncludeVectors = includeVectors
        }).ToListAsync();

        // Assert
        Assert.Single(results);

        var score = results[0].Score;
        var record = results[0].Record;

        Assert.Equal(0.5, score);

        Assert.Equal(id, record.HotelId);
        Assert.Equal("My Hotel", record.HotelName);
        Assert.Equal("This is a great hotel.", record.Description);
        Assert.Equal(42, record.HotelCode);
        Assert.Equal(4.5f, record.HotelRating);
        Assert.True(record.ParkingIncluded);
        Assert.Equal(["t1", "t2"], record.Tags);
        Assert.Equal(new DateTimeOffset(new DateTime(2024, 8, 28, 10, 11, 12), TimeSpan.FromHours(-7)), record.Timestamp);

        if (includeVectors)
        {
            Assert.True(record.DescriptionEmbedding.HasValue);
            Assert.Equal(vector.ToArray(), record.DescriptionEmbedding.Value.ToArray());
        }
        else
        {
            Assert.False(record.DescriptionEmbedding.HasValue);
        }
    }

    [Fact]
    public async Task SearchEmbeddingWithUnsupportedVectorTypeThrowsExceptionAsync()
    {
        // Arrange
        var sut = new WeaviateVectorStoreRecordCollection<Guid, WeaviateHotel>(this._mockHttpClient, "Collection");

        // Act & Assert
        await Assert.ThrowsAsync<NotSupportedException>(async () =>
            await sut.SearchEmbeddingAsync(new List<double>([1, 2, 3]), top: 3).ToListAsync());
    }

    [Fact]
    public async Task SearchEmbeddingWithNonExistentVectorPropertyNameThrowsExceptionAsync()
    {
        // Arrange
        var sut = new WeaviateVectorStoreRecordCollection<Guid, WeaviateHotel>(this._mockHttpClient, "Collection");

        // Act & Assert
        await Assert.ThrowsAsync<InvalidOperationException>(async () =>
            await sut.SearchEmbeddingAsync(
                new ReadOnlyMemory<float>([1f, 2f, 3f]),
                top: 3,
                new() { VectorProperty = r => "non-existent-property" })
                .ToListAsync());
    }

    public void Dispose()
    {
        this._mockHttpClient.Dispose();
        this._messageHandlerStub.Dispose();
    }

    public static TheoryData<HttpResponseMessage, bool> CollectionExistsData => new()
    {
        { new HttpResponseMessage(HttpStatusCode.OK) { Content = new StringContent(JsonSerializer.Serialize(new WeaviateGetCollectionSchemaResponse { CollectionName = "Collection" })) }, true },
        { new HttpResponseMessage(HttpStatusCode.NotFound), false }
    };

    #region private

    private void AssertSchemaProperty(
        WeaviateCollectionSchemaProperty property,
        string propertyName,
        string dataType,
        bool indexFilterable,
        bool indexSearchable)
    {
        Assert.NotNull(property);
        Assert.Equal(propertyName, property.Name);
        Assert.Equal(dataType, property.DataType[0]);
        Assert.Equal(indexFilterable, property.IndexFilterable);
        Assert.Equal(indexSearchable, property.IndexSearchable);
    }

#pragma warning disable CA1812
    private sealed class TestModel
    {
        public Guid Id { get; set; }

        public string? HotelName { get; set; }
    }
#pragma warning restore CA1812

    #endregion
}
