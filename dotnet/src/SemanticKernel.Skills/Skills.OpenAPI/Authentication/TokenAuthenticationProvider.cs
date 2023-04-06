// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Skills.OpenAPI.Authentication;

/// <summary>
/// Retrieves an access token via the provided delegate and uses it to authenticate HTTP requests.
/// This class implements the <see cref="AuthenticateRequestAsyncCallback"/> delegate.
/// </summary>
public class TokenAuthenticationProvider
{
    private readonly Func<string> _accessToken;

    /// <summary>
    /// Create an instance of the TokenAuthenticationProvider class.
    /// </summary>
    /// <param name="accessToken">Delegate to retrieve the access token.</param>
    public TokenAuthenticationProvider(Func<string> accessToken)
    {
        this._accessToken = accessToken;
    }

    /// <summary>
    /// Apply the token to the provided HTTP request message. The signature of this function matches
    /// the signature of the <see cref="AuthenticateRequestAsyncCallback"/> delegate.
    /// </summary>
    /// <param name="request">The HTTP request message.</param>
    /// <returns></returns>
    public Task AuthenticateRequestAsync(HttpRequestMessage request)
    {
        request.Headers.Authorization = new AuthenticationHeaderValue("Bearer", this._accessToken());
        return Task.CompletedTask;
    }
}
