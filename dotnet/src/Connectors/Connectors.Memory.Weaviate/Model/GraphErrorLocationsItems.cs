// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Connectors.Memory.Weaviate.Model;

internal sealed class GraphErrorLocationsItems
{
    public long? Column { get; set; }
    public long? Line { get; set; }
}
