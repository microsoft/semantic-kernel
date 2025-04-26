// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.IO;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Data;
using Microsoft.SemanticKernel.Embeddings;
using SemanticKernel.IntegrationTests.Connectors.OpenAI;
using static Microsoft.SemanticKernel.Data.VectorStoreExtensions;

namespace SemanticKernel.IntegrationTests.Data;

/// <summary>
/// Base class for integration tests for using various vector stores with <see cref="ITextSearch"/>.
/// </summary>
public abstract class BaseVectorStoreTextSearchTests : BaseTextSearchTests
{
    protected IVectorStore? VectorStore { get; set; }

    protected ITextEmbeddingGenerationService? EmbeddingGenerator { get; set; }

    protected new IConfigurationRoot Configuration { get; } = new ConfigurationBuilder()
        .AddJsonFile(path: "testsettings.json", optional: true, reloadOnChange: true)
        .AddJsonFile(path: "testsettings.development.json", optional: true, reloadOnChange: true)
        .AddEnvironmentVariables()
        .AddUserSecrets<OpenAITextEmbeddingTests>()
        .Build();

    /// <summary>
    /// Add sample records to the vector store record collection.
    /// </summary>
    public static async Task<IVectorStoreRecordCollection<TKey, TRecord>> AddRecordsAsync<TKey, TRecord>(
        IVectorStore vectorStore,
        string collectionName,
        ITextEmbeddingGenerationService embeddingGenerationService,
        CreateRecordFromString<TKey, TRecord> createRecord)
        where TKey : notnull
        where TRecord : notnull
    {
        var lines = await File.ReadAllLinesAsync("./TestData/semantic-kernel-info.txt");

        return await vectorStore.CreateCollectionFromListAsync<TKey, TRecord>(
                collectionName, lines, embeddingGenerationService, createRecord);
    }

    /// <summary>
    /// String mapper which converts a DataModel to a string.
    /// </summary>
    protected sealed class DataModelTextSearchStringMapper : ITextSearchStringMapper
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
    protected sealed class DataModelTextSearchResultMapper : ITextSearchResultMapper
    {
        /// <inheritdoc />
        public TextSearchResult MapFromResultToTextSearchResult(object result)
        {
            if (result is DataModel dataModel)
            {
                return new TextSearchResult(value: dataModel.Text) { Name = dataModel.Key.ToString(), Link = dataModel.Link };
            }
            throw new ArgumentException("Invalid result type.");
        }
    }

    /// <summary>
    /// Mock implementation of <see cref="ITextEmbeddingGenerationService"/>.
    /// </summary>
    protected sealed class MockTextEmbeddingGenerationService : ITextEmbeddingGenerationService
    {
        /// <inheritdoc />
        public IReadOnlyDictionary<string, object?> Attributes { get; } = ReadOnlyDictionary<string, object?>.Empty;

        /// <inheritdoc />
        public Task<IList<ReadOnlyMemory<float>>> GenerateEmbeddingsAsync(IList<string> data, Kernel? kernel = null, CancellationToken cancellationToken = default)
        {
            IList<ReadOnlyMemory<float>> result = [new float[] { 0, 1, 2, 3 }];
            return Task.FromResult(result);
        }
    }

    /// <summary>
    /// Sample model class that represents a record entry.
    /// </summary>
    /// <remarks>
    /// Note that each property is decorated with an attribute that specifies how the property should be treated by the vector store.
    /// This allows us to create a collection in the vector store and upsert and retrieve instances of this class without any further configuration.
    /// </remarks>
#pragma warning disable CA1812 // Avoid uninstantiated internal classes
    protected sealed class DataModel
#pragma warning restore CA1812 // Avoid uninstantiated internal classes
    {
        [VectorStoreRecordKey]
        public Guid Key { get; init; }

        [VectorStoreRecordData]
        public required string Text { get; init; }

        [VectorStoreRecordData]
        public required string Link { get; init; }

        [VectorStoreRecordData(IsIndexed = true)]
        public required string Tag { get; init; }

        [VectorStoreRecordVector(1536)]
        public ReadOnlyMemory<float> Embedding { get; init; }
    }
}
