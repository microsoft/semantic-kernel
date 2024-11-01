// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Runtime.Serialization;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Process.Models;

/// <summary>
/// Process state used for State Persistence serialization
/// </summary>
public record class KernelProcessStateMetadata : KernelProcessStepStateMetadata<object>
{
    /// <summary>
    /// Process State of Steps if provided
    /// </summary>
    [DataMember]
    [JsonPropertyName("stepsState")]
    public Dictionary<string, KernelProcessStateMetadata>? StepsState { get; init; }
}
