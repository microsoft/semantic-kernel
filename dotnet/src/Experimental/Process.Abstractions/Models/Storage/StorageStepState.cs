// Copyright (c) Microsoft. All rights reserved.

using System.Runtime.Serialization;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Process.Models.Storage;

/// <summary>
/// Storage representation of a step state.
/// </summary>
public record StorageStepState
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
    public string? Name { get; set; }

    /// <summary>
    /// Version of the state that is stored. Used for validation and versioning
    /// purposes when reading a state and applying it to a ProcessStepBuilder/ProcessBuilder
    /// </summary>
    [DataMember]
    [JsonPropertyName("versionInfo")]
    public string? VersionInfo { get; init; } = null;

    /// <summary>
    /// The user-defined state object associated with the Step (if the step is stateful)
    /// </summary>
    [DataMember]
    [JsonPropertyName("state")]
    public KernelProcessEventData? State { get; set; } = null;
}

/// <summary>
/// Extension methods for converting between StorageStepState and KernelProcessStepStateMetadata.
/// </summary>
public static class StorageProcessStepExtension
{
    /// <summary>
    /// Converts a <see cref="StorageStepState"/> to a <see cref="KernelProcessStepStateMetadata"/>.
    /// </summary>
    /// <param name="storageStateData"></param>
    /// <returns></returns>
    public static KernelProcessStepStateMetadata ToKernelStepMetadata(this StorageStepState storageStateData)
    {
        return new KernelProcessStepStateMetadata()
        {
            Id = storageStateData.Id,
            Name = storageStateData.Name,
            VersionInfo = storageStateData.VersionInfo,
            State = storageStateData.State?.ToObject(),
        };
    }

    /// <summary>
    /// Converts a <see cref="KernelProcessStepStateMetadata"/> to a <see cref="StorageStepState"/>.
    /// </summary>
    /// <param name="stepMetadata"></param>
    /// <returns></returns>
    public static StorageStepState ToKernelStorageStepState(this KernelProcessStepStateMetadata stepMetadata)
    {
        return new StorageStepState()
        {
            Id = stepMetadata.Id,
            Name = stepMetadata.Name,
            VersionInfo = stepMetadata.VersionInfo,
            State = KernelProcessEventData.FromObject(stepMetadata.State),
        };
    }
}
