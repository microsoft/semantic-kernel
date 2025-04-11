// Copyright (c) Microsoft. All rights reserved.

using ModelContextProtocol.Protocol.Types;
using ModelContextProtocol.Server;

namespace MCPServer.Resources;

/// <summary>
/// Represents the resource registry that contains the resource and resource template definitions and provides the handlers for the `List` and `Get` requests.
/// </summary>
internal static class ResourceRegistry
{
    private static readonly Dictionary<string, ResourceDefinition> s_resourceDefinitions = [];

    private static readonly IList<ResourceTemplateDefinition> s_resourceTemplateDefinitions = [];

    /// <summary>
    /// Registers a resource.
    /// </summary>
    /// <param name="definition">The resource to register.</param>
    public static void RegisterResource(ResourceDefinition definition)
    {
        if (s_resourceDefinitions.ContainsKey(definition.Resource.Uri))
        {
            throw new ArgumentException($"A resource with the uri '{definition.Resource.Uri}' is already registered.");
        }

        s_resourceDefinitions[definition.Resource.Uri] = definition;
    }

    /// <summary>
    /// Registers a resource template.
    /// </summary>
    /// <param name="definition">The resource template to register.</param>
    public static void RegisterResourceTemplate(ResourceTemplateDefinition definition)
    {
        if (s_resourceTemplateDefinitions.Any(d => d.ResourceTemplate.UriTemplate == definition.ResourceTemplate.UriTemplate))
        {
            throw new ArgumentException($"A resource template with the uri template '{definition.ResourceTemplate.UriTemplate}' is already registered.");
        }

        s_resourceTemplateDefinitions.Add(definition);
    }

    /// <summary>
    /// Handles the `ListResourceTemplates` request.
    /// </summary>
    /// <param name="context">The MCP server context.</param>
    /// <param name="cancellationToken">The cancellation token.</param>
    /// <returns>The result of the request.</returns>
    public static Task<ListResourceTemplatesResult> HandleListResourceTemplatesRequestAsync(RequestContext<ListResourceTemplatesRequestParams> context, CancellationToken cancellationToken)
    {
        return Task.FromResult(new ListResourceTemplatesResult
        {
            ResourceTemplates = [.. s_resourceTemplateDefinitions.Select(d => d.ResourceTemplate)]
        });
    }

    /// <summary>
    /// Handles the `ListResources` request.
    /// </summary>
    /// <param name="context">The MCP server context.</param>
    /// <param name="cancellationToken">The cancellation token.</param>
    /// <returns>The result of the request.</returns>
    public static Task<ListResourcesResult> HandleListResourcesRequestAsync(RequestContext<ListResourcesRequestParams> context, CancellationToken cancellationToken)
    {
        return Task.FromResult(new ListResourcesResult
        {
            Resources = [.. s_resourceDefinitions.Values.Select(d => d.Resource)]
        });
    }

    /// <summary>
    /// Handles the `ReadResource` request.
    /// </summary>
    /// <param name="context">The MCP server context.</param>
    /// <param name="cancellationToken">The cancellation token.</param>
    /// <returns>The result of the request.</returns>
    public static Task<ReadResourceResult> HandleReadResourceRequestAsync(RequestContext<ReadResourceRequestParams> context, CancellationToken cancellationToken)
    {
        // Make sure the uri of the resource or resource template is provided
        if (context.Params?.Uri is not string { } resourceUri || string.IsNullOrEmpty(resourceUri))
        {
            throw new ArgumentException("Resource uri is required.");
        }

        // Look up in registered resource first
        if (s_resourceDefinitions.TryGetValue(resourceUri, out ResourceDefinition? resourceDefinition))
        {
            return resourceDefinition.InvokeHandlerAsync(context, cancellationToken);
        }

        // Look up in registered resource templates
        foreach (var resourceTemplateDefinition in s_resourceTemplateDefinitions)
        {
            if (resourceTemplateDefinition.IsMatch(resourceUri))
            {
                return resourceTemplateDefinition.InvokeHandlerAsync(context, cancellationToken);
            }
        }

        throw new ArgumentException($"No handler found for the resource uri '{resourceUri}'.");
    }
}
