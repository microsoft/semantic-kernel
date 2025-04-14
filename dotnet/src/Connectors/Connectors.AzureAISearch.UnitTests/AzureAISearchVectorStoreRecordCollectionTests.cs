// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Threading;
using System.Threading.Tasks;
using Azure;
using Azure.Search.Documents;
using Azure.Search.Documents.Indexes;
using Azure.Search.Documents.Indexes.Models;
using Azure.Search.Documents.Models;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.AzureAISearch;
using Moq;
using Xunit;

namespace SemanticKernel.Connectors.AzureAISearch.UnitTests;

#pragma warning disable CS0618 // VectorSearchFilter is obsolete

/// <summary>
/// Contains tests for the <see cref="AzureAISearchVectorStoreRecordCollection{TKey, TRecord}"/> class.
/// </summary>
public class AzureAISearchVectorStoreRecordCollectionTests
{
    private const string TestCollectionName = "testcollection";
    private const string TestRecordKey1 = "testid1";
    private const string TestRecordKey2 = "testid2";

    private readonly Mock<SearchIndexClient> _searchIndexClientMock;
    private readonly Mock<SearchClient> _searchClientMock;

    private readonly CancellationToken _testCancellationToken = new(false);

    public AzureAISearchVectorStoreRecordCollectionTests()
    {
        this._searchClientMock = new Mock<SearchClient>(MockBehavior.Strict);
        this._searchIndexClientMock = new Mock<SearchIndexClient>(MockBehavior.Strict);
        this._searchIndexClientMock.Setup(x => x.GetSearchClient(TestCollectionName)).Returns(this._searchClientMock.Object);
        this._searchIndexClientMock.Setup(x => x.ServiceName).Returns("TestService");
    }

    [Theory]
    [InlineData(TestCollectionName, true)]
    [InlineData("nonexistentcollection", false)]
    public async Task CollectionExistsReturnsCollectionStateAsync(string collectionName, bool expectedExists)
    {
        this._searchIndexClientMock.Setup(x => x.GetSearchClient(collectionName)).Returns(this._searchClientMock.Object);

        // Arrange.
        if (expectedExists)
        {
            this._searchIndexClientMock
                .Setup(x => x.GetIndexAsync(collectionName, this._testCancellationToken))
                .Returns(Task.FromResult<Response<SearchIndex>?>(null));
        }
        else
        {
            this._searchIndexClientMock
                .Setup(x => x.GetIndexAsync(collectionName, this._testCancellationToken))
                .ThrowsAsync(new RequestFailedException(404, "Index not found"));
        }

        var sut = new AzureAISearchVectorStoreRecordCollection<string, MultiPropsModel>(this._searchIndexClientMock.Object, collectionName);

        // Act.
        var actual = await sut.CollectionExistsAsync(this._testCancellationToken);

        // Assert.
        Assert.Equal(expectedExists, actual);
    }

    [Theory]
    [InlineData(true, true)]
    [InlineData(true, false)]
    [InlineData(false, true)]
    [InlineData(false, false)]
    public async Task CreateCollectionCallsSDKAsync(bool useDefinition, bool useCustomJsonSerializerOptions)
    {
        // Arrange.
        this._searchIndexClientMock
            .Setup(x => x.CreateIndexAsync(It.IsAny<SearchIndex>(), this._testCancellationToken))
            .ReturnsAsync(Response.FromValue(new SearchIndex(TestCollectionName), Mock.Of<Response>()));

        var sut = this.CreateRecordCollection(useDefinition, useCustomJsonSerializerOptions);

        // Act.
        await sut.CreateCollectionAsync();

        // Assert.
        var expectedFieldNames = useCustomJsonSerializerOptions ? new[] { "key", "storage_data1", "data2", "storage_vector1", "vector2" } : new[] { "Key", "storage_data1", "Data2", "storage_vector1", "Vector2" };
        this._searchIndexClientMock
            .Verify(
                x => x.CreateIndexAsync(
                    It.Is<SearchIndex>(si => si.Fields.Count == 5 && si.Fields.Select(f => f.Name).SequenceEqual(expectedFieldNames) && si.Name == TestCollectionName && si.VectorSearch.Profiles.Count == 2 && si.VectorSearch.Algorithms.Count == 2),
                    this._testCancellationToken),
                Times.Once);
    }

