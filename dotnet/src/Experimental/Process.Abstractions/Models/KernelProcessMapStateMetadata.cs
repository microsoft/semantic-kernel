// Copyright (c) Microsoft. All rights reserved.
using System.Runtime.Serialization;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Process.Models;

/// <summary>
/// Process state used for State Persistence serialization
/// </summary>
public record KernelProcessMapStateMetadata : KernelProcessStepStateMetadata<object>
{
    /// <summary>
    /// Process State of Steps if provided
    /// </summary>
    [DataMember]
    [JsonPropertyName("mapState")]
    public KernelProcessStateMetadata? MapState { get; set; }
}
