// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Connectors.Weaviate;

[Experimental("SKEXP0020")]
internal sealed class Property
{
    public string? Name { get; set; }
    public string[]? DataType { get; set; }
    public bool IndexInverted { get; set; }
}