    [Theory]
    [InlineData(true, true)]
    [InlineData(true, false)]
    [InlineData(false, true)]
    [InlineData(false, false)]
    public async Task CreateCollectionIfNotExistsSDKAsync(bool useDefinition, bool expectedExists)
    {
        // Arrange.
        if (expectedExists)
        {
            this._searchIndexClientMock
                .Setup(x => x.GetIndexAsync(TestCollectionName, this._testCancellationToken))
                .Returns(Task.FromResult<Response<SearchIndex>?>(null));
        }
        else
        {
            this._searchIndexClientMock
                .Setup(x => x.GetIndexAsync(TestCollectionName, this._testCancellationToken))
                .ThrowsAsync(new RequestFailedException(404, "Index not found"));
        }

        this._searchIndexClientMock
            .Setup(x => x.CreateIndexAsync(It.IsAny<SearchIndex>(), this._testCancellationToken))
            .ReturnsAsync(Response.FromValue(new SearchIndex(TestCollectionName), Mock.Of<Response>()));

        var sut = this.CreateRecordCollection(useDefinition);

        // Act.
        await sut.CreateCollectionIfNotExistsAsync();

        // Assert.
        if (expectedExists)
        {
            this._searchIndexClientMock
                .Verify(
                    x => x.CreateIndexAsync(
                        It.IsAny<SearchIndex>(),
                        this._testCancellationToken),
                    Times.Never);
        }
        else
        {
            this._searchIndexClientMock
                .Verify(
                    x => x.CreateIndexAsync(
                        It.Is<SearchIndex>(si => si.Fields.Count == 5 && si.Name == TestCollectionName && si.VectorSearch.Profiles.Count == 2 && si.VectorSearch.Algorithms.Count == 2),
                        this._testCancellationToken),
                    Times.Once);
        }
    }

