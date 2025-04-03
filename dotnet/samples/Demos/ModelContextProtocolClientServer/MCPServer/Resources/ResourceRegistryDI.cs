// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics;
using System.Text;
using System.Threading;
using MCPServer.Resources;
using ModelContextProtocol.Protocol.Types;
using ModelContextProtocol.Server;

namespace MCPServer.Prompts;

/// <summary>
/// Represents the resource registry that contains the prompt definitions and provides the handlers for the prompt `List` and `Get` requests.
/// </summary>
internal class ResourceRegistryDI
{
    private readonly IList<ResourceTemplateDefinition> _resourceTemplateDefinitions;

    public ResourceRegistryDI(IList<ResourceTemplateDefinition> resourceTemplateDefinitions)
    {
        Debugger.Break();
        this._resourceTemplateDefinitions = resourceTemplateDefinitions;
    }

    public Task<ListResourceTemplatesResult> HandleListResourceTemplatesRequestAsync(RequestContext<ListResourceTemplatesRequestParams> context, CancellationToken cancellationToken)
    {
        Debugger.Break();
        return Task.FromResult(new ListResourceTemplatesResult
        {
            ResourceTemplates = [.. this._resourceTemplateDefinitions.Select(d => d.ResourceTemplate)]
        });
    }

    public Task<ReadResourceResult> HandleReadResourceRequestAsync(RequestContext<ReadResourceRequestParams> context, CancellationToken cancellationToken)
    {
        Debugger.Break();
        // Make sure the uri of the resource or resource template is provided
        if (context.Params?.Uri is not string { } resourceUri || string.IsNullOrEmpty(resourceUri))
        {
            throw new ArgumentException("Resource uri is required.");
        }

        foreach (ResourceTemplateDefinition resourceTemplateDefinition in this._resourceTemplateDefinitions)
        {
            if (resourceTemplateDefinition.IsMatch(resourceUri))
            {
                return resourceTemplateDefinition.Handler(context, cancellationToken);
            }
        }

        throw new ArgumentException($"No handler found for the resource uri '{resourceUri}'.");

        //// Look up in registered resource first
        //if (s_resourceDefinitions.TryGetValue(resourceUri, out ResourceDefinition? resourceDefinition))
        //{
        //    return resourceDefinition.Handler(context, cancellationToken);
        //}

        //// Look up in registered resource templates
        //if (s_resourceTemplateDefinitions.TryGetValue(resourceUri, out ResourceTemplateDefinition? resourceTemplateDefinition))
        //{
        //    return resourceTemplateDefinition.Handler(context, cancellationToken);
        //}

        //throw new ArgumentException($"No handler found for the resource uri '{resourceUri}'.");

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
