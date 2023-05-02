// Copyright (c) Microsoft. All rights reserved.

using Azure.Search.Documents.Indexes;
using Azure.Search.Documents.Indexes.Models;

namespace Microsoft.SemanticKernel.Connectors.Memory.AzureCognitiveSearch;

public class AzureCognitiveSearchRecord
{
    [SimpleField(IsKey = true, IsFilterable = true)]
    public string Id { get; set; } = string.Empty;

    [SearchableField(AnalyzerName = LexicalAnalyzerName.Values.EnMicrosoft)]
    public string? Text { get; set; } = string.Empty;

    [SearchableField(AnalyzerName = LexicalAnalyzerName.Values.EnMicrosoft)]
    public string? Description { get; set; } = string.Empty;

    [SearchableField(AnalyzerName = LexicalAnalyzerName.Values.EnMicrosoft)]
    public string? AdditionalMetadata { get; set; } = string.Empty;

    [SimpleField(IsFilterable = false)]
    public string ExternalSourceName { get; set; } = string.Empty;

    [SimpleField(IsFilterable = false)]
    public bool IsReference { get; set; } = false;
}
