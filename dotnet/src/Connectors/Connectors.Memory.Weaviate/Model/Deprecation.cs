// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.SemanticKernel.Connectors.Weaviate;

#pragma warning disable CA1812 // 'Deprecation' is an internal class that is apparently never instantiated. If so, remove the code from the assembly. If this class is intended to contain only static members, make it 'static' (Module in Visual Basic).
[Obsolete("The IMemoryStore abstraction is being obsoleted, use Microsoft.Extensions.VectorData and WeaviateVectorStore")]
internal sealed class Deprecation
#pragma warning restore CA1812 // 'Deprecation' is an internal class that is apparently never instantiated. If so, remove the code from the assembly. If this class is intended to contain only static members, make it 'static' (Module in Visual Basic).
{
    public string? ApiType { get; set; }
    public string? Id { get; set; }
    public string[]? Locations { get; set; }
    public string? Mitigation { get; set; }
    public string? Msg { get; set; }
    public string? PlannedRemovalVersion { get; set; }
    public string? RemovedIn { get; set; }
    public DateTime? RemovedTime { get; set; }
    public DateTime? SinceTime { get; set; }
    public string? SinceVersion { get; set; }
    public string? Status { get; set; }
}
