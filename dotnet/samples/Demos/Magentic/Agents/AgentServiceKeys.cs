// Copyright (c) Microsoft. All rights reserved.

namespace Magentic.Agents;

/// <summary>
/// Service keys so agents may use the service associated with the expected model.
/// </summary>
internal static class AgentServiceKeys
{
    /// <summary>
    /// A regular / generative chat completion model.
    /// </summary>
    public const string ChatService = nameof(ChatService);

    /// <summary>
    /// A reasoning model (used by the chat manager)
    /// </summary>
    public const string ReasoningService = nameof(ReasoningService);

    /// <summary>
    /// A model with web-search functionality enabled.
    /// </summary>
    public const string SearchService = nameof(SearchService);
}
