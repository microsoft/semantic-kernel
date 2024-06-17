// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Nodes;

namespace Microsoft.SemanticKernel.Connectors.AzureAISearch;

/// <summary>
/// The types of mapper supported by <see cref="AzureAISearchVectorRecordStore{TRecord}"/>.
/// </summary>
public enum AzureAISearchRecordMapperType
{
    /// <summary>
    /// Use the default mapper that is provided by the Azure AI Search client SDK.
    /// </summary>
    Default,

    /// <summary>
    /// Use a custom mapper between <see cref="JsonObject"/> and the data model.
    /// </summary>
    JsonObjectCustomMapper
}
