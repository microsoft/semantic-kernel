// Copyright (c) Microsoft. All rights reserved.

<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
using System;
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
using System;
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
using System;
>>>>>>> main
>>>>>>> Stashed changes
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Data;
using Xunit;

namespace SemanticKernel.UnitTests.Data;

/// <summary>
/// Contains tests for <see cref="KernelBuilderExtensions"/>.
/// </summary>
public class KernelBuilderExtensionsTests
{
    private readonly IKernelBuilder _kernelBuilder;

    public KernelBuilderExtensionsTests()
    {
        this._kernelBuilder = Kernel.CreateBuilder();
    }

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
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
>>>>>>> Stashed changes

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
            obj => new TextSearchResult(name: ((DataModel)obj).Key.ToString(), value: ((DataModel)obj).Text));

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
                return new TextSearchResult(name: dataModel.Key.ToString(), value: dataModel.Text);
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
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes
}
