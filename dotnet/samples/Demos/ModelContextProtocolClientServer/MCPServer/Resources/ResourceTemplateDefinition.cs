// Copyright (c) Microsoft. All rights reserved.

using ModelContextProtocol.Protocol.Types;
using ModelContextProtocol.Server;

namespace MCPServer.Resources;

internal class ResourceTemplateDefinition
{
    /// <summary>
    /// Gets or sets the MCP resource template.
    /// </summary>
    public required ResourceTemplate ResourceTemplate { get; init; }

    /// <summary>
    /// Gets or sets the handler for the MCP resource template.
    /// </summary>
    public required Func<RequestContext<ReadResourceRequestParams>, CancellationToken, Task<ReadResourceResult>> Handler { get; init; }

    /// <summary>
    /// Gets or sets the function that checks if the resource template matches a given Uri.
    /// </summary>
    public required Func<string, bool> IsMatch { get; init; }
}
