// Copyright (c) Microsoft. All rights reserved.
namespace Microsoft.SemanticKernel.Connectors.AI.SourceGraph.Context;

public class FileResult
{
    public FileContext FileContext { get; set; }
    public string[]? Results { get; set; }
}
