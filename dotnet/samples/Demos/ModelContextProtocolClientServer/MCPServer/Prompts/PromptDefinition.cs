// Copyright (c) Microsoft. All rights reserved.

using ModelContextProtocol.Protocol.Types;
using ModelContextProtocol.Server;

namespace MCPServer.Prompts;

/// <summary>
/// Represents a prompt definition.
/// </summary>
internal class PromptDefinition
{
    /// <summary>
    /// Gets or sets the prompt.
    /// </summary>
    public required Prompt Prompt { get; init; }

    /// <summary>
    /// Gets or sets the handler for the prompt.
    /// </summary>
    public required Func<RequestContext<GetPromptRequestParams>, CancellationToken, Task<GetPromptResult>> Handler { get; init; }
}
