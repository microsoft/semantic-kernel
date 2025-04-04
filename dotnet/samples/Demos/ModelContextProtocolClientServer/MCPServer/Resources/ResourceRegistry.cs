// Copyright (c) Microsoft. All rights reserved.

using MCPServer.Resources;
using ModelContextProtocol.Protocol.Types;
using ModelContextProtocol.Server;

namespace MCPServer.Prompts;

/// <summary>
/// Represents the resource registry that contains the prompt definitions and provides the handlers for the prompt `List` and `Get` requests.
/// </summary>
internal static class ResourceRegistry
{
    private static readonly Dictionary<string, ResourceDefinition> s_resourceDefinitions = [];

    private static readonly IList<ResourceTemplateDefinition> s_resourceTemplateDefinitions = [];

    /// <summary>
    /// Registers a resource definition.
    /// </summary>
    /// <param name="definition">The prompt definition to register.</param>
    public static void RegisterResource(ResourceDefinition definition)
    {
        if (s_resourceDefinitions.ContainsKey(definition.Resource.Uri))
        {
            throw new ArgumentException($"A resource with the uri '{definition.Resource.Uri}' is already registered.");
        }

        s_resourceDefinitions[definition.Resource.Uri] = definition;
    }

    /// <summary>
    /// Registers a resource template definition.
    /// </summary>
    /// <param name="definition">The resource template definition to register.</param>
    public static void RegisterResourceTemplate(ResourceTemplateDefinition definition)
    {
        if (s_resourceTemplateDefinitions.Any(d => d.ResourceTemplate.UriTemplate == definition.ResourceTemplate.UriTemplate))
        {
            throw new ArgumentException($"A resource template with the uri template '{definition.ResourceTemplate.UriTemplate}' is already registered.");
        }

        s_resourceTemplateDefinitions.Add(definition);
    }

    internal static Task<ListResourceTemplatesResult> HandleListResourceTemplatesRequestAsync(RequestContext<ListResourceTemplatesRequestParams> context, CancellationToken cancellationToken)
    {
        return Task.FromResult(new ListResourceTemplatesResult
        {
            ResourceTemplates = [.. s_resourceTemplateDefinitions.Select(d => d.ResourceTemplate)]
        });
    }

    internal static Task<ListResourcesResult> HandleListResourcesRequestAsync(RequestContext<ListResourcesRequestParams> context, CancellationToken cancellationToken)
    {
        return Task.FromResult(new ListResourcesResult
        {
            Resources = [.. s_resourceDefinitions.Values.Select(d => d.Resource)]
        });
    }

    internal static Task<ReadResourceResult> HandleReadResourceRequestAsync(RequestContext<ReadResourceRequestParams> context, CancellationToken cancellationToken)
    {
        // Make sure the uri of the resource or resource template is provided
        if (context.Params?.Uri is not string { } resourceUri || string.IsNullOrEmpty(resourceUri))
        {
            throw new ArgumentException("Resource uri is required.");
        }

        // Look up in registered resource first
        if (s_resourceDefinitions.TryGetValue(resourceUri, out ResourceDefinition? resourceDefinition))
        {
            return resourceDefinition.Handler(context, cancellationToken);
        }

        // Look up in registered resource templates
        foreach (var resourceTemplateDefinition in s_resourceTemplateDefinitions)
        {
            if (resourceTemplateDefinition.IsMatch(resourceUri))
            {
                var args = resourceTemplateDefinition.GetArguments(resourceUri);

                return resourceTemplateDefinition.Handler(context, args, cancellationToken);
            }
        }

        throw new ArgumentException($"No handler found for the resource uri '{resourceUri}'.");
    }
}
