// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Plugins.AI.CrewAI.Models;

/// <summary>
/// Represents the requirements for kicking off a CrewAI Crew.
/// </summary>
public record CrewAIRequiredInputs
{
    /// <summary>
    /// The inputs required for the Crew.
    /// </summary>
    [JsonPropertyName("inputs")]
    public IList<string> Inputs { get; set; } = [];
}
