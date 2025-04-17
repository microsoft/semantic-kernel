// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using ModelContextProtocol.Protocol.Types;
using ModelContextProtocol.Server;

namespace MCPServer.Resources;

/// <summary>
/// Represents a resource definition.
/// </summary>
public sealed class ResourceDefinition
{
    /// <summary>
    /// The kernel function to invoke the resource handler.
    /// </summary>
    private KernelFunction? _kernelFunction = null;

    /// <summary>
    /// Gets or sets the MCP resource.
    /// </summary>
    public required Resource Resource { get; init; }

    /// <summary>
    /// Gets or sets the handler for the MCP resource.
    /// </summary>
    public required Delegate Handler { get; init; }

    /// <summary>
    /// Gets or sets the kernel instance to invoke the resource handler.
    /// If not provided, an instance registered in DI container will be used.
    /// </summary>
    public Kernel? Kernel { get; set; }

    /// <summary>
    /// Creates a new blob resource definition.
    /// </summary>
    /// <param name="uri">The URI of the resource.</param>
    /// <param name="name">The name of the resource.</param>
    /// <param name="content">The content of the resource.</param>
    /// <param name="mimeType">The MIME type of the resource.</param>
    /// <param name="description">The description of the resource.</param>
    /// <param name="kernel">The kernel instance to invoke the resource handler.
    /// If not provided, an instance registered in DI container will be used.
    /// </param>
    /// <returns>The created resource definition.</returns>
    public static ResourceDefinition CreateBlobResource(string uri, string name, byte[] content, string mimeType, string? description = null, Kernel? kernel = null)
    {
        return new()
        {
            Kernel = kernel,
            Resource = new() { Uri = uri, Name = name, Description = description },
            Handler = async (RequestContext<ReadResourceRequestParams> context, CancellationToken cancellationToken) =>
            {
                return new ReadResourceResult()
                {
                    Contents =
                    [
                        new BlobResourceContents()
                        {
                            Blob = Convert.ToBase64String(content),
                            Uri = uri,
                            MimeType = mimeType,
                        }
                    ],
                };
            }
        };
    }

    /// <summary>
    /// Invokes the resource handler.
    /// </summary>
    /// <param name="context">The MCP server context.</param>
    /// <param name="cancellationToken">The cancellation token.</param>
    /// <returns>The result of the invocation.</returns>
    public async ValueTask<ReadResourceResult> InvokeHandlerAsync(RequestContext<ReadResourceRequestParams> context, CancellationToken cancellationToken)
    {
        if (this._kernelFunction == null)
        {
            this._kernelFunction = KernelFunctionFactory.CreateFromMethod(this.Handler);
        }

        this.Kernel
            ??= context.Server.Services?.GetRequiredService<Kernel>()
            ?? throw new InvalidOperationException("Kernel is not available.");

        KernelArguments args = new()
        {
            { "context", context },
        };

        FunctionResult result = await this._kernelFunction.InvokeAsync(kernel: this.Kernel, arguments: args, cancellationToken: cancellationToken);

        return result.GetValue<ReadResourceResult>() ?? throw new InvalidOperationException("The handler did not return a valid result.");
    }
}
