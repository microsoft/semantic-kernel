// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Memory;

namespace SemanticKernel.Service.CopilotChat.Storage;

/// <summary>
/// Wrapper around IMemoryStore to allow for null values.
/// </summary>
public sealed class OptionalIMemoryStore
{
    /// <summary>
    /// Optional memory store.
    /// </summary>
    public IMemoryStore? MemoryStore { get; set; }
}
