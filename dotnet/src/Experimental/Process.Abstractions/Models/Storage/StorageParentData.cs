// Copyright (c) Microsoft. All rights reserved.

using System.Runtime.Serialization;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Process.Models.Storage;

// it seems all properties needed are already in KernelProcessStepStateMetadata
// using new class for now in case there some extra props needed while
// plumbing
/// <summary>
/// Data class for the parent of a step.
/// </summary>
public record StorageParentData
{
    /// <summary>
    /// The ID of the parent step.
    /// </summary>
    [DataMember]
    [JsonPropertyName("parentId")]
    public string ParentId { get; set; } = string.Empty;
}
