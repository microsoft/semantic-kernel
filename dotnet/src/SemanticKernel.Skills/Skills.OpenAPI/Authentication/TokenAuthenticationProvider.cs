// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Skills.OpenAPI.Authentication;

/// <summary>
/// Retrieves an access token via the provided delegate and uses it to authentication HTTP requests.
/// </summary>
public class TokenAuthenticationProvider
{
    private readonly Func<Task<string>> _accessToken;

    /// <summary>
    /// Creates an instance of the <see cref="TokenAuthenticationProvider"/> class.
    /// </summary>
    /// <param name="accessToken">Delegate to retrieve the access token.</param>
    public TokenAuthenticationProvider(Func<Task<string>> accessToken)
    {
        this._accessToken = accessToken;
    }

    /// <summary>
    /// Applies the token to the provided HTTP request message.
    /// </summary>
    /// <param name="request">The HTTP request message.</param>
    /// <returns></returns>
    public async Task AuthenticateRequestAsync(HttpRequestMessage request)
    {
        var token = await this._accessToken();
        request.Headers.Authorization = new AuthenticationHeaderValue("Bearer", token);
    }
}
