// Copyright (c) Microsoft. All rights reserved.

namespace ChatWithAgent.ApiService;

/// <summary>
/// The agent completion request model.
/// </summary>
public sealed class AgentCompletionRequest
{
    /// <summary>
    /// Gets or sets the prompt.
    /// </summary>
    public required string Prompt { get; set; }

    /// <summary>
    /// Gets or sets a value indicating whether streaming is requested.
    /// </summary>
    public bool IsStreaming { get; set; }
}
