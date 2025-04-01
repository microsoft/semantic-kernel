// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using ModelContextProtocol.Server;

namespace MCPServer;

/// <summary>
/// Extension methods for <see cref="IMcpServerBuilder"/>.
/// </summary>
public static class McpServerBuilderExtensions
{
    /// <summary>
    /// Adds all functions of the kernel plugins as tools to the server.
    /// </summary>
    /// <param name="builder">The builder instance.</param>
    /// <param name="plugins">The kernel plugins to add as tools to the server.</param>
    /// <returns>The builder instance.</returns>
    public static IMcpServerBuilder WithTools(this IMcpServerBuilder builder, KernelPluginCollection plugins)
    {
        foreach (var plugin in plugins)
        {
            foreach (var function in plugin)
            {
                builder.Services.AddSingleton(services => McpServerTool.Create(function.AsAIFunction()));
            }
        }

        return builder;
    }
}
