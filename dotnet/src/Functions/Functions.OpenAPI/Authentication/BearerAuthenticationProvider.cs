// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Functions.OpenAPI.Authentication;

/// <summary>
/// Retrieves a token via the provided delegate and applies it to HTTP requests using the
/// "bearer" authentication scheme.
/// </summary>
public class BearerAuthenticationProvider
{
    private readonly Func<Task<string>> _bearerToken;

    /// <summary>
    /// Creates an instance of the <see cref="BearerAuthenticationProvider"/> class.
    /// </summary>
    /// <param name="bearerToken">Delegate to retrieve the bearer token.</param>
    public BearerAuthenticationProvider(Func<Task<string>> bearerToken)
    {
        this._bearerToken = bearerToken;
    }

    /// <summary>
    /// Applies the token to the provided HTTP request message.
    /// </summary>
    /// <param name="request">The HTTP request message.</param>
    /// <param name="openAIManifestAuth">The <see cref="OpenAIManifestAuthentication"/> used to authenticate.</param>
    public async Task AuthenticateRequestAsync(HttpRequestMessage request, OpenAIManifestAuthentication? openAIManifestAuth = null)
    {
        var token = await this._bearerToken().ConfigureAwait(false);
        request.Headers.Authorization = new AuthenticationHeaderValue("Bearer", token);
    }
}
