// Copyright (c) Microsoft. All rights reserved.

using MCPServer.Resources;
using Microsoft.SemanticKernel;
using ModelContextProtocol.Protocol.Types;
using ModelContextProtocol.Server;
using MCPServer.Prompts;

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

    /// <summary>
    /// Adds a resource template to the server.
    /// </summary>
    /// <param name="builder">The MCP server builder.</param>
    /// <param name="template">The MCP resource template.</param>
    /// <param name="handler">The MCP resource template handler.</param>
    /// <returns></returns>
    public static IMcpServerBuilder AddResourceTemplate(
        this IMcpServerBuilder builder,
        ResourceTemplate template,
        Func<RequestContext<ReadResourceRequestParams>, IDictionary<string, string>, CancellationToken, Task<ReadResourceResult>> handler)
    {
        ResourceRegistry.RegisterResourceTemplate(new ResourceTemplateDefinition { ResourceTemplate = template, Handler = handler, });

        builder.WithListResourceTemplatesHandler(ResourceRegistry.HandleListResourceTemplatesRequestAsync);
        builder.WithReadResourceHandler(ResourceRegistry.HandleReadResourceRequestAsync);

        return builder;
    }
}
