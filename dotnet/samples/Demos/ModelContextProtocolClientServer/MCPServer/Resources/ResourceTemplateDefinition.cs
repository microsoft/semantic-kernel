// Copyright (c) Microsoft. All rights reserved.

using System.Text.RegularExpressions;
using ModelContextProtocol.Protocol.Types;
using ModelContextProtocol.Server;

namespace MCPServer.Resources;

internal class ResourceTemplateDefinition
{
    private Regex? _regex = null;

    /// <summary>
    /// Gets or sets the MCP resource template.
    /// </summary>
    public required ResourceTemplate ResourceTemplate { get; init; }

    /// <summary>
    /// Gets or sets the handler for the MCP resource template.
    /// </summary>
    public required Func<RequestContext<ReadResourceRequestParams>, IDictionary<string, string>, CancellationToken, Task<ReadResourceResult>> Handler { get; init; }

    /// <summary>
    /// Gets or sets the function that checks if the resource template matches a given Uri.
    /// </summary>
    public bool IsMatch(string uri)
    {
        return this.GetRegex().IsMatch(uri);
    }

    public IDictionary<string, string> GetArguments(string uri)
    {
        var match = this.GetRegex().Match(uri);
        if (!match.Success)
        {
            throw new ArgumentException($"The uri '{uri}' does not match the template '{this.ResourceTemplate.UriTemplate}'.");
        }

        return match.Groups.Cast<Group>().Where(g => g.Name != "0").ToDictionary(g => g.Name, g => g.Value);
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
                    .Replace("}", @">[^/]+)") + "$";

        return this._regex = new(pattern);
    }
}
