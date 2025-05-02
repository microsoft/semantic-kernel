// Copyright (c) Microsoft. All rights reserved.

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
    internal RestApiOAuthFlows()
    {
    }

    internal void Freeze()
    {
        this.Implicit?.Freeze();
        this.Password?.Freeze();
        this.ClientCredentials?.Freeze();
        this.AuthorizationCode?.Freeze();
    }
}
