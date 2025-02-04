// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Plugins.AI.CrewAI;

/// <summary>
/// Models the response object of a call to get the state of a CrewAI Crew kickoff.
/// </summary>
public class CrewAIStatusResponse
{
    /// <summary>
    /// The current state of the CrewAI Crew kickoff.
    /// </summary>
    [JsonPropertyName("state")]
    [JsonConverter(typeof(CrewAIStateEnumConverter))]
    public CrewAIKickoffState State { get; set; }

    /// <summary>
    /// The result of the CrewAI Crew kickoff.
    /// </summary>
    [JsonPropertyName("result")]
    public string? Result { get; set; }

    /// <summary>
    /// The last step of the CrewAI Crew kickoff.
    /// </summary>
    [JsonPropertyName("last_step")]
    public Dictionary<string, object>? LastStep { get; set; }
}