    [Fact]
    public async Task CanDeleteCollectionAsync()
    {
        // Arrange.
        this._searchIndexClientMock
            .Setup(x => x.DeleteIndexAsync(TestCollectionName, this._testCancellationToken))
            .Returns(Task.FromResult<Response?>(null));

        var sut = this.CreateRecordCollection(false);

        // Act.
        await sut.DeleteCollectionAsync(this._testCancellationToken);

        // Assert.
        this._searchIndexClientMock.Verify(x => x.DeleteIndexAsync(TestCollectionName, this._testCancellationToken), Times.Once);
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public async Task CanGetRecordWithVectorsAsync(bool useDefinition)
    {
        // Arrange.
        this._searchClientMock.Setup(
            x => x.GetDocumentAsync<MultiPropsModel>(
                TestRecordKey1,
                It.Is<GetDocumentOptions>(x => !x.SelectedFields.Any()),
                this._testCancellationToken))
            .ReturnsAsync(Response.FromValue(CreateModel(TestRecordKey1, true), Mock.Of<Response>()));

        var sut = this.CreateRecordCollection(useDefinition);

        // Act.
        var actual = await sut.GetAsync(
            TestRecordKey1,
            new() { IncludeVectors = true },
            this._testCancellationToken);

        // Assert.
        Assert.NotNull(actual);
        Assert.Equal(TestRecordKey1, actual.Key);
        Assert.Equal("data 1", actual.Data1);
        Assert.Equal("data 2", actual.Data2);
        Assert.Equal(new float[] { 1, 2, 3, 4 }, actual.Vector1!.Value.ToArray());
        Assert.Equal(new float[] { 1, 2, 3, 4 }, actual.Vector2!.Value.ToArray());
    }

    [Theory]
    [InlineData(true, true)]
    [InlineData(true, false)]
    [InlineData(false, true)]
    [InlineData(false, false)]
    public async Task CanGetRecordWithoutVectorsAsync(bool useDefinition, bool useCustomJsonSerializerOptions)
    {
        // Arrange.
        var storageObject = JsonSerializer.SerializeToNode(CreateModel(TestRecordKey1, false))!.AsObject();

        string[] expectedSelectFields = useCustomJsonSerializerOptions ? ["key", "storage_data1", "data2"] : ["Key", "storage_data1", "Data2"];
        this._searchClientMock.Setup(
            x => x.GetDocumentAsync<MultiPropsModel>(
                TestRecordKey1,
                It.IsAny<GetDocumentOptions>(),
                this._testCancellationToken))
            .ReturnsAsync(Response.FromValue(CreateModel(TestRecordKey1, true), Mock.Of<Response>()));

        var sut = this.CreateRecordCollection(useDefinition, useCustomJsonSerializerOptions);

        // Act.
        var actual = await sut.GetAsync(
            TestRecordKey1,
            new() { IncludeVectors = false },
            this._testCancellationToken);

        // Assert.
        Assert.NotNull(actual);
        Assert.Equal(TestRecordKey1, actual.Key);
        Assert.Equal("data 1", actual.Data1);
        Assert.Equal("data 2", actual.Data2);

        this._searchClientMock.Verify(
            x => x.GetDocumentAsync<MultiPropsModel>(
                TestRecordKey1,
                It.Is<GetDocumentOptions>(x => x.SelectedFields.SequenceEqual(expectedSelectFields)),
                this._testCancellationToken),
            Times.Once);
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public async Task CanGetManyRecordsWithVectorsAsync(bool useDefinition)
    {
        // Arrange.
        this._searchClientMock.Setup(
            x => x.GetDocumentAsync<MultiPropsModel>(
                It.IsAny<string>(),
                It.IsAny<GetDocumentOptions>(),
                this._testCancellationToken))
            .ReturnsAsync((string id, GetDocumentOptions options, CancellationToken cancellationToken) =>
            {
                return Response.FromValue(CreateModel(id, true), Mock.Of<Response>());
            });

        var sut = this.CreateRecordCollection(useDefinition);

        // Act.
        var actual = await sut.GetAsync(
            [TestRecordKey1, TestRecordKey2],
            new() { IncludeVectors = true },
            this._testCancellationToken).ToListAsync();

        // Assert.
        Assert.NotNull(actual);
        Assert.Equal(2, actual.Count);
        Assert.Equal(TestRecordKey1, actual[0].Key);
        Assert.Equal(TestRecordKey2, actual[1].Key);
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public async Task CanDeleteRecordAsync(bool useDefinition)
    {
        // Arrange.
#pragma warning disable Moq1002 // Moq: No matching constructor
        var indexDocumentsResultMock = new Mock<IndexDocumentsResult>(MockBehavior.Strict, new List<IndexingResult>());
#pragma warning restore Moq1002 // Moq: No matching constructor

        this._searchClientMock.Setup(
            x => x.DeleteDocumentsAsync(
                It.IsAny<string>(),
                It.IsAny<IEnumerable<string>>(),
                It.IsAny<IndexDocumentsOptions>(),
                this._testCancellationToken))
            .ReturnsAsync(Response.FromValue(indexDocumentsResultMock.Object, Mock.Of<Response>()));

        var sut = this.CreateRecordCollection(useDefinition);

        // Act.
        await sut.DeleteAsync(
            TestRecordKey1,
            cancellationToken: this._testCancellationToken);

        // Assert.
        this._searchClientMock.Verify(
            x => x.DeleteDocumentsAsync(
                "Key",
                It.Is<IEnumerable<string>>(x => x.Count() == 1 && x.Contains(TestRecordKey1)),
                It.IsAny<IndexDocumentsOptions>(),
                this._testCancellationToken),
            Times.Once);
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public async Task CanDeleteManyRecordsWithVectorsAsync(bool useDefinition)
    {
        // Arrange.
#pragma warning disable Moq1002 // Moq: No matching constructor
        var indexDocumentsResultMock = new Mock<IndexDocumentsResult>(MockBehavior.Strict, new List<IndexingResult>());
#pragma warning restore Moq1002 // Moq: No matching constructor

        this._searchClientMock.Setup(
            x => x.DeleteDocumentsAsync(
                It.IsAny<string>(),
                It.IsAny<IEnumerable<string>>(),
                It.IsAny<IndexDocumentsOptions>(),
                this._testCancellationToken))
            .ReturnsAsync(Response.FromValue(indexDocumentsResultMock.Object, Mock.Of<Response>()));

        var sut = this.CreateRecordCollection(useDefinition);

        // Act.
        await sut.DeleteAsync(
            [TestRecordKey1, TestRecordKey2],
            cancellationToken: this._testCancellationToken);

        // Assert.
        this._searchClientMock.Verify(
            x => x.DeleteDocumentsAsync(
                "Key",
                It.Is<IEnumerable<string>>(x => x.Count() == 2 && x.Contains(TestRecordKey1) && x.Contains(TestRecordKey2)),
                It.IsAny<IndexDocumentsOptions>(),
                this._testCancellationToken),
            Times.Once);
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public async Task CanUpsertRecordAsync(bool useDefinition)
    {
        // Arrange upload result object.
#pragma warning disable Moq1002 // Moq: No matching constructor
        var indexingResult = new Mock<IndexingResult>(MockBehavior.Strict, TestRecordKey1, true, 200);
        var indexingResults = new List<IndexingResult>();
        indexingResults.Add(indexingResult.Object);
        var indexDocumentsResultMock = new Mock<IndexDocumentsResult>(MockBehavior.Strict, indexingResults);
#pragma warning restore Moq1002 // Moq: No matching constructor

        // Arrange upload.
        this._searchClientMock.Setup(
            x => x.UploadDocumentsAsync(
                It.IsAny<IEnumerable<MultiPropsModel>>(),
                It.IsAny<IndexDocumentsOptions>(),
                this._testCancellationToken))
            .ReturnsAsync(Response.FromValue(indexDocumentsResultMock.Object, Mock.Of<Response>()));

        // Arrange sut.
        var sut = this.CreateRecordCollection(useDefinition);

        var model = CreateModel(TestRecordKey1, true);

        // Act.
        var actual = await sut.UpsertAsync(
            model,
            cancellationToken: this._testCancellationToken);

        // Assert.
        Assert.NotNull(actual);
        Assert.Equal(TestRecordKey1, actual);
        this._searchClientMock.Verify(
            x => x.UploadDocumentsAsync(
                It.Is<IEnumerable<MultiPropsModel>>(x => x.Count() == 1 && x.First().Key == TestRecordKey1),
                It.Is<IndexDocumentsOptions>(x => x.ThrowOnAnyError == true),
                this._testCancellationToken),
            Times.Once);
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public async Task CanUpsertManyRecordsAsync(bool useDefinition)
    {
        // Arrange upload result object.
#pragma warning disable Moq1002 // Moq: No matching constructor
        var indexingResult1 = new Mock<IndexingResult>(MockBehavior.Strict, TestRecordKey1, true, 200);
        var indexingResult2 = new Mock<IndexingResult>(MockBehavior.Strict, TestRecordKey2, true, 200);

        var indexingResults = new List<IndexingResult>();
        indexingResults.Add(indexingResult1.Object);
        indexingResults.Add(indexingResult2.Object);
        var indexDocumentsResultMock = new Mock<IndexDocumentsResult>(MockBehavior.Strict, indexingResults);
#pragma warning restore Moq1002 // Moq: No matching constructor

        // Arrange upload.
        this._searchClientMock.Setup(
            x => x.UploadDocumentsAsync(
                It.IsAny<IEnumerable<MultiPropsModel>>(),
                It.IsAny<IndexDocumentsOptions>(),
                this._testCancellationToken))
            .ReturnsAsync(Response.FromValue(indexDocumentsResultMock.Object, Mock.Of<Response>()));

        // Arrange sut.
        var sut = this.CreateRecordCollection(useDefinition);

        var model1 = CreateModel(TestRecordKey1, true);
        var model2 = CreateModel(TestRecordKey2, true);

        // Act.
        var actual = await sut.UpsertAsync(
            [model1, model2],
            cancellationToken: this._testCancellationToken);

        // Assert.
        Assert.NotNull(actual);
        Assert.Equal(2, actual.Count);
        Assert.Equal(TestRecordKey1, actual[0]);
        Assert.Equal(TestRecordKey2, actual[1]);

        this._searchClientMock.Verify(
            x => x.UploadDocumentsAsync(
                It.Is<IEnumerable<MultiPropsModel>>(x => x.Count() == 2 && x.First().Key == TestRecordKey1 && x.ElementAt(1).Key == TestRecordKey2),
                It.Is<IndexDocumentsOptions>(x => x.ThrowOnAnyError == true),
                this._testCancellationToken),
            Times.Once);
    }

    /// <summary>
    /// Tests that the collection can be created even if the definition and the type do not match.
    /// In this case, the expectation is that a custom mapper will be provided to map between the
    /// schema as defined by the definition and the different data model.
    /// </summary>
    [Fact]
    public void CanCreateCollectionWithMismatchedDefinitionAndType()
    {
        // Arrange.
        var definition = new VectorStoreRecordDefinition()
        {
            Properties = new List<VectorStoreRecordProperty>
            {
                new VectorStoreRecordKeyProperty("Key", typeof(string)),
                new VectorStoreRecordDataProperty("Data1", typeof(string)),
                new VectorStoreRecordVectorProperty("Vector1", typeof(ReadOnlyMemory<float>), 4),
            }
        };

        // Act.
        var sut = new AzureAISearchVectorStoreRecordCollection<string, MultiPropsModel>(
            this._searchIndexClientMock.Object,
            TestCollectionName,
            new() { VectorStoreRecordDefinition = definition });
    }

    [Fact]
    public async Task CanSearchWithVectorAndFilterAsync()
    {
        // Arrange.
#pragma warning disable Moq1002 // Could not find a matching constructor for arguments: SearchResults has an internal parameterless constructor.
        var searchResultsMock = Mock.Of<SearchResults<MultiPropsModel>>();
#pragma warning restore Moq1002 // Could not find a matching constructor for arguments: SearchResults has an internal parameterless constructor.
        this._searchClientMock
            .Setup(x => x.SearchAsync<MultiPropsModel>(null, It.IsAny<SearchOptions>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(Response.FromValue(searchResultsMock, Mock.Of<Response>()));

        var sut = new AzureAISearchVectorStoreRecordCollection<string, MultiPropsModel>(
            this._searchIndexClientMock.Object,
            TestCollectionName);
        var filter = new VectorSearchFilter().EqualTo(nameof(MultiPropsModel.Data1), "Data1FilterValue");

        // Act.
        var searchResults = await sut.VectorizedSearchAsync(
            new ReadOnlyMemory<float>(new float[4]),
            top: 5,
            new()
            {
                Skip = 3,
                OldFilter = filter,
                VectorProperty = record => record.Vector1
            },
            this._testCancellationToken).ToListAsync();

        // Assert.
        this._searchClientMock.Verify(
            x => x.SearchAsync<MultiPropsModel>(
                null,
                It.Is<SearchOptions>(x =>
                    x.Filter == "storage_data1 eq 'Data1FilterValue'" &&
                    x.Size == 5 &&
                    x.Skip == 3 &&
                    x.VectorSearch.Queries.First().GetType() == typeof(VectorizedQuery) &&
                    x.VectorSearch.Queries.First().Fields.First() == "storage_vector1"),
                It.IsAny<CancellationToken>()),
            Times.Once);
    }

    [Fact]
    public async Task CanSearchWithTextAndFilterAsync()
    {
        // Arrange.
#pragma warning disable Moq1002 // Could not find a matching constructor for arguments: SearchResults has an internal parameterless constructor.
        var searchResultsMock = Mock.Of<SearchResults<MultiPropsModel>>();
#pragma warning restore Moq1002 // Could not find a matching constructor for arguments: SearchResults has an internal parameterless constructor.
        this._searchClientMock
            .Setup(x => x.SearchAsync<MultiPropsModel>(null, It.IsAny<SearchOptions>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(Response.FromValue(searchResultsMock, Mock.Of<Response>()));

        var sut = new AzureAISearchVectorStoreRecordCollection<string, MultiPropsModel>(
            this._searchIndexClientMock.Object,
            TestCollectionName);
        var filter = new VectorSearchFilter().EqualTo(nameof(MultiPropsModel.Data1), "Data1FilterValue");

        // Act.
        var searchResults = await sut.VectorizableTextSearchAsync(
            "search string",
            top: 5,
            new()
            {
                Skip = 3,
                OldFilter = filter,
                VectorProperty = record => record.Vector1
            },
            this._testCancellationToken).ToListAsync();

        // Assert.
        this._searchClientMock.Verify(
            x => x.SearchAsync<MultiPropsModel>(
                null,
                It.Is<SearchOptions>(x =>
                    x.Filter == "storage_data1 eq 'Data1FilterValue'" &&
                    x.Size == 5 &&
                    x.Skip == 3 &&
                    x.VectorSearch.Queries.First().GetType() == typeof(VectorizableTextQuery) &&
                    x.VectorSearch.Queries.First().Fields.First() == "storage_vector1" &&
                    ((VectorizableTextQuery)x.VectorSearch.Queries.First()).Text == "search string"),
                It.IsAny<CancellationToken>()),
            Times.Once);
    }

    private AzureAISearchVectorStoreRecordCollection<string, MultiPropsModel> CreateRecordCollection(bool useDefinition, bool useCustomJsonSerializerOptions = false)
    {
        return new AzureAISearchVectorStoreRecordCollection<string, MultiPropsModel>(
            this._searchIndexClientMock.Object,
            TestCollectionName,
            new()
            {
                VectorStoreRecordDefinition = useDefinition ? this._multiPropsDefinition : null,
                JsonSerializerOptions = useCustomJsonSerializerOptions ? this._customJsonSerializerOptions : null
            });
    }

    private static MultiPropsModel CreateModel(string key, bool withVectors)
    {
        return new MultiPropsModel
        {
            Key = key,
            Data1 = "data 1",
            Data2 = "data 2",
            Vector1 = withVectors ? new float[] { 1, 2, 3, 4 } : null,
            Vector2 = withVectors ? new float[] { 1, 2, 3, 4 } : null,
            NotAnnotated = null,
        };
    }

    private readonly JsonSerializerOptions _customJsonSerializerOptions = new()
    {
        PropertyNamingPolicy = JsonNamingPolicy.CamelCase
    };

    private readonly VectorStoreRecordDefinition _multiPropsDefinition = new()
    {
        Properties =
        [
            new VectorStoreRecordKeyProperty("Key", typeof(string)),
            new VectorStoreRecordDataProperty("Data1", typeof(string)),
            new VectorStoreRecordDataProperty("Data2", typeof(string)),
            new VectorStoreRecordVectorProperty("Vector1", typeof(ReadOnlyMemory<float>), 4),
            new VectorStoreRecordVectorProperty("Vector2", typeof(ReadOnlyMemory<float>), 4)
        ]
    };

    public sealed class MultiPropsModel
    {
        [VectorStoreRecordKey]
        public string Key { get; set; } = string.Empty;

        [JsonPropertyName("storage_data1")]
        [VectorStoreRecordData(IsIndexed = true)]
        public string Data1 { get; set; } = string.Empty;

        [VectorStoreRecordData]
        public string Data2 { get; set; } = string.Empty;

        [JsonPropertyName("storage_vector1")]
        [VectorStoreRecordVector(4)]
        public ReadOnlyMemory<float>? Vector1 { get; set; }

        [VectorStoreRecordVector(4)]
        public ReadOnlyMemory<float>? Vector2 { get; set; }

        public string? NotAnnotated { get; set; }
    }
}
