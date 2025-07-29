// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Process.Models.Storage;

/// <summary>
/// Storage representation of a process state.
/// </summary>
public record StorageProcessState
{
    // Properties here should match properties used by LocalUserStateStore

    /// <summary>
    /// Collection of shared variables used by the process and process steps.
    /// Saving values as KernelProcessEventData to allow serialization and deserialization of custom objects.
    /// </summary>
    [JsonPropertyName("sharedVariables")]
    public Dictionary<string, KernelProcessEventData?> SharedVariables { get; init; } = [];
}
