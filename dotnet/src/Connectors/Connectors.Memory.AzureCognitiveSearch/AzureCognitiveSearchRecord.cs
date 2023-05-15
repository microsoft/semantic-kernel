// Copyright (c) Microsoft. All rights reserved.

using Azure.Search.Documents.Indexes;
using Azure.Search.Documents.Indexes.Models;

namespace Microsoft.SemanticKernel.Connectors.Memory.AzureCognitiveSearch;

/// <summary>
/// Azure Cognitive Search record and index definition.
/// Note: once defined, index cannot be modified.
/// </summary>
public class AzureCognitiveSearchRecord
{
    /// <summary>
    /// Record Id.
    /// The record is not filterable to save quota, also SK uses only semantic search.
    /// </summary>
    [SimpleField(IsKey = true, IsFilterable = false)]
    public string Id { get; set; } = string.Empty;

    /// <summary>
    /// Content is stored here.
    /// </summary>
    [SearchableField(AnalyzerName = LexicalAnalyzerName.Values.StandardLucene)]
    public string? Text { get; set; } = string.Empty;

    /// <summary>
    /// Optional description of the content, e.g. a title. This can be useful when
    /// indexing external data without pulling in the entire content.
    /// </summary>
    [SearchableField(AnalyzerName = LexicalAnalyzerName.Values.StandardLucene)]
    public string? Description { get; set; } = string.Empty;

    /// <summary>
    /// Additional metadata. Currently this is a string, where you could store serialized data as JSON.
    /// In future the design might change to allow storing named values and leverage filters.
    /// </summary>
    [SearchableField(AnalyzerName = LexicalAnalyzerName.Values.StandardLucene)]
    public string? AdditionalMetadata { get; set; } = string.Empty;

    /// <summary>
    /// Name of the external source, in cases where the content and the Id are
    /// referenced to external information.
    /// </summary>
    [SimpleField(IsFilterable = false)]
    public string ExternalSourceName { get; set; } = string.Empty;

    /// <summary>
    /// Whether the record references external information.
    /// </summary>
    [SimpleField(IsFilterable = false)]
    public bool IsReference { get; set; } = false;

    // TODO: add one more field with the vector, float array, mark it as searchable
}
