// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;

namespace Microsoft.SemanticKernel.Plugins.OpenApi;

/// <summary>
/// REST API Operation Server.
/// </summary>
public sealed class RestApiOperationServer
{
    /// <summary>
    /// A URL to the target host. This URL supports Server Variables and MAY be relative,
    /// to indicate that the host location is relative to the location where the OpenAPI document is being served.
    /// Variable substitutions will be made when a variable is named in {brackets}.
    /// </summary>
#pragma warning disable CA1056 // URI-like properties should not be strings
    public string? Url { get; }
#pragma warning restore CA1056 // URI-like properties should not be strings

    /// <summary>
    /// A map between a variable name and its value. The value is used for substitution in the server's URL template.
    /// </summary>
    public IDictionary<string, RestApiOperationServerVariable> Variables { get; }

    /// <summary>
    /// Construct a new <see cref="RestApiOperationServer"/> object.
    /// </summary>
    /// <param name="url">URL to the target host</param>
    /// <param name="variables">Substitution variables for the server's URL template</param>
#pragma warning disable CA1054 // URI-like parameters should not be strings
    public RestApiOperationServer(string? url = null, IDictionary<string, RestApiOperationServerVariable>? variables = null)
#pragma warning restore CA1054 // URI-like parameters should not be strings
    {
        this.Url = string.IsNullOrEmpty(url) ? null : url;
        this.Variables = variables ?? new Dictionary<string, RestApiOperationServerVariable>();
    }
}
