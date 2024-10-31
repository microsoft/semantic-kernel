// Copyright (c) Microsoft. All rights reserved.

using Microsoft.OpenApi.Models;

namespace Microsoft.SemanticKernel.Plugins.OpenApi;

/// <summary>
/// REST API OAuth Flows.
/// </summary>
public sealed class RestApiOAuthFlows
{
    /// <summary>
    /// Configuration for the OAuth Implicit flow
    /// </summary>
    public RestApiOAuthFlow? Implicit { get; init; }

    /// <summary>
    /// Configuration for the OAuth Resource Owner Password flow.
    /// </summary>
    public RestApiOAuthFlow? Password { get; init; }

    /// <summary>
    /// Configuration for the OAuth Client Credentials flow.
    /// </summary>
    public RestApiOAuthFlow? ClientCredentials { get; init; }

    /// <summary>
    /// Configuration for the OAuth Authorization Code flow.
    /// </summary>
    public RestApiOAuthFlow? AuthorizationCode { get; init; }

    /// <summary>
    /// Creates an instance of a <see cref="RestApiOAuthFlows"/> class.
    /// </summary>
    /// <param name="flows"></param>
    internal RestApiOAuthFlows(OpenApiOAuthFlows flows)
    {
        this.Implicit = flows.Implicit is not null ? new RestApiOAuthFlow(flows.Implicit) : null;
        this.Password = flows.Password is not null ? new RestApiOAuthFlow(flows.Password) : null;
        this.ClientCredentials = flows.ClientCredentials is not null ? new RestApiOAuthFlow(flows.ClientCredentials) : null;
        this.AuthorizationCode = flows.AuthorizationCode is not null ? new RestApiOAuthFlow(flows.AuthorizationCode) : null;
    }
}
