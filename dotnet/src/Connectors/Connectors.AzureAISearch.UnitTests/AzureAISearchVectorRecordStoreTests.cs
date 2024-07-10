// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Threading;
using System.Threading.Tasks;
using Azure;
using Azure.Search.Documents;
using Azure.Search.Documents.Indexes;
using Azure.Search.Documents.Models;
using Microsoft.SemanticKernel.Connectors.AzureAISearch;
using Microsoft.SemanticKernel.Data;
using Moq;
using Xunit;

namespace SemanticKernel.Connectors.AzureAISearch.UnitTests;

/// <summary>
/// Contains tests for the <see cref="AzureAISearchVectorRecordStore{TRecord}"/> class.
/// </summary>
public class AzureAISearchVectorRecordStoreTests
{
    private const string TestCollectionName = "testcollection";
    private const string TestRecordKey1 = "testid1";
    private const string TestRecordKey2 = "testid2";

    private readonly Mock<SearchIndexClient> _searchIndexClientMock;
    private readonly Mock<SearchClient> _searchClientMock;

    private readonly CancellationToken _testCancellationToken = new(false);

    public AzureAISearchVectorRecordStoreTests()
    {
        this._searchClientMock = new Mock<SearchClient>(MockBehavior.Strict);
        this._searchIndexClientMock = new Mock<SearchIndexClient>(MockBehavior.Strict);
        this._searchIndexClientMock.Setup(x => x.GetSearchClient(TestCollectionName)).Returns(this._searchClientMock.Object);
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public async Task CanGetRecordWithVectorsAsync(bool useDefinition)
    {
        // Arrange.
        this._searchClientMock.Setup(
            x => x.GetDocumentAsync<SinglePropsModel>(
                TestRecordKey1,
                It.Is<GetDocumentOptions>(x => !x.SelectedFields.Any()),
                this._testCancellationToken))
            .ReturnsAsync(Response.FromValue(CreateModel(TestRecordKey1, true), Mock.Of<Response>()));

        var sut = this.CreateVectorRecordStore(useDefinition);

        // Act.
        var actual = await sut.GetAsync(
            TestRecordKey1,
            new() { IncludeVectors = true },
            this._testCancellationToken);

        // Assert.
        Assert.NotNull(actual);
        Assert.Equal(TestRecordKey1, actual.Key);
        Assert.Equal("data 1", actual.Data);
        Assert.Equal(new float[] { 1, 2, 3, 4 }, actual.Vector!.Value.ToArray());
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public async Task CanGetRecordWithoutVectorsAsync(bool useDefinition)
    {
        // Arrange.
        var storageObject = JsonSerializer.SerializeToNode(CreateModel(TestRecordKey1, false))!.AsObject();

        this._searchClientMock.Setup(
            x => x.GetDocumentAsync<SinglePropsModel>(
                TestRecordKey1,
                It.Is<GetDocumentOptions>(x => x.SelectedFields.Contains("Key") && x.SelectedFields.Contains("Data")),
                this._testCancellationToken))
            .ReturnsAsync(Response.FromValue(CreateModel(TestRecordKey1, true), Mock.Of<Response>()));

        var sut = this.CreateVectorRecordStore(useDefinition);

        // Act.
        var actual = await sut.GetAsync(
            TestRecordKey1,
            new() { IncludeVectors = false },
            this._testCancellationToken);

        // Assert.
        Assert.NotNull(actual);
        Assert.Equal(TestRecordKey1, actual.Key);
        Assert.Equal("data 1", actual.Data);
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public async Task CanGetManyRecordsWithVectorsAsync(bool useDefinition)
    {
        // Arrange.
        this._searchClientMock.Setup(
            x => x.GetDocumentAsync<SinglePropsModel>(
                It.IsAny<string>(),
                It.IsAny<GetDocumentOptions>(),
                this._testCancellationToken))
            .ReturnsAsync((string id, GetDocumentOptions options, CancellationToken cancellationToken) =>
            {
                return Response.FromValue(CreateModel(id, true), Mock.Of<Response>());
            });

        var sut = this.CreateVectorRecordStore(useDefinition);

        // Act.
        var actual = await sut.GetBatchAsync(
            [TestRecordKey1, TestRecordKey2],
            new() { IncludeVectors = true },
            this._testCancellationToken).ToListAsync();

        // Assert.
        Assert.NotNull(actual);
        Assert.Equal(2, actual.Count);
        Assert.Equal(TestRecordKey1, actual[0].Key);
        Assert.Equal(TestRecordKey2, actual[1].Key);
    }

    [Fact]
    public async Task CanGetRecordWithCustomMapperAsync()
    {
        // Arrange.
        var storageObject = JsonSerializer.SerializeToNode(CreateModel(TestRecordKey1, true))!.AsObject();

        // Arrange GetDocumentAsync mock returning JsonObject.
        this._searchClientMock.Setup(
            x => x.GetDocumentAsync<JsonObject>(
                TestRecordKey1,
                It.Is<GetDocumentOptions>(x => !x.SelectedFields.Any()),
                this._testCancellationToken))
            .ReturnsAsync(Response.FromValue(storageObject, Mock.Of<Response>()));

        // Arrange mapper mock from JsonObject to data model.
        var mapperMock = new Mock<IVectorStoreRecordMapper<SinglePropsModel, JsonObject>>(MockBehavior.Strict);
        mapperMock.Setup(
            x => x.MapFromStorageToDataModel(
                storageObject,
                It.Is<StorageToDataModelMapperOptions>(x => x.IncludeVectors)))
            .Returns(CreateModel(TestRecordKey1, true));

        // Arrange target with custom mapper.
        var sut = new AzureAISearchVectorRecordStore<SinglePropsModel>(
            this._searchIndexClientMock.Object,
            TestCollectionName,
            new()
            {
                MapperType = AzureAISearchRecordMapperType.JsonObjectCustomMapper,
                JsonObjectCustomMapper = mapperMock.Object
            });

        // Act.
        var actual = await sut.GetAsync(TestRecordKey1, new() { IncludeVectors = true }, this._testCancellationToken);

        // Assert.
        Assert.NotNull(actual);
        Assert.Equal(TestRecordKey1, actual.Key);
        Assert.Equal("data 1", actual.Data);
        Assert.Equal(new float[] { 1, 2, 3, 4 }, actual.Vector!.Value.ToArray());
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

        var sut = this.CreateVectorRecordStore(useDefinition);

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

        var sut = this.CreateVectorRecordStore(useDefinition);

        // Act.
        await sut.DeleteBatchAsync(
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
                It.IsAny<IEnumerable<SinglePropsModel>>(),
                It.IsAny<IndexDocumentsOptions>(),
                this._testCancellationToken))
            .ReturnsAsync(Response.FromValue(indexDocumentsResultMock.Object, Mock.Of<Response>()));

        // Arrange sut.
        var sut = this.CreateVectorRecordStore(useDefinition);

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
                It.Is<IEnumerable<SinglePropsModel>>(x => x.Count() == 1 && x.First().Key == TestRecordKey1),
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
                It.IsAny<IEnumerable<SinglePropsModel>>(),
                It.IsAny<IndexDocumentsOptions>(),
                this._testCancellationToken))
            .ReturnsAsync(Response.FromValue(indexDocumentsResultMock.Object, Mock.Of<Response>()));

        // Arrange sut.
        var sut = this.CreateVectorRecordStore(useDefinition);

        var model1 = CreateModel(TestRecordKey1, true);
        var model2 = CreateModel(TestRecordKey2, true);

        // Act.
        var actual = await sut.UpsertBatchAsync(
            [model1, model2],
            cancellationToken: this._testCancellationToken).ToListAsync();

        // Assert.
        Assert.NotNull(actual);
        Assert.Equal(2, actual.Count);
        Assert.Equal(TestRecordKey1, actual[0]);
        Assert.Equal(TestRecordKey2, actual[1]);

        this._searchClientMock.Verify(
            x => x.UploadDocumentsAsync(
                It.Is<IEnumerable<SinglePropsModel>>(x => x.Count() == 2 && x.First().Key == TestRecordKey1 && x.ElementAt(1).Key == TestRecordKey2),
                It.Is<IndexDocumentsOptions>(x => x.ThrowOnAnyError == true),
                this._testCancellationToken),
            Times.Once);
    }

