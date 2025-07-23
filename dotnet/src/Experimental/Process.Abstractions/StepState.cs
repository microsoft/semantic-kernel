// Copyright (c) Microsoft. All rights reserved.

using System.Runtime.Serialization;

namespace Microsoft.SemanticKernel;

/// <summary>
/// The state of a step
/// </summary>
[DataContract]
public class StepState
{
    /// <summary>
    /// The step Id
    /// </summary>
    [DataMember]
    public string? Id { get; set; }

    /// <summary>
    /// State
    /// </summary>
    [DataMember]
    public object? State { get; set; }
}
