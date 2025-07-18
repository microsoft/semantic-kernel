// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Wrapper class for the content of a declarative condition.
/// </summary>
public class DeclarativeConditionContentWrapper
{
    /// <summary>
    /// The state of the process.
    /// </summary>
    [JsonPropertyName("_state_")]
    public object? State { get; set; }

    /// <summary>
    /// The event data associated with the process.
    /// </summary>
    [JsonPropertyName("_event_")]
    public object? Event { get; set; }
}

/// <summary>
/// Wrapper class for the content of a state resolver.
/// </summary>
public class StateResolverContentWrapper
{
    /// <summary>
    /// The state of the process.
    /// </summary>
    [JsonPropertyName("_state_")]
    public object? State { get; set; }
}
