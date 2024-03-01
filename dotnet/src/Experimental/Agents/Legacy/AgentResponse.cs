// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Experimental.Agents;

/// <summary>
/// Response from agent when called as a <see cref="KernelFunction"/>.
/// </summary>
public class AgentResponse
{
    /// <summary>
    /// The thread-id for the agent conversation.
    /// </summary>
    [JsonPropertyName("thread_id")]
    public string ThreadId { get; set; } = string.Empty;

    /// <summary>
    /// The agent response.
    /// </summary>
    [JsonPropertyName("response")]
    public string Message { get; set; } = string.Empty;

    /// <summary>
    /// Instructions from agent on next steps.
    /// </summary>
    [JsonPropertyName("system_instructions")]
    public string Instructions { get; set; } = string.Empty;
}
