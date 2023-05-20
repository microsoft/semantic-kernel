// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Connectors.Memory.Weaviate.Model;

internal sealed class GraphError
{
    public string? Message { get; set; }
    public string[]? Path { get; set; }
    public GraphErrorLocationsItems[]? Locations { get; set; }
}
