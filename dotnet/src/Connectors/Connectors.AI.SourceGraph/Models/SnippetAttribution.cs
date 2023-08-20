// Copyright (c) Microsoft. All rights reserved.
namespace Microsoft.SemanticKernel.Connectors.AI.SourceGraph.Models;

public class SnippetAttribution
{
    public bool LimitHit { get; set; }

    public string? RepositoryName { get; set; }
}
