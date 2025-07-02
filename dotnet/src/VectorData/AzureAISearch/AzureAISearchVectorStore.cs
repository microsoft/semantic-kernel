// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Runtime.CompilerServices;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Azure;
using Azure.Search.Documents.Indexes;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.VectorData;
using Microsoft.Extensions.VectorData.ProviderServices;
using static Microsoft.Extensions.VectorData.VectorStoreErrorHandler;

namespace Microsoft.SemanticKernel.Connectors.AzureAISearch;

/// <summary>
/// Class for accessing the list of collections in a Azure AI Search vector store.
/// </summary>
/// <remarks>
/// This class can be used with collections of any schema type, but requires you to provide schema information when getting a collection.
/// </remarks>
public sealed class AzureAISearchVectorStore : VectorStore
{
    /// <summary>Metadata about vector store.</summary>
    private readonly VectorStoreMetadata _metadata;

    /// <summary>Azure AI Search client that can be used to manage the list of indices in an Azure AI Search Service.</summary>
    private readonly SearchIndexClient _searchIndexClient;

    private readonly IEmbeddingGenerator? _embeddingGenerator;
    private readonly JsonSerializerOptions? _jsonSerializerOptions;

    /// <summary>A general purpose definition that can be used to construct a collection when needing to proxy schema agnostic operations.</summary>
    private static readonly VectorStoreCollectionDefinition s_generalPurposeDefinition = new() { Properties = [new VectorStoreKeyProperty("Key", typeof(string))] };

    /// <summary>
    /// Initializes a new instance of the <see cref="AzureAISearchVectorStore"/> class.
    /// </summary>
    /// <param name="searchIndexClient">Azure AI Search client that can be used to manage the list of indices in an Azure AI Search Service.</param>
    /// <param name="options">Optional configuration options for this class.</param>
    [RequiresUnreferencedCode("The Azure AI Search provider is currently incompatible with trimming.")]
    [RequiresDynamicCode("The Azure AI Search provider is currently incompatible with NativeAOT.")]
    public AzureAISearchVectorStore(SearchIndexClient searchIndexClient, AzureAISearchVectorStoreOptions? options = default)
    {
        Verify.NotNull(searchIndexClient);

        this._searchIndexClient = searchIndexClient;
        this._embeddingGenerator = options?.EmbeddingGenerator;
        this._jsonSerializerOptions = options?.JsonSerializerOptions;

        this._metadata = new()
        {
            VectorStoreSystemName = AzureAISearchConstants.VectorStoreSystemName,
            VectorStoreName = searchIndexClient.ServiceName
        };
    }

#pragma warning disable IDE0090 // Use 'new(...)'
    /// <inheritdoc />
    [RequiresDynamicCode("This overload of GetCollection() is incompatible with NativeAOT. For dynamic mapping via Dictionary<string, object?>, call GetDynamicCollection() instead.")]
    [RequiresUnreferencedCode("This overload of GetCollecttion() is incompatible with trimming. For dynamic mapping via Dictionary<string, object?>, call GetDynamicCollection() instead.")]
#if NET8_0_OR_GREATER
    public override AzureAISearchCollection<TKey, TRecord> GetCollection<TKey, TRecord>(string name, VectorStoreCollectionDefinition? definition = null)
#else
    public override VectorStoreCollection<TKey, TRecord> GetCollection<TKey, TRecord>(string name, VectorStoreCollectionDefinition? definition = null)
#endif
        => typeof(TRecord) == typeof(Dictionary<string, object?>)
            ? throw new ArgumentException(VectorDataStrings.GetCollectionWithDictionaryNotSupported)
            : new AzureAISearchCollection<TKey, TRecord>(
                this._searchIndexClient,
                name,
                new AzureAISearchCollectionOptions()
                {
                    JsonSerializerOptions = this._jsonSerializerOptions,
                    Definition = definition,
                    EmbeddingGenerator = this._embeddingGenerator
                });

    /// <inheritdoc />
    [RequiresUnreferencedCode("The Azure AI Search provider is currently incompatible with trimming.")]
    [RequiresDynamicCode("The Azure AI Search provider is currently incompatible with NativeAOT.")]
#if NET8_0_OR_GREATER
    public override AzureAISearchDynamicCollection GetDynamicCollection(string name, VectorStoreCollectionDefinition definition)
#else
    public override VectorStoreCollection<object, Dictionary<string, object?>> GetDynamicCollection(string name, VectorStoreCollectionDefinition definition)
#endif
        => new AzureAISearchDynamicCollection(
            this._searchIndexClient,
            name,
            new()
            {
                JsonSerializerOptions = this._jsonSerializerOptions,
                Definition = definition,
                EmbeddingGenerator = this._embeddingGenerator
            }
        );
#pragma warning restore IDE0090

    /// <inheritdoc />
    public override async IAsyncEnumerable<string> ListCollectionNamesAsync([EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        const string OperationName = "GetIndexNames";

        var indexNamesEnumerable = this._searchIndexClient.GetIndexNamesAsync(cancellationToken).ConfigureAwait(false);
        var errorHandlingEnumerable = new ConfiguredCancelableErrorHandlingAsyncEnumerable<string, RequestFailedException>(indexNamesEnumerable, this._metadata, OperationName);

#pragma warning disable CA2007 // Consider calling ConfigureAwait on the awaited task: False Positive
        await foreach (var item in errorHandlingEnumerable.ConfigureAwait(false))
#pragma warning restore CA2007 // Consider calling ConfigureAwait on the awaited task
        {
            yield return item;
        }
    }

    /// <inheritdoc />
    public override Task<bool> CollectionExistsAsync(string name, CancellationToken cancellationToken = default)
    {
        var collection = this.GetDynamicCollection(name, s_generalPurposeDefinition);
        return collection.CollectionExistsAsync(cancellationToken);
    }

    /// <inheritdoc />
    public override Task EnsureCollectionDeletedAsync(string name, CancellationToken cancellationToken = default)
    {
        var collection = this.GetDynamicCollection(name, s_generalPurposeDefinition);
        return collection.EnsureCollectionDeletedAsync(cancellationToken);
    }

    /// <inheritdoc />
    public override object? GetService(Type serviceType, object? serviceKey = null)
    {
        Verify.NotNull(serviceType);

        return
            serviceKey is not null ? null :
            serviceType == typeof(VectorStoreMetadata) ? this._metadata :
            serviceType == typeof(SearchIndexClient) ? this._searchIndexClient :
            serviceType.IsInstanceOfType(this) ? this :
            null;
    }
}
