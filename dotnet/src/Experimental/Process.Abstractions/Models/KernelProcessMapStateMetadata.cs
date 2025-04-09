// Copyright (c) Microsoft. All rights reserved.
using System.Runtime.Serialization;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Process.Models;

/// <summary>
/// Process state used for State Persistence serialization
/// </summary>
public sealed record class KernelProcessMapStateMetadata : KernelProcessStepStateMetadata
{
    /// <summary>
    /// Process State of Steps if provided
    /// </summary>
    [DataMember]
    [JsonPropertyName("operationState")]
    public KernelProcessStepStateMetadata? OperationState { get; set; }
}
