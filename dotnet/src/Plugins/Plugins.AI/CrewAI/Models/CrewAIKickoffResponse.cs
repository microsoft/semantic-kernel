// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Plugins.AI.CrewAI;

/// <summary>
/// Models the response object of a call to kickoff a CrewAI Crew.
/// </summary>
#pragma warning disable CA1812 // Avoid uninstantiated internal classes
internal sealed class CrewAIKickoffResponse
{
    [JsonPropertyName("kickoff_id")]
    public string KickoffId { get; set; } = string.Empty;
}
#pragma warning restore CA1812 // Avoid uninstantiated internal classes