    [Fact]
    public async Task CanUpsertRecordWithCustomMapperAsync()
    {
        // Arrange.
#pragma warning disable Moq1002 // Moq: No matching constructor
        var indexingResult = new Mock<IndexingResult>(MockBehavior.Strict, TestRecordKey1, true, 200);
        var indexingResults = new List<IndexingResult>();
        indexingResults.Add(indexingResult.Object);
        var indexDocumentsResultMock = new Mock<IndexDocumentsResult>(MockBehavior.Strict, indexingResults);
#pragma warning restore Moq1002 // Moq: No matching constructor

        var model = CreateModel(TestRecordKey1, true);
        var storageObject = JsonSerializer.SerializeToNode(model)!.AsObject();

        // Arrange UploadDocumentsAsync mock returning upsert result.
        this._searchClientMock.Setup(
            x => x.UploadDocumentsAsync(
                It.IsAny<IEnumerable<JsonObject>>(),
                It.IsAny<IndexDocumentsOptions>(),
                this._testCancellationToken))
            .ReturnsAsync((IEnumerable<JsonObject> documents, IndexDocumentsOptions options, CancellationToken cancellationToken) =>
            {
                // Need to force a materialization of the documents enumerable here, otherwise the mapper (and therefore its mock) doesn't get invoked.
                var materializedDocuments = documents.ToList();
                return Response.FromValue(indexDocumentsResultMock.Object, Mock.Of<Response>());
            });

        // Arrange mapper mock from data model to JsonObject.
        var mapperMock = new Mock<IVectorStoreRecordMapper<SinglePropsModel, JsonObject>>(MockBehavior.Strict);
        mapperMock
            .Setup(x => x.MapFromDataToStorageModel(It.IsAny<SinglePropsModel>()))
            .Returns(storageObject);

        // Arrange target with custom mapper.
        var sut = new AzureAISearchVectorRecordStore<SinglePropsModel>(
            this._searchIndexClientMock.Object,
            TestCollectionName,
            new()
            {
                MapperType = AzureAISearchRecordMapperType.JsonObjectCustomMapper,
                JsonObjectCustomMapper = mapperMock.Object
            });

        // Act.
        await sut.UpsertAsync(
            model,
            null,
            this._testCancellationToken);

        // Assert.
        mapperMock
            .Verify(
                x => x.MapFromDataToStorageModel(It.Is<SinglePropsModel>(x => x.Key == TestRecordKey1)),
                Times.Once);
    }

