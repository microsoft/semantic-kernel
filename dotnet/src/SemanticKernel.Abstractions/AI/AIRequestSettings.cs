// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.AI.ChatCompletion;
using Microsoft.SemanticKernel.AI.TextCompletion;

namespace Microsoft.SemanticKernel.AI;

/// <summary>
/// Request settings for an AI request.
/// Implementors of <see cref="ITextCompletion"/> or <see cref="IChatCompletion"/> can extend this
/// if the service they are calling supports additional properties. For an example please reference
/// the Microsoft.SemanticKernel.Connectors.AI.OpenAI.OpenAIRequestSettings implementation.
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
    public Dictionary<string, object>? ExtensionData { get; set; }
}
