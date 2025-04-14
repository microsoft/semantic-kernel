// Copyright (c) Microsoft. All rights reserved.

using MCPServer.Prompts;
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

    /// <summary>
    /// Adds a resource template to the server.
    /// </summary>
    /// <param name="builder">The MCP server builder.</param>
    /// <param name="templateDefinition">The resource template definition.</param>
    /// <returns>The builder instance.</returns>
    public static IMcpServerBuilder WithPrompt(this IMcpServerBuilder builder, PromptDefinition templateDefinition)
    {
        PromptRegistry.RegisterPrompt(templateDefinition);

        builder.WithListPromptsHandler(PromptRegistry.HandlerListPromptRequestsAsync);
        builder.WithGetPromptHandler(PromptRegistry.HandlerGetPromptRequestsAsync);

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
