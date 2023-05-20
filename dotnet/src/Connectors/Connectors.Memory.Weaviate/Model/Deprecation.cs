// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.SemanticKernel.Connectors.Memory.Weaviate.Model;

internal sealed class Deprecation
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
