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
    /// Adds a prompt definition and handlers for listing and reading prompts.
    /// </summary>
    /// <param name="builder">The MCP server builder.</param>
    /// <param name="promptDefinition">The prompt definition.</param>
    /// <returns>The builder instance.</returns>
    public static IMcpServerBuilder WithPrompt(this IMcpServerBuilder builder, PromptDefinition promptDefinition)
    {
        // Register the prompt definition in the DI container
        builder.Services.AddSingleton(promptDefinition);

        builder.WithPromptHandlers();

        return builder;
    }

    /// <summary>
    /// Adds handlers for listing and reading prompts.
    /// </summary>
    /// <param name="builder">The MCP server builder.</param>
    /// <returns>The builder instance.</returns>
    public static IMcpServerBuilder WithPromptHandlers(this IMcpServerBuilder builder)
    {
        builder.WithListPromptsHandler(HandleListPromptRequestsAsync);
        builder.WithGetPromptHandler(HandleGetPromptRequestsAsync);

        return builder;
    }

    /// <summary>
    /// Adds a resource template and handlers for listing and reading resource templates.
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
    /// Adds a resource template and handlers for listing and reading resource templates.
    /// </summary>
    /// <param name="builder">The MCP server builder.</param>
    /// <param name="templateDefinition">The resource template definition.</param>
    /// <returns>The builder instance.</returns>
    public static IMcpServerBuilder WithResourceTemplate(this IMcpServerBuilder builder, ResourceTemplateDefinition templateDefinition)
    {
        // Register the resource template definition in the DI container
        builder.Services.AddSingleton(templateDefinition);

        builder.WithResourceTemplateHandlers();

        return builder;
    }

    /// <summary>
    /// Adds handlers for listing and reading resource templates.
    /// </summary>
    /// <param name="builder">The MCP server builder.</param>
    /// <returns>The builder instance.</returns>
    public static IMcpServerBuilder WithResourceTemplateHandlers(this IMcpServerBuilder builder)
    {
        builder.WithListResourceTemplatesHandler(HandleListResourceTemplatesRequestAsync);
        builder.WithReadResourceHandler(HandleReadResourceRequestAsync);

        return builder;
    }

    /// <summary>
    /// Adds a resource and handlers for listing and reading resources.
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
    /// Adds a resource and handlers for listing and reading resources.
    /// </summary>
    /// <param name="builder">The MCP server builder.</param>
    /// <param name="resourceDefinition">The resource definition.</param>
    /// <returns>The builder instance.</returns>
    public static IMcpServerBuilder WithResource(this IMcpServerBuilder builder, ResourceDefinition resourceDefinition)
    {
        // Register the resource definition in the DI container
        builder.Services.AddSingleton(resourceDefinition);

        builder.WithResourceHandlers();

        return builder;
    }

    /// <summary>
    /// Adds handlers for listing and reading resources.
    /// </summary>
    /// <param name="builder">The MCP server builder.</param>
    /// <returns>The builder instance.</returns>
    public static IMcpServerBuilder WithResourceHandlers(this IMcpServerBuilder builder)
    {
        builder.WithListResourcesHandler(HandleListResourcesRequestAsync);
        builder.WithReadResourceHandler(HandleReadResourceRequestAsync);

        return builder;
    }

    private static ValueTask<ListPromptsResult> HandleListPromptRequestsAsync(RequestContext<ListPromptsRequestParams> context, CancellationToken cancellationToken)
    {
        // Get and return all prompt definitions registered in the DI container
        IEnumerable<PromptDefinition> promptDefinitions = context.Server.Services!.GetServices<PromptDefinition>();

        return ValueTask.FromResult(new ListPromptsResult
        {
            Prompts = [.. promptDefinitions.Select(d => d.Prompt)]
        });
    }

    private static async ValueTask<GetPromptResult> HandleGetPromptRequestsAsync(RequestContext<GetPromptRequestParams> context, CancellationToken cancellationToken)
    {
        // Make sure the prompt name is provided
        if (context.Params?.Name is not string { } promptName || string.IsNullOrEmpty(promptName))
        {
            throw new ArgumentException("Prompt name is required.");
        }

        // Get all prompt definitions registered in the DI container
        IEnumerable<PromptDefinition> promptDefinitions = context.Server.Services!.GetServices<PromptDefinition>();

        // Look up the prompt definition
        PromptDefinition? definition = promptDefinitions.FirstOrDefault(d => d.Prompt.Name == promptName);
        if (definition is null)
        {
            throw new ArgumentException($"No handler found for the prompt '{promptName}'.");
        }

        // Invoke the handler
        return await definition.Handler(context, cancellationToken);
    }

    private static ValueTask<ReadResourceResult> HandleReadResourceRequestAsync(RequestContext<ReadResourceRequestParams> context, CancellationToken cancellationToken)
    {
        // Make sure the uri of the resource or resource template is provided
        if (context.Params?.Uri is not string { } resourceUri || string.IsNullOrEmpty(resourceUri))
        {
            throw new ArgumentException("Resource uri is required.");
        }

        // Look up in registered resource first
        IEnumerable<ResourceDefinition> resourceDefinitions = context.Server.Services!.GetServices<ResourceDefinition>();

        ResourceDefinition? resourceDefinition = resourceDefinitions.FirstOrDefault(d => d.Resource.Uri == resourceUri);
        if (resourceDefinition is not null)
        {
            return resourceDefinition.InvokeHandlerAsync(context, cancellationToken);
        }

        // Look up in registered resource templates
        IEnumerable<ResourceTemplateDefinition> resourceTemplateDefinitions = context.Server.Services!.GetServices<ResourceTemplateDefinition>();

        foreach (var resourceTemplateDefinition in resourceTemplateDefinitions)
        {
            if (resourceTemplateDefinition.IsMatch(resourceUri))
            {
                return resourceTemplateDefinition.InvokeHandlerAsync(context, cancellationToken);
            }
        }

        throw new ArgumentException($"No handler found for the resource uri '{resourceUri}'.");
    }

    private static ValueTask<ListResourceTemplatesResult> HandleListResourceTemplatesRequestAsync(RequestContext<ListResourceTemplatesRequestParams> context, CancellationToken cancellationToken)
    {
        // Get and return all resource template definitions registered in the DI container
        IEnumerable<ResourceTemplateDefinition> definitions = context.Server.Services!.GetServices<ResourceTemplateDefinition>();

        return ValueTask.FromResult(new ListResourceTemplatesResult
        {
            ResourceTemplates = [.. definitions.Select(d => d.ResourceTemplate)]
        });
    }

    private static ValueTask<ListResourcesResult> HandleListResourcesRequestAsync(RequestContext<ListResourcesRequestParams> context, CancellationToken cancellationToken)
    {
        // Get and return all resource template definitions registered in the DI container
        IEnumerable<ResourceDefinition> definitions = context.Server.Services!.GetServices<ResourceDefinition>();

        return ValueTask.FromResult(new ListResourcesResult
        {
            Resources = [.. definitions.Select(d => d.Resource)]
        });
    }
}
