// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Connectors.Memory.Weaviate.Model;

internal sealed class Property
{
    public string? Name { get; set; }
    public string[]? DataType { get; set; }
    public bool IndexInverted { get; set; }
}
