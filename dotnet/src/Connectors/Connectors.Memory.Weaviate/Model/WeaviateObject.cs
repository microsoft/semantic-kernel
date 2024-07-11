// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;

namespace Microsoft.SemanticKernel.Connectors.Memory.Weaviate.Model;

internal class WeaviateObject
{
    public string? Id { get; set; }
    public string? Class { get; set; }
    public Dictionary<string, object>? Properties { get; set; }
    public ReadOnlyMemory<float> Vector { get; set; }
}
