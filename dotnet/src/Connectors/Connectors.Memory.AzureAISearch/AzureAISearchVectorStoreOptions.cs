﻿// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using Azure.Search.Documents.Indexes;

namespace Microsoft.SemanticKernel.Connectors.AzureAISearch;

/// <summary>
/// Options when creating a <see cref="AzureAISearchVectorStore"/>.
/// </summary>
public sealed class AzureAISearchVectorStoreOptions
{
    /// <summary>
    /// An optional factory to use for constructing <see cref="AzureAISearchVectorStoreRecordCollection{TRecord}"/> instances, if a custom record collection is required.
    /// </summary>
    public IAzureAISearchVectorStoreRecordCollectionFactory? VectorStoreCollectionFactory { get; init; }

    /// <summary>
    /// Gets or sets the JSON serializer options to use when converting between the data model and the Azure AI Search record.
    /// Note that when using the default mapper and you are constructing your own <see cref="SearchIndexClient"/>, you will need
    /// to provide the same set of <see cref="System.Text.Json.JsonSerializerOptions"/> both here and when constructing the <see cref="SearchIndexClient"/>.
    /// </summary>
    public JsonSerializerOptions? JsonSerializerOptions { get; init; } = null;
}
