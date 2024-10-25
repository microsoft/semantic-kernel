// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using Microsoft.OpenApi.Models;

namespace Microsoft.SemanticKernel.Plugins.OpenApi;

/// <summary>
/// REST API OAuth Flow.
/// </summary>
public sealed class RestApiOAuthFlow
{
    /// <summary>
    /// REQUIRED. The authorization URL to be used for this flow.
    /// Applies to implicit and authorizationCode OAuthFlow.
    /// </summary>
    public Uri AuthorizationUrl { get; init; }

    /// <summary>
    /// REQUIRED. The token URL to be used for this flow.
    /// Applies to password, clientCredentials, and authorizationCode OAuthFlow.
    /// </summary>
    public Uri TokenUrl { get; init; }

    /// <summary>
    /// The URL to be used for obtaining refresh tokens.
    /// </summary>
    public Uri? RefreshUrl { get; init; }

    /// <summary>
    /// REQUIRED. A map between the scope name and a short description for it.
    /// </summary>
    public IReadOnlyDictionary<string, string> Scopes { get; init; }

    /// <summary>
    /// Creates an instance of a <see cref="RestApiOAuthFlow"/> class.
    /// </summary>
    /// <param name="authFlow"></param>
    public RestApiOAuthFlow(OpenApiOAuthFlow authFlow)
    {
        this.AuthorizationUrl = authFlow.AuthorizationUrl;
        this.TokenUrl = authFlow.TokenUrl;
        this.RefreshUrl = authFlow.RefreshUrl;
        this.Scopes = new ReadOnlyDictionary<string, string>(authFlow.Scopes ?? new Dictionary<string, string>());
    }
}
