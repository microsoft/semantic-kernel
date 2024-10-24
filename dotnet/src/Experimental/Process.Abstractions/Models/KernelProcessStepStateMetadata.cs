// Copyright (c) Microsoft. All rights reserved.

using System.Runtime.Serialization;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Process.Models;

/// <summary>
/// Step state used for State Persistence serialization
/// </summary>
public record class KernelProcessStepStateMetadata
{
    /// <summary>
    /// The identifier of the Step which is required to be unique within an instance of a Process.
    /// This may be null until a process containing this step has been invoked.
    /// </summary>
    [DataMember]
    [JsonPropertyName("id")]
    public string? Id { get; init; }

    /// <summary>
    /// The name of the Step. This is intended to be human readable and is not required to be unique. If
    /// not provided, the name will be derived from the steps .NET type.
    /// </summary>
    [DataMember]
    [JsonPropertyName("name")]
    public string? Name { get; init; }

    /// <summary>
    /// Version of the state that is stored. Used for validation and versioning
    /// purposes when reading a state and applying it to a ProcessStepBuilder/ProcessBuilder
    /// </summary>
    [DataMember]
    [JsonPropertyName("versionInfo")]
    public string? VersionInfo { get; init; } = null;
}

/// <summary>
/// Step state used for State Persistence serialization for stateful steps
/// </summary>
public record class KernelProcessStepStateMetadata<TState> : KernelProcessStepStateMetadata where TState : class, new()
{
    /// <summary>
    /// The user-defined state object associated with the Step.
    /// </summary>
    [DataMember]
    [JsonPropertyName("state")]
    public TState? State { get; set; } = null;
}
