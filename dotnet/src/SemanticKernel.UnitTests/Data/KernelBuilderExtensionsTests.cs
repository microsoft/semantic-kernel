// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Data;
using Xunit;

namespace SemanticKernel.UnitTests.Data;

/// <summary>
/// Contains tests for KernelBuilderExtensions".
/// </summary>
public class KernelBuilderExtensionsTests
{
    private readonly IKernelBuilder _kernelBuilder;

    public KernelBuilderExtensionsTests()
    {
        this._kernelBuilder = Kernel.CreateBuilder();
    }

    [Obsolete("The VolatileVectorStore is obsolete so this test is as well.")]
    [Fact]
    public void AddVectorStoreRegistersClass()
    {
        // Act.
        this._kernelBuilder.AddVolatileVectorStore();

        // Assert.
        var kernel = this._kernelBuilder.Build();
        var vectorStore = kernel.Services.GetRequiredService<IVectorStore>();
        Assert.NotNull(vectorStore);
        Assert.IsType<VolatileVectorStore>(vectorStore);
    }

    [Obsolete("The VolatileVectorStore is obsolete so this test is as well.")]
    [Fact]
    public void AddVolatileVectorStoreTextSearchRegistersClass()
    {
        // Arrange.
        this._kernelBuilder.AddVolatileVectorStore();
        this._kernelBuilder.AddOpenAITextEmbeddingGeneration("modelId", "apiKey");

        // Act.
        this._kernelBuilder.AddVolatileVectorStoreTextSearch<Guid, DataModel>(
            "records",
            new DataModelTextSearchStringMapper(),
            new DataModelTextSearchResultMapper());

        // Assert.
        var kernel = this._kernelBuilder.Build();
        var vectorStoreTextSearch = kernel.Services.GetRequiredService<VectorStoreTextSearch<DataModel>>();
        Assert.NotNull(vectorStoreTextSearch);
        Assert.IsType<VectorStoreTextSearch<DataModel>>(vectorStoreTextSearch);
    }

    [Obsolete("The VolatileVectorStore is obsolete so this test is as well.")]
    [Fact]
    public void AddVolatileVectorStoreTextSearchWithDelegatesRegistersClass()
    {
        // Arrange.
        this._kernelBuilder.AddVolatileVectorStore();
        this._kernelBuilder.AddOpenAITextEmbeddingGeneration("modelId", "apiKey");

        // Act.
        this._kernelBuilder.AddVolatileVectorStoreTextSearch<Guid, DataModel>(
            "records",
            obj => ((DataModel)obj).Text,
            obj => new TextSearchResult(value: ((DataModel)obj).Text) { Name = ((DataModel)obj).Key.ToString() });

        // Assert.
        var kernel = this._kernelBuilder.Build();
        var vectorStoreTextSearch = kernel.Services.GetRequiredService<VectorStoreTextSearch<DataModel>>();
        Assert.NotNull(vectorStoreTextSearch);
        Assert.IsType<VectorStoreTextSearch<DataModel>>(vectorStoreTextSearch);
    }

    /// <summary>
    /// String mapper which converts a DataModel to a string.
    /// </summary>
    private sealed class DataModelTextSearchStringMapper : ITextSearchStringMapper
    {
        /// <inheritdoc />
        public string MapFromResultToString(object result)
        {
            if (result is DataModel dataModel)
            {
                return dataModel.Text;
            }
            throw new ArgumentException("Invalid result type.");
        }
    }

    /// <summary>
    /// Result mapper which converts a DataModel to a TextSearchResult.
    /// </summary>
    private sealed class DataModelTextSearchResultMapper : ITextSearchResultMapper
    {
        /// <inheritdoc />
        public TextSearchResult MapFromResultToTextSearchResult(object result)
        {
            if (result is DataModel dataModel)
            {
                return new TextSearchResult(value: dataModel.Text) { Name = dataModel.Key.ToString() };
            }
            throw new ArgumentException("Invalid result type.");
        }
    }

#pragma warning disable CA1812 // Avoid uninstantiated internal classes
    private sealed class DataModel
#pragma warning restore CA1812 // Avoid uninstantiated internal classes
    {
        [VectorStoreRecordKey]
        public Guid Key { get; init; }

        [VectorStoreRecordData]
        public required string Text { get; init; }

        [VectorStoreRecordVector(1536)]
        public ReadOnlyMemory<float> Embedding { get; init; }
    }
}
