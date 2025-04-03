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

    private static readonly Dictionary<string, ResourceTemplateDefinition> s_resourceTemplateDefinitions = [];

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
        if (s_resourceDefinitions.ContainsKey(definition.ResourceTemplate.UriTemplate))
        {
            throw new ArgumentException($"A resource template with the uri template '{definition.ResourceTemplate.UriTemplate}' is already registered.");
        }

        s_resourceTemplateDefinitions[definition.ResourceTemplate.UriTemplate] = definition;
    }

    internal static Task<ListResourceTemplatesResult> HandleListResourceTemplatesRequestAsync(RequestContext<ListResourceTemplatesRequestParams> context, CancellationToken cancellationToken)
    {
        return Task.FromResult(new ListResourceTemplatesResult
        {
            ResourceTemplates = [.. s_resourceTemplateDefinitions.Values.Select(d => d.ResourceTemplate)]
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
        if (s_resourceTemplateDefinitions.TryGetValue(resourceUri, out ResourceTemplateDefinition? resourceTemplateDefinition))
        {
            return resourceTemplateDefinition.Handler(context, cancellationToken);
        }

        throw new ArgumentException($"No handler found for the resource uri '{resourceUri}'.");

        //// Invoke the handler
        //return await definition.Handler(context, cancellationToken);

        //List<ResourceContents> contents = [];

        //if (context.Params?.Uri == "r1://r1")
        //{
        //    contents.Add(new TextResourceContents()
        //    {
        //        Uri = "r1://r1",
        //        MimeType = "plain/text",
        //        Text = "Test resource content",
        //    });
        //}

        //if (context.Params?.Uri == "r2://r2")
        //{
        //    contents.Add(new BlobResourceContents()
        //    {
        //        Uri = "r2://r2",
        //        MimeType = "application/octet-stream",
        //        Blob = Convert.ToBase64String(Encoding.UTF8.GetBytes("base 64 encoded string"))
        //    });
        //}

        //if (context.Params?.Uri == "r1://test")
        //{
        //    contents.Add(new TextResourceContents()
        //    {
        //        Uri = "r1://test",
        //        Text = "Test resource",
        //        MimeType = "plain/text",
        //    });
        //}

        //if (context.Params?.Uri == "r2://test")
        //{
        //    contents.Add(new BlobResourceContents()
        //    {
        //        Uri = "r2://test",
        //        MimeType = "application/octet-stream",
        //        Blob = Convert.ToBase64String(Encoding.UTF8.GetBytes("base 64 encoded string"))
        //    });
        //}

        //return await Task.FromResult(new ReadResourceResult()
        //{
        //    Contents = contents
        //});
    }
}
