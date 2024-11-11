// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Plugins.OpenApi;

/// <summary>
/// REST API OAuth Flow.
/// </summary>
[Experimental("SKEXP0040")]
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
#pragma warning disable CS8618 // Non-nullable field must contain a non-null value when exiting constructor. Consider adding the 'required' modifier or declaring as nullable.
    internal RestApiOAuthFlow()
#pragma warning restore CS8618 // Non-nullable field must contain a non-null value when exiting constructor. Consider adding the 'required' modifier or declaring as nullable.
    {
    }
}
