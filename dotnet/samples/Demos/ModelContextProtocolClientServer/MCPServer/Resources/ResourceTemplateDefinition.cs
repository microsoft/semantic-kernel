// Copyright (c) Microsoft. All rights reserved.

using System.Text.RegularExpressions;
using Microsoft.SemanticKernel;
using ModelContextProtocol.Protocol.Types;
using ModelContextProtocol.Server;

namespace MCPServer.Resources;

/// <summary>
/// Represents a resource template definition.
/// </summary>
public sealed class ResourceTemplateDefinition
{
    /// <summary>
    /// The regular expression to match the resource template.
    /// </summary>
    private Regex? _regex = null;

    /// <summary>
    /// The kernel function to invoke the resource template handler.
    /// </summary>
    private KernelFunction? _kernelFunction = null;

    /// <summary>
    /// Gets or sets the MCP resource template.
    /// </summary>
    public required ResourceTemplate ResourceTemplate { get; init; }

    /// <summary>
    /// Gets or sets the handler for the MCP resource template.
    /// </summary>
    public required Delegate Handler { get; init; }

    /// <summary>
    /// Gets or sets the kernel instance to invoke the resource template handler.
    /// If not provided, an instance registered in DI container will be used.
    /// </summary>
    public Kernel? Kernel { get; set; }

    /// <summary>
    /// Checks if the given Uri matches the resource template.
    /// </summary>
    /// <param name="uri">The Uri to check for match.</param>
    public bool IsMatch(string uri)
    {
        return this.GetRegex().IsMatch(uri);
    }

    /// <summary>
    /// Invokes the resource template handler.
    /// </summary>
    /// <param name="context">The MCP server context.</param>
    /// <param name="cancellationToken">The cancellation token.</param>
    /// <returns>The result of the invocation.</returns>
    public async ValueTask<ReadResourceResult> InvokeHandlerAsync(RequestContext<ReadResourceRequestParams> context, CancellationToken cancellationToken)
    {
        this._kernelFunction ??= KernelFunctionFactory.CreateFromMethod(this.Handler);

        this.Kernel
            ??= context.Server.Services?.GetRequiredService<Kernel>()
            ?? throw new InvalidOperationException("Kernel is not available.");

        KernelArguments args = new(source: this.GetArguments(context.Params!.Uri!))
        {
            { "context", context },
        };

        FunctionResult result = await this._kernelFunction.InvokeAsync(kernel: this.Kernel, arguments: args, cancellationToken: cancellationToken);

        return result.GetValue<ReadResourceResult>() ?? throw new InvalidOperationException("The handler did not return a valid result.");
    }

    private Regex GetRegex()
    {
        if (this._regex != null)
        {
            return this._regex;
        }

        var pattern = "^" +
                      Regex.Escape(this.ResourceTemplate.UriTemplate)
                           .Replace("\\{", "(?<")
                           .Replace("}", ">[^/]+)") +
                      "$";

        return this._regex = new(pattern, RegexOptions.Compiled);
    }

    private Dictionary<string, object?> GetArguments(string uri)
    {
        var match = this.GetRegex().Match(uri);
        if (!match.Success)
        {
            throw new ArgumentException($"The uri '{uri}' does not match the template '{this.ResourceTemplate.UriTemplate}'.");
        }

        return match.Groups.Cast<Group>().Where(g => g.Name != "0").ToDictionary(g => g.Name, g => (object?)g.Value);
    }
}