    private AzureAISearchVectorRecordStore<SinglePropsModel> CreateVectorRecordStore(bool useDefinition)
    {
        return new AzureAISearchVectorRecordStore<SinglePropsModel>(
            this._searchIndexClientMock.Object,
            TestCollectionName,
            new()
            {
                VectorStoreRecordDefinition = useDefinition ? this._singlePropsDefinition : null
            });
    }

    private static SinglePropsModel CreateModel(string key, bool withVectors)
    {
        return new SinglePropsModel
        {
            Key = key,
            Data = "data 1",
            Vector = withVectors ? new float[] { 1, 2, 3, 4 } : null,
            NotAnnotated = null,
        };
    }

    private readonly VectorStoreRecordDefinition _singlePropsDefinition = new()
    {
        Properties =
        [
            new VectorStoreRecordKeyProperty("Key"),
            new VectorStoreRecordDataProperty("Data"),
            new VectorStoreRecordVectorProperty("Vector")
        ]
    };

    public sealed class SinglePropsModel
    {
        [VectorStoreRecordKey]
        public string Key { get; set; } = string.Empty;

        [VectorStoreRecordData]
        public string Data { get; set; } = string.Empty;

        [VectorStoreRecordVector]
        public ReadOnlyMemory<float>? Vector { get; set; }

        public string? NotAnnotated { get; set; }
    }
}
