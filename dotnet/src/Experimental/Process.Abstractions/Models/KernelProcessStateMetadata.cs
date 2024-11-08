// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Runtime.Serialization;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Process.Models;

/// <summary>
/// Process state used for State Persistence serialization
/// </summary>
public sealed record class KernelProcessStateMetadata : KernelProcessStepStateMetadata
{
    /// <summary>
    /// Process State of Steps if provided
    /// </summary>
    [DataMember]
    [JsonPropertyName("stepsState")]
    public Dictionary<string, KernelProcessStepStateMetadata>? StepsState { get; set; } = null;
}
