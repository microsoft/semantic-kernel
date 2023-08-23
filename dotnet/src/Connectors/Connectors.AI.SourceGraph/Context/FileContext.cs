// Copyright (c) Microsoft. All rights reserved.
namespace Microsoft.SemanticKernel.Connectors.AI.SourceGraph.Context;

public class FileContext
{
    public string? FileName { get; set; }
    public string? RepoName { get; set; }
    public string? Revision { get; set; }
    public string? Source { get; set; }
}
