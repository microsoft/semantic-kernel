// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Connectors.Weaviate;

[Experimental("SKEXP0020")]
internal class WeaviateObject
{
    public string? Id { get; set; }
    public string? Class { get; set; }
    public Dictionary<string, object>? Properties { get; set; }
    public ReadOnlyMemory<float> Vector { get; set; }
}
