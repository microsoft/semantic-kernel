// Copyright (c) Microsoft. All rights reserved.

using MCPServer.Resources;
using Microsoft.SemanticKernel;
using ModelContextProtocol.Protocol.Types;
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
    /// <param name="kernel">The kernel instance.</param>
    /// <param name="template">The MCP resource template.</param>
    /// <param name="handler">The MCP resource template handler.</param>
    /// <returns>The builder instance.</returns>
    public static IMcpServerBuilder WithResourceTemplate(
        this IMcpServerBuilder builder,
        Kernel kernel,
        ResourceTemplate template,
        Delegate handler)
    {
        builder.WithResourceTemplate(new ResourceTemplateDefinition { ResourceTemplate = template, Handler = handler, Kernel = kernel });

        return builder;
    }

    /// <summary>
    /// Adds a resource template to the server.
    /// </summary>
    /// <param name="builder">The MCP server builder.</param>
    /// <param name="templateDefinition">The resource template definition.</param>
    /// <returns>The builder instance.</returns>
    public static IMcpServerBuilder WithResourceTemplate(this IMcpServerBuilder builder, ResourceTemplateDefinition templateDefinition)
    {
        ResourceRegistry.RegisterResourceTemplate(templateDefinition);

        builder.WithListResourceTemplatesHandler(ResourceRegistry.HandleListResourceTemplatesRequestAsync);
        builder.WithReadResourceHandler(ResourceRegistry.HandleReadResourceRequestAsync);

        return builder;
    }

    /// <summary>
    /// Adds a resource to the server.
    /// </summary>
    /// <param name="builder">The MCP server builder.</param>
    /// <param name="kernel">The kernel instance.</param>
    /// <param name="resource">The MCP resource.</param>
    /// <param name="handler">The MCP resource handler.</param>
    /// <returns>The builder instance.</returns>
    public static IMcpServerBuilder WithResource(
        this IMcpServerBuilder builder,
        Kernel kernel,
        Resource resource,
        Delegate handler)
    {
        builder.WithResource(new ResourceDefinition { Resource = resource, Handler = handler, Kernel = kernel });

        return builder;
    }

    /// <summary>
    /// Adds a resource to the server.
    /// </summary>
    /// <param name="builder">The MCP server builder.</param>
    /// <param name="resourceDefinition">The resource definition.</param>
    /// <returns>The builder instance.</returns>
    public static IMcpServerBuilder WithResource(this IMcpServerBuilder builder, ResourceDefinition resourceDefinition)
    {
        ResourceRegistry.RegisterResource(resourceDefinition);

        builder.WithListResourcesHandler(ResourceRegistry.HandleListResourcesRequestAsync);
        builder.WithReadResourceHandler(ResourceRegistry.HandleReadResourceRequestAsync);

        return builder;
    }
}
