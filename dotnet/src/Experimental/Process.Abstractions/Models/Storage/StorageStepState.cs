// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Process.Models.Storage;

/// <summary>
/// Storage representation of a step state.
/// </summary>
public record StorageStepState
{
    /// <summary>
    /// Custom step type assembly name
    /// </summary>
    [JsonPropertyName("stateType")]
    public string StateType { get; init; } = string.Empty;

    // Not needed if using KernelProcessEventData
    ///// <summary>
    ///// Version of the state that is stored. Used for validation and versioning
    ///// purposes when reading a state and applying it to a ProcessStepBuilder/ProcessBuilder
    ///// </summary>
    //[JsonPropertyName("versionInfo")]
    //public string VersionInfo { get; init; } = string.Empty;

    /// <summary>
    /// The user-defined state object associated with the Step (if the step is stateful) -> Original object comes from StepStateMetadata
    /// </summary>
    [JsonPropertyName("state")]
    public KernelProcessEventData? State { get; set; } = null;
}
