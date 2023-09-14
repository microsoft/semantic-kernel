// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.AI;

/// <summary>
/// Request settings for an AI request.
/// </summary>
public class AIRequestSettings
{
    /// <summary>
    /// Service identifier.
    /// </summary>
    [JsonPropertyName("service_id")]
    [JsonPropertyOrder(10)]
    public string? ServiceId { get; set; } = null;

    /// <summary>
    /// Extra properties
    /// </summary>
    [JsonExtensionData]
    public Dictionary<string, object>? ExtraProperties { get; set; }
}
