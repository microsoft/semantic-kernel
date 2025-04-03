// Copyright (c) Microsoft. All rights reserved.

using ModelContextProtocol.Protocol.Types;
using ModelContextProtocol.Server;

namespace MCPServer.Resources;

internal class ResourceDefinition
{
    /// <summary>
    /// Gets or sets the MCP resource.
    /// </summary>
    public required Resource Resource { get; init; }

    /// <summary>
    /// Gets or sets the handler for the MCP resource.
    /// </summary>
    public required Func<RequestContext<ReadResourceRequestParams>, CancellationToken, Task<ReadResourceResult>> Handler { get; init; }
}
