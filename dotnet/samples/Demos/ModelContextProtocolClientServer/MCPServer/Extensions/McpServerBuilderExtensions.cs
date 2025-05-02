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
    /// <param name="builder">The MCP builder instance.</param>
    /// <param name="kernel">An optional kernel instance which plugins will be added as tools.
    /// If not provided, all functions from the kernel plugins registered in DI container will be added.
    /// </param>
    /// <returns>The builder instance.</returns>
    public static IMcpServerBuilder WithTools(this IMcpServerBuilder builder, Kernel? kernel = null)
    {
        // If plugins are provided directly, add them as tools
        if (kernel is not null)
        {
            foreach (var plugin in kernel.Plugins)
            {
                foreach (var function in plugin)
                {
                    builder.Services.AddSingleton(McpServerTool.Create(function.AsAIFunction(kernel)));
                }
            }

            return builder;
        }

        // If no plugins are provided explicitly, add all functions from the kernel plugins registered in DI container as tools
        builder.Services.AddSingleton<IEnumerable<McpServerTool>>(services =>
        {
            IEnumerable<KernelPlugin> plugins = services.GetServices<KernelPlugin>();
            Kernel kernel = services.GetRequiredService<Kernel>();

            List<McpServerTool> tools = new(plugins.Count());

            foreach (var plugin in plugins)
            {
                foreach (var function in plugin)
                {
                    tools.Add(McpServerTool.Create(function.AsAIFunction(kernel)));
                }
            }

            return tools;
        });

        return builder;
    }
}
